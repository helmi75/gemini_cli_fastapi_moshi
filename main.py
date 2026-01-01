import os
import asyncio
import logging
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from audio_engine import AudioEngine
from vertex_rag import VertexRAGService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances for models
engine = None
rag_service = None

@app.on_event("startup")
async def startup_event():
    global engine, rag_service
    logger.info("Starting up: Loading models...")
    loop = asyncio.get_running_loop()
    # Initialize models in threads to keep the loop responsive
    engine = await loop.run_in_executor(None, AudioEngine)
    rag_service = await loop.run_in_executor(None, VertexRAGService)
    logger.info("Models loaded successfully.")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get():
    return FileResponse("static/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected via WebSocket")
    
    audio_buffer = bytearray()
    history = []
    
    try:
        while True:
            # Receive any message (bytes or text)
            # We use the generic receive() but handle the disconnect type explicitly
            message = await websocket.receive()
            
            if message["type"] == "websocket.disconnect":
                logger.info("Client sent disconnect message")
                break

            if "bytes" in message:
                audio_buffer.extend(message["bytes"])
                
            elif "text" in message:
                try:
                    data = json.loads(message["text"])
                except json.JSONDecodeError:
                    continue

                if data.get("type") == "end_of_speech":
                    if len(audio_buffer) == 0:
                        continue
                        
                    logger.info(f"Processing audio buffer: {len(audio_buffer)} bytes")
                    current_audio = bytes(audio_buffer)
                    audio_buffer = bytearray() # Reset buffer
                    
                    # 1. STT
                    text_input = await asyncio.to_thread(engine.speech_to_text, current_audio, 44100)
                    
                    if not text_input or len(text_input) < 2:
                        logger.info("No speech detected.")
                        continue
                        
                    logger.info(f"User: {text_input}")
                    await websocket.send_json({"type": "transcription", "text": text_input})
                    
                    # 2. RAG + LLM
                    response_text = await asyncio.to_thread(rag_service.query, text_input, history)
                    logger.info(f"Assistant: {response_text}")
                    
                    history.append(f"Utilisateur: {text_input}")
                    history.append(f"Assistant: {response_text}")
                    if len(history) > 10: history = history[-10:]
                        
                    await websocket.send_json({"type": "response_text", "text": response_text})
                    
                    # 3. TTS (if available)
                    if engine.tts:
                        try:
                            for audio_pcm in engine.text_to_speech_stream(response_text):
                                await websocket.send_bytes(audio_pcm)
                                await asyncio.sleep(0.01)
                        except Exception as e:
                            logger.error(f"TTS Error: {e}")

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected normally")
    except Exception as e:
        logger.error(f"Error in websocket loop: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    ssl_key_path = "secrets/ssl_key.pem"
    ssl_cert_path = "secrets/ssl_cert.pem"
    
    if os.path.exists(ssl_key_path) and os.path.exists(ssl_cert_path):
        logger.info("Starting in HTTPS mode")
        uvicorn.run(app, host="0.0.0.0", port=8000, ssl_keyfile=ssl_key_path, ssl_certfile=ssl_cert_path)
    else:
        logger.info("Starting in HTTP mode")
        uvicorn.run(app, host="0.0.0.0", port=8000)