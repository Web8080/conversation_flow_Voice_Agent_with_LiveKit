# Voice Agent System Design (LiveKit + Python)

## 1. Overview

This project implements a real-time voice agent using LiveKit. 
The agent joins a LiveKit room, listens to user speech, transcribes it, processes it via an LLM, and responds with synthesized speech.

The system is designed in two stages:
- **Stage 1:** Stateless single-prompt voice agent
- **Stage 2:** Structured, state-based conversation flow (DAG)

The primary goal is correctness, clarity, and extensibility rather than UI polish.

---

## 2. Goals & Non-Goals

### Goals
- Real-time voice interaction via LiveKit
- Clear separation of audio, NLP, and conversation logic
- Deterministic conversation flow using states
- Graceful handling of misunderstandings
- Deployable to LiveKit Cloud

### Non-Goals
- Ultra-low latency optimization
- Advanced UI/UX
- Fully production-hardened monitoring

---

## 3. User Requirements

### Functional Requirements
- User can speak to the agent via browser
- Agent responds with synthesized speech
- Agent maintains conversational context
- Agent follows a structured conversation flow (Stage 2)

### Non-Functional Requirements
- Low perceived latency (< 2–3 seconds per turn)
- Clear failure and retry behavior
- Easy to reason about and extend

---

## 4. High-Level Architecture

```
[ Browser (Mic) ]
|
v
[ LiveKit Room ]
|
v
[ Python Voice Agent ]
| | |
| | |
[STT] [LLM] [TTS]
| |
+--------+
|
v
[ Audio Response → LiveKit ]
```

---

## 5. Component Responsibilities

### Frontend
- Join LiveKit room
- Capture microphone input
- Play agent audio output

### Voice Agent (Python)
- Connect to LiveKit room
- Receive audio streams
- Coordinate STT → LLM → TTS pipeline
- Maintain conversation state (Stage 2)

### Speech-to-Text (STT)
- Convert incoming audio to text
- Return partial or final transcripts

### LLM
- Generate responses
- Assist with intent classification and slot filling

### Text-to-Speech (TTS)
- Convert LLM output to audio
- Stream audio back to LiveKit

---

## 6. Wire Flow (Stage 1)

```
User speaks
↓
Audio captured in LiveKit
↓
Python agent receives audio
↓
STT converts audio → text
↓
Text sent to LLM
↓
LLM response text
↓
TTS converts text → audio
↓
Audio played back into room
```

This stage is **stateless**. Each user utterance is treated independently.

---

## 7. Conversation Flow Design (Stage 2)

### Use Case: Appointment Scheduling

The agent guides the user through scheduling an appointment.

### States

1. **GreetingState**
 - Introduces agent
 - Explains purpose

2. **CollectDateState**
 - Asks for preferred date
 - Extracts date entity

3. **CollectTimeState**
 - Asks for preferred time
 - Extracts time entity

4. **ConfirmationState**
 - Repeats collected info
 - Asks user to confirm

5. **FallbackState**
 - Handles unclear or invalid input
 - Prompts user to retry

6. **TerminalState**
 - Confirms booking
 - Ends conversation

---

## 8. Conversation State Diagram (DAG)

```
Greeting
↓
CollectDate 
↓ 
CollectTime 
↓ 
Confirmation ←
↓
Terminal

Fallback can be entered from any state and returns to the previous state.
```

---

## 9. State Transition Logic

- Each state defines:
 - Prompt to the user
 - Expected input (intent/slots)
 - Transition conditions

### Example:
- Transition from `CollectDateState` → `CollectTimeState`
 - Condition: valid date extracted
- Transition to `FallbackState`
 - Condition: low confidence or invalid input

---

## 10. Why State-Based Design for Voice

Voice interactions are:
- Linear
- Error-prone
- Ambiguous

A state-based approach:
- Makes agent behavior predictable
- Simplifies retry logic
- Avoids hallucinated flow jumps
- Improves user trust

LLMs assist within states but do not control the flow.

---

## 11. Deployment Strategy

### Backend
- Deployed to LiveKit Cloud
- Environment variables for API keys

### Frontend
- Deployed to Vercel
- Minimal UI for joining room

---

## 12. Future Improvements

- Intent confidence scoring
- Partial transcript handling
- Analytics per state
- Multi-language support

---

## 13. UI/UX Design

### Design Philosophy
Minimalist, functional, trustworthy interface that supports voice-first interaction.

### Key Components
- **Connection Panel**: Room joining with status indicators
- **Conversation Area**: Chat-like interface with message bubbles
- **State Progress Indicator**: Visual feedback of conversation stage
- **Audio Controls**: Microphone and speaker toggles
- **Error Handling**: Clear error messages and recovery paths

### User Flows
1. **Connection Flow**: Initial → Connecting → Connected → Active
2. **Conversation Flow**: Greeting → Information Collection → Confirmation → Completion
3. **Error Recovery**: Clear error messages with retry options

Detailed wireframes, mockups, and user journey maps available in `uiux/` directory.

## 14. Database Design

### Schema Overview
- **Conversations**: Session tracking and metadata
- **Conversation Turns**: Individual message exchanges
- **State Transitions**: State machine transition logs
- **Extracted Slots**: Information extracted during conversation
- **Appointments**: Final appointment data (future integration)
- **System Metrics**: Performance and monitoring data (TimescaleDB)
- **Error Logs**: Error tracking and debugging
- **User Feedback**: User satisfaction and feedback

### Database Choice
- **Primary**: PostgreSQL (ACID compliance, relational data)
- **Time Series**: TimescaleDB extension for metrics
- **Optional**: MongoDB for flexible conversation logs

Complete schema design and migrations available in `database/` directory.

## 15. Security & DevSecOps

### Security Measures
- **Authentication**: LiveKit token-based authentication
- **Input Validation**: All user inputs sanitized and validated
- **Secrets Management**: Environment variables, no hardcoded credentials
- **API Security**: Rate limiting, CORS configuration, HTTPS enforcement
- **Dependency Scanning**: Automated vulnerability scanning
- **Penetration Testing**: Security checklist and automated tests

### Security Tools
- Automated security scanning script (`security/scripts/security_scan.py`)
- Dependency vulnerability checks (pip-audit, npm audit)
- Secrets detection in code
- API security validation
- CORS and configuration checks

Complete security documentation and pentest checklist in `security/` directory.

## 16. Observability & Monitoring

### Logging Strategy
- **Structured Logging**: JSON format for all logs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Categories**: Application, Access, Error, Security, Performance
- **Log Aggregation**: Centralized logging (ELK Stack, CloudWatch, etc.)

### Metrics Collection
- **Conversation Metrics**: Success rates, durations, abandonment
- **Service Metrics**: Latency (STT, LLM, TTS), error rates
- **State Machine Metrics**: Transitions, retry counts, fallback rates
- **Infrastructure Metrics**: CPU, memory, network, connections

### Monitoring Dashboards
- System health dashboard
- Conversation analytics dashboard
- Performance monitoring dashboard
- Business metrics dashboard

### Alerting
- **Critical Alerts**: Service down, high error rates
- **Warning Alerts**: High latency, low success rates
- **Channels**: PagerDuty, Email, Slack

Complete logging strategy and monitoring setup in `monitoring/` directory.

## 17. Authentication & Security

### Authentication Strategy

**Multi-layer authentication approach**:

1. **LiveKit Token Authentication** (Primary)
 - JWT-based tokens for room access
 - Server-side token generation with validation
 - Token expiration (1 hour default)
 - Room name validation and security checks

2. **API Authentication** (Secondary)
 - Optional JWT for authenticated users
 - Anonymous access with rate limiting
 - Role-based permissions (anonymous, user, admin)

3. **Security Measures**
 - Rate limiting (60 requests/minute per IP)
 - Room name validation (alphanumeric, dash, underscore only)
 - Reserved name blocking
 - HTTPS enforcement for all token transmission
 - No secrets in client-side code

### Token Generation Flow

```
User Request → API Endpoint → Validate Room Name → Rate Limit Check → 
Generate Token → Return Token (with expiration)
```

### Permission System

- **Anonymous Users**: Can create conversations, join rooms (rate limited)
- **Authenticated Users**: All anonymous permissions + conversation history, appointments
- **Admin Users**: All user permissions + system management, monitoring access

Complete authentication design and implementation in `security/auth/AUTHENTICATION_DESIGN.md`.

## 18. Summary

This system prioritizes clarity, correctness, and extensibility. 
It demonstrates how LLMs can be safely combined with deterministic conversation logic in real-time voice applications.

**Additional Documentation**:
- UI/UX Design: `uiux/` directory
- Database Schema: `database/` directory
- Security & DevSecOps: `security/` directory
- Monitoring & Logging: `monitoring/` directory