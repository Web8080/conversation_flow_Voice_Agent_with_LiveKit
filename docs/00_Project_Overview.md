# Voice Agent with LiveKit - Project Overview

## Project Structure

This repository contains the complete documentation, design, and implementation plan for a Python-based voice agent using LiveKit. The project is organized into two stages, as specified in the technical exercise requirements.

## Quick Start - Read These First

1. **`VOICE_AGENT_DESIGN.md`** ⭐ **START HERE** - Clean, presentation-ready system design
2. **`EXECUTIVE_APPROACH.md`** - Professional execution strategy and what they're really testing
3. **`CURSOR_AI_PROMPTS.md`** - Implementation prompts for incremental development

## Documentation Index

### Primary Documents (Interview Ready)

**`VOICE_AGENT_DESIGN.md`** ⭐
- Clean, focused system design document
- Architecture, state machine design, and rationale
- **This is what you'll walk through in the interview**

**`EXECUTIVE_APPROACH.md`**
- Professional approach and execution strategy
- What they're really testing (insights)
- Interview narrative flow and success criteria

**`03_Project_Presentation_Thought_Process.md`**
- Detailed thought process narrative
- Design decisions and tradeoffs explained
- Use this to prepare your verbal presentation

### Detailed Reference Documents

**`01_Requirements_Document.md`**
- Comprehensive requirements specification
- Functional and non-functional requirements
- Success criteria, assumptions, risks

**`02_System_Design.md`**
- Extended system architecture (detailed reference)
- Component diagrams, data models, API designs
- Deployment, security, scalability considerations

### Implementation Guide

**`CURSOR_AI_PROMPTS.md`**
- 8 prompts for incremental implementation
- Execute in sequence for professional development
- Aligned to the system design

## Project Stages

### Stage 1: Basic Voice Agent
Build a simple voice agent that:
- Joins a LiveKit room
- Listens to user voice input
- Transcribes speech to text
- Sends text to an LLM
- Speaks LLM response back to the user

**Deliverables:**
- GitHub repository with source code
- Deployed backend (LiveKit Cloud)
- Deployed frontend (Vercel or similar)
- Working demo link

### Stage 2: Conversation Flow Agent
Extend the agent with state machine-based conversation flow:
- Implement appointment scheduling use case
- Design 5+ conversation states (greeting, collect info, confirm, retry, complete)
- Handle state transitions based on user input
- Implement error handling and retry logic

**Deliverables:**
- Extended codebase with state machine
- State diagram documentation
- Design explanation
- Working demo with conversation flow

## Technology Stack

- **Backend**: Python 3.8+ with LiveKit Python SDK
- **Frontend**: Next.js (TypeScript) - recommended
- **STT**: OpenAI Whisper, Google Speech-to-Text, or Azure Speech
- **LLM**: OpenAI GPT, Groq, or Anthropic Claude
- **TTS**: OpenAI TTS, Google Cloud TTS, or Azure TTS
- **Deployment**: LiveKit Cloud (backend), Vercel (frontend)

## Key Design Principles

1. **Clear Thinking**: Break complex problems into manageable components
2. **Structure**: Use proven architectural patterns for maintainability
3. **Correctness**: Implement robust error handling and validation

## Architecture Highlights

- **Layered Architecture**: Separation of transport, processing, interface, and external services
- **Service Abstraction**: Interchangeable STT, LLM, and TTS providers
- **State Machine Pattern**: For Stage 2 conversation flow management
- **Stateless Design**: Enables horizontal scaling and simplifies deployment

## Next Steps

1. Review all documentation files
2. Set up development environment
3. Implement Stage 1 basic voice agent
4. Test and deploy Stage 1
5. Design and implement Stage 2 state machine
6. Test and deploy Stage 2
7. Prepare presentation using thought process document

## Important Notes

- Focus on clarity, structure, and correctness over polish
- Document design decisions and rationale
- Ensure code is maintainable and well-structured
- Test error handling and edge cases
- Provide clear setup and deployment instructions

## Contact and Questions

For questions about this project or design decisions, refer to the presentation document (`03_Project_Presentation_Thought_Process.md`) which contains detailed explanations of the approach and rationale.

