# Deployment Checklist

## Redeploy on LiveKit Cloud (pick up code changes)

Use this when you’ve changed code (e.g. Stage 3, schema, flows) and want the cloud agent to use it.

### 1. Push your code

```bash
cd /Users/user/Fortell_AI_Product
git add -A
git commit -m "your message"
git push origin master
```

### 2. Deploy the agent from your machine

**Prereqs:** [LiveKit CLI](https://docs.livekit.io/reference/other/agent-cli/) installed and logged in:

```bash
lk cloud auth
```

**Deploy from the backend directory:**

```bash
cd /Users/user/Fortell_AI_Product/backend
lk agent deploy
```

If your project name isn’t inferred from `livekit.toml`, pass it explicitly:

```bash
lk agent deploy --project voiceagent007
# or
lk agent deploy --project voiceagent008
```

(Use the project name that matches your [LiveKit Cloud](https://cloud.livekit.io) project.)

### 3. Optional: push secrets (env vars)

If you changed `.env` or need to sync secrets (API keys, `AGENT_STAGE`, etc.):

```bash
cd /Users/user/Fortell_AI_Product/backend
lk agent update-secrets --secrets-file .env.secrets --project voiceagent007 --overwrite
lk agent deploy --project voiceagent007
```

### 4. Check that it’s running

```bash
lk agent status --project voiceagent007
lk agent logs --project voiceagent007
```

Then open your Vercel app, join a room, and confirm the agent joins and behaves as expected.

---

## Stage 2 Deployment

### 1. Enable Stage 2

Add to `backend/.env`:
```bash
AGENT_STAGE=stage2
```

### 2. Deploy Agent

```bash
cd backend
lk agent deploy --project voiceagent007
```

### 3. Verify Deployment

Check agent logs:
```bash
lk agent logs --project voiceagent007 | grep -E "(Stage 2|state machine|calendar)"
```

You should see:
```
Stage 2 agent started
State machine initialized
Google Calendar service initialized
```

## Google Calendar Setup

### Quick Setup Steps

1. **Enable Google Calendar API**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - APIs & Services > Library > Search "Google Calendar API" > Enable

2. **Create Service Account**
   - APIs & Services > Credentials > Create Credentials > Service Account
   - Create and download JSON key file

3. **Grant Calendar Access**
   - Copy service account email from JSON file
   - Open Google Calendar > Settings > Share with specific people
   - Add service account email with "Make changes to events" permission

4. **Configure Credentials**

   **For Local Development:**
   ```bash
   # In backend/.env
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-credentials.json
   ```

   **For LiveKit Cloud:**
   ```bash
   # Create backend/.env.secrets
   GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type":"service_account",...}'
   
   # Update secrets
   lk agent update-secrets --project voiceagent007 --secrets-file .env.secrets
   ```

5. **Verify Calendar Integration**
   - Test appointment booking via voice agent
   - Check Google Calendar for new events
   - Verify event details are correct

See `docs/GOOGLE_CALENDAR_SETUP.md` for detailed instructions.

## Current Status

- ✅ Stage 2 code implemented
- ✅ Calendar service created
- ✅ State machine enhanced
- ⏳ **Stage 2 not yet deployed** (needs `AGENT_STAGE=stage2` in .env)
- ⏳ **Google Calendar not configured** (needs API setup)

## Next Steps

1. Set `AGENT_STAGE=stage2` in backend/.env
2. Deploy agent: `lk agent deploy --project voiceagent007`
3. Configure Google Calendar (follow guide above)
4. Test appointment booking flow
5. Verify state progress updates in frontend


