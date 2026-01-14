# Deployment Checklist

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

