# Stage 2 Implementation Guide

## Overview

Stage 2 implements a structured conversation flow using a state machine for appointment scheduling. This guide explains how to use Stage 2, configure it, and understand its architecture.

## Quick Start

### Enable Stage 2

Set the following in `backend/.env`:
```
AGENT_STAGE=stage2
```

### Deploy Stage 2 Agent

```bash
cd backend
lk agent deploy --project voiceagent007
```

## Architecture

### State Machine Flow

```
Greeting → CollectDate → CollectTime → Confirmation → Terminal
    ↓           ↓             ↓              ↓
 Fallback ← Fallback ← Fallback ← Fallback
```

### States Explained

1. **Greeting**: Introduces agent and explains purpose
2. **CollectDate**: Extracts appointment date from user input
3. **CollectTime**: Extracts appointment time from user input  
4. **Confirmation**: Verifies details and books appointment
5. **Terminal**: Ends conversation (appointment booked or user ended)
6. **Fallback**: Handles unclear input with retry logic

### State Transitions

- **Greeting → CollectDate**: After greeting, ask for date
- **CollectDate → CollectTime**: When date slot is filled
- **CollectTime → Confirmation**: When time slot is filled
- **Confirmation → Terminal**: When user confirms (appointment booked)
- **Confirmation → CollectDate**: When user rejects (restart)
- **Any State → Fallback**: On unclear input
- **Fallback → Previous State**: After successful retry
- **Fallback → Terminal**: After max retries (3)

## Appointment Booking

### Google Calendar Integration

Appointments are automatically booked to Google Calendar when:
1. User confirms in `ConfirmationState`
2. Calendar service is enabled and configured
3. Date and time slots are filled

### Database Storage

All appointments are stored in PostgreSQL `appointments` table:
- Conversation ID linkage
- Date, time, appointment type
- Confirmation code
- Status (confirmed, cancelled, completed)

### Calendar Configuration

Ensure Google Calendar API is enabled and credentials are configured:
- Service account with Calendar API access
- `GOOGLE_APPLICATION_CREDENTIALS` or `GOOGLE_APPLICATION_CREDENTIALS_JSON` set
- Calendar API scope: `https://www.googleapis.com/auth/calendar`

## Frontend State Tracking

The frontend receives state updates via LiveKit data messages:
- `state_update`: Contains current state and collected slots
- Progress indicator updates automatically
- Conversation context displays collected information

## Terminal State Detection

Conversation ends when:
- `should_continue=False` is returned from state handler
- User confirms appointment (moves to terminal)
- Max retries exceeded in fallback state
- User explicitly ends conversation

Terminal state can restart if user says "restart", "start over", or "new appointment".

## Fallback State Logic

- Max 3 retry attempts per unclear input
- Returns to previous state after successful retry
- Escalates to terminal if max retries exceeded
- Provides clear feedback on retry count

## Testing

1. Connect to frontend
2. Say "Hello" to start conversation
3. Follow prompts: provide date, then time
4. Confirm appointment
5. Check Google Calendar for booked event
6. Verify state progress indicator updates correctly

## Troubleshooting

**State not updating in UI**: Check that `state_update` messages are being sent from backend and received in frontend.

**Appointment not booking**: Verify Google Calendar credentials and API access.

**Stuck in fallback**: Check LLM responses and slot extraction logic.


