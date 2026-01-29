# Stage 3: JSON-Driven Conversational Flow Engine

## Overview

Stage 3 introduces a Retell AI-style conversational flow system with:

1. **JSON-Driven Flows** - Define conversation flows in JSON, no code changes needed
2. **Voice Activity Detection (VAD)** - Properly detects when users finish speaking
3. **Node-Based Architecture** - Multiple node types for different conversation scenarios
4. **Dynamic Variables** - Extract and interpolate variables throughout the conversation
5. **Intelligent Transitions** - Both equation-based and LLM-evaluated transition conditions

## Key Improvements Over Stage 1/2

### Problem: "Bot Responds Too Fast"

**Before (Stage 1/2):** Fixed 1.5-second audio buffer - bot responds every 1.5 seconds regardless of whether user finished speaking.

**After (Stage 3):** Voice Activity Detection (VAD) detects actual speech boundaries. Bot waits for natural pauses to indicate user finished speaking.

### Problem: Hardcoded Conversation Flows

**Before:** States defined in Python classes. Any change requires code deployment.

**After:** Flows defined in JSON files. Update `flows/appointment_booking.json` and restart.

## Quick Start

### 1. Enable Stage 3

Set in your `.env`:

```bash
AGENT_STAGE=stage3
```

### 2. Run the Agent

```bash
cd backend
python main.py dev
```

The agent will:
1. Load the flow from `flows/appointment_booking.json`
2. Initialize VAD for speech detection
3. Start conversation with the initial greeting

## Flow JSON Structure

```json
{
  "id": "my-flow",
  "name": "My Conversation Flow",
  "version": "1.0.0",
  
  "global_settings": {
    "system_prompt": "You are a helpful assistant...",
    "vad_enabled": true,
    "silence_threshold_ms": 600,
    "allow_interruptions": true
  },
  
  "start_node_id": "greeting",
  
  "nodes": [
    {
      "id": "greeting",
      "type": "conversation",
      "name": "Greeting",
      "instruction": "Greet the user...",
      "response_template": "Hello! How can I help?",
      "extract_variables": ["name"],
      "edges": [
        {
          "id": "greeting-to-next",
          "target_node_id": "next_node",
          "conditions": [
            {
              "type": "prompt",
              "condition": "User provided their name"
            }
          ]
        }
      ]
    }
  ]
}
```

## Node Types

### Conversation Node
Handles dialogue with users. Can extract variables and generate responses.

```json
{
  "id": "collect_date",
  "type": "conversation",
  "instruction": "Ask for appointment date",
  "extract_variables": ["date"],
  "response_template": "What date works for you, {{name}}?"
}
```

### Function Node
Executes registered functions (API calls, calendar booking, etc.)

```json
{
  "id": "book_appointment",
  "type": "function",
  "function_name": "create_calendar_event",
  "parameters": {
    "name": "{{name}}",
    "date": "{{date}}"
  },
  "success_message": "Booked! See you on {{date}}."
}
```

### Logic Split Node
Routes based on variable conditions (no dialogue).

```json
{
  "id": "check_vip",
  "type": "logic_split",
  "edges": [
    {
      "target_node_id": "vip_flow",
      "conditions": [{"type": "equation", "condition": "{{is_vip}} == true"}]
    },
    {
      "target_node_id": "normal_flow",
      "is_default": true
    }
  ]
}
```

### End Node
Terminates the conversation.

```json
{
  "id": "end_success",
  "type": "end",
  "message": "Thank you! Goodbye!",
  "end_reason": "completed"
}
```

### Transfer Node
Transfers to a human agent.

```json
{
  "id": "transfer",
  "type": "transfer",
  "message": "Let me connect you with someone...",
  "destination": "support_queue"
}
```

## Transition Conditions

### Equation Conditions (Fast)
Evaluated without LLM call. Use for variable checks.

```json
{
  "type": "equation",
  "condition": "{{age}} >> 18"
}
```

Supported operators:
- `>>` greater than
- `<<` less than
- `==` equals
- `!=` not equals
- `>=` greater or equal
- `<=` less or equal
- `CONTAINS` string contains
- `NOT CONTAINS` string does not contain
- `exists` variable exists
- `not exists` variable does not exist
- `AND` / `OR` logical operators

### Prompt Conditions (Intelligent)
LLM evaluates if user input matches condition.

```json
{
  "type": "prompt",
  "condition": "User confirmed the appointment"
}
```

## VAD Configuration

In `global_settings`:

```json
{
  "vad_enabled": true,
  "silence_threshold_ms": 600,    // Wait 600ms of silence before processing
  "min_speech_duration_ms": 250,  // Ignore speech shorter than 250ms
  "allow_interruptions": true     // Let user interrupt agent
}
```

Or in `.env`:

```bash
VAD_ENABLED=true
VAD_SILENCE_THRESHOLD_MS=600
VAD_MIN_SPEECH_DURATION_MS=250
ALLOW_INTERRUPTIONS=true
```

## Dynamic Variables

### Setting Variables
Variables are extracted from user input using LLM:

```json
{
  "extract_variables": ["name", "date", "time"]
}
```

### Using Variables
Interpolate with `{{variable_name}}`:

```json
{
  "response_template": "Hello {{name}}, your appointment is on {{date}} at {{time}}."
}
```

### Checking Variables in Transitions

```json
{
  "type": "equation",
  "condition": "{{name}} exists AND {{date}} exists"
}
```

## Registering Custom Functions

In your agent code:

```python
# Register function
flow_engine.register_function("send_sms", send_sms_function)

# Function signature
async def send_sms_function(phone: str, message: str) -> dict:
    # Your implementation
    return {"success": True, "message_id": "123"}
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Stage 3 Agent                        │
├─────────────────────────────────────────────────────────────┤
│  User Audio → VAD → STT → Flow Engine → TTS → Agent Audio  │
│                           │                                 │
│              ┌────────────┴────────────┐                    │
│              │      Flow Engine        │                    │
│              │  ┌──────────────────┐   │                    │
│              │  │ JSON Flow Loader │   │                    │
│              │  │ Node Executor    │   │                    │
│              │  │ Edge Evaluator   │   │                    │
│              │  │ Variable Store   │   │                    │
│              │  └──────────────────┘   │                    │
│              └─────────────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

## Migration from Stage 1/2

1. Set `AGENT_STAGE=stage3` in `.env`
2. Create your flow JSON in `backend/flows/`
3. Restart the agent

The Stage 3 agent is backward compatible - if no flow file is found, it uses a default minimal flow.

## Files Created

```
backend/
├── agent/
│   └── flow_engine/
│       ├── __init__.py          # Module exports
│       ├── schema.py            # JSON schema definitions
│       ├── engine.py            # Main flow engine
│       ├── nodes.py             # Node execution logic
│       ├── dynamic_variables.py # Variable store & interpolation
│       └── vad_processor.py     # Voice Activity Detection
├── flows/
│   └── appointment_booking.json # Sample flow
└── main_stage3.py               # Stage 3 entry point
```

## Comparison with Retell AI

| Feature | Fortell Stage 3 | Retell AI |
|---------|-----------------|-----------|
| JSON Flows | ✅ | ✅ |
| Node Types | 5 types | 10+ types |
| VAD | Silero/Energy | Built-in |
| Transitions | Prompt + Equation | Prompt + Equation |
| Variables | ✅ | ✅ |
| Visual Editor | ❌ | ✅ |
| Flex Mode | ❌ | ✅ |

The Stage 3 implementation covers the core Retell architecture patterns while remaining lightweight and self-hosted.
