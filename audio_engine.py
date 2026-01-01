import torch
import numpy as np
from faster_whisper import WhisperModel
from TTS.api import TTS
import io
import soundfile as sf
import os
import librosa

class AudioEngine:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compute_type = "float16" if self.device == "cuda" else "int8"
        
        # Accept Coqui TOS
        os.environ["COQUI_TOS_AGREED"] = "1"
        
        print(f"Initializing AudioEngine on {self.device}...")
        
        # 1. Load Whisper Turbo (STT)
        print("Loading Whisper Turbo...")
        try:
            self.stt_model = WhisperModel("large-v3-turbo", device=self.device, compute_type=self.compute_type)
        except Exception as e:
            print(f"Failed to load Whisper model: {e}")
            self.stt_model = None
        
        # 2. Load XTTS v2 (TTS)
        print("Loading XTTS v2...")
        try:
            self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
        except Exception as e:
            print(f"Failed to load XTTS model: {e}")
            self.tts = None
            
        self.speaker_wav = "static/reference.wav"
        if not os.path.exists(self.speaker_wav):
            print(f"Warning: Speaker reference {self.speaker_wav} not found. Using default voice.")

    def speech_to_text(self, audio_bytes: bytes, input_sr: int = 44100) -> str:
        if not self.stt_model:
            return "STT model not loaded."
            
        # Convert bytes to numpy array (Int16 to Float32)
        audio_data = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Resample to 16kHz if necessary
        if input_sr != 16000:
            audio_data = librosa.resample(audio_data, orig_sr=input_sr, target_sr=16000)
        
        try:
            # language="fr" for French transcription
            segments, _ = self.stt_model.transcribe(audio_data, beam_size=1, language="fr")
            text = "".join([s.text for s in segments])
            return text.strip()
        except Exception as e:
            print(f"STT Error: {e}")
            return ""

    def text_to_speech_stream(self, text: str):
        if not self.tts:
            print("TTS model not loaded.")
            return

        try:
            # language="fr" for French synthesis
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
