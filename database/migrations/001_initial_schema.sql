-- Initial Database Schema Migration
-- Version: 001
-- Date: 2025-01-10

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enable TimescaleDB for metrics (if installed)
-- CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Conversations Table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    room_name VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    final_state VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Conversation Turns
CREATE TABLE IF NOT EXISTS conversation_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'agent')),
    text TEXT NOT NULL,
    audio_url TEXT,
    transcribed_text TEXT,
    llm_response TEXT,
    state_at_turn VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- State Transitions
CREATE TABLE IF NOT EXISTS state_transitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    from_state VARCHAR(100),
    to_state VARCHAR(100) NOT NULL,
    trigger_type VARCHAR(50),
    trigger_data JSONB DEFAULT '{}',
    transition_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    latency_ms INTEGER,
    metadata JSONB DEFAULT '{}'
);

-- Extracted Slots
CREATE TABLE IF NOT EXISTS extracted_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    turn_id UUID REFERENCES conversation_turns(id) ON DELETE SET NULL,
    slot_name VARCHAR(100) NOT NULL,
    slot_value TEXT NOT NULL,
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    extraction_method VARCHAR(50),
    validated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Appointments
CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_name VARCHAR(255),
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    appointment_type VARCHAR(100),
    contact_info VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'confirmed',
    confirmation_code VARCHAR(50) UNIQUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- System Metrics (for TimescaleDB)
CREATE TABLE IF NOT EXISTS system_metrics (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(12,2) NOT NULL,
    tags JSONB DEFAULT '{}',
    conversation_id UUID REFERENCES conversations(id)
);

-- Error Logs
CREATE TABLE IF NOT EXISTS error_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    context JSONB DEFAULT '{}',
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- User Feedback
CREATE TABLE IF NOT EXISTS user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    feedback_type VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);
CREATE INDEX IF NOT EXISTS idx_conversations_started_at ON conversations(started_at);

CREATE INDEX IF NOT EXISTS idx_turns_conversation_id ON conversation_turns(conversation_id);
CREATE INDEX IF NOT EXISTS idx_turns_created_at ON conversation_turns(created_at);
CREATE INDEX IF NOT EXISTS idx_turns_role ON conversation_turns(role);

CREATE INDEX IF NOT EXISTS idx_transitions_conversation_id ON state_transitions(conversation_id);
CREATE INDEX IF NOT EXISTS idx_transitions_to_state ON state_transitions(to_state);
CREATE INDEX IF NOT EXISTS idx_transitions_transition_time ON state_transitions(transition_time);

CREATE INDEX IF NOT EXISTS idx_slots_conversation_id ON extracted_slots(conversation_id);
CREATE INDEX IF NOT EXISTS idx_slots_slot_name ON extracted_slots(slot_name);

CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_conversation_id ON appointments(conversation_id);
CREATE INDEX IF NOT EXISTS idx_appointments_confirmation_code ON appointments(confirmation_code);

CREATE INDEX IF NOT EXISTS idx_metrics_name_time ON system_metrics(metric_name, time DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_tags ON system_metrics USING GIN(tags);

CREATE INDEX IF NOT EXISTS idx_errors_type ON error_logs(error_type);
CREATE INDEX IF NOT EXISTS idx_errors_severity ON error_logs(severity);
CREATE INDEX IF NOT EXISTS idx_errors_created_at ON error_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_errors_resolved ON error_logs(resolved);

CREATE INDEX IF NOT EXISTS idx_feedback_conversation_id ON user_feedback(conversation_id);
CREATE INDEX IF NOT EXISTS idx_feedback_rating ON user_feedback(rating);

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_conversations_updated_at BEFORE UPDATE ON conversations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Convert to hypertable if TimescaleDB is available
-- SELECT create_hypertable('system_metrics', 'time', if_not_exists => TRUE);

