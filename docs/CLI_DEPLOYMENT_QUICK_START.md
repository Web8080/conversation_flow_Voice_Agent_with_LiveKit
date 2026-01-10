# Quick Start: Deploy via LiveKit CLI

## Why CLI Deployment?

The dashboard code editor is **read-only** because custom Python agents must be deployed via:
- **LiveKit CLI** (recommended for custom code)
- **Git repository connection** (if supported in your dashboard)

We'll use the CLI method which is the official way to deploy custom Python agents.

---

## Step-by-Step Deployment

### Step 1: Install LiveKit CLI

```bash
# Option 1: Via npm (recommended - fastest)
npm install -g livekit-cli

# Option 2: Via pip
pip install livekit-cli

# Option 3: Via Homebrew (macOS)
brew install livekit-cli

# Option 4: Via curl (universal)
curl -sSL https://get.livekit.io/cli | bash
```

**Verify installation:**
```bash
lk --version
```

If you get an error, make sure Node.js/npm is installed first:
```bash
# Check if npm is installed
npm --version

# If not installed, install Node.js from https://nodejs.org/
```

### Step 2: Navigate to Backend Directory

```bash
cd /Users/user/Fortell_AI_Product/backend
```

### Step 3: Authenticate with LiveKit Cloud

```bash
lk cloud auth
```

This will:
- Open a browser window automatically
- Prompt you to log in to LiveKit Cloud
- Link your local CLI to your LiveKit Cloud project (Voice_Agent_007)
- Authorize the CLI to deploy agents

**Follow the browser prompts** to complete authentication.

### Step 4: Create Agent (First Time Only)

```bash
lk agent create
```

This command will:
- Register your agent with LiveKit Cloud
- Use the existing agent ID: `ab_52g3l8eyf4y` (or create new one)
- Generate a `livekit.toml` configuration file
- Link your local codebase to the cloud agent

**Note**: If you already have an agent in the dashboard, this will link to it. If not, it creates a new one.

### Step 5: Configure Environment Variables

The CLI will use environment variables. You can set them in two ways:

**Option A: Add to `livekit.toml` (generated after `lk agent create`)**

Open the generated `livekit.toml` file and add:

```toml
[env]
LIVEKIT_URL = "wss://voiceagent007-fnileh5c.livekit.cloud"
LIVEKIT_API_KEY = "YOUR_LIVEKIT_API_KEY"
LIVEKIT_API_SECRET = "YOUR_LIVEKIT_API_SECRET"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"
LLM_PROVIDER = "openai"
STT_PROVIDER = "openai"
TTS_PROVIDER = "openai"
```

**Option B: Use Dashboard Secrets (Recommended)**

1. Go to LiveKit Cloud dashboard → Agents → Advanced tab
2. In "Secrets" section, add each secret:
   - `LIVEKIT_URL` = `wss://voiceagent007-fnileh5c.livekit.cloud`
   - `LIVEKIT_API_KEY` = `YOUR_LIVEKIT_API_KEY`
   - `LIVEKIT_API_SECRET` = `YOUR_LIVEKIT_API_SECRET`
   - `OPENAI_API_KEY` = `YOUR_OPENAI_API_KEY`
   - `LLM_PROVIDER` = `openai`
   - `STT_PROVIDER` = `openai`
   - `TTS_PROVIDER` = `openai`
3. Click "Save changes"

The CLI will automatically use these secrets when deploying.

### Step 6: Deploy Agent

```bash
lk agent deploy
```

This will:
- Build Docker image from your `Dockerfile`
- Push image to LiveKit Cloud's container registry
- Deploy agent as a worker service
- Use secrets from dashboard or `livekit.toml`
- Start the agent with your custom Python code

**Wait for deployment to complete** (may take 2-5 minutes).

### Step 7: Check Deployment Status

```bash
lk agent status
```

You should see:
```
Status: RUNNING
Agent ID: ab_52g3l8eyf4y
```

### Step 8: View Logs

```bash
lk agent logs
```

Or view logs in the dashboard:
- Go to LiveKit Cloud dashboard → Agents
- Click on your agent
- View logs section

Look for: "Stage 1 agent started" or "Agent initialized"

---

## Troubleshooting

### "Command not found: lk"

**Problem**: LiveKit CLI is not installed or not in PATH.

**Solution**:
```bash
# Install via npm (if Node.js is installed)
npm install -g livekit-cli

# Verify installation
lk --version

# If still not found, try:
npx livekit-cli --version
```

### "Authentication failed"

**Problem**: CLI not authenticated with LiveKit Cloud.

**Solution**:
```bash
lk cloud auth
# Follow browser prompts to complete authentication
```

### "Agent deployment failed"

**Problem**: Build or deployment error.

**Solutions**:
1. **Check Dockerfile exists**:
   ```bash
   ls backend/Dockerfile
   ```

2. **Check requirements.txt**:
   ```bash
   cat backend/requirements.txt
   ```

3. **Check logs**:
   ```bash
   lk agent logs
   ```

4. **Verify environment variables** are set correctly in dashboard or `livekit.toml`

### "Module not found" errors

**Problem**: Missing Python dependencies.

**Solution**:
1. Check `backend/requirements.txt` includes all required packages
2. Verify `Dockerfile` installs requirements correctly
3. Check deployment logs for missing modules

### Agent stays "PENDING"

**Problem**: Agent deployed but not running.

**Solution**:
1. Check logs: `lk agent logs`
2. Verify all secrets are added in dashboard
3. Check OpenAI API key is valid
4. Verify LiveKit credentials are correct

---

## Quick Command Reference

```bash
# Install CLI
npm install -g livekit-cli

# Navigate to backend
cd backend

# Authenticate
lk cloud auth

# Create agent (first time only)
lk agent create

# Deploy agent
lk agent deploy

# Check status
lk agent status

# View logs
lk agent logs

# Update agent (after code changes)
lk agent deploy

# Rollback to previous version
lk agent rollback
```

---

## Next Steps After Deployment

Once agent is deployed and status is "RUNNING":

1. **Open frontend**: https://conversation-flow-voice-agent-with.vercel.app
2. **Enter room name**: e.g., "test-room-123"
3. **Click "Connect"**
4. **Allow microphone permissions**
5. **Speak**: "Hello, how are you?"
6. **Wait for agent response**: Should hear synthesized speech

---

## What Happens During Deployment

1. **Build**: CLI builds Docker image from `Dockerfile`
2. **Push**: Image pushed to LiveKit Cloud's container registry
3. **Deploy**: Agent deployed as worker service in LiveKit Cloud
4. **Start**: Agent starts and connects to LiveKit Cloud using your credentials
5. **Ready**: Agent is ready to join rooms when users connect

---

## Using Secrets from Dashboard vs livekit.toml

**Dashboard Secrets (Recommended)**:
- ✅ More secure (encrypted in LiveKit Cloud)
- ✅ Easy to update via UI
- ✅ Don't need to commit secrets to git
- ✅ Shared across all deployments

**livekit.toml**:
- ✅ Version controlled (use `.gitignore` for sensitive values)
- ✅ Local development friendly
- ⚠️ Must be careful not to commit secrets to git

**Best Practice**: Use dashboard secrets for production, `livekit.toml` for local development (with `.gitignore`).

---

## Support Resources

- **LiveKit Agents Docs**: https://docs.livekit.io/agents/
- **LiveKit CLI Docs**: https://docs.livekit.io/agents/cli/
- **LiveKit Cloud Deploy**: https://docs.livekit.io/agents/deployment/
- **LiveKit Cloud Dashboard**: https://cloud.livekit.io/

---

## Summary

Since the dashboard code editor is read-only, we must use the CLI method. This is actually the **recommended approach** for custom Python agents because:

1. ✅ Full control over your code
2. ✅ Version control friendly
3. ✅ Can use custom services (your STT/LLM/TTS)
4. ✅ Better for development workflow
5. ✅ Official LiveKit method for custom agents

The dashboard UI is primarily for LiveKit's built-in AI agents, while the CLI is for custom code like yours.

