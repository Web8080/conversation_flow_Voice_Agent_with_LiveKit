# LiveKit Cloud Dashboard - Agent Deployment Guide

## Understanding the Interface

The LiveKit Cloud dashboard you're seeing supports **two types of agents**:

1. **Built-in AI Agents** (configured through UI - Instructions/Models tabs)
2. **Custom Python Agents** (deployed via CLI or configured in Advanced tab)

Our backend uses **custom Python code**, so we need to deploy it as a **custom agent**.

---

## Method 1: Deploy via LiveKit CLI (Recommended)

LiveKit Cloud provides a CLI tool to deploy custom Python agents directly from your codebase.

### Step 1: Install LiveKit CLI

```bash
# Install via npm
npm install -g livekit-cli

# OR install via pip
pip install livekit-cli

# OR install via homebrew (macOS)
brew install livekit-cli
```

Verify installation:
```bash
lk --version
```

### Step 2: Authenticate with LiveKit Cloud

```bash
lk cloud auth
```

This will:
- Open a browser window
- Prompt you to link your LiveKit Cloud project
- Authenticate the CLI with your account

### Step 3: Navigate to Backend Directory

```bash
cd backend
```

### Step 4: Initialize Agent Configuration

```bash
lk agent create
```

This command will:
- Register your agent with LiveKit Cloud
- Assign a unique agent ID
- Generate a `livekit.toml` configuration file
- Optionally create a `Dockerfile` if one doesn't exist

### Step 5: Configure Environment Variables

The CLI will prompt you for environment variables, OR you can set them in the generated `livekit.toml` file:

```toml
[build]
dockerfile = "Dockerfile"

[agent]
entrypoint = "python main.py dev"

[env]
LIVEKIT_URL = "wss://voiceagent007-fnileh5c.livekit.cloud"
LIVEKIT_API_KEY = "YOUR_LIVEKIT_API_KEY"
LIVEKIT_API_SECRET = "YOUR_LIVEKIT_API_SECRET"
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"
LLM_PROVIDER = "openai"
STT_PROVIDER = "openai"
TTS_PROVIDER = "openai"
```

**Important**: For sensitive values like API keys, use LiveKit Cloud's **Secrets** feature in the dashboard instead of putting them in `livekit.toml`.

### Step 6: Deploy the Agent

```bash
lk agent deploy
```

This will:
- Build a Docker image from your `Dockerfile`
- Push it to LiveKit Cloud's container registry
- Deploy the agent as a worker service
- Automatically connect to LiveKit Cloud

### Step 7: Monitor Deployment

Check agent status:
```bash
lk agent status
```

View logs:
```bash
lk agent logs
```

Or check the LiveKit Cloud dashboard → Agents section.

---

## Method 2: Configure via LiveKit Cloud Dashboard

If the dashboard interface supports custom agents, you may be able to configure it there. Here's what to look for:

### In the Dashboard Interface You're Seeing:

1. **Check the "Advanced" Tab**:
   - Look for options to upload custom code
   - Check for Dockerfile/container image settings
   - Look for environment variable configuration

2. **Check the "Code" Tab** (if visible):
   - May allow you to paste or upload custom Python code
   - May have Git repository integration

3. **Agent Configuration Settings**:
   - Look for "Entrypoint" or "Command" field
   - Should be: `python main.py dev`
   - Look for "Working Directory" or "Root Directory"
   - Should be: `backend/` (if deploying from repo root)

4. **Environment Variables**:
   - Look for "Environment Variables" or "Secrets" section
   - Add these variables:
     ```
     LIVEKIT_URL=wss://voiceagent007-fnileh5c.livekit.cloud
     LIVEKIT_API_KEY=YOUR_LIVEKIT_API_KEY
     LIVEKIT_API_SECRET=YOUR_LIVEKIT_API_SECRET
     OPENAI_API_KEY=YOUR_OPENAI_API_KEY
     LLM_PROVIDER=openai
     STT_PROVIDER=openai
     TTS_PROVIDER=openai
     ```

5. **Docker/Container Settings**:
   - If there's a Docker image option, you may need to:
     - Build and push to a container registry (Docker Hub, GCR, ECR)
     - Reference the image URL
   - OR connect a Git repository and let LiveKit build from `Dockerfile`

6. **Deploy Button**:
   - After configuring, click "Deploy agent" (the blue button you saw)
   - Wait for deployment to complete
   - Check status shows "RUNNING" or "ACTIVE" instead of "PENDING"

---

## What Each Tab Does (If You're Using Built-in Agents)

If the interface is for LiveKit's built-in AI agents, here's what each tab does:

- **Instructions**: System prompt and behavior guidelines
- **Models & Voice**: LLM model selection and TTS voice settings
- **Actions**: Tools/functions the agent can call
- **Advanced**: Custom configurations, environment variables, webhooks

**However**, for our **custom Python agent**, we need to use the **CLI method** or look for custom agent deployment options in the dashboard.

---

## Recommended Approach: CLI Method

Since we have custom Python code, the **CLI method is recommended** because:

1. ✅ Direct deployment from your codebase
2. ✅ Automatic Docker image building
3. ✅ Version control integration
4. ✅ Easy updates with `lk agent deploy`
5. ✅ Better for custom code

---

## Quick Start: Deploy Now

### Option A: Use CLI (Fastest)

```bash
# 1. Install CLI
npm install -g livekit-cli

# 2. Authenticate
cd backend
lk cloud auth

# 3. Create agent (will generate livekit.toml)
lk agent create

# 4. Edit livekit.toml to add environment variables (or use dashboard secrets)

# 5. Deploy
lk agent deploy

# 6. Check status
lk agent status
```

### Option B: Use Dashboard (If Supported)

1. In LiveKit Cloud dashboard → Agents section
2. Look for "Advanced" or "Custom Agent" option
3. Configure:
   - Entrypoint: `python main.py dev`
   - Environment variables (add all required)
   - Docker image or Git repository connection
4. Click "Deploy agent"
5. Wait for deployment to complete

---

## Environment Variables Required

Add these in the dashboard "Secrets" or "Environment Variables" section:

```
LIVEKIT_URL=wss://voiceagent007-fnileh5c.livekit.cloud
LIVEKIT_API_KEY=YOUR_LIVEKIT_API_KEY
LIVEKIT_API_SECRET=YOUR_LIVEKIT_API_SECRET
OPENAI_API_KEY=YOUR_OPENAI_API_KEY
LLM_PROVIDER=openai
STT_PROVIDER=openai
TTS_PROVIDER=openai
```

**Important**: Use the **Secrets** feature for sensitive values (API keys) instead of plain environment variables.

---

## Troubleshooting

### Agent Stays "PENDING"

1. Check deployment logs in dashboard
2. Verify environment variables are set correctly
3. Check Dockerfile builds successfully
4. Verify entrypoint command is correct

### Agent Fails to Start

1. Check logs: `lk agent logs` or dashboard logs
2. Verify all environment variables are present
3. Check OpenAI API key is valid
4. Verify LiveKit credentials are correct

### Connection Issues

1. Verify `LIVEKIT_URL` matches your LiveKit Cloud project URL
2. Check `LIVEKIT_API_KEY` and `LIVEKIT_API_SECRET` are correct
3. Ensure agent has permission to join rooms

---

## Next Steps

1. **Choose deployment method** (CLI recommended)
2. **Deploy backend agent** to LiveKit Cloud
3. **Test end-to-end**:
   - Open frontend: https://conversation-flow-voice-agent-with.vercel.app
   - Enter room name
   - Click "Connect"
   - Speak to agent
   - Verify agent responds

---

## Support Resources

- **LiveKit Agents Docs**: https://docs.livekit.io/agents/
- **LiveKit Cloud Deploy**: https://docs.livekit.io/agents/deployment/
- **LiveKit CLI**: https://docs.livekit.io/agents/cli/
- **LiveKit Cloud Dashboard**: https://cloud.livekit.io/

