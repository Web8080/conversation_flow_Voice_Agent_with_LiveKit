# Testing Strategy

## Testing Pyramid

```
 /\
 /E2E\ 10% - End-to-End Tests
 /------\
 /Integration\ 20% - Integration Tests
 /------------\
 / Unit Tests \ 70% - Unit Tests
 /----------------\
```

## Test Types

### 1. Unit Tests
**Goal**: Test individual components in isolation

**Coverage Targets**:
- Backend: 80%+ coverage
- Frontend: 75%+ coverage
- Critical paths: 95%+ coverage

**Tools**:
- Python: `pytest`, `pytest-cov`, `pytest-asyncio`
- JavaScript/TypeScript: `Jest`, `Vitest`, `React Testing Library`

**What to Test**:
- Service classes (STT, LLM, TTS)
- State machine logic
- Utility functions
- Helper functions

### 2. Integration Tests
**Goal**: Test component interactions

**Coverage**:
- Service integration (STT → LLM → TTS pipeline)
- Database operations
- API endpoints
- LiveKit integration

**Tools**:
- Python: `pytest` with fixtures
- Frontend: `Jest` + MSW (Mock Service Worker)

**What to Test**:
- Full conversation flow
- State transitions
- Database queries
- External API calls (mocked)

### 3. End-to-End Tests
**Goal**: Test complete user workflows

**Coverage**:
- Full appointment scheduling flow
- Error scenarios
- Authentication flows

**Tools**:
- Playwright
- Cypress
- Selenium

**What to Test**:
- User can connect to room
- User can have conversation
- Agent responds correctly
- State machine transitions work
- Errors are handled gracefully

### 4. Performance Tests
**Goal**: Ensure system meets performance requirements

**Metrics**:
- Response time < 2 seconds (end-to-end)
- STT latency < 1 second
- LLM latency < 2 seconds
- TTS latency < 1 second
- Concurrent users: 100+

**Tools**:
- Locust (Python load testing)
- k6 (Performance testing)
- Artillery

**What to Test**:
- Latency under load
- Throughput capacity
- Resource usage (CPU, memory)
- Concurrent conversation handling

### 5. Security Tests
**Goal**: Verify security controls

**Coverage**:
- Authentication bypass attempts
- Input validation
- Rate limiting
- Token security
- SQL injection
- XSS attacks

**Tools**:
- OWASP ZAP
- Burp Suite
- Custom security test scripts

## Test Structure

```
testing/
 unit/
 backend/
 test_stt_service.py
 test_llm_service.py
 test_tts_service.py
 test_state_machine.py
 test_token_service.py
 frontend/
 components/
 utils/
 integration/
 test_conversation_flow.py
 test_api_endpoints.py
 test_database.py
 e2e/
 test_appointment_flow.spec.ts
 test_error_handling.spec.ts
 test_authentication.spec.ts
 performance/
 load_test.py
 stress_test.py
 benchmark.py
```

## Test Data Management

- **Fixtures**: Reusable test data
- **Factories**: Generate test data dynamically
- **Mocks**: Mock external services (OpenAI, LiveKit)
- **Seeds**: Database seed data for testing

## Continuous Testing

- **Pre-commit**: Run unit tests
- **Pre-push**: Run unit + integration tests
- **CI Pipeline**: Run all tests
- **Nightly**: Run performance and security tests

## Coverage Goals

| Component | Target Coverage |
|-----------|----------------|
| Core Services | 90%+ |
| State Machine | 95%+ |
| API Endpoints | 85%+ |
| Frontend Components | 75%+ |
| Utilities | 80%+ |
| **Overall** | **80%+** |

## Test Execution

```bash
# Run all tests
pytest backend/tests/
npm test -- frontend

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html
npm test -- --coverage

# Run specific test type
pytest backend/tests/unit/
pytest backend/tests/integration/
npm run test:e2e

# Run performance tests
locust -f testing/performance/load_test.py
