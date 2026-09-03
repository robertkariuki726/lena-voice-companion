"""
Text-to-speech — free Microsoft Edge neural voices via edge-tts, decoded and
played through sounddevice with INTERRUPT support: while Lena is speaking,
pressing the talk key stops playback instantly (barge-in).

Voice options to try in .env (TTS_VOICE):
    en-US-JennyNeural   warm, friendly female   (default — 'Lena')
    en-US-AriaNeural    natural female
    en-GB-SoniaNeural   British female
    en-US-GuyNeural     male

Full voice list: `python -m edge_tts --list-voices`
"""
import asyncio
import os
import tempfile
import threading
import time

import numpy as np
import sounddevice as sd
import edge_tts
import miniaudio


class Speaker:
    def __init__(self, voice="en-US-JennyNeural", rate="+0%"):
        self.voice = voice
        self.rate = rate
        self._stop = threading.Event()

    def stop(self):
        """Interrupt playback immediately (called by the hotkey handler)."""
        self._stop.set()

    def speak(self, text):
        """Synthesize and play `text`. Blocks until done or interrupted."""
        if not text.strip():
            return
        self._stop.clear()
        mp3_bytes = self._synthesize(text)
        samples, sr = self._decode(mp3_bytes)
        self._play(samples, sr)

    # ------------------------------------------------------------------ #

    def _synthesize(self, text):
        """Generate MP3 audio bytes with edge-tts (needs internet)."""
        async def run():
            chunks = []
            communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    chunks.append(chunk["data"])
            return b"".join(chunks)

        audio = asyncio.run(run())
        if not audio:
            raise RuntimeError("edge-tts returned no audio. Check your internet connection.")
        return audio

    def _decode(self, mp3_bytes):
        """Decode MP3 to mono float32 samples using miniaudio (no ffmpeg needed)."""
        decoded = miniaudio.decode(
            mp3_bytes,
            nchannels=1,
            output_format=miniaudio.SampleFormat.FLOAT32,
            sample_rate=24000,
        )
        samples = np.array(decoded.samples, dtype=np.float32)
        return samples, decoded.sample_rate

    def _play(self, samples, sample_rate):
        """Play samples in small chunks so we can stop instantly mid-sentence."""
        chunk = 4096
        with sd.OutputStream(samplerate=sample_rate, channels=1, dtype="float32") as stream:
            for i in range(0, len(samples), chunk):
                if self._stop.is_set():
                    return  # interrupted — barge-in wins
                stream.write(samples[i:i + chunk])
                time.sleep(0)  # yield
