# LiveKit Backend Deployment Guide

## Current Status

**Frontend (Vercel)**: ✅ Deployed and live
- URL: https://conversation-flow-voice-agent-with.vercel.app
- Environment variables: ✅ All 3 LiveKit variables configured
- OpenAI API Key: ❌ NOT needed (frontend only connects to LiveKit)

**Backend (LiveKit Cloud)**: ⏳ Needs deployment
- Environment variables: Need to be configured in LiveKit Cloud
- OpenAI API Key: ✅ REQUIRED (for STT/LLM/TTS processing)

---

## Why OpenAI Key is NOT in Vercel

The **frontend** (Vercel) only needs LiveKit credentials because:

1. **Frontend responsibilities**:
   - User interface (UI)
   - Connect to LiveKit rooms
   - Generate LiveKit access tokens
   - Display conversation messages
   - Handle microphone/speaker controls

2. **Frontend does NOT**:
   - Process audio (no STT)
   - Generate responses (no LLM)
   - Synthesize speech (no TTS)

3. **Backend responsibilities** (LiveKit Cloud agent):
   - Join LiveKit rooms
   - Receive audio from users
   - Transcribe audio (STT) → Uses OpenAI
   - Generate responses (LLM) → Uses OpenAI
   - Synthesize speech (TTS) → Uses OpenAI
   - Send audio back to room

**Architecture**:
```
User Browser (Vercel)
    ↓ [audio via LiveKit]
LiveKit Cloud
    ↓ [routes to backend agent]
Backend Agent (LiveKit Cloud) ← OpenAI API key needed here
    ↓ [uses OpenAI for STT/LLM/TTS]
OpenAI APIs
```

---

## Next Step: Deploy Backend to LiveKit Cloud

The **backend agent** needs to be deployed to LiveKit Cloud so it can:
1. Join rooms when users connect
2. Process voice interactions (STT → LLM → TTS)
3. Respond to users

## Important Note

The interface you see in LiveKit Cloud dashboard (with "Instructions", "Models & Voice" tabs) is for **LiveKit's built-in AI agents** (configured through UI). 

**Our backend uses custom Python code** that needs to be deployed as a **worker service** to a cloud provider (Railway, Render, AWS, etc.), not through LiveKit Cloud's dashboard.

See `docs/DEPLOYMENT_STEP_BY_STEP.md` for detailed deployment instructions.

---

### Option 1: Deploy to Cloud Provider (Recommended)

**Recommended: Railway or Render** (easiest setup)

1. **Go to Railway.app or Render.com**:
   - Sign up/login
   - Create new project
   - Connect GitHub repository

2. **Configure Deployment**:
   - **Root Directory**: Set to `backend/` (if deploying from repo root)
   - **Build Command**: `docker build -t voice-agent .` (or auto-detect Dockerfile)
   - **Start Command**: `python main.py dev`
   - **Environment Variables**: Add these:

```
LIVEKIT_URL=wss://voiceagent007-fnileh5c.livekit.cloud
LIVEKIT_API_KEY=YOUR_LIVEKIT_API_KEY
LIVEKIT_API_SECRET=YOUR_LIVEKIT_API_SECRET
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
LLM_PROVIDER=openai
STT_PROVIDER=openai
TTS_PROVIDER=openai
```

4. **Deploy**:
   - Click "Deploy" or "Save"
   - Wait for deployment to complete
   - Check logs to verify agent is running

### Option 2: Deploy via LiveKit CLI (Alternative)

1. **Install LiveKit CLI** (if not installed):
   ```bash
   npm install -g livekit-cli
   # or
   pip install livekit-cli
   ```

2. **Authenticate**:
   ```bash
   livekit-cli login
   # Enter your LiveKit Cloud credentials
   ```

3. **Deploy Agent**:
   ```bash
   cd backend
   livekit-cli deploy \
     --name voice-agent \
     --env LIVEKIT_URL=wss://voiceagent007-fnileh5c.livekit.cloud \
     --env LIVEKIT_API_KEY=YOUR_LIVEKIT_API_KEY \
     --env LIVEKIT_API_SECRET=YOUR_LIVEKIT_API_SECRET \
     --env OPENAI_API_KEY=YOUR_OPENAI_API_KEY \
     --env LLM_PROVIDER=openai \
     --env STT_PROVIDER=openai \
     --env TTS_PROVIDER=openai \
     .
   ```

### Option 3: Deploy via Docker to Cloud Provider

1. **Build Docker Image**:
   ```bash
   cd backend
   docker build -t voice-agent-backend .
   ```

2. **Push to Container Registry** (Docker Hub, GCR, ECR, etc.)

3. **Deploy to LiveKit Cloud** or use LiveKit's agent deployment feature

---

## Testing End-to-End

Once backend is deployed:

1. **Open Frontend**: https://conversation-flow-voice-agent-with.vercel.app
2. **Enter Room Name**: e.g., "test-room"
3. **Click "Connect"**
4. **Allow Microphone Permissions**
5. **Speak**: "Hello, how are you?"
6. **Wait for Agent Response**: Should hear synthesized response

### Troubleshooting

**"Agent not responding"**:
- Check backend agent is deployed and running
- Check backend logs in LiveKit Cloud dashboard
- Verify environment variables are set correctly
- Verify OpenAI API key is valid

**"Connection failed"**:
- Verify LiveKit URL is correct in both frontend and backend
- Check LiveKit API key/secret are correct
- Check browser console for errors

**"No audio response"**:
- Check backend logs for errors
- Verify OpenAI API key is valid and has credits
- Check STT/TTS service initialization in logs

---

## Environment Variables Summary

### Vercel (Frontend) - ✅ Already Configured
```
NEXT_PUBLIC_LIVEKIT_URL=wss://voiceagent007-fnileh5c.livekit.cloud
LIVEKIT_API_KEY=APIjAbndhXSoyis
LIVEKIT_API_SECRET=D1pm5XYaXHUJe3iiIjU7Uk5fo7n1ebU2WcBIKDy5sGRA
```

### LiveKit Cloud (Backend) - ⏳ Need to Configure
```
LIVEKIT_URL=wss://voiceagent007-fnileh5c.livekit.cloud
LIVEKIT_API_KEY=YOUR_LIVEKIT_API_KEY
LIVEKIT_API_SECRET=YOUR_LIVEKIT_API_SECRET
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
LLM_PROVIDER=openai
STT_PROVIDER=openai
TTS_PROVIDER=openai
```

---

## Quick Reference

**Frontend URL**: https://conversation-flow-voice-agent-with.vercel.app
**LiveKit URL**: wss://voiceagent007-fnileh5c.livekit.cloud
**LiveKit Dashboard**: https://cloud.livekit.io/

**Next Step**: Deploy backend agent to LiveKit Cloud with OpenAI API key configured

---

## Support

- **LiveKit Docs**: https://docs.livekit.io/agents/
- **LiveKit Cloud**: https://cloud.livekit.io/
- **OpenAI API**: https://platform.openai.com/

