# Vercel vs Backend Environment Variables

## Vercel (Frontend) - What You Need

You've correctly added these 3 variables to Vercel:

1. `NEXT_PUBLIC_LIVEKIT_URL` = `wss://voiceagent007-fnileh5c.livekit.cloud`
2. `LIVEKIT_API_KEY` = `YOUR_LIVEKIT_API_KEY`
3. `LIVEKIT_API_SECRET` = `YOUR_LIVEKIT_API_SECRET`

**OpenAI API Key: NOT NEEDED in Vercel**

The frontend (Next.js) only:
- Connects to LiveKit rooms
- Generates LiveKit access tokens (uses LIVEKIT_API_KEY and LIVEKIT_API_SECRET)
- Displays the UI and conversation
- Does NOT process audio or call OpenAI APIs

---

## Backend (LiveKit Cloud) - What You'll Need

When you deploy the Python backend agent to LiveKit Cloud, you'll need:

1. **LiveKit credentials** (same as frontend):
   - `LIVEKIT_URL` = `wss://voiceagent007-fnileh5c.livekit.cloud`
   - `LIVEKIT_API_KEY` = `APIjAbndhXSoyis`
   - `LIVEKIT_API_SECRET` = `D1pm5XYaXHUJe3iiIjU7Uk5fo7n1ebU2WcBIKDy5sGRA`

2. **OpenAI API Key** (required for backend):
   - `OPENAI_API_KEY` = `YOUR_OPENAI_API_KEY`

The backend uses OpenAI for:
- **STT (Speech-to-Text)**: Converting user's voice to text
- **LLM (Language Model)**: Generating responses
- **TTS (Text-to-Speech)**: Converting responses to voice

---

## Architecture Flow

```
User speaks in browser
    ↓
Frontend (Vercel) → Sends audio to LiveKit room
    ↓
LiveKit Cloud → Routes audio to backend agent
    ↓
Backend Agent (LiveKit Cloud):
  - Uses OpenAI STT to transcribe audio
  - Uses OpenAI LLM to generate response
  - Uses OpenAI TTS to synthesize speech
    ↓
Backend → Sends audio back to LiveKit room
    ↓
LiveKit Cloud → Routes audio to frontend
    ↓
Frontend (Vercel) → Plays audio to user
```

**Key Point**: The frontend never touches OpenAI APIs. All AI processing happens in the backend.

---

## Summary

### Vercel (Frontend) Environment Variables:
- [x] `NEXT_PUBLIC_LIVEKIT_URL` (you've added)
- [x] `LIVEKIT_API_KEY` (you've added)
- [x] `LIVEKIT_API_SECRET` (you've added)
- [ ] `OPENAI_API_KEY` (NOT needed - backend only)

### Backend (LiveKit Cloud) Environment Variables (for later):
- [ ] `LIVEKIT_URL` (same as frontend)
- [ ] `LIVEKIT_API_KEY` (same as frontend)
- [ ] `LIVEKIT_API_SECRET` (same as frontend)
- [ ] `OPENAI_API_KEY` (your key: `sk-proj-wSGpPc...`)

---

## Next Steps

1. **Vercel is ready** - You have all the variables you need
2. **Deploy frontend** - Should work now
3. **Later: Deploy backend** - Add OpenAI key to backend environment when deploying to LiveKit Cloud

---

## Quick Test

Once Vercel is deployed, you can:
1. Open the deployment URL
2. Connect to a room
3. The UI should work (you can see the interface)

**However**, the voice agent won't respond until the backend is deployed to LiveKit Cloud with the OpenAI API key configured.

---

## Deployment Status

- [x] Frontend variables configured in Vercel
- [ ] Frontend deployed to Vercel
- [ ] Backend deployed to LiveKit Cloud (needs OpenAI key)
- [ ] End-to-end voice interaction working

