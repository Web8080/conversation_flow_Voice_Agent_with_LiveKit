# Local Test Guide

Run the voice agent locally so you can test VAD fixes and capture debug logs.

**Requirement:** Python **3.10+** (livekit-agents needs `TypeAlias` from `typing`). Python 3.9 will fail with `ImportError: cannot import name 'TypeAlias'`.

## 1. Backend (agent)

Create venv with Python 3.10+ and install deps once:

```bash
cd /Users/user/Fortell_AI_Product/backend
# Use Python 3.10 or 3.12 (not 3.9)
python3.10 -m venv venv   # or: python3.12 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Then run the agent:

```bash
cd /Users/user/Fortell_AI_Product/backend
source venv/bin/activate   # Windows: venv\Scripts\activate
python main.py dev
```

- Uses `backend/.env` (LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET, STT/LLM/TTS keys).
- Stage 3 is default; agent will log "Routing to Stage 3 agent".
- Debug logs go to `.cursor/debug.log` in the project root when you speak.

## 2. Frontend (UI)

In a **second terminal**:

```bash
cd /Users/user/Fortell_AI_Product/frontend
npm run dev
```

- Open http://localhost:3000
- Enter a room name (e.g. `test-room`) and click **Connect**
- Allow microphone; speak in full sentences to test VAD (1.8s silence threshold)

## 3. Test and logs

- Say e.g. *"I'd like to book an appointment for tomorrow at 4 p.m."* and pause.
- You should get **one** agent response after you finish (no cutting in, no duplicate replies).
- To inspect runtime: `cat /Users/user/Fortell_AI_Product/.cursor/debug.log` (NDJSON, one line per event).

## Troubleshooting

- **Agent not joining**: Check backend terminal for errors; ensure LIVEKIT_URL is `wss://…` and keys are set.
- **No debug log**: Log file is created when the agent processes audio; speak after connecting.
- **Still cutting in**: Increase `VAD_SILENCE_THRESHOLD_MS` in backend `.env` (e.g. 2200 or 2500).
