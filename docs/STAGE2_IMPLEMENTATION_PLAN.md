# Stage 2 Implementation Plan

## Overview

Stage 2 extends the basic voice agent (Stage 1) to support structured conversation flows using a state machine (DAG) approach. This document outlines the implementation plan with production-ready considerations: error handling, API orchestration, performance, scaling, logging, and security.

## Stage 1 Status

### Recent Fixes (Deployed)
- Fixed STT service to accept `sample_rate` and `num_channels` parameters
- Added WAV format conversion for Google and OpenAI STT services
- Updated audio processing pipeline to pass correct audio format parameters
- Frontend already displays user and agent transcriptions

### Testing Stage 1
Before proceeding to Stage 2, verify Stage 1 works correctly:
1. Agent greets user automatically when joining room
2. Agent responds to user speech within 2-3 seconds
3. User transcriptions appear in conversation UI
4. Agent transcriptions appear in conversation UI
5. Audio quality is clear and understandable

## Stage 2 Requirements

### Use Case: Appointment Scheduling

The agent guides users through scheduling an appointment by collecting:
- Date preference
- Time preference
- Confirmation of details
- Final booking confirmation

### Conversation States

1. **GreetingState** - Initial introduction and explanation
2. **CollectDateState** - Collect preferred appointment date
3. **CollectTimeState** - Collect preferred appointment time
4. **ConfirmationState** - Confirm collected information
5. **FallbackState** - Handle misunderstandings and retries
6. **TerminalState** - End conversation with confirmation

### State Transitions

```
Greeting → CollectDate
  ↓
CollectDate → CollectTime (if date extracted)
  ↓
CollectTime → Confirmation (if time extracted)
  ↓
Confirmation → Terminal (if confirmed)
  ↓
Any State → Fallback (if misunderstanding/error)
  ↓
Fallback → Previous State (after retry)
```

## Implementation Architecture

### 1. Error Handling

#### Strategy
- **Graceful Degradation**: Fallback to simpler responses if LLM/STT/TTS fails
- **Retry Logic**: Exponential backoff for transient failures
- **Circuit Breaker**: Prevent cascading failures
- **Error Recovery**: State machine can recover from errors without restarting

#### Implementation Points
```python
# Error handling in state machine
- Network timeouts (STT/LLM/TTS API calls)
- Invalid user input (unclear speech, background noise)
- State transition errors (invalid transitions)
- Service unavailability (fallback to alternative providers)
- Rate limiting (backoff and retry)
```

#### Error Types to Handle
1. **STT Errors**: Empty transcriptions, API failures, timeout
2. **LLM Errors**: API failures, rate limits, invalid responses
3. **TTS Errors**: API failures, audio generation errors
4. **State Machine Errors**: Invalid transitions, context corruption
5. **Network Errors**: Connection timeouts, DNS failures

### 2. API Orchestration

#### Strategy
- **Service Abstraction**: Clean interfaces for STT, LLM, TTS
- **Fallback Chain**: Primary → Fallback 1 → Fallback 2
- **Request Batching**: Batch multiple requests when possible
- **Caching**: Cache LLM responses for common queries
- **Rate Limiting**: Respect API rate limits per provider

#### Implementation
```python
# API orchestration layer
class APIOchestrator:
    - Coordinate STT → LLM → TTS pipeline
    - Handle provider fallbacks
    - Manage rate limits per provider
    - Cache common responses
    - Batch requests when possible
```

#### Provider Priority
- **STT**: Google (primary) → OpenAI (fallback)
- **LLM**: Google Gemini (primary) → OpenAI GPT (fallback) → Ollama (local fallback)
- **TTS**: Google TTS (primary) → OpenAI TTS (fallback)

### 3. Performance Optimization

#### Latency Targets
- **STT**: < 1 second
- **LLM**: < 2 seconds
- **TTS**: < 1 second
- **Total Turn**: < 4 seconds

#### Optimization Strategies
1. **Audio Buffering**: Optimize buffer duration (currently 1.5s)
2. **Parallel Processing**: Process STT and prepare TTS in parallel when possible
3. **Streaming**: Use streaming STT for faster responses
4. **Connection Pooling**: Reuse HTTP connections for API calls
5. **Audio Compression**: Optimize audio format for faster transmission
6. **Caching**: Cache common LLM prompts and responses

#### Metrics to Track
- End-to-end latency per turn
- STT latency
- LLM latency
- TTS latency
- Audio buffer processing time
- State transition time

### 4. Scaling Considerations

#### Horizontal Scaling
- **Stateless Design**: Agent instances are stateless (state in context)
- **Load Balancing**: LiveKit Cloud handles agent distribution
- **Auto-scaling**: LiveKit Cloud auto-scales based on demand

#### Vertical Scaling
- **Resource Limits**: Configure CPU/memory limits per agent
- **Concurrent Sessions**: Support multiple concurrent conversations per agent instance

#### Database Scaling (Future)
- **Conversation Storage**: Store conversation history for analytics
- **State Persistence**: Persist state for long-running conversations
- **Analytics**: Track metrics for performance optimization

### 5. Logging & Observability

#### Structured Logging
- **JSON Logs**: All logs in structured JSON format
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Context**: Include conversation ID, state, user ID in all logs
- **Correlation IDs**: Track requests across services

#### Log Categories
1. **Audio Processing**: Frame processing, buffer management
2. **STT**: Transcription requests, results, errors
3. **LLM**: Prompt/response pairs, latency, errors
4. **TTS**: Synthesis requests, audio generation, errors
5. **State Machine**: State transitions, slot extraction, errors
6. **API Calls**: Request/response, latency, errors
7. **Performance**: Latency metrics, throughput

#### Monitoring & Alerting
- **Metrics**: Prometheus-compatible metrics
- **Dashboards**: Grafana dashboards for visualization
- **Alerts**: Alert on error rates, latency spikes, service failures
- **Tracing**: Distributed tracing for request flow

### 6. Security

#### Authentication & Authorization
- **LiveKit Tokens**: JWT-based authentication for room access
- **API Keys**: Secure storage of API keys (environment variables, secrets management)
- **Rate Limiting**: Prevent abuse and DoS attacks
- **Input Validation**: Validate and sanitize all user inputs

#### Data Protection
- **PII Handling**: Minimize collection, encrypt at rest
- **Audio Data**: Don't store raw audio, only transcriptions
- **Conversation History**: Encrypt sensitive data
- **Compliance**: GDPR, CCPA compliance considerations

#### Security Best Practices
1. **Secrets Management**: Use LiveKit Cloud secrets, never commit keys
2. **Input Sanitization**: Sanitize all user inputs before LLM processing
3. **Output Filtering**: Filter LLM outputs for sensitive information
4. **Audit Logging**: Log all security-relevant events
5. **Vulnerability Scanning**: Regular dependency scanning

## Implementation Steps

### Phase 1: Core State Machine Integration (Week 1)
1. Integrate existing state machine into `main.py`
2. Replace simple LLM prompt with state-based prompts
3. Implement state transitions based on slot extraction
4. Add fallback state handling
5. Test basic flow: Greeting → Date → Time → Confirmation → Terminal

### Phase 2: Error Handling (Week 1-2)
1. Add try-catch blocks around all API calls
2. Implement retry logic with exponential backoff
3. Add circuit breaker for API failures
4. Implement graceful degradation (fallback responses)
5. Add error recovery in state machine

### Phase 3: API Orchestration (Week 2)
1. Create API orchestrator class
2. Implement provider fallback chain
3. Add rate limiting per provider
4. Implement request caching
5. Add connection pooling

### Phase 4: Performance Optimization (Week 2-3)
1. Optimize audio buffering
2. Implement parallel processing where possible
3. Add streaming STT support
4. Optimize audio format conversion
5. Add performance metrics collection

### Phase 5: Logging & Observability (Week 3)
1. Enhance structured logging
2. Add correlation IDs
3. Implement metrics collection
4. Set up monitoring dashboards
5. Configure alerting rules

### Phase 6: Security Hardening (Week 3-4)
1. Review and secure all API keys
2. Implement input validation and sanitization
3. Add output filtering
4. Set up audit logging
5. Perform security audit

### Phase 7: Testing & Documentation (Week 4)
1. End-to-end testing
2. Performance testing
3. Security testing
4. Documentation updates
5. Deployment preparation

## Testing Strategy

### Unit Tests
- State machine transitions
- Slot extraction logic
- Error handling paths
- API fallback logic

### Integration Tests
- Full conversation flow
- Error recovery scenarios
- Provider fallback scenarios
- State persistence

### End-to-End Tests
- Complete appointment scheduling flow
- Error scenarios (network failures, API errors)
- Performance benchmarks
- Security validation

### Performance Tests
- Latency benchmarks
- Throughput testing
- Concurrent session handling
- Resource usage under load

## Success Criteria

### Functional
- [ ] Agent successfully guides user through appointment scheduling
- [ ] All states implemented and working
- [ ] Fallback state handles misunderstandings correctly
- [ ] Terminal state ends conversation gracefully

### Non-Functional
- [ ] Average response time < 4 seconds
- [ ] Error rate < 1%
- [ ] 99.9% uptime
- [ ] Supports 100+ concurrent sessions
- [ ] All security requirements met

## Next Steps

1. **Test Stage 1 thoroughly** - Ensure basic agent works perfectly
2. **Review existing state machine code** - Understand current implementation
3. **Plan Phase 1 implementation** - Integrate state machine into main agent
4. **Set up monitoring** - Prepare logging and metrics infrastructure
5. **Begin Phase 1** - Start with core state machine integration

## Notes

- The existing state machine code in `backend/agent/state_machine/` provides a good foundation
- Focus on production-readiness: error handling, performance, security
- Iterate based on testing results
- Document all design decisions and trade-offs

