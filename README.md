# Lena — Personal Voice Companion

A desktop voice assistant that talks to **you** the way a friend would — because
behind it is Lena, a real AI agent living on Base44 with persistent memory, your
calendar, your Gmail, your job-search automations, and her own personality.
This app is just her **voice**.

```
                 ┌────────────────────────────────────┐
                 │       LENA (Base44 Superagent)     │
                 │  personality · tools · memory      │
                 └──────────────▲─────────────────────┘
                                │ Base44 Agent API
 mic ──► faster-whisper ──► text ┴─► reply text ──► edge-tts ──► speakers
 (hold        local STT,                │
  SPACE)      free & private            └─ she remembers it, can act on it:
                                          calendar, email, notes, web, reminders
```

## Features

- **Push-to-talk**: hold `SPACE`, speak naturally, release to send.
- **Barge-in**: press `SPACE` while she's talking and she stops instantly.
- **Persistent memory**: the conversation id is saved to `session.json`, and
  Lena's long-term memory lives on Base44 — she remembers across sessions.
  Say *"remember that I love road trips"* and she keeps it. Say *"what do you
  remember about me?"* and she'll tell you. Say *"don't remember that"* and
  she deletes it.
- **Her tools work over voice**: "check my calendar for tomorrow",
  "did anyone reply to my job applications?", "remind me to email Belfor at 4".
- **Free to run**: STT is local (faster-whisper), TTS is Microsoft's free
  edge-tts. No OpenAI/Anthropic bills.

## Setup (Windows / macOS / Linux, Python 3.9+)

```bash
# 1. Get the code onto your PC and enter the folder
cd lena-companion

# 2. Create a virtual environment and install everything
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

# 3. Configure
copy .env.example .env      # (macOS/Linux: cp .env.example .env)
```

Open `.env` and set `BASE44_API_KEY` — get it from the **Lena agent editor**:
**Settings → Developer / API Docs panel** (that panel also shows the exact API
base URL and full request reference if anything ever needs adjusting).

## Run

```bash
python main.py          # voice mode (hold SPACE to talk, ESC to quit)
python main.py --text   # text mode — same brain, no mic needed
```

First voice run downloads the Whisper model (~150 MB, one time).

> **Linux note:** the `keyboard` library needs root for global hotkeys —
> run with `sudo`, or just use `--text` mode.
> **No internet note:** STT works offline, but edge-tts and the agent API
> need a connection.

## Project structure

```
lena-companion/
├── main.py           # the conversation loop + hotkeys
├── config.py         # settings from .env
├── agent_client.py   # Base44 Agent API client (Lena's brain)
├── recorder.py       # microphone capture (sounddevice)
├── transcriber.py    # local speech-to-text (faster-whisper)
├── speaker.py        # neural TTS with interrupt support (edge-tts)
├── requirements.txt
├── .env.example
└── session.json      # created at runtime — keeps the conversation alive
```

## Roadmap

- [x] **Phase 1 — Voice conversation** (this version)
- [x] **Phase 2 — Personality** — lives on Base44 (identity + soul, editable)
- [x] **Phase 3 — Memory** — separate short-term conversation vs persistent
      long-term memory, with user control (remember / show / forget)
- [x] **Phase 4 — Tools** — calendar, email, notes, web, reminders are already
      part of the agent; voice just unlocks them
- [ ] **Phase 5 — Full-duplex real-time** — continuous listening with VAD and
      wake word instead of push-to-talk
- [ ] **Phase 6 — Phone** — WhatsApp voice notes (already possible) and a
      mobile client

## Design notes

- Your **voice never leaves your PC** until it's text, and only the text you
  choose to send reaches Lena.
- Lena is a **consistent AI companion, not a fake human** — and her design
  brief explicitly says she nudges you toward real people and opportunities,
  not away from them.
- Want her to sound different? Change `TTS_VOICE` in `.env`
  (`python -m edge_tts --list-voices`).
