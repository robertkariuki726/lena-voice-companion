"""
Lena — personal voice companion for Robert.
Configuration loaded from .env (see .env.example).
"""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

def _env(name, default=None, required=False):
    val = os.getenv(name, default)
    if required and not val:
        raise SystemExit(
            f"Missing {name} in your .env file. "
            "Copy .env.example to .env and fill it in."
        )
    return val


@dataclass
class Settings:
    # --- Base44 Agent API (Lena's brain) ---
    BASE44_API_KEY: str = field(default_factory=lambda: _env("BASE44_API_KEY", required=True))
    AGENT_ID: str = field(default_factory=lambda: _env(
        "BASE44_AGENT_ID", "6a0ebc236c3234fc81a8acf3"))
    API_BASE_URL: str = field(default_factory=lambda: _env(
        "BASE44_API_URL", "https://app.base44.com"))

    # --- Voice ---
    TTS_VOICE: str = field(default_factory=lambda: _env("TTS_VOICE", "en-US-JennyNeural"))
    TTS_RATE: str = field(default_factory=lambda: _env("TTS_RATE", "+0%"))

    # --- Speech-to-text (local, free, private) ---
    WHISPER_MODEL: str = field(default_factory=lambda: _env("WHISPER_MODEL", "base"))
    WHISPER_DEVICE: str = field(default_factory=lambda: _env("WHISPER_DEVICE", "cpu"))
    WHISPER_COMPUTE: str = field(default_factory=lambda: _env("WHISPER_COMPUTE", "int8"))

    # --- Audio capture ---
    SAMPLE_RATE: int = field(default_factory=lambda: int(_env("SAMPLE_RATE", "16000")))

    # --- Session persistence (keeps the same Base44 conversation alive) ---
    SESSION_FILE: str = "session.json"


settings = Settings()
