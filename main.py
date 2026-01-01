import os
import asyncio
import logging
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

# Lazy loading to avoid delay on startup if GPU models take time
engine = None
rag_service = None

def get_engine():
    global engine
    if engine is None:
        engine = AudioEngine()
    return engine

def get_rag_service():
    global rag_service
    if rag_service is None:
        rag_service = VertexRAGService()
    return rag_service

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get():
    return FileResponse("static/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Client connected via WebSocket")
    
    # Initialize services
    eng = get_engine()
    rag = get_rag_service()
    
    try:
        while True:
            # 1. Receive Binary Audio Chunk (PCM 16-bit)
            audio_chunk = await websocket.receive_bytes()
            
            # 2. STT (Whisper) - Default to 44.1kHz if unknown, browser usually provides this
            # In a production app, we might send the sample rate in a header or first packet
            text_input = eng.speech_to_text(audio_chunk, input_sr=44100)
            
            if not text_input or len(text_input) < 2:
                continue
                
            logger.info(f"User: {text_input}")
            
            # Send the transcribed text back to UI for feedback
            await websocket.send_json({"type": "transcription", "text": text_input})
            
            # 3. RAG + LLM (Vertex AI)
            response_text = await rag.query(text_input)
            logger.info(f"Assistant: {response_text}")
            
            # Send the response text back to UI
            await websocket.send_json({"type": "response_text", "text": response_text})
            
            # 4. TTS (Local GPU) + Streaming Back
            # We send audio in a specific format (e.g., float32 PCM at 24000Hz)
            for audio_pcm in eng.text_to_speech_stream(response_text):
                await websocket.send_bytes(audio_pcm)
                
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error in websocket loop: {e}")
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    # Use 0.0.0.0 for docker compatibility
    uvicorn.run(app, host="0.0.0.0", port=8000)
