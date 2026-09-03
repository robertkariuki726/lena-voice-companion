"""
Speech-to-text — local and free with faster-whisper.

The model runs entirely on your PC, so nothing you say leaves the machine
until you choose to send the transcript to Lena. The first run downloads the
model (~150 MB for 'base'); after that it's instant and works offline.

Models (set WHISPER_MODEL in .env):
    tiny   -> fastest, lower accuracy   (~75 MB)
    base   -> good balance (default)    (~145 MB)
    small  -> more accurate, slower     (~490 MB)
"""
from faster_whisper import WhisperModel


class Transcriber:
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        print(f"[stt] Loading Whisper model '{model_size}' "
              f"(first run downloads it, please wait)...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("[stt] Ready.")

    def transcribe(self, audio_float32, sample_rate=16000):
        """Transcribe float32 mono audio at 16 kHz. Returns plain text."""
        if audio_float32 is None or len(audio_float32) == 0:
            return ""
        segments, _info = self.model.transcribe(
            audio_float32,
            language="en",
            vad_filter=True,           # trims silence so short presses don't hallucinate
            beam_size=5,
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return text
