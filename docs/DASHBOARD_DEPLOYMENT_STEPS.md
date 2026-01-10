# LiveKit Cloud Dashboard - Step-by-Step Deployment

## What You're Seeing

The LiveKit Cloud dashboard interface you're viewing is primarily designed for **LiveKit's built-in AI agents** (configured through the UI). However, you can still use parts of it for deploying your custom Python agent.

## Important Understanding

There are **two types of agents** in LiveKit Cloud:

1. **Built-in AI Agents** (what the dashboard UI is for)
   - Configured through UI tabs (Instructions, Models & Voice, Actions)
   - Uses pre-configured services (GPT-4, Cartesia Sonic, AssemblyAI)
   - No custom Python code needed

2. **Custom Python Agents** (what we built)
   - Uses LiveKit Agents framework (`cli.run_app()`)
   - Requires deploying Python code via CLI
   - Can use Secrets from dashboard for environment variables

**Our backend is a Custom Python Agent**, so we need to deploy it via CLI, but we can configure secrets in the dashboard.

---

## Step-by-Step: Deploy Custom Python Agent

### Step 1: Add Secrets in Dashboard (Advanced Tab)

1. **Go to "Advanced" tab** (you're already there!)

2. **In the "Secrets" section**, click **"+ Add secret"**

3. **Add these secrets one by one**:

   Click "+ Add secret" for each of these:

   ```
   Key: LIVEKIT_URL
   Value: wss://voiceagent007-fnileh5c.livekit.cloud
   ```

   ```
   Key: LIVEKIT_API_KEY
   Value: APIjAbndhXSoyis
   ```

   ```
   Key: LIVEKIT_API_SECRET
   Value: D1pm5XYaXHUJe3iiIjU7Uk5fo7n1ebU2WcBIKDy5sGRA
   ```

   ```
   Key: OPENAI_API_KEY
   Value: YOUR_OPENAI_API_KEY
   ```

   ```
   Key: LLM_PROVIDER
   Value: openai
   ```

   ```
   Key: STT_PROVIDER
   Value: openai
   ```

   ```
   Key: TTS_PROVIDER
   Value: openai
   ```

4. **Click "Save changes"** (top right)

### Step 2: Check "Code" Tab

1. **Click on the "Code" tab** (in the right panel, next to "Preview")

2. **Look for**:
   - Git repository connection option
   - Docker image upload option
   - Custom code deployment option
   - Or instructions to use CLI

   **If the Code tab shows instructions to use CLI**, proceed to Step 3.

   **If the Code tab has Git/Docker options**, you can deploy through the UI (see alternative below).

### Step 3: Deploy via LiveKit CLI (Recommended Method)

Since our agent uses custom Python code, we need to deploy it via CLI. The dashboard secrets you added will be used automatically.

#### Install LiveKit CLI

```bash
# Option 1: Via npm (recommended)
npm install -g livekit-cli

# Option 2: Via pip
pip install livekit-cli

# Option 3: Via Homebrew (macOS)
brew install livekit-cli
```

Verify installation:
```bash
lk --version
```

#### Authenticate with LiveKit Cloud

```bash
cd /Users/user/Fortell_AI_Product/backend
lk cloud auth
```

This will:
- Open a browser window
- Link your LiveKit Cloud project to the CLI
- Authenticate your local machine

#### Create Agent (First Time)

```bash
lk agent create
```

This command will:
- Register your agent with LiveKit Cloud (uses the agent ID: `ab_52g3l8eyf4y`)
- Generate a `livekit.toml` configuration file
- Link your local code to the cloud agent

**Note**: If you've already created the agent through the dashboard, this might link to the existing one.

#### Deploy Agent

```bash
lk agent deploy
```

This will:
- Build Docker image from your `Dockerfile`
- Push to LiveKit Cloud's container registry
- Deploy the agent as a worker service
- **Automatically use the secrets** you configured in the dashboard

#### Check Deployment Status

```bash
lk agent status
```

You should see status: `RUNNING` or `ACTIVE`

#### View Logs

```bash
lk agent logs
```

Look for: "Stage 1 agent started" or "Agent initialized"

---

## Alternative: If Dashboard Has Git/Docker Options

If the "Code" tab in the dashboard allows connecting a Git repository or uploading a Docker image:

### Option A: Connect Git Repository

1. In the "Code" tab, look for "Connect Repository" or "Git Repository"
2. Connect your GitHub repository
3. Set:
   - **Root Directory**: `backend/`
   - **Dockerfile Path**: `backend/Dockerfile`
   - **Build Command**: (auto-detected from Dockerfile)
   - **Start Command**: `python main.py dev`
4. The secrets you added in "Advanced" tab will be automatically injected as environment variables

### Option B: Upload Docker Image

1. First, build and push your Docker image to a registry:
   ```bash
   cd backend
   docker build -t voice-agent-backend .
   docker tag voice-agent-backend yourusername/voice-agent-backend:latest
   docker push yourusername/voice-agent-backend:latest
   ```

2. In the "Code" tab, select "Docker Image"
3. Enter image URL: `yourusername/voice-agent-backend:latest`
4. Set entrypoint: `python main.py dev`
5. Secrets from "Advanced" tab will be injected automatically

---

## What to Do Right Now

### Immediate Action Items:

1. ✅ **Add Secrets** in "Advanced" tab (you can do this now in the dashboard)
   - Go to Advanced → Secrets
   - Click "+ Add secret" for each required variable
   - Save changes

2. ⏳ **Check "Code" tab** to see if it supports Git/Docker deployment
   - If yes: Use that method
   - If no: Use CLI method (Step 3 above)

3. ⏳ **Deploy agent**:
   - Via CLI: `lk agent deploy` (recommended)
   - Via Dashboard: If "Code" tab supports it

4. ⏳ **Verify deployment**:
   - Status should change from "PENDING" to "RUNNING"
   - Check logs to see "Stage 1 agent started"

---

## Testing After Deployment

Once your agent is deployed and status is "RUNNING":

1. **Open frontend**: https://conversation-flow-voice-agent-with.vercel.app
2. **Enter room name**: e.g., "test-room-123"
3. **Click "Connect"**
4. **Allow microphone permissions**
5. **Speak**: "Hello, how are you?"
6. **Wait for agent response**: Should hear synthesized speech

---

## Troubleshooting

### Agent Status Stays "PENDING"

- Check deployment logs in dashboard or via `lk agent logs`
- Verify all secrets are added correctly
- Check Dockerfile builds successfully
- Verify entrypoint command: `python main.py dev`

### Agent Deploys But Doesn't Respond

- Check logs: `lk agent logs`
- Verify OpenAI API key is valid and has credits
- Check LiveKit URL matches your project URL
- Verify agent is connecting to LiveKit Cloud (look for connection messages in logs)

### Secrets Not Being Used

- Ensure secrets are saved in "Advanced" tab
- Verify secret names match exactly (case-sensitive)
- Check if CLI is using the correct agent ID: `ab_52g3l8eyf4y`

---

## Next Steps

1. **Add all secrets** in the "Advanced" tab now
2. **Check "Code" tab** to see deployment options
3. **Install LiveKit CLI** if Code tab doesn't support custom deployment
4. **Deploy agent** using CLI or dashboard method
5. **Test end-to-end** with frontend

---

## Quick Reference Commands

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
```

---

## Support

- **LiveKit Agents Docs**: https://docs.livekit.io/agents/
- **LiveKit Cloud Deploy**: https://docs.livekit.io/agents/deployment/
- **LiveKit CLI**: https://docs.livekit.io/agents/cli/

