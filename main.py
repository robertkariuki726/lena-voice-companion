"""
Lena — desktop voice companion.

Voice mode (default):
    Press and HOLD the SPACE bar to talk. Release to send.
    While Lena is speaking, press SPACE to interrupt her mid-sentence.
    Press ESC to quit.

Text mode (for testing without a mic):
    python main.py --text

Architecture:
    mic -> faster-whisper (local STT) -> Base44 Agent API (Lena's brain:
    personality, tools, memory) -> edge-tts (neural TTS) -> speakers
"""
import sys

import keyboard

from config import settings
from agent_client import AgentClient
from recorder import Recorder
from transcriber import Transcriber
from speaker import Speaker

BANNER = r"""
   _                 _
  | |    ___   ___  | |     _   _ _ __
  | |   / _ \ / _ \ | |____| | | | '_ \
  | |__| (_) | (_) | |____| |_| | | | |
  |_____\___/ \___/|_|     \__,_|_| |_|

  Hold SPACE to talk. Release to send. SPACE interrupts me. ESC quits.
"""


class Lena:
    def __init__(self, text_mode=False):
        self.text_mode = text_mode
        self.agent = AgentClient(
            api_key=settings.BASE44_API_KEY,
            agent_id=settings.AGENT_ID,
            base_url=settings.API_BASE_URL,
            session_file=settings.SESSION_FILE,
        )
        self.recorder = Recorder(sample_rate=settings.SAMPLE_RATE)
        self.speaker = Speaker(voice=settings.TTS_VOICE)
        self.transcriber = None          # lazy-loaded: whisper takes a moment
        self._recording = False

    # ------------------------------------------------------------------ #

    def start(self):
        print(BANNER)
        print("[lena] Connecting to my brain on Base44...")
        cid = self.agent.ensure_conversation()
        print(f"[lena] Connected. Conversation: {cid}")
        print("[lena] You can talk to me about anything — jobs, ideas, life. "
              "Say \"remember that...\" and I'll keep it.\n")

        if self.text_mode:
            self._text_loop()
        else:
            self._voice_loop()

    # ------------------------------------------------------------------ #
    # Voice mode
    # ------------------------------------------------------------------ #

    def _voice_loop(self):
        # We need the mic, so warm up STT now (loads the whisper model).
        if self.transcriber is None:
            self.transcriber = Transcriber(
                model_size=settings.WHISPER_MODEL,
                device=settings.WHISPER_DEVICE,
                compute_type=settings.WHISPER_COMPUTE,
            )
        print("[lena] Listening. Hold SPACE and talk to me.\n")

        def on_press(event):
            if event.name != "space":
                return
            # Barge-in: silence me mid-sentence if I'm speaking.
            if self.speaker._stop and not self._recording:
                self.speaker.stop()
            if not self._recording:
                self._recording = True
                self.recorder.start()
                print("\n[you] ... (recording)")

        def on_release(event):
            if event.name != "space" or not self._recording:
                return
            self._recording = False
            audio = self.recorder.stop()
            self._handle_utterance(audio)

        keyboard.on_press(on_press)
        keyboard.on_release(on_release)
        print("[lena] Press ESC to quit.")
        keyboard.wait("esc")
        print("\n[lena] Talk soon. I'll remember where we left off.")

    def _handle_utterance(self, audio):
        text = self.transcriber.transcribe(audio, sample_rate=settings.SAMPLE_RATE)
        if not text.strip():
            print("[lena] (didn't catch that — hold SPACE a bit longer)")
            return
        print(f"[you] {text}")
        self._respond(text)

    # ------------------------------------------------------------------ #
    # Shared response path
    # ------------------------------------------------------------------ #

    def _respond(self, text):
        try:
            print("[lena] (thinking...)")
            reply = self.agent.send_message(text)
        except Exception as exc:
            print(f"[lena] Connection hiccup: {exc}")
            self.speaker.speak("Sorry, I couldn't reach my brain just now. Give it a second and try again.")
            return
        print(f"[lena] {reply}\n")
        if not self.text_mode:
            try:
                self.speaker.speak(reply)
            except Exception as exc:
                print(f"[lena] (voice failed, check internet: {exc})")

    # ------------------------------------------------------------------ #
    # Text mode
    # ------------------------------------------------------------------ #

    def _text_loop(self):
        print("[lena] Text mode. Type 'exit' to quit.\n")
        while True:
            try:
                text = input("[you] ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not text:
                continue
            if text.lower() in ("exit", "quit"):
                break
            self._respond(text)


def main():
    text_mode = "--text" in sys.argv
    try:
        Lena(text_mode=text_mode).start()
    except KeyboardInterrupt:
        print("\n[lena] Bye for now.")


if __name__ == "__main__":
    main()
