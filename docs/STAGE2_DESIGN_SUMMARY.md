# Stage 2: Structured Conversation Flow - Design Summary

## State-Based Conversation Design

This voice agent implements a **state-based conversation flow** (similar to Retell AI's Conversation Flow agents) to handle appointment scheduling. The system models conversations as a directed acyclic graph (DAG) of states, where each state has a specific purpose and transitions occur based on user input and slot extraction.

**State Design and Transitions**: The conversation flow consists of five core states: `Greeting` (introduces the agent and purpose), `CollectDate` (extracts appointment date via LLM), `CollectTime` (extracts appointment time), `Confirmation` (verifies details and books appointment to Google Calendar), and `Terminal` (ends conversation). Additionally, a `Fallback` state handles unclear input with retry logic (max 3 attempts before escalating to terminal). Transitions occur when required slots are filled (e.g., date extracted → move to `CollectTime`), user confirms (`Confirmation` → `Terminal`), or retry limit is reached (`Fallback` → `Terminal`). The state machine ensures deterministic flow control while leveraging LLM capabilities for natural language understanding and slot extraction.

**Why State-Based for Voice**: Voice interactions are inherently linear, error-prone, and ambiguous. A state-based approach provides predictable agent behavior, simplifies retry logic, prevents hallucinated flow jumps, and improves user trust. Unlike pure LLM-driven conversations that can drift off-topic, the state machine maintains conversation structure while allowing natural language flexibility within each state. This design enables graceful error recovery, clear conversation progress tracking, and reliable appointment booking integration with external systems like Google Calendar.

## Implementation Details

### State Machine Architecture

- **State Classes**: Each state (`GreetingState`, `CollectDateState`, `CollectTimeState`, `ConfirmationState`, `FallbackState`, `TerminalState`) extends `ConversationState` and implements:
  - `get_prompt()`: Returns the prompt/question for the current state
  - `handle_input()`: Processes user input and returns `StateResponse` with next state and response text
  - Slot extraction via LLM for natural language understanding

- **State Transitions**: Controlled by the `StateMachine` class which:
  - Maintains current state
  - Validates transitions
  - Updates conversation context
  - Sends state updates to frontend via LiveKit data messages

### Appointment Booking Integration

- **Google Calendar Integration**: The `ConfirmationState` integrates with Google Calendar API via `CalendarService`:
  - Creates calendar events when user confirms appointment
  - Stores event ID and calendar link in conversation context
  - Falls back gracefully if calendar service is unavailable

- **Database Storage**: Appointments are stored in PostgreSQL `appointments` table with:
  - Conversation ID linkage
  - Date, time, appointment type
  - Confirmation code
  - Status tracking

### Fallback and Terminal States

- **Fallback State**: 
  - Handles unclear or invalid input
  - Implements retry logic (max 3 attempts)
  - Returns to previous state after successful retry
  - Transitions to terminal if max retries exceeded

- **Terminal State**:
  - Detects conversation end via `should_continue=False` flag
  - Handles restart requests ("restart", "start over", "new appointment")
  - Confirms appointment booking status
  - Ends conversation gracefully

### Frontend State Tracking

- **State Updates**: Backend sends `state_update` data messages with:
  - Current state name
  - Collected slots (date, time, name, etc.)
  
- **Progress Indicator**: Frontend `StateProgressIndicator` component:
  - Displays all states in order
  - Marks completed states (states before current)
  - Highlights current state
  - Updates in real-time as conversation progresses

## File Structure

- `backend/main_stage2.py`: Stage 2 agent implementation with state machine
- `backend/agent/state_machine/`: State machine implementation
  - `state_machine.py`: Main state machine orchestrator
  - `state.py`: Individual state implementations
  - `context.py`: Conversation context management
- `backend/agent/services/calendar_service.py`: Google Calendar integration
- `frontend/components/StateProgressIndicator.tsx`: UI component for state progress
- `frontend/components/VoiceAgentUI.tsx`: Main UI with state update handling


