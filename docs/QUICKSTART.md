# Quick Start Guide

Get the Voice Agent running in 5 minutes.

## Step 1: Set Up Services

Read `services/SERVICES_SETUP.md` and sign up for:
- LiveKit Cloud (free tier)
- OpenAI (for STT/TTS - $5 free credit)
- Ollama (optional, install locally - free)

## Step 2: Configure Environment

```bash
# Backend
cd backend
cp .env.example .env
# Edit .env with your API keys

# Frontend 
cd ../frontend
cp .env.example .env.local
# Edit .env.local with your LiveKit URL
```

## Step 3: Run the System

### Option A: Use Launch Script (Recommended)

```bash
./launch.sh
```

### Option B: Manual Start

**Terminal 1:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py dev
```

**Terminal 2:**
```bash
cd frontend
npm install
npm run dev
```

**Terminal 3 (Optional - for local LLM):**
```bash
ollama serve
ollama pull llama3.2
```

## Step 4: Test

1. Open http://localhost:3000
2. Enter room name (e.g., "test")
3. Click "Connect"
4. Allow microphone access
5. Say: "Hello, my name is John"
6. Agent should respond and guide you through appointment scheduling

## Troubleshooting

**"API key not found"**
→ Check `.env` files are configured correctly

**"Cannot connect to LiveKit"**
→ Verify `LIVEKIT_URL` starts with `wss://`

**"Microphone not working"**
→ Check browser permissions, try HTTPS

**"Ollama connection failed"**
→ Ensure Ollama is running: `ollama list`

## Next Steps

- Customize prompts in `backend/agent/state_machine/state.py`
- Train prompts: `python backend/scripts/train_prompts.py`
- Deploy: See `SETUP_AND_RUN.md`

For detailed setup, see `SETUP_AND_RUN.md`.