# External Services Setup Guide

This document outlines all external services required for the Voice Agent system and how to obtain API keys/credentials.

## Required Services

### 1. LiveKit Cloud (REQUIRED)
**Purpose**: WebRTC media server for real-time audio streaming

**Setup Steps**:
1. Go to https://cloud.livekit.io/
2. Sign up for a free account
3. Create a new project
4. Navigate to "API Keys" section
5. Create a new API key with these permissions:
 - `room:create`
 - `room:list`
 - `room:record`
6. Copy the following:
 - `LIVEKIT_URL` (WebSocket URL, e.g., `wss://your-project.livekit.cloud`)
 - `LIVEKIT_API_KEY` (API Key)
 - `LIVEKIT_API_SECRET` (API Secret)

**Free Tier**: Includes limited usage, suitable for development/testing
**Pricing**: Pay-as-you-go after free tier
**Documentation**: https://docs.livekit.io/

---

### 2. OpenAI API (REQUIRED - Primary LLM/TTS/STT)
**Purpose**: 
- Speech-to-Text (Whisper)
- Large Language Model (GPT-4o-mini recommended for cost)
- Text-to-Speech (TTS)

**Setup Steps**:
1. Go to https://platform.openai.com/
2. Sign up or log in
3. Navigate to "API Keys" section
4. Click "Create new secret key"
5. Copy the key immediately (you won't see it again)
6. Add payment method (required for API usage, but GPT-4o-mini is very cheap)

**API Keys Needed**:
- `OPENAI_API_KEY` (used for all OpenAI services)

**Models Used**:
- STT: `whisper-1`
- LLM: `gpt-4o-mini` (fallback to `gpt-3.5-turbo` if needed)
- TTS: `tts-1` or `tts-1-hd` (voice options: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`)

**Pricing** (approximate):
- Whisper: $0.006 per minute
- GPT-4o-mini: ~$0.15 per 1M input tokens
- TTS: $15 per 1M characters

**Free Credits**: New accounts get $5 free credit

**Documentation**: https://platform.openai.com/docs/

---

### 3. Ollama (LOCAL - Optional but Recommended)
**Purpose**: Local LLM for development/testing (no API costs)

**Setup Steps**:
1. Go to https://ollama.ai/
2. Download Ollama for your OS (macOS, Linux, Windows)
3. Install the application
4. Open terminal and run:
 ```bash
 ollama pull llama3.2
 # or
 ollama pull mistral
 # or
 ollama pull qwen2.5
 ```
5. Test it:
 ```bash
 ollama run llama3.2 "Hello, how are you?"
 ```

**Configuration**:
- `OLLAMA_BASE_URL`: Default is `http://localhost:11434`
- `OLLAMA_MODEL`: Model name (e.g., `llama3.2`, `mistral`, `qwen2.5`)

**No API Key Required**: Runs locally
**Cost**: Free (uses your local compute)

**Documentation**: https://ollama.ai/docs/

**Note**: Ollama will be used as primary LLM, with GPT as fallback if Ollama is unavailable.

---

### 4. Groq (OPTIONAL - Fast LLM Alternative)
**Purpose**: Ultra-fast LLM inference (alternative to OpenAI)

**Setup Steps**:
1. Go to https://console.groq.com/
2. Sign up for free account
3. Navigate to "API Keys"
4. Create a new API key
5. Copy the key

**API Key**:
- `GROQ_API_KEY`

**Models Available**:
- `llama-3.1-70b-versatile`
- `mixtral-8x7b-32768`
- `gemma-7b-it`

**Free Tier**: Very generous free tier for development
**Pricing**: Free tier includes substantial usage

**Documentation**: https://console.groq.com/docs

---

### 5. Google Cloud Platform (OPTIONAL - Alternative STT/TTS)
**Purpose**: Alternative STT/TTS provider with generous free tier

**Setup Steps**:
1. **Create Account**: Go to https://cloud.google.com/
   - Click "Get started for free"
   - Sign in with Google account
   - Complete billing setup (credit card required, but free tier won't charge)
   - Google gives $300 free credit for 90 days

2. **Create Project**: Go to https://console.cloud.google.com/
   - Click "Select a project" → "New Project"
   - Name: "VoiceAgent-TTS" (or any name)
   - Click "Create"

3. **Enable APIs**:
   - Go to https://console.cloud.google.com/apis/library
   - Search and enable "Cloud Text-to-Speech API" (for TTS fallback)
   - (Optional) Enable "Cloud Speech-to-Text API" (for STT fallback)

4. **Get Credentials** (choose one method):

   **Method A: API Key (EASIEST - for testing)**
   - Go to https://console.cloud.google.com/apis/credentials
   - Click "Create Credentials" → "API Key"
   - Copy the API key
   - (Optional) Restrict key to "Cloud Text-to-Speech API" for security

   **Method B: Service Account (RECOMMENDED - for production)**
   - Go to https://console.cloud.google.com/iam-admin/serviceaccounts
   - Click "Create Service Account"
   - Name: "voice-agent-tts"
   - Role: "Cloud Text-to-Speech API User"
   - Go to "Keys" tab → "Add Key" → "Create new key" → Choose "JSON"
   - Download the JSON file (keep it secure!)

**Configuration**:
- **Method A**: `GOOGLE_API_KEY=your_api_key_here`
- **Method B**: `GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json`

**Pricing**:
- **Free Tier**: 
  - Standard voices: 4 million characters/month FREE
  - WaveNet/Neural2 voices: 1 million characters/month FREE
- **Paid** (after free tier):
  - Standard: $4 per 1M characters
  - WaveNet/Neural2: $16 per 1M characters

**Free Tier**: $300 credit for new accounts + 4M chars/month (Standard voices)
**Documentation**: 
- Text-to-Speech: https://cloud.google.com/text-to-speech/docs
- Speech-to-Text: https://cloud.google.com/speech-to-text/docs

---

## Service Priority Configuration

The system uses this fallback order:

### LLM Service:
1. **Primary**: Ollama (local, free)
2. **Fallback 1**: Groq (if configured and Ollama fails)
3. **Fallback 2**: OpenAI GPT (always available if API key set)

### STT Service:
1. **Primary**: OpenAI Whisper
2. **Fallback**: Google Cloud STT (if configured)

### TTS Service:
1. **Primary**: OpenAI TTS
2. **Fallback**: Google Cloud TTS (if configured)

---

## Environment Variables Summary

Copy these to your `.env` file (see `.env.example`):

```bash
# LiveKit (REQUIRED)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# OpenAI (REQUIRED for STT/TTS, optional for LLM)
OPENAI_API_KEY=sk-...

# Ollama (OPTIONAL but recommended for local LLM)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Groq (OPTIONAL - fast LLM alternative)
GROQ_API_KEY=gsk_...

# Google Cloud (OPTIONAL - alternative STT/TTS)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
# OR
GOOGLE_API_KEY=your-google-api-key

# Application Configuration
LOG_LEVEL=INFO
MAX_RETRY_ATTEMPTS=3
CONVERSATION_TIMEOUT=300
```

---

## Quick Start Checklist

For minimal setup (recommended for first run):
- [ ] Sign up for LiveKit Cloud
- [ ] Sign up for OpenAI (for STT/TTS)
- [ ] Install Ollama locally (for LLM)
- [ ] Configure `.env` file with credentials

For full production setup:
- [ ] All minimal setup items
- [ ] Add Groq API key (optional)
- [ ] Set up Google Cloud (optional)
- [ ] Configure all fallback services

---

## Cost Estimation

**Development/Testing** (estimated monthly):
- LiveKit Cloud: $0 (free tier) - $20 (low usage)
- OpenAI: $5-20 (depending on usage)
- Ollama: $0 (local)
- **Total**: ~$5-40/month for development

**Production** (estimated monthly for 1000 conversations):
- LiveKit Cloud: ~$50-100
- OpenAI: ~$100-200 (STT + TTS + some LLM)
- Ollama: $0 (if using local server)
- **Total**: ~$150-300/month

---

## Security Best Practices

1. **Never commit `.env` files** to version control
2. Use environment variables, not hardcoded keys
3. Rotate API keys periodically
4. Use least-privilege API keys (LiveKit)
5. Store production keys in secure secret management (AWS Secrets Manager, etc.)
6. Monitor API usage to detect anomalies

---

## Troubleshooting

### LiveKit Connection Issues
- Verify WebSocket URL format (must start with `wss://`)
- Check API key permissions
- Ensure room creation is allowed

### OpenAI API Errors
- Verify API key is valid
- Check account has payment method added
- Monitor usage limits in dashboard

### Ollama Connection Issues
- Ensure Ollama is running: `ollama list`
- Check port 11434 is not blocked
- Verify model is downloaded: `ollama list`

### Groq API Issues
- Check rate limits (free tier has limits)
- Verify API key format
- Monitor usage in Groq dashboard

---

## Support Links

- LiveKit Discord: https://livekit.io/discord
- OpenAI Support: https://help.openai.com/
- Ollama GitHub: https://github.com/ollama/ollama
