# Developer Onboarding Guide

## Welcome! 

This guide will help you get started with the Voice Agent project.

## Prerequisites

- Python 3.11+
- Node.js 20+
- Git
- Docker (optional)
- IDE (VS Code recommended)

## First Day Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd Fortell_AI_Product
```

### 2. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt # Dev dependencies
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

### 4. Environment Configuration
```bash
# Backend
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# Frontend
cp frontend/.env.example frontend/.env.local
# Edit frontend/.env.local
```

### 5. Install Pre-commit Hooks
```bash
pip install pre-commit
pre-commit install
```

### 6. Run Tests
```bash
# Backend
cd backend
pytest tests/ -v

# Frontend
cd frontend
npm test
```

### 7. Start Development
```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python main.py dev

# Terminal 2 - Frontend
cd frontend
npm run dev
```

## Project Structure

```
Fortell_AI_Product/
 backend/ # Python backend
 agent/ # Core agent logic
 config/ # Configuration
 auth/ # Authentication
 tests/ # Tests
 frontend/ # Next.js frontend
 app/ # Next.js app directory
 components/ # React components
 tests/ # Frontend tests
 testing/ # Test documentation
 ci-cd/ # CI/CD workflows
 docs/ # Documentation
 scripts/ # Utility scripts
```

## Key Technologies

### Backend
- **Python 3.11+**: Main language
- **LiveKit**: Real-time communication
- **OpenAI**: STT/TTS services
- **Ollama**: Local LLM
- **PostgreSQL**: Database
- **Pytest**: Testing framework

### Frontend
- **Next.js 14**: React framework
- **TypeScript**: Type safety
- **LiveKit Client**: WebRTC client
- **Tailwind CSS**: Styling
- **Jest/Playwright**: Testing

## Development Workflow

### Making Changes

1. **Create Branch**
 ```bash
 git checkout -b feature/your-feature-name
 ```

2. **Make Changes**
 - Write code
 - Write tests
 - Update documentation

3. **Test Locally**
 ```bash
 # Run tests
 pytest backend/tests/
 npm test -- frontend

 # Run linters
 black backend/
 npm run lint -- frontend
 ```

4. **Commit**
 ```bash
 git commit -m "feat: your feature description"
 ```
 Pre-commit hooks will run automatically

5. **Push & Create PR**
 ```bash
 git push origin feature/your-feature-name
 ```
 Create pull request on GitHub

### Code Review Process

1. Submit PR with description
2. CI pipeline runs automatically
3. Team reviews code
4. Address feedback
5. Merge when approved

## Common Tasks

### Adding a New State

1. Create state class in `backend/agent/state_machine/state.py`
2. Add to state machine in `backend/agent/state_machine/state_machine.py`
3. Write tests in `backend/tests/unit/test_state_machine.py`
4. Update documentation

### Adding a New API Endpoint

1. Create route in appropriate file
2. Add authentication if needed
3. Write integration tests
4. Update OpenAPI spec
5. Document in API docs

### Debugging

**Backend**:
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python main.py dev
```

**Frontend**:
- Use React DevTools
- Check browser console
- Use Next.js debug mode

## Resources

### Documentation
- System Design: `VOICE_AGENT_DESIGN.md`
- API Docs: `docs/api/OPENAPI_SPEC.yaml`
- Testing: `testing/TESTING_STRATEGY.md`
- Security: `security/auth/AUTHENTICATION_DESIGN.md`

### External Resources
- LiveKit Docs: https://docs.livekit.io/
- OpenAI API: https://platform.openai.com/docs
- Next.js Docs: https://nextjs.org/docs

## Getting Help

1. **Check Documentation**: Most questions are answered in docs
2. **Search Issues**: Check GitHub issues for similar problems
3. **Ask Team**: Slack channel or team chat
4. **Create Issue**: If you find a bug or need a feature

## Next Steps

- [ ] Read `VOICE_AGENT_DESIGN.md`
- [ ] Review `TESTING_STRATEGY.md`
- [ ] Complete first small task (label: "good first issue")
- [ ] Attend team standup
- [ ] Set up monitoring access
- [ ] Review incident response runbook

