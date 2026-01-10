# Deploy Agent via CLI - Step by Step

## Current Situation

- ✅ Dashboard code editor is **read-only** (expected for custom agents)
- ✅ Need to deploy via **LiveKit CLI** (official method for custom code)
- ⏳ LiveKit CLI installation in progress

## Installation Methods

### Method 1: Install via pip (Python) - Recommended

```bash
# Make sure you're using the right Python version
python3 --version

# Install livekit-agents package (includes CLI)
pip3 install livekit-agents --upgrade

# Verify installation
python3 -m livekit.agents.cli --help
```

If this doesn't work, try:
```bash
# Install with user flag
pip3 install --user livekit-agents --upgrade

# Or install in a virtual environment (recommended)
cd backend
python3 -m venv venv
source venv/bin/activate
pip install livekit-agents --upgrade
python -m livekit.agents.cli --help
```

### Method 2: Install via Homebrew (macOS)

```bash
brew install livekit/livekit/livekit-cli
```

### Method 3: Install via npm (if available)

```bash
npm install -g @livekit/cli
```

---

## After Installation: Deploy Agent

Once LiveKit CLI is installed, follow these steps:

### Step 1: Navigate to Backend Directory

```bash
cd /Users/user/Fortell_AI_Product/backend
```

### Step 2: Authenticate with LiveKit Cloud

```bash
# If using pip installation:
python3 -m livekit.agents.cli cloud auth

# OR if CLI is in PATH:
livekit cloud auth
# OR
lk cloud auth
```

This will open a browser to link your LiveKit Cloud project.

### Step 3: Create Agent Configuration

```bash
# If using pip installation:
python3 -m livekit.agents.cli agent create

# OR if CLI is in PATH:
livekit agent create
# OR
lk agent create
```

This creates a `livekit.toml` configuration file.

### Step 4: Configure Secrets

**Option A: Add Secrets in Dashboard** (Recommended)

1. Go to LiveKit Cloud dashboard → Agents → Advanced tab
2. In "Secrets" section, add:
   - `OPENAI_API_KEY` = your OpenAI key
   - (Other secrets as needed)
3. Click "Save changes"

**Option B: Add to livekit.toml** (for local development)

Edit `livekit.toml`:
```toml
[env]
OPENAI_API_KEY = "sk-proj-..."
LLM_PROVIDER = "openai"
STT_PROVIDER = "openai"
TTS_PROVIDER = "openai"
```

**Important**: Never commit secrets to git! Use `.gitignore` for `livekit.toml` if it contains secrets.

### Step 5: Deploy Agent

```bash
# If using pip installation:
python3 -m livekit.agents.cli agent deploy

# OR if CLI is in PATH:
livekit agent deploy
# OR
lk agent deploy
```

This will:
- Build Docker image from `Dockerfile`
- Push to LiveKit Cloud
- Deploy agent as worker service
- Use secrets from dashboard or `livekit.toml`

### Step 6: Check Status

```bash
# If using pip installation:
python3 -m livekit.agents.cli agent status

# OR if CLI is in PATH:
livekit agent status
# OR
lk agent status
```

### Step 7: View Logs

```bash
# If using pip installation:
python3 -m livekit.agents.cli agent logs

# OR if CLI is in PATH:
livekit agent logs
# OR
lk agent logs
```

Look for: "Stage 1 agent started" or "Agent initialized"

---

## Troubleshooting Installation

### "ModuleNotFoundError: No module named 'livekit'"

**Problem**: Package installed to wrong Python version.

**Solution**:
```bash
# Check which Python pip3 is using
pip3 show livekit-agents

# Or create virtual environment (recommended)
cd backend
python3 -m venv venv
source venv/bin/activate
pip install livekit-agents
python -m livekit.agents.cli --help
```

### "Command not found: livekit" or "Command not found: lk"

**Problem**: CLI not in PATH or using pip installation.

**Solution**: Use `python3 -m livekit.agents.cli` instead of `livekit` or `lk`

### "Permission denied" during installation

**Problem**: Need sudo or user installation.

**Solution**:
```bash
# Install for current user only
pip3 install --user livekit-agents --upgrade

# OR use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install livekit-agents
```

---

## Quick Reference: CLI Commands

**If using pip installation (no PATH entry):**
```bash
python3 -m livekit.agents.cli cloud auth
python3 -m livekit.agents.cli agent create
python3 -m livekit.agents.cli agent deploy
python3 -m livekit.agents.cli agent status
python3 -m livekit.agents.cli agent logs
```

**If CLI is in PATH (after Homebrew or npm install):**
```bash
livekit cloud auth
livekit agent create
livekit agent deploy
livekit agent status
livekit agent logs

# OR shorter alias:
lk cloud auth
lk agent create
lk agent deploy
lk agent status
lk agent logs
```

---

## Next Steps

1. **Complete CLI installation** (try pip method in virtual environment)
2. **Authenticate with LiveKit Cloud** (`cloud auth`)
3. **Create agent** (`agent create`)
4. **Add secrets in dashboard** (Advanced tab → Secrets)
5. **Deploy agent** (`agent deploy`)
6. **Test end-to-end** with frontend

---

## Alternative: Deploy via Git Repository (If Dashboard Supports It)

Some LiveKit Cloud dashboards support connecting a Git repository. If your dashboard has this option:

1. Push your code to GitHub (already done)
2. In LiveKit Cloud dashboard → Agents → Code tab
3. Look for "Connect Repository" or "Git Repository" option
4. Connect your GitHub repository
5. Set root directory: `backend/`
6. Deploy

But since the code editor is read-only, this option might not be available in your dashboard version.

---

## Summary

Since the dashboard code editor is read-only, we **must use CLI deployment**. This is actually the **official method** for custom Python agents.

**Current status**: Installation in progress. Once complete, follow the deployment steps above.

**Recommended approach**: Use pip installation in a virtual environment for clean dependency management.

