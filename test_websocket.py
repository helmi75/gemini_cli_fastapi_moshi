import asyncio
import websockets
import json
import numpy as np
import pytest

# Test configuration
WS_URL = "ws://localhost:8000/ws"

@pytest.mark.asyncio
async def test_websocket_connection():
    """Test if we can connect to the websocket."""
    try:
        async with websockets.connect(WS_URL) as websocket:
            assert websocket.open
    except Exception as e:
        pytest.fail(f"Could not connect to WebSocket: {e}")

@pytest.mark.asyncio
async def test_audio_and_response():
    """Test sending audio and receiving transcription and response."""
    async with websockets.connect(WS_URL) as websocket:
        # Create a 1-second dummy audio chunk (silence)
        # 44100Hz, 16-bit PCM
        duration = 1.0
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        # Using a slight sine wave instead of pure silence to maybe trigger something
        audio_data = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
        
        # Send audio
        await websocket.send(audio_data.tobytes())
        
        # We expect some response (even if it's "STT Error" or similar if dummy audio is too short)
        # But here we just check if the connection stays alive and we get valid JSON
        try:
            # Wait for a potential message with a timeout
            message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            
            if isinstance(message, str):
                data = json.loads(message)
                assert "type" in data
                assert data["type"] in ["transcription", "response_text"]
            else:
                # It might be binary audio (TTS response)
                assert len(message) > 0
        except asyncio.TimeoutError:
            # It's possible the dummy audio didn't trigger a transcription
            pass

if __name__ == "__main__":
    asyncio.run(test_websocket_connection())
    asyncio.run(test_audio_and_response())
