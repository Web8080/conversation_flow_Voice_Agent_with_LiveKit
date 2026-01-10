# Cursor AI Prompts - Voice Agent Implementation

These prompts are aligned to the system design in `VOICE_AGENT_DESIGN.md`. 
Execute them in order for incremental, professional implementation.

---

## Prompt 1: Architecture Skeleton

```
You are a senior Python engineer implementing a LiveKit voice agent.

Based on the system design document, implement the skeleton structure:

1. Main VoiceAgent class that:
 - Connects to LiveKit room using livekit SDK
 - Receives audio tracks from participants
 - Coordinates STT → LLM → TTS pipeline
 - Handles room events (participant_connected, track_subscribed)

2. Abstract service interfaces:
 - STTService: transcribe(audio_data) -> text
 - LLMService: generate_response(user_text, context) -> text
 - TTSService: synthesize(text) -> audio_data

3. Provider implementations (stubs initially):
 - OpenAISTTService, OpenAILLMService, OpenAITTSService

Requirements:
- Clean separation of concerns
- Type hints throughout
- Async/await for I/O operations
- Error handling at service boundaries
- No conversation state machine yet (Stage 1 only)

Focus on structure and readability. Use dependency injection pattern.
```

---

## Prompt 2: State Machine Abstraction

```
Design and implement a Python conversation state machine abstraction for the voice agent.

Requirements:

1. Base State class:
 - handle_input(text: str, context: ConversationContext) -> StateResponse
 - get_prompt() -> str
 - can_transition_to(target_state: str) -> bool

2. StateResponse dataclass:
 - next_state: Optional[str]
 - response_text: str
 - should_continue: bool
 - extracted_slots: Dict[str, Any]

3. ConversationContext class:
 - current_state: str
 - slots: Dict[str, Any]
 - history: List[Dict]
 - retry_count: int
 - update_slot(key: str, value: Any)
 - get_slot(key: str) -> Optional[Any]

4. StateMachine orchestrator:
 - states: Dict[str, State]
 - current_state: str
 - context: ConversationContext
 - transition_to(state_name: str) -> bool
 - process_user_input(text: str) -> str

5. FallbackState implementation:
 - Handles unclear input
 - Provides retry logic
 - Returns to previous state on success

Design for extensibility. Each state should be independently testable.
Use clear naming and minimal dependencies between states.
```

---

## Prompt 3: Appointment Scheduling Flow

```
Implement the appointment scheduling conversation flow using the state machine abstraction.

States to implement:

1. GreetingState:
 - Welcome message
 - Transitions to CollectDateState on any response

2. CollectDateState:
 - Asks for preferred date
 - Extracts date using simple regex + LLM assistance
 - Validates date is in future
 - Transitions to CollectTimeState on valid date
 - Transitions to FallbackState on invalid/unclear input

3. CollectTimeState:
 - Asks for preferred time
 - Extracts time (handles "2pm", "14:00", "afternoon")
 - Validates reasonable time range (9am-5pm)
 - Transitions to ConfirmationState on valid time
 - Transitions to FallbackState on invalid/unclear input

4. ConfirmationState:
 - Summarizes collected info: "You want an appointment on [date] at [time]. Is that correct?"
 - Extracts yes/no from user response
 - Transitions to TerminalState on confirmation
 - Transitions to CollectDateState on rejection (allows corrections)

5. TerminalState:
 - Confirms booking: "Great! Your appointment is scheduled for [date] at [time]."
 - Sets should_continue=False
 - Ends conversation gracefully

6. FallbackState (already implemented):
 - "I didn't catch that. Could you repeat?"
 - Returns to previous state after retry
 - Max 3 retries before escalating

Implementation notes:
- Use LLM for intent extraction within states, but state transitions are deterministic
- Simple slot extraction is acceptable (regex + LLM fallback)
- Don't over-engineer date/time parsing
- Focus on clear state boundaries and transition logic
```

---

## Prompt 4: Error Handling & Retries

```
Enhance the voice agent to handle errors gracefully at multiple levels:

1. Service-level error handling:
 - STT failures: Return None, log error, agent asks user to repeat
 - LLM failures: Use cached fallback response or simple template response
 - TTS failures: Log error, retry with different voice, or return error message as text

2. State-level error handling:
 - Invalid slot values: Transition to FallbackState
 - Max retries exceeded: Transition to TerminalState with escalation message
 - Timeout handling: If no user input for X seconds, prompt again

3. Connection-level error handling:
 - LiveKit disconnection: Implement reconnection logic with exponential backoff
 - Room join failures: Retry with backoff, fail gracefully with user message

4. Conversation context recovery:
 - If state machine enters invalid state: Reset to GreetingState
 - If context becomes corrupted: Log error, restart conversation gracefully

Implementation requirements:
- All errors should be logged with context (state, user input, error type)
- User-facing error messages should be friendly and actionable
- No silent failures - all errors should be handled explicitly
- Add retry decorator for transient failures
- Add circuit breaker pattern for external API calls

Explain the reasoning in code comments for each error handling decision.
```

---

## Prompt 5: Integration & Pipeline Optimization

```
Integrate all components into a working voice agent pipeline:

1. Connect VoiceAgent to StateMachine:
 - After STT transcription, pass text to state machine
 - State machine returns response text
 - Response text goes to TTS
 - Audio streamed back to LiveKit room

2. Handle conversation lifecycle:
 - Initialize state machine on agent connection
 - Maintain one state machine per conversation session
 - Clean up state machine on conversation end

3. Optimize pipeline for latency:
 - Buffer audio chunks before STT (wait for pause or max duration)
 - Overlap TTS generation with user's next potential speech (if possible)
 - Cache common LLM responses (greetings, confirmations)

4. Add observability:
 - Log state transitions with timestamps
 - Log latency metrics (STT time, LLM time, TTS time, total latency)
 - Add simple metrics: conversation duration, states visited, retry counts

5. Configuration:
 - Externalize all configuration (API keys, model names, timeouts, retry limits)
 - Use environment variables with sensible defaults
 - Add config validation on startup

Requirements:
- End-to-end flow should work: User speaks → Agent responds
- State machine should correctly transition through appointment flow
- Errors should be handled gracefully without crashing
- Code should be production-ready structure (even if features are minimal)

Focus on making the pipeline robust and observable, not just functional.
```

---

## Prompt 6: Frontend Integration (Next.js)

```
Create a minimal Next.js frontend for the voice agent:

1. Main page:
 - Input field for LiveKit room name
 - Connect button
 - Connection status indicator
 - Conversation transcript display (optional, for debugging)

2. LiveKit integration:
 - Use @livekit/client-react for room connection
 - Capture microphone input
 - Play audio output from room
 - Handle connection/disconnection events

3. UI components:
 - Microphone on/off toggle
 - Speaker on/off toggle
 - Connection status badge
 - Simple transcript viewer (shows user and agent messages)

4. Error handling:
 - Display connection errors
 - Handle microphone permission errors
 - Show user-friendly error messages

Requirements:
- Minimal but functional UI (as per requirements)
- TypeScript for type safety
- Responsive design (mobile-friendly)
- No advanced styling needed, but should be clean

Deploy configuration for Vercel should be included.
```

---

## Prompt 7: Interview Walkthrough Preparation

```
Act as a technical interviewer for a senior engineering role.

I've built a voice agent system with LiveKit. The design document is in VOICE_AGENT_DESIGN.md.

Ask me deep technical questions about:

1. Architecture decisions:
 - Why separate STT/LLM/TTS as distinct services?
 - Why state machine over pure LLM-driven conversation?
 - Tradeoffs between streaming vs batch audio processing?

2. State machine design:
 - How do you handle state transitions that depend on LLM output?
 - What happens if LLM suggests an invalid transition?
 - How would you test state machine correctness?

3. Failure modes:
 - What happens if STT returns gibberish?
 - How do you handle LLM hallucinations in slot extraction?
 - What if user goes completely off-script?

4. Scaling considerations:
 - How would this scale to 1000 concurrent conversations?
 - What are the bottlenecks?
 - How would you deploy this to handle variable load?

5. Production concerns:
 - How would you monitor conversation quality?
 - How would you debug a conversation that went wrong?
 - What metrics matter for a voice agent?

After I answer, critique my answers:
- Point out gaps in my reasoning
- Suggest better approaches
- Challenge my assumptions
- Ask follow-up questions

Be rigorous but constructive. Help me improve my technical communication.
```

---

## Prompt 8: Documentation & README

```
Create comprehensive documentation for the voice agent project:

1. README.md with:
 - Project overview and architecture
 - Prerequisites and setup instructions
 - Environment variable configuration
 - Local development setup
 - Deployment instructions (LiveKit Cloud + Vercel)
 - API/service provider setup (OpenAI, etc.)

2. Architecture documentation:
 - Component diagram explanation
 - State machine flow explanation
 - Data flow diagrams
 - Error handling strategy

3. Development guide:
 - How to add a new state
 - How to modify state transitions
 - How to add a new STT/LLM/TTS provider
 - Testing strategy

4. Deployment guide:
 - LiveKit Cloud setup
 - Environment configuration
 - Monitoring and debugging
 - Common issues and solutions

Requirements:
- Clear, concise writing
- Code examples where helpful
- Assumes reader has basic LiveKit/Python knowledge
- Includes troubleshooting section
- Links to relevant external documentation

Focus on making it easy for another engineer to understand and extend the system.
```

---

## Execution Order

Execute prompts in this sequence:

1. **Prompt 1** → Get basic architecture working
2. **Prompt 2** → Build state machine foundation
3. **Prompt 3** → Implement conversation flow
4. **Prompt 4** → Add robustness
5. **Prompt 5** → Integrate and optimize
6. **Prompt 6** → Build frontend
7. **Prompt 7** → Practice explaining (use repeatedly)
8. **Prompt 8** → Document everything

Between prompts, test incrementally. Commit after each working milestone.

---

## Key Principles

- **Incremental**: Build one piece at a time
- **Testable**: Each component can be tested independently
- **Clear**: Code should explain itself, comments explain why
- **Extensible**: Easy to add states, providers, or features
- **Robust**: Handle errors explicitly, no silent failures