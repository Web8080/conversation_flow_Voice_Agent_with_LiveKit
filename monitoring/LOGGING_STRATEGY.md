# Logging Strategy & Observability

## Logging Architecture

### Log Levels

```
DEBUG - Detailed diagnostic information (development only)
INFO - General informational messages (normal operations)
WARNING - Warning messages (recoverable issues)
ERROR - Error messages (non-fatal errors)
CRITICAL - Critical errors (system failures)
```

### Log Structure (Structured Logging)

All logs use structured JSON format:

```json
{
 "timestamp": "2025-01-10T10:30:00Z",
 "level": "INFO",
 "service": "voice-agent",
 "component": "stt_service",
 "session_id": "abc123",
 "conversation_id": "conv-456",
 "message": "STT transcription completed",
 "metadata": {
 "audio_duration_ms": 2500,
 "text_length": 45,
 "language": "en",
 "latency_ms": 800
 },
 "trace_id": "trace-789",
 "span_id": "span-101"
}
```

## Log Categories

### 1. Application Logs

**Location**: `logs/app/`
**Rotation**: Daily, keep 30 days
**Format**: JSON

```python
# Example logging in code
logger.info(
 "user_input_received",
 session_id=session_id,
 text_length=len(user_text),
 state=current_state,
 metadata={"retry_count": retry_count}
)
```

### 2. Access Logs

**Location**: `logs/access/`
**Format**: Combined log format (Apache-style)

```
127.0.0.1 - - [10/Jan/2025:10:30:00 +0000] "POST /api/livekit-token HTTP/1.1" 200 234
```

### 3. Error Logs

**Location**: `logs/errors/`
**Format**: JSON with stack traces

```json
{
 "timestamp": "2025-01-10T10:30:00Z",
 "level": "ERROR",
 "error_type": "STTServiceError",
 "error_message": "OpenAI API rate limit exceeded",
 "stack_trace": "...",
 "context": {
 "session_id": "abc123",
 "retry_count": 3,
 "api_key_prefix": "sk-abc..."
 }
}
```

### 4. Security Logs

**Location**: `logs/security/`
**Format**: JSON

**Events to Log**:
- Authentication attempts (success/failure)
- Token generation
- Permission denied events
- Suspicious activity patterns
- Rate limit violations

```json
{
 "timestamp": "2025-01-10T10:30:00Z",
 "event_type": "authentication_failure",
 "ip_address": "192.168.1.100",
 "user_agent": "Mozilla/5.0...",
 "reason": "invalid_token",
 "severity": "medium"
}
```

### 5. Performance Logs

**Location**: `logs/performance/`
**Format**: JSON with metrics

```json
{
 "timestamp": "2025-01-10T10:30:00Z",
 "metric": "request_latency",
 "component": "stt_service",
 "value": 850,
 "unit": "milliseconds",
 "percentiles": {
 "p50": 800,
 "p95": 1200,
 "p99": 2000
 }
}
```

## Log Aggregation

### Development
- Local file-based logging
- Console output for debugging
- Rotating file handlers

### Production
- **Centralized Logging**: ELK Stack (Elasticsearch, Logstash, Kibana) or Datadog
- **Cloud Logging**: AWS CloudWatch, Google Cloud Logging, Azure Monitor
- **Real-time Monitoring**: Grafana + Loki or similar

## Metrics Collection

### Key Metrics

1. **Conversation Metrics**
 - Total conversations started
 - Conversations completed successfully
 - Average conversation duration
 - Average turns per conversation
 - Abandonment rate

2. **Service Metrics**
 - STT latency (p50, p95, p99)
 - LLM latency (p50, p95, p99)
 - TTS latency (p50, p95, p99)
 - End-to-end latency
 - Error rates per service

3. **State Machine Metrics**
 - State transition counts
 - Average time per state
 - Fallback rate
 - Retry counts

4. **Infrastructure Metrics**
 - CPU usage
 - Memory usage
 - Network I/O
 - Active connections
 - Queue depths

### Metrics Format (Prometheus)

```prometheus
# Counter
conversations_total{status="completed"} 1250
conversations_total{status="failed"} 45

# Histogram
stt_latency_ms_bucket{le="100"} 10
stt_latency_ms_bucket{le="500"} 85
stt_latency_ms_bucket{le="1000"} 95
stt_latency_ms_bucket{le="+Inf"} 100

# Gauge
active_conversations 12
```

## Distributed Tracing

### Trace Context

```python
# Trace propagation
trace_id = generate_trace_id()
span_id = generate_span_id()

# Each service adds span
with tracer.start_span("stt_transcription", trace_id=trace_id, parent_span_id=span_id):
 result = await stt_service.transcribe(audio)
```

### Trace Visualization

- **Jaeger**: Open-source distributed tracing
- **Zipkin**: Distributed tracing system
- **AWS X-Ray**: AWS-native tracing

## Alerting Rules

### Critical Alerts (Page On-Call)

1. **Service Down**: Agent service unavailable > 1 minute
2. **High Error Rate**: Error rate > 10% for 5 minutes
3. **Database Connection Lost**: Cannot connect to database
4. **API Key Exhausted**: Rate limit reached with no fallback

### Warning Alerts (Notification Only)

1. **High Latency**: P95 latency > 3 seconds for 10 minutes
2. **High Retry Rate**: Retry rate > 20% for 15 minutes
3. **Low Success Rate**: Success rate < 80% for 30 minutes
4. **Disk Space**: Disk usage > 80%

### Alert Channels

- **Critical**: PagerDuty, phone call, SMS
- **Warning**: Email, Slack, Microsoft Teams
- **Info**: Dashboard updates

## Log Retention Policy

| Log Type | Retention | Storage |
|----------|-----------|---------|
| Application Logs | 30 days | Standard storage |
| Access Logs | 90 days | Standard storage |
| Error Logs | 1 year | Standard storage |
| Security Logs | 7 years | Compliance storage |
| Performance Logs | 90 days | Time-series DB |
| Audit Logs | 7 years | Compliance storage |

## Implementation

### Python Logging Configuration

```python
# config/logging_config.py
import logging
import structlog
from pythonjsonlogger import jsonlogger

def setup_logging(log_level="INFO", output_format="json"):
 if output_format == "json":
 handler = logging.StreamHandler()
 formatter = jsonlogger.JsonFormatter(
 '%(timestamp)s %(level)s %(name)s %(message)s'
 )
 handler.setFormatter(formatter)
 else:
 handler = logging.StreamHandler()
 formatter = logging.Formatter(
 '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
 )
 handler.setFormatter(formatter)

 root_logger = logging.getLogger()
 root_logger.addHandler(handler)
 root_logger.setLevel(getattr(logging, log_level))
```

### Frontend Logging

```typescript
// utils/logger.ts
export const logger = {
 info: (message: string, metadata?: object) => {
 console.log(JSON.stringify({
 timestamp: new Date().toISOString(),
 level: 'INFO',
 message,
 ...metadata
 }))
 },
 error: (message: string, error?: Error, metadata?: object) => {
 console.error(JSON.stringify({
 timestamp: new Date().toISOString(),
 level: 'ERROR',
 message,
 error: error?.message,
 stack: error?.stack,
 ...metadata
 }))
 }
}
```

## Monitoring Dashboards

### Dashboard 1: System Health
- Service uptime
- Error rates
- Request rates
- Latency percentiles

### Dashboard 2: Conversation Analytics
- Conversation success rate
- Average duration
- State transition flows
- Abandonment points

### Dashboard 3: Performance
- Service latencies (STT, LLM, TTS)
- Resource usage (CPU, memory)
- Queue depths
- Throughput

### Dashboard 4: Business Metrics
- Total appointments scheduled
- User satisfaction scores
- Peak usage times
- Geographic distribution

## Compliance & Audit

- All security events logged
- User actions logged (for audit trail)
- Data access logged (for compliance)
- Regular log reviews scheduled
