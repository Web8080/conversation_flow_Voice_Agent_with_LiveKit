# Database Schema Design

## Overview

We need to store:
1. **Conversation sessions** (for analytics, debugging, compliance)
2. **User interactions** (turns, state transitions)
3. **Appointment data** (if integrated with calendar system)
4. **System metrics** (performance, errors)
5. **User feedback** (satisfaction, errors)

## Database Choice

**Primary**: PostgreSQL (relational, ACID compliance for appointments)
**Secondary**: MongoDB (optional, for flexible conversation logs)
**Time Series**: TimescaleDB extension (for metrics)

## Schema Design

### 1. Conversations Table

```sql
CREATE TABLE conversations (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 session_id VARCHAR(255) UNIQUE NOT NULL,
 room_name VARCHAR(255) NOT NULL,
 user_id VARCHAR(255), -- Anonymous or authenticated user
 status VARCHAR(50) NOT NULL, -- 'active', 'completed', 'failed', 'abandoned'
 started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
 ended_at TIMESTAMP WITH TIME ZONE,
 duration_seconds INTEGER,
 final_state VARCHAR(100), -- 'terminal', 'fallback', etc.
 metadata JSONB, -- Additional flexible data
 created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
 updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_started_at ON conversations(started_at);
```

### 2. Conversation Turns Table

```sql
CREATE TABLE conversation_turns (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
 turn_number INTEGER NOT NULL,
 role VARCHAR(20) NOT NULL, -- 'user', 'agent'
 text TEXT NOT NULL,
 audio_url TEXT, -- S3/cloud storage URL if storing audio
 transcribed_text TEXT, -- STT output
 llm_response TEXT, -- LLM output (for agent turns)
 state_at_turn VARCHAR(100), -- Conversation state
 metadata JSONB, -- Timing, latency, etc.
 created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_turns_conversation_id ON conversation_turns(conversation_id);
CREATE INDEX idx_turns_created_at ON conversation_turns(created_at);
CREATE INDEX idx_turns_role ON conversation_turns(role);
```

### 3. State Transitions Table

```sql
CREATE TABLE state_transitions (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
 from_state VARCHAR(100),
 to_state VARCHAR(100) NOT NULL,
 trigger_type VARCHAR(50), -- 'user_input', 'timeout', 'error', etc.
 trigger_data JSONB, -- What caused the transition
 transition_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
 latency_ms INTEGER, -- Time to process transition
 metadata JSONB
);

CREATE INDEX idx_transitions_conversation_id ON state_transitions(conversation_id);
CREATE INDEX idx_transitions_to_state ON state_transitions(to_state);
CREATE INDEX idx_transitions_transition_time ON state_transitions(transition_time);
```

### 4. Extracted Slots Table

```sql
CREATE TABLE extracted_slots (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
 turn_id UUID REFERENCES conversation_turns(id) ON DELETE SET NULL,
 slot_name VARCHAR(100) NOT NULL, -- 'name', 'date', 'time', etc.
 slot_value TEXT NOT NULL,
 confidence_score DECIMAL(3,2), -- 0.00 to 1.00
 extraction_method VARCHAR(50), -- 'llm', 'regex', 'nlp', etc.
 validated BOOLEAN DEFAULT FALSE,
 created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_slots_conversation_id ON extracted_slots(conversation_id);
CREATE INDEX idx_slots_slot_name ON extracted_slots(slot_name);
```

### 5. Appointments Table (Future Integration)

```sql
CREATE TABLE appointments (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
 user_name VARCHAR(255),
 appointment_date DATE NOT NULL,
 appointment_time TIME NOT NULL,
 appointment_type VARCHAR(100),
 contact_info VARCHAR(255),
 status VARCHAR(50) NOT NULL DEFAULT 'confirmed', -- 'confirmed', 'cancelled', 'completed'
 confirmation_code VARCHAR(50) UNIQUE,
 metadata JSONB,
 created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
 updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_appointments_conversation_id ON appointments(conversation_id);
CREATE INDEX idx_appointments_confirmation_code ON appointments(confirmation_code);
```

### 6. System Metrics Table (Time Series)

```sql
-- Using TimescaleDB extension
CREATE TABLE system_metrics (
 time TIMESTAMP WITH TIME ZONE NOT NULL,
 metric_name VARCHAR(100) NOT NULL,
 metric_value DECIMAL(12,2) NOT NULL,
 tags JSONB, -- Additional context: service, state, error_type, etc.
 conversation_id UUID REFERENCES conversations(id)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('system_metrics', 'time');

CREATE INDEX idx_metrics_name_time ON system_metrics(metric_name, time DESC);
CREATE INDEX idx_metrics_tags ON system_metrics USING GIN(tags);
```

**Metrics to Track**:
- `stt_latency_ms`: STT processing time
- `llm_latency_ms`: LLM response time
- `tts_latency_ms`: TTS generation time
- `total_latency_ms`: End-to-end latency
- `error_count`: Error occurrences
- `state_transition_count`: Number of transitions per conversation
- `slot_extraction_confidence`: Average confidence scores

### 7. Error Logs Table

```sql
CREATE TABLE error_logs (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
 error_type VARCHAR(100) NOT NULL, -- 'stt_error', 'llm_error', 'tts_error', 'connection_error'
 error_message TEXT NOT NULL,
 stack_trace TEXT,
 context JSONB, -- Additional error context
 severity VARCHAR(20) NOT NULL, -- 'low', 'medium', 'high', 'critical'
 resolved BOOLEAN DEFAULT FALSE,
 created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_errors_type ON error_logs(error_type);
CREATE INDEX idx_errors_severity ON error_logs(severity);
CREATE INDEX idx_errors_created_at ON error_logs(created_at);
CREATE INDEX idx_errors_resolved ON error_logs(resolved);
```

### 8. User Feedback Table

```sql
CREATE TABLE user_feedback (
 id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
 rating INTEGER CHECK (rating >= 1 AND rating <= 5),
 feedback_text TEXT,
 feedback_type VARCHAR(50), -- 'positive', 'negative', 'suggestion', 'bug'
 metadata JSONB,
 created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_feedback_conversation_id ON user_feedback(conversation_id);
CREATE INDEX idx_feedback_rating ON user_feedback(rating);
```

## Data Retention Policy

```sql
-- Automatically archive old conversations (older than 90 days)
CREATE TABLE conversations_archive (LIKE conversations INCLUDING ALL);

-- Partition conversations by month for easier archival
-- Keep last 3 months active, archive older
```

## Views for Analytics

```sql
-- Conversation Success Rate
CREATE VIEW conversation_success_rate AS
SELECT 
 DATE_TRUNC('day', started_at) as date,
 COUNT(*) FILTER (WHERE status = 'completed') * 100.0 / COUNT(*) as success_rate,
 COUNT(*) as total_conversations
FROM conversations
WHERE started_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', started_at)
ORDER BY date DESC;

-- Average Conversation Duration by State
CREATE VIEW avg_duration_by_state AS
SELECT 
 final_state,
 AVG(duration_seconds) as avg_duration_seconds,
 COUNT(*) as conversation_count
FROM conversations
WHERE status = 'completed'
GROUP BY final_state;

-- Error Rate by Type
CREATE VIEW error_rate_by_type AS
SELECT 
 error_type,
 COUNT(*) as error_count,
 COUNT(*) FILTER (WHERE severity = 'critical') as critical_count
FROM error_logs
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY error_type
ORDER BY error_count DESC;

-- Slot Extraction Accuracy
CREATE VIEW slot_extraction_accuracy AS
SELECT 
 slot_name,
 AVG(confidence_score) as avg_confidence,
 COUNT(*) as total_extractions,
 COUNT(*) FILTER (WHERE validated = TRUE) as validated_count
FROM extracted_slots
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY slot_name;
```

## Migration Scripts


