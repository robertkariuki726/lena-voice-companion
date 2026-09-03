"""
Microphone capture — push-to-talk.

Records 16 kHz mono float32 audio using sounddevice's PortAudio backend.
Works on Windows / macOS / Linux with any default microphone.
"""
import threading
import numpy as np
import sounddevice as sd


class Recorder:
    def __init__(self, sample_rate=16000):
        self.sr = sample_rate
        self._stream = None
        self._blocks = []
        self._lock = threading.Lock()

    def _callback(self, indata, frames, time_info, status):
        if status:
            print(f"[audio] {status}")
        with self._lock:
            self._blocks.append(indata.copy())

    def start(self):
        """Begin capturing from the default microphone."""
        self._blocks = []
        self._stream = sd.InputStream(
            samplerate=self.sr,
            channels=1,
            dtype="float32",
            blocksize=2048,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self):
        """Stop capturing and return the recorded audio (float32, mono)."""
        if self._stream is None:
            return np.empty(0, dtype=np.float32)
        self._stream.stop()
        self._stream.close()
        self._stream = None
        with self._lock:
            if not self._blocks:
                return np.empty(0, dtype=np.float32)
            audio = np.concatenate(self._blocks, axis=0).flatten()
            self._blocks = []
        return audio
