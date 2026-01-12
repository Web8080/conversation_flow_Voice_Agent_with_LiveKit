# Voice Agent with LiveKit - Complete Implementation

A production-ready voice agent system with LiveKit, featuring state-machine-based conversation flows, comprehensive security, monitoring, and professional UI/UX design.

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

## Documentation

### Getting Started
- **[QUICKSTART.md](docs/QUICKSTART.md)** - Get running in 5 minutes
- **[SETUP_AND_RUN.md](docs/SETUP_AND_RUN.md)** - Detailed setup guide
- **[services/SERVICES_SETUP.md](services/SERVICES_SETUP.md)** - Service configuration

### Design & Architecture
- **[VOICE_AGENT_DESIGN.md](docs/VOICE_AGENT_DESIGN.md)** - System design (presentation-ready)
- **[COMPLETE_SYSTEM_OVERVIEW.md](docs/COMPLETE_SYSTEM_OVERVIEW.md)** - Full system overview
- **[EXECUTIVE_APPROACH.md](docs/EXECUTIVE_APPROACH.md)** - Professional approach narrative
- **[uiux/](uiux/)** - Complete UI/UX design documentation

### Implementation Details
- **[database/SCHEMA_DESIGN.md](database/SCHEMA_DESIGN.md)** - Database schema
- **[monitoring/LOGGING_STRATEGY.md](monitoring/LOGGING_STRATEGY.md)** - Observability
- **[security/scripts/](security/scripts/)** - Security scanning tools


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

## UI/UX Design

Complete design documentation includes:
- Wireframes for all screens
- Component specifications
- User journey maps
- Accessibility guidelines
- Mobile responsiveness

See `uiux/` directory for full documentation.

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
- [x] State machine implementation complete
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

1. **Configure Services**: Read `services/SERVICES_SETUP.md`
2. **Set Environment Variables**: Configure `.env` files
3. **Run Security Scan**: Execute security scripts
4. **Test Locally**: Use `./launch.sh`
5. **Review Design**: Check `uiux/` for UI/UX
6. **Prepare Presentation**: Review `docs/VOICE_AGENT_DESIGN.md`

## Contributing

This is a technical exercise submission. For questions or improvements, see documentation.

## License

This project is a technical exercise implementation.

---

**Built with** clarity, structure, and correctness in mind. 
**Designed for** production readiness and professional presentation.