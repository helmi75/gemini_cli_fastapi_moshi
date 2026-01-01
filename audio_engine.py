import torch
import numpy as np
from faster_whisper import WhisperModel
import io
import soundfile as sf
import os
import librosa
import functools

# Monkeypatch torch.load for compatibility with Coqui TTS and PyTorch 2.6+
orig_load = torch.load
def patched_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return orig_load(*args, **kwargs)
torch.load = patched_load

from TTS.api import TTS

class AudioEngine:
    def __init__(self):
        self.device = "cpu" 
        self.compute_type = "int8"
        os.environ["COQUI_TOS_AGREED"] = "1"
        
        print(f"Initializing AudioEngine on {self.device}...")
        
        print("Loading Whisper Turbo...")
        try:
            self.stt_model = WhisperModel("tiny", device=self.device, compute_type=self.compute_type)
        except Exception as e:
            print(f"Failed to load Whisper model: {e}")
            self.stt_model = None
        
        print("Loading XTTS v2...")
        try:
            self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
        except Exception as e:
            print(f"Failed to load XTTS model: {e}")
            self.tts = None
            
        self.speaker_wav = "static/reference.wav"

    def speech_to_text(self, audio_bytes: bytes, input_sr: int = 44100) -> str:
        if not self.stt_model: return "STT model not loaded."
        audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        if input_sr != 16000:
            audio_data = librosa.resample(audio_data, orig_sr=input_sr, target_sr=16000)
        try:
            segments, _ = self.stt_model.transcribe(audio_data, beam_size=1, language="fr")
            text = "".join([s.text for s in segments])
            return text.strip()
        except Exception as e:
            print(f"STT Error: {e}")
            return ""

    def text_to_speech_stream(self, text: str):
        if not self.tts: return
        try:
            chunks = self.tts.tts_stream(
                text=text,
                language="fr",
                speaker_wav=self.speaker_wav if os.path.exists(self.speaker_wav) else None,
                stream_chunk_size=20
            )
            for chunk in chunks:
                yield chunk.cpu().numpy().tobytes()
        except Exception as e:
            print(f"TTS Error: {e}")
