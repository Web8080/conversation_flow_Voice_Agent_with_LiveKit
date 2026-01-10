# Quick Configuration Check

## Currently Configured

- **LiveKit API Key**: `APIjAbndhXSoyis` (configured in both backend/.env and frontend/.env.local)
- **OpenAI API Key**: `sk-proj-wSGpPc...` (configured in backend/.env)

## Still Need to Add

### 1. LiveKit WebSocket URL
**Where to find it:**
- Go to https://cloud.livekit.io/
- Navigate to your project dashboard
- Look for "WebSocket URL" or "Server URL"
- It should look like: `wss://your-project-name.livekit.cloud`

**Update in both files:**
- `backend/.env`: Change `LIVEKIT_URL=wss://your-project.livekit.cloud` to your actual URL
- `frontend/.env.local`: Change `NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud` to your actual URL

### 2. LiveKit API Secret
**Where to find it:**
- Go to https://cloud.livekit.io/
- Navigate to "API Keys" section
- Find your API Key (`APIjAbndhXSoyis`)
- Next to it, click "Show Secret" or "Reveal"
- Copy the entire secret (long string)

**Update in both files:**
- `backend/.env`: Change `LIVEKIT_API_SECRET=your-api-secret-here` to your actual secret
- `frontend/.env.local`: Change `LIVEKIT_API_SECRET=your-api-secret-here` to your actual secret

---

## Quick Edit Commands

### Edit Backend .env
```bash
cd backend
nano .env
# or
code .env
```

**Look for and update these lines:**
```
LIVEKIT_URL=wss://your-actual-websocket-url-here
LIVEKIT_API_SECRET=your-actual-api-secret-here
```

### Edit Frontend .env.local
```bash
cd frontend
nano .env.local
# or
code .env.local
```

**Look for and update these lines:**
```
NEXT_PUBLIC_LIVEKIT_URL=wss://your-actual-websocket-url-here
LIVEKIT_API_SECRET=your-actual-api-secret-here
```

---

## Once All Configured, You Can:

### 1. Test Backend Configuration
```bash
cd backend
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print(' LIVEKIT_URL:', os.getenv('LIVEKIT_URL')[:30] + '...' if os.getenv('LIVEKIT_URL') else ' Missing')
print(' LIVEKIT_API_KEY:', os.getenv('LIVEKIT_API_KEY')[:15] + '...' if os.getenv('LIVEKIT_API_KEY') else ' Missing')
print(' LIVEKIT_API_SECRET:', 'Set' if os.getenv('LIVEKIT_API_SECRET') and os.getenv('LIVEKIT_API_SECRET') != 'your-api-secret-here' else ' Missing')
print(' OPENAI_API_KEY:', 'Set' if os.getenv('OPENAI_API_KEY') else ' Missing')
"
```

### 2. Start the System
```bash
# Terminal 1: Backend
cd backend
pip install -r requirements.txt # First time only
python main.py dev

# Terminal 2: Frontend
cd frontend
npm run dev # If not already running
```

### 3. Test in Browser
- Open http://localhost:3000
- Enter a room name (e.g., "test-room")
- Click "Connect"
- Check browser console for any errors

---

## Security Reminder

- `.env` files are already in `.gitignore` (won't be committed)
- Never share your API keys publicly
- Never commit real API keys to Git
- API keys are safe to use in development locally

---

## Final Checklist

Before running the system:

- [x] LiveKit API Key added 
- [x] OpenAI API Key added 
- [ ] LiveKit WebSocket URL added 
- [ ] LiveKit API Secret added 
- [ ] Payment method added to OpenAI account (if using API)

Once all checked, you're ready to run!