# Environment Variables Setup Guide

## ✅ Files Created

I've created the `.env` files for you with your LiveKit API Key already included:

- ✅ `backend/.env` - Backend configuration
- ✅ `frontend/.env.local` - Frontend configuration

---

## 🔑 What You Need to Update

### 1. **LiveKit WebSocket URL** (REQUIRED)
**Where to find it:**
- Go to https://cloud.livekit.io/
- Navigate to your project
- Look for "WebSocket URL" or "Server URL"
- It should look like: `wss://your-project-name.livekit.cloud`

**Update in both files:**
- `backend/.env`: `LIVEKIT_URL=wss://your-project-name.livekit.cloud`
- `frontend/.env.local`: `NEXT_PUBLIC_LIVEKIT_URL=wss://your-project-name.livekit.cloud`

### 2. **LiveKit API Secret** (REQUIRED)
**Where to find it:**
- Go to https://cloud.livekit.io/
- Navigate to "API Keys" section
- Find your API Key (the one you already have: `APIjAbndhXSoyis`)
- Next to it, you should see the **API Secret**
- Click "Show Secret" or "Reveal" to see it
- Copy the entire secret (it's usually a long string)

**Update in both files:**
- `backend/.env`: `LIVEKIT_API_SECRET=your-actual-secret-here`
- `frontend/.env.local`: `LIVEKIT_API_SECRET=your-actual-secret-here`

### 3. **OpenAI API Key** (REQUIRED for STT/TTS)
**Why you need it:**
- Speech-to-Text (STT) - converts audio to text
- Text-to-Speech (TTS) - converts text to audio
- Optional for LLM (we're using Ollama for that)

**Where to get it:**
1. Go to https://platform.openai.com/
2. Sign up or log in
3. Navigate to "API Keys" section (left sidebar)
4. Click "Create new secret key"
5. Name it (e.g., "Voice Agent Dev")
6. Copy the key immediately (starts with `sk-`)
7. **Important**: Add a payment method (required for API usage, but GPT-4o-mini is very cheap)

**Update in:**
- `backend/.env`: `OPENAI_API_KEY=sk-your-actual-key-here`

**Cost**: Very cheap for development (~$5-20/month)

---

## 📝 Quick Edit Commands

### Edit Backend .env
```bash
cd backend
nano .env
# or
code .env  # if using VS Code
```

### Edit Frontend .env.local
```bash
cd frontend
nano .env.local
# or
code .env.local  # if using VS Code
```

---

## ✅ Current Status

### ✅ Already Configured:
- ✅ `LIVEKIT_API_KEY=APIjAbndhXSoyis` (added to both files)

### ⚠️ Need to Update:
- ⚠️ `LIVEKIT_URL` - Add your WebSocket URL
- ⚠️ `LIVEKIT_API_SECRET` - Add your API Secret from dashboard
- ⚠️ `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys

### 📌 Optional (but recommended):
- **Ollama** (for local LLM - FREE):
  - Install: https://ollama.ai/
  - Run: `ollama pull llama3.2`
  - Already configured in `.env`, just needs Ollama running locally

---

## 🔍 How to Verify LiveKit Credentials

Once you've updated the files, you can verify they work:

### Test Backend Connection:
```bash
cd backend
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('LIVEKIT_URL:', os.getenv('LIVEKIT_URL'))
print('LIVEKIT_API_KEY:', os.getenv('LIVEKIT_API_KEY')[:10] + '...')
print('LIVEKIT_API_SECRET:', 'Set' if os.getenv('LIVEKIT_API_SECRET') else 'Missing')
"
```

### Test Frontend Connection:
```bash
cd frontend
npm run dev
# Open http://localhost:3000
# Try connecting to a room
# Check browser console for errors
```

---

## 🚨 Security Notes

1. **Never commit `.env` files** to Git (they're already in `.gitignore`)
2. **API Secret** should be kept secure - never share it publicly
3. **OpenAI API Key** starts with `sk-` - treat it like a password
4. In production, use environment variables or secret management (AWS Secrets Manager, etc.)

---

## 📋 Quick Checklist

Before running the system, make sure:

- [ ] LiveKit WebSocket URL added to both files
- [ ] LiveKit API Secret added to both files
- [ ] OpenAI API Key added to `backend/.env`
- [ ] Payment method added to OpenAI account (required for API usage)
- [ ] Ollama installed locally (optional but recommended - free LLM)

---

## 🚀 Next Steps

Once you've updated the `.env` files:

1. **Install backend dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Install frontend dependencies** (if not already done):
   ```bash
   cd frontend
   npm install
   ```

3. **Start the system:**
   ```bash
   # Terminal 1: Backend agent
   cd backend
   python main.py dev
   
   # Terminal 2: Frontend (already running on port 3000)
   cd frontend
   npm run dev
   ```

4. **Test the connection:**
   - Open http://localhost:3000
   - Enter a room name
   - Click "Connect"
   - Check console for connection status

---

## 🆘 Troubleshooting

### "Missing LiveKit credentials" error
- Check that `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` are set in `frontend/.env.local`
- Make sure the file is named exactly `.env.local` (not `.env`)

### "Connection failed" error
- Verify `NEXT_PUBLIC_LIVEKIT_URL` starts with `wss://`
- Check that your LiveKit project is active
- Verify API Key has correct permissions (room:create, room:join)

### OpenAI API errors
- Verify API key is correct (starts with `sk-`)
- Check that payment method is added to OpenAI account
- Monitor usage in OpenAI dashboard

### Ollama connection issues
- Ensure Ollama is running: `ollama list`
- Check model is downloaded: `ollama list` should show `llama3.2`
- Verify port 11434 is accessible

---

## 📞 Support

- **LiveKit**: https://docs.livekit.io/
- **OpenAI**: https://platform.openai.com/docs/
- **Ollama**: https://ollama.ai/docs/

---

## 📝 Example Values (DO NOT USE THESE - Get your own!)

```
LIVEKIT_URL=wss://my-project.livekit.cloud
LIVEKIT_API_KEY=APIjAbndhXSoyis  ✅ You already have this
LIVEKIT_API_SECRET=abc123xyz789secretkey  ⚠️ Get from dashboard
OPENAI_API_KEY=sk-proj-abc123xyz789  ⚠️ Get from platform.openai.com
```

**Remember**: Never commit real API keys to Git!

