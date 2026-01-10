# Deploy Agent Code via LiveKit Cloud Dashboard

## Overview

The LiveKit Cloud dashboard has a **Code** tab where you can write/edit Python agent code directly in the browser. The code shown uses LiveKit's built-in `AgentServer`/`AgentSession` framework which simplifies deployment.

## What You're Seeing

The dashboard code editor shows a **template** using LiveKit's built-in inference services:
- **STT**: AssemblyAI Universal-Streaming (or OpenAI Whisper)
- **LLM**: OpenAI GPT-4.1 mini
- **TTS**: Cartesia Sonic 3

This is different from our custom implementation, but **easier to deploy** and works perfectly with the dashboard.

## Option 1: Use Dashboard Code Editor (Simplest)

### Step 1: Replace Code in Dashboard

1. **Go to the "Code" tab** (you're already there!)

2. **Delete all the existing code** in the editor

3. **Copy and paste** the code from `backend/agent_dashboard.py`

   OR use this simplified version:

```python
import logging
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
    room_io,
)
from livekit.plugins import (
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent-voice-assistant")

load_dotenv()

STAGE1_SYSTEM_PROMPT = """You are a helpful and friendly voice assistant. 
Respond naturally to the user's questions and conversations. 
Keep your responses concise (1-2 sentences) suitable for voice interaction.
Be conversational and helpful."""


class DefaultAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=STAGE1_SYSTEM_PROMPT + """

# Output rules
- Respond in plain text only. Never use JSON, markdown, lists, tables, code, emojis.
- Keep replies brief: one to three sentences. Ask one question at a time.
- Spell out numbers, phone numbers, or email addresses.
- Omit https:// and other formatting if listing a web url.

# Guardrails
- Stay within safe, lawful, and appropriate use.
- For medical, legal, or financial topics, provide general information only.
- Protect privacy and minimize sensitive data.
""",
        )

    async def on_enter(self):
        await self.session.generate_reply(
            instructions="""Greet the user: "Hello! I'm your voice assistant. How can I help you today?" """,
            allow_interruptions=True,
        )


server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    logger.info("VAD model preloaded")


server.setup_fnc = prewarm


@server.rtc_session(agent_name="appointment-scheduler")
async def entrypoint(ctx: JobContext):
    logger.info("Agent job started", room=ctx.room.name)
    
    session = AgentSession(
        stt=inference.STT(
            model="assemblyai/universal-streaming",
            language="en"
        ),
        llm=inference.LLM(
            model="openai/gpt-4.1-mini"
        ),
        tts=inference.TTS(
            model="cartesia/sonic-3",
            voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
            language="en"
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(
        agent=DefaultAgent(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony() 
                    if params.participant.kind == rtc.ParticipantKind.PARTICIPANT_KIND_SIP 
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )


if __name__ == "__main__":
    cli.run_app(server)
```

4. **Click "Save changes"** (top right)

### Step 2: Add Secrets in Advanced Tab

1. **Go to "Advanced" tab** (left panel)

2. **In "Secrets" section**, click **"+ Add secret"** for each:

   ```
   Key: OPENAI_API_KEY
   Value: YOUR_OPENAI_API_KEY
   ```

   ```
   Key: ASSEMBLYAI_API_KEY
   Value: (optional - LiveKit may use built-in AssemblyAI if not set)
   ```

   ```
   Key: CARTESIA_API_KEY
   Value: (optional - LiveKit may use built-in Cartesia if not set)
   ```

   **Note**: For STT and TTS, LiveKit Cloud may provide default API keys. If you have issues, you may need to:
   - Sign up for AssemblyAI API key (for STT)
   - Sign up for Cartesia API key (for TTS)
   - OR use OpenAI for both STT and TTS (configure in code)

3. **Click "Save changes"**

### Step 3: Configure Models (Optional)

1. **Go to "Models & Voice" tab** (left panel)

2. The models should match what's in the code:
   - **STT**: AssemblyAI Universal-Streaming
   - **LLM**: GPT-4.1 mini
   - **TTS**: Cartesia Sonic 3

3. These are already configured, so you may not need to change anything.

### Step 4: Deploy Agent

1. **Click "Deploy agent"** button (top right, blue button)

2. **Wait for deployment** to complete

3. **Status should change** from "PENDING" to "RUNNING" or "ACTIVE"

4. **Check logs** if there are errors (usually shown in dashboard or via CLI: `lk agent logs`)

---

## Option 2: Use LiveKit CLI (For Custom Code)

If you want to use your **custom Python code** (with your own STT/LLM/TTS services), use the CLI method instead:

### Step 1: Install LiveKit CLI

```bash
npm install -g livekit-cli
# OR
pip install livekit-cli
```

### Step 2: Authenticate

```bash
cd backend
lk cloud auth
```

### Step 3: Deploy Custom Code

```bash
lk agent create  # First time only
lk agent deploy  # Deploys your custom main.py
```

This will deploy `backend/main.py` with your custom services.

**Note**: Your custom code uses `JobContext` and `WorkerOptions`, which works perfectly with CLI deployment but may not work directly in the dashboard code editor.

---

## Which Method to Use?

### Use Dashboard Code Editor (Option 1) If:
- ✅ You want the simplest deployment
- ✅ You're okay using LiveKit's built-in inference services
- ✅ You want to edit code in the browser
- ✅ You want to use the dashboard UI for configuration

### Use CLI Method (Option 2) If:
- ✅ You need your custom STT/LLM/TTS services
- ✅ You have complex custom logic
- ✅ You want to keep your current code structure
- ✅ You prefer version control and local development

---

## Important Notes

### For Dashboard Code Editor:

1. **Environment Variables**: The code uses `load_dotenv()` which may not work in the dashboard. Instead, use **Secrets** in the Advanced tab - they're automatically available as environment variables.

2. **API Keys**: 
   - **OpenAI API Key** is required for LLM (GPT-4.1 mini)
   - **AssemblyAI API Key** may be required for STT (or LiveKit provides default)
   - **Cartesia API Key** may be required for TTS (or LiveKit provides default)

3. **Custom Services**: If you need your custom services (OpenAI Whisper STT, custom LLM logic, etc.), use the CLI method instead.

---

## Troubleshooting

### "Module not found" errors

- The dashboard may have limitations on what modules can be imported
- Use only LiveKit SDK modules and standard library
- If you need custom modules, use CLI deployment instead

### "API key not found" errors

- Ensure secrets are added in Advanced tab
- Verify secret names match what the code expects
- Check that secrets are saved before deploying

### Agent stays "PENDING"

- Check deployment logs in dashboard
- Verify code syntax is correct
- Ensure all required secrets are added
- Try deploying via CLI as an alternative

---

## Next Steps

1. **Choose deployment method** (Dashboard or CLI)
2. **Add secrets** in Advanced tab (at minimum: OPENAI_API_KEY)
3. **Deploy agent** via dashboard or CLI
4. **Test end-to-end** with frontend: https://conversation-flow-voice-agent-with.vercel.app

---

## Quick Reference

**Dashboard Method**:
- Edit code in "Code" tab
- Add secrets in "Advanced" tab
- Click "Deploy agent"

**CLI Method**:
```bash
npm install -g livekit-cli
cd backend
lk cloud auth
lk agent create
lk agent deploy
```

