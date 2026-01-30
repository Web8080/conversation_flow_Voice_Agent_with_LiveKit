# Voice Agent with LiveKit - Complete Implementation

A production-ready real-time voice agent system built with LiveKit, featuring state-machine-based conversation flows, comprehensive security, monitoring, and professional UI/UX design. This full-stack application enables natural voice interactions through advanced Speech-to-Text (STT), Large Language Model (LLM), and Text-to-Speech (TTS) integration, deployed on LiveKit Cloud and Vercel.

## About

This project demonstrates a complete end-to-end voice agent implementation combining real-time WebRTC communication, AI-powered natural language processing, and cloud infrastructure. The system features a Python backend with state machine-based conversation management, a Next.js TypeScript frontend, and comprehensive DevOps practices including security scanning, monitoring, and automated deployment.

**Key Technologies**: Python, Next.js, TypeScript, LiveKit, Google Cloud (Speech-to-Text, Text-to-Speech, Gemini), OpenAI (fallback), WebRTC, PostgreSQL, Docker, Vercel, LiveKit Cloud

## Architecture Overview

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Next.js Frontend (React + TypeScript)            │  │
│  │  • LiveKit Client SDK                                    │  │
│  │  • Audio Capture (Microphone)                            │  │
│  │  • Audio Playback (Speakers)                             │  │
│  │  • UI Components (VoiceAgentUI, StateProgressIndicator)  │  │
│  └───────────────────┬──────────────────────────────────────┘  │
└──────────────────────┼──────────────────────────────────────────┘
                       │ WebRTC (DTLS/SRTP)
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LiveKit Cloud (Media Server)                 │
│  • WebRTC Signaling                                             │
│  • Audio Stream Routing                                         │
│  • Room Management                                              │
│  • Participant Tracking                                         │
└───────────────────────┬──────────────────────────────────────────┘
                       │ gRPC/WebSocket
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│              Python Voice Agent (Backend)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ STT Service  │  │ LLM Service  │  │ TTS Service  │        │
│  │ (Google/     │  │ (Gemini/     │  │ (Google/     │        │
│  │  OpenAI)     │  │  OpenAI)     │  │  OpenAI)     │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                 │                 │                 │
│         └─────────┬───────┴─────────────────┘                 │
│                   │                                             │
│         ┌─────────▼─────────┐                                  │
│         │  State Machine    │                                  │
│         │  • Greeting       │                                  │
│         │  • CollectDate    │                                  │
│         │  • CollectTime    │                                  │
│         │  • Confirmation   │                                  │
│         │  • Terminal       │                                  │
│         │  • Fallback       │                                  │
│         └─────────┬─────────┘                                  │
│                   │                                             │
│         ┌─────────▼─────────┐                                  │
│         │ Conversation      │                                  │
│         │ Context Manager   │                                  │
│         │ • Slots           │                                  │
│         │ • History         │                                  │
│         │ • State Tracking  │                                  │
│         └─────────┬─────────┘                                  │
└───────────────────┼─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│              External Services                                   │
│  • Google Cloud Speech-to-Text                                  │
│  • Google Cloud Text-to-Speech                                  │
│  • Google Gemini (LLM)                                           │
│  • Google Calendar API                                           │
│  • OpenAI (Fallback for STT/LLM/TTS)                            │
└─────────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│              PostgreSQL + TimescaleDB                            │
│  • Conversations                                                │
│  • Conversation Turns                                           │
│  • State Transitions                                            │
│  • Extracted Slots                                              │
│  • System Metrics (Time-series)                                │
│  • Error Logs                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture

**Stage 1/2 (Legacy - Fixed Buffer):**
```
User Speech → [Microphone] → [LiveKit] → [Audio Buffer 1.5s] → [STT] → [State Machine] → [LLM] → [TTS] → [LiveKit] → [Speakers]
```

**Stage 3 (New - VAD-based):**
```
User Speech
    │
    ▼
[Browser Microphone]
    │
    ▼
[LiveKit WebRTC] ──────────► [Python Agent]
    │                              │
    │                              ▼
    │                    [VAD Processor]  ◄── NEW: Detects speech boundaries
    │                    • Speech detection
    │                    • End-of-speech detection
    │                    • Barge-in support
    │                              │
    │                              ▼ (only when speech complete)
    │                    [STT Service]
    │                              │
    │                              ▼
    │                    [Flow Engine]  ◄── NEW: JSON-driven
    │                    • Load JSON flow
    │                    • Execute nodes
    │                    • Evaluate transitions
    │                    • Extract variables
    │                              │
    │                              ▼
    │                    [LLM Service]
    │                              │
    │                              ▼
    │                    [Response Text]
    │                              │
    │                              ▼
    │                    [TTS Service]
    │                              │
    │                              ▼
    │                    [Audio Stream]
    │                              │
    └──────────────────────────────┘
              │
              ▼
    [LiveKit WebRTC]
              │
              ▼
    [Browser Speakers]
              │
              ▼
    User Hears Response
```

### State Machine Flow (Drill-Down)

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Greeting   │◄────────┐
                    │  State      │         │
                    └──────┬──────┘         │
                           │                │
                           │ (User responds)│
                           ▼                │
                    ┌─────────────┐         │
                    │ CollectDate │         │
                    │   State     │         │
                    └──────┬──────┘         │
                           │                │
                           │ (Date extracted)│
                           ▼                │
                    ┌─────────────┐         │
                    │ CollectTime │         │
                    │   State     │         │
                    └──────┬──────┘         │
                           │                │
                           │ (Time extracted)│
                           ▼                │
                    ┌─────────────┐         │
                    │ Confirmation│         │
                    │   State     │         │
                    └──────┬──────┘         │
                           │                │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        │ (Confirmed)      │ (Rejected)       │ (Error)
        ▼                  ▼                  ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  Terminal   │   │ CollectDate  │   │  Fallback   │
│   State     │   │   (Reset)    │   │   State     │
│             │   └──────────────┘   │             │
│ • Book      │                      │ • Retry     │
│   Calendar  │                      │ • Clarify   │
│ • End       │                      │ • Escalate  │
│   Session   │                      └──────┬──────┘
└──────┬──────┘                             │
       │                                    │
       │                                    │ (Retry < Max)
       │                                    └──────────┐
       │                                                │
       └────────────────────────────────────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │     END     │
                    └─────────────┘
```


## Quick Start

```bash
# 1. Configure services (see services/SERVICES_SETUP.md)
# 2. Set up environment variables
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# 3. Install and run
./launch.sh
```

See `docs/QUICKSTART.md` for detailed instructions.

## Project Structure

```
 backend/ # Python agent (STT/LLM/TTS + State Machine)
 frontend/ # Next.js UI (React + LiveKit Client)
 docs/ # Documentation (all .md files)
 uiux/ # UI/UX Design (Wireframes, Mockups, User Flows)
 database/ # Database Schema & Migrations
 security/ # DevSecOps (Security Scans, Pentest Checklist)
 monitoring/ # Logging Strategy & Observability
 services/ # External Services Setup Guide
```

## Features

### Core Functionality
- [x] Real-time voice interaction via LiveKit
- [x] Speech-to-Text (Google Cloud Speech-to-Text primary + OpenAI fallback)
- [x] LLM (Google Gemini primary + OpenAI/Ollama fallback)
- [x] Text-to-Speech (Google Cloud TTS primary + OpenAI fallback)
- [x] State machine conversation flow (5+ states)
- [x] Appointment scheduling use case

### Professional Features
- [x] **UI/UX Design**: Complete wireframes, mockups, user journey maps
- [x] **Database Schema**: PostgreSQL + TimescaleDB with full migrations
- [x] **Security**: Automated scanning, pentest checklist, config validation
- [x] **Monitoring**: Structured logging, metrics, distributed tracing
- [x] **DevSecOps**: Security-first approach with automated checks

---

## 🆕 New Implementation: Stage 3 - JSON-Driven Flow Engine with VAD

### Overview

Stage 3 introduces a **Retell AI-style** conversational flow system with intelligent speech detection:

```
┌─────────────────────────────────────────────────────────────┐
│                     Stage 3 Architecture                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  User Audio → [VAD] → [STT] → [Flow Engine] → [TTS] → Audio │
│                                    │                        │
│                         ┌──────────┴──────────┐             │
│                         │   JSON Flow File    │             │
│                         │  • Nodes            │             │
│                         │  • Edges            │             │
│                         │  • Transitions      │             │
│                         │  • Variables        │             │
│                         └─────────────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

### Key Improvements

| Problem | Before (Stage 1/2) | After (Stage 3) |
|---------|-------------------|-----------------|
| **Bot responds too fast** | Fixed 1.5s audio buffer | VAD detects actual speech boundaries |
| **Hardcoded flows** | Python code changes required | JSON config - edit & restart |
| **Limited transitions** | Basic state machine | Equation + LLM-evaluated conditions |
| **Variable handling** | Simple slot dict | Dynamic variable store with interpolation |

### 1. Voice Activity Detection (VAD)

Fixes the "bot responds too fast" problem:

```python
# Before: Process every 1.5 seconds regardless of user speech
self.buffer_duration = 1.5  # Fixed timing

# After: Wait for actual speech boundaries
VAD_CONFIG = {
    "silence_threshold_ms": 600,    # Wait 600ms silence before responding
    "min_speech_duration_ms": 250,  # Ignore very short sounds
    "allow_interruptions": True     # User can interrupt agent
}
```

### 2. JSON-Driven Conversation Flows

Define flows in JSON without code changes:

```json
{
  "id": "appointment-booking",
  "start_node_id": "greeting",
  "nodes": [
    {
      "id": "greeting",
      "type": "conversation",
      "instruction": "Greet the user and ask for their name",
      "extract_variables": ["name"],
      "edges": [
        {
          "target_node_id": "collect_date",
          "conditions": [
            { "type": "prompt", "condition": "User provided their name" }
          ]
        }
      ]
    }
  ]
}
```

### 3. Node Types

| Node Type | Purpose |
|-----------|---------|
| `conversation` | Dialogue with user, variable extraction |
| `function` | Execute registered functions (calendar, APIs) |
| `logic_split` | Conditional branching based on variables |
| `end` | Terminate conversation |
| `transfer` | Handoff to human agent |

### 4. Transition Conditions

**Equation-based** (fast, no LLM call):
```json
{ "type": "equation", "condition": "{{name}} exists AND {{date}} exists" }
```

**Prompt-based** (intelligent, LLM evaluates):
```json
{ "type": "prompt", "condition": "User confirmed the appointment" }
```

### Quick Start

1. **Enable Stage 3** in `.env`:
   ```bash
   AGENT_STAGE=stage3
   ```

2. **Run the agent**:
   ```bash
   cd backend
   python main.py dev
   ```

3. **Customize** by editing `backend/flows/appointment_booking.json`

### New Files

```
backend/
├── agent/flow_engine/
│   ├── schema.py            # JSON schema definitions
│   ├── engine.py            # Flow orchestrator
│   ├── nodes.py             # Node execution
│   ├── dynamic_variables.py # Variable interpolation
│   └── vad_processor.py     # Voice Activity Detection
├── flows/
│   └── appointment_booking.json  # Sample flow
└── main_stage3.py           # Stage 3 entry point
```

### Configuration

```bash
# .env settings
AGENT_STAGE=stage3              # Enable Stage 3
VAD_ENABLED=true                # Enable VAD
VAD_SILENCE_THRESHOLD_MS=600    # Silence to detect end of speech
VAD_MIN_SPEECH_DURATION_MS=250  # Minimum speech to process
ALLOW_INTERRUPTIONS=true        # Let user interrupt agent
```

**Full documentation**: See [`docs/STAGE3_FLOW_ENGINE.md`](docs/STAGE3_FLOW_ENGINE.md)

---

## Documentation

### Getting Started
- **[QUICKSTART.md](docs/QUICKSTART.md)** - Get running in 5 minutes
- **[SETUP_AND_RUN.md](docs/SETUP_AND_RUN.md)** - Detailed setup guide
- **[services/SERVICES_SETUP.md](services/SERVICES_SETUP.md)** - Service configuration

### Design & Architecture
- **[VOICE_AGENT_DESIGN.md](docs/VOICE_AGENT_DESIGN.md)** - System design (presentation-ready)
- **[COMPLETE_SYSTEM_OVERVIEW.md](docs/COMPLETE_SYSTEM_OVERVIEW.md)** - Full system overview

### Implementation Details
- **[database/SCHEMA_DESIGN.md](database/SCHEMA_DESIGN.md)** - Database schema
- **[monitoring/LOGGING_STRATEGY.md](monitoring/LOGGING_STRATEGY.md)** - Observability
- **[security/scripts/](security/scripts/)** - Security scanning tools
- **[STAGE3_FLOW_ENGINE.md](docs/STAGE3_FLOW_ENGINE.md)** - Stage 3 JSON flow engine & VAD 🆕


## Tech Stack

**Backend**
- Python 3.11+
- LiveKit Python SDK
- Google Cloud (STT/TTS/LLM primary)
- OpenAI (STT/TTS/LLM fallback)
- Ollama (Local LLM fallback)
- PostgreSQL + TimescaleDB

**Frontend**
- Next.js 14 (TypeScript)
- LiveKit Client SDK
- Tailwind CSS
- React

**Infrastructure**
- Docker & Docker Compose
- LiveKit Cloud
- Vercel (Frontend deployment)

## Security

```bash
# Run security scan
python security/scripts/security_scan.py

# Check dependencies
./security/scripts/dependency_audit.sh

# Validate configuration
python security/scripts/config_validator.py
```

## Monitoring

- Structured JSON logging
- Prometheus-compatible metrics
- Distributed tracing (Jaeger/Zipkin)
- Real-time dashboards
- Automated alerting

## Database

PostgreSQL schema with:
- Conversation tracking
- State transitions
- Extracted slots
- System metrics (TimescaleDB)
- Error logs
- User feedback

See `database/SCHEMA_DESIGN.md` for complete schema.

## Installation

```bash
# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

## Deployment

### Development
```bash
./launch.sh
```

### Production
- Backend: Deploy to LiveKit Cloud
- Frontend: Deploy to Vercel
- Database: Managed PostgreSQL (AWS RDS, etc.)

See `docs/SETUP_AND_RUN.md` for detailed deployment instructions.

## Project Status

### Core Implementation 
- [x] Backend implementation complete
- [x] Frontend implementation complete
- [x] State machine implementation complete (Stage 1/2)
- [x] **JSON Flow Engine implementation complete (Stage 3)** 🆕
- [x] **Voice Activity Detection (VAD) implemented** 🆕
- [x] Authentication system implemented

### Design & Documentation 
- [x] UI/UX design documentation complete
- [x] Database schema designed
- [x] System design documents complete
- [x] API documentation (OpenAPI spec)

### DevOps & Operations 
- [x] Security scripts implemented
- [x] Monitoring strategy defined
- [x] CI/CD pipeline configured
- [x] Testing framework set up
- [x] Deployment scripts ready
- [x] Backup & recovery scripts
- [x] Incident response runbooks
- [x] Developer onboarding guide

### Code Quality 
- [x] Pre-commit hooks configured
- [x] Linting and formatting setup
- [x] Code quality standards defined

**Status**: Production-ready framework complete. Ready for service configuration, test implementation, and deployment.

**See**: `docs/SDLC_COMPLETE.md` for complete SDLC overview

## Next Steps


### Performance optimization

- **Tune VAD parameters** (silence threshold, min speech duration)
- **Add caching for common responses**
- **Optimize audio processing pipeline**
- **Parallelize STT/LLM calls where possible**

### Error handling

- **Better error messages for users**
- **Retry logic for failed API calls**
- **Graceful degradation when services are down**

### Feature enhancements

- **Multi-language support**
  - Detect user language
  - Configure STT/LLM/TTS for multiple languages
  - Localize UI and prompts
- **User authentication**
  - Add login/signup
  - Personalize conversations
  - Store user preferences and history
- **Email/SMS notifications**
  - Send appointment confirmations
  - Reminders before appointments
  - Follow-up messages
- **Analytics dashboard**
  - Track conversation success rates
  - Monitor agent performance
  - Identify drop-off points

### Production readiness

- **Testing suite**
  - Unit tests for state machine
  - Integration tests for API calls
  - E2E tests for full conversation flow
- **Monitoring and alerting**
  - Set up error tracking (Sentry, etc.)
  - Performance monitoring
  - Alert on critical failures
- **Documentation**
  - API documentation
  - Deployment runbooks
  - Troubleshooting guides

## Contributing

For questions or improvements, see documentation.

## License

This project is open source.

---

**Built by Victor ibhafidon with** clarity, structure, and correctness in mind. 
**Designed for** production readiness and scalability.
