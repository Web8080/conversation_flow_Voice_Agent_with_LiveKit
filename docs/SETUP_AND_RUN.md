# Setup and Run Guide

This guide walks you through setting up and running the Voice Agent system.

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose (optional, for containerized deployment)
- LiveKit Cloud account
- OpenAI API key (for STT/TTS)
- Ollama (optional, for local LLM)

## Quick Start

### 1. Clone and Navigate

```bash
cd /Users/user/Fortell_AI_Product
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your credentials (see services/SERVICES_SETUP.md)
nano .env # or use your preferred editor
```

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Edit .env.local with your LiveKit URL
nano .env.local # or use your preferred editor
```

### 4. Configure Environment Variables

See `services/SERVICES_SETUP.md` for detailed instructions on obtaining API keys.

Minimum required configuration:
- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `OPENAI_API_KEY` (for STT/TTS)

Optional:
- Install Ollama for local LLM: https://ollama.ai/
- Add `GROQ_API_KEY` for fast LLM alternative

### 5. Run the System

#### Option A: Local Development

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python main.py dev
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - Ollama (if using local LLM):**
```bash
ollama serve
# In another terminal:
ollama pull llama3.2
```

#### Option B: Docker Compose

```bash
# From project root
docker-compose up
```

This will start:
- Backend agent
- Ollama (local LLM)
- Frontend (Next.js)

### 6. Access the Application

- Frontend: http://localhost:3000
- Connect to a LiveKit room using the UI

## Development Workflow

### Testing the Agent

1. Start backend agent
2. Start frontend
3. Open http://localhost:3000
4. Enter room name (e.g., "test-room")
5. Click "Connect"
6. Allow microphone permissions
7. Start speaking - agent will respond

### Testing State Machine

The agent follows this flow:
1. **Greeting**: Agent introduces itself
2. **Collect Date**: Asks for appointment date
3. **Collect Time**: Asks for appointment time
4. **Confirmation**: Confirms details
5. **Terminal**: Ends conversation

### Running Training Scripts

```bash
cd backend/scripts
python train_prompts.py
python optimize_conversation.py
```

## Troubleshooting

### Backend Issues

**Error: "OpenAI API key not configured"**
- Check `.env` file has `OPENAI_API_KEY` set
- Verify the key is valid

**Error: "Ollama connection failed"**
- Ensure Ollama is running: `ollama list`
- Check `OLLAMA_BASE_URL` in `.env`
- Default: `http://localhost:11434`

**Error: "LiveKit connection failed"**
- Verify `LIVEKIT_URL` format (must start with `wss://`)
- Check API key and secret are correct
- Ensure room creation permissions are enabled

### Frontend Issues

**Error: "Failed to connect to room"**
- Check `NEXT_PUBLIC_LIVEKIT_URL` in `.env.local`
- Verify LiveKit credentials in API route
- Check browser console for detailed errors

**Microphone not working**
- Check browser permissions
- Ensure HTTPS (required for microphone access)
- Try in different browser

### Common Issues

**High latency**
- Check network connection
- Verify API keys are for correct regions
- Consider using Groq for faster LLM responses

**Agent not responding**
- Check backend logs for errors
- Verify all services (STT, LLM, TTS) are working
- Check LiveKit room has active participants

## Production Deployment

### Backend (LiveKit Cloud)

1. Build Docker image
2. Push to container registry
3. Deploy to LiveKit Cloud using their dashboard
4. Configure environment variables in LiveKit Cloud

### Frontend (Vercel)

1. Connect GitHub repository to Vercel
2. Configure environment variables:
 - `NEXT_PUBLIC_LIVEKIT_URL`
 - `LIVEKIT_API_KEY` (server-side)
 - `LIVEKIT_API_SECRET` (server-side)
3. Deploy

See deployment guides in `services/SERVICES_SETUP.md` for more details.

## Next Steps

1. **Sign up for services** (see `services/SERVICES_SETUP.md`)
2. **Configure API keys** in `.env` files
3. **Test locally** with the frontend
4. **Customize prompts** using training scripts
5. **Deploy to production** when ready

## Support

- Check logs: Backend logs appear in terminal, frontend logs in browser console
- Review documentation: `VOICE_AGENT_DESIGN.md` for architecture
- Service setup: `services/SERVICES_SETUP.md` for API configuration