# Incident Response Runbook

## Incident Severity Levels

### P1 - Critical
- **Impact**: Service completely down
- **Response Time**: Immediate (< 5 minutes)
- **Example**: All users cannot access service

### P2 - High
- **Impact**: Major functionality broken
- **Response Time**: 15 minutes
- **Example**: Voice agent not responding, high error rate

### P3 - Medium
- **Impact**: Partial functionality affected
- **Response Time**: 1 hour
- **Example**: Specific feature not working, minor errors

### P4 - Low
- **Impact**: Minor issue, workaround available
- **Response Time**: 4 hours
- **Example**: UI bug, minor latency issues

## Incident Response Process

### 1. Detection
- **Automated**: Monitoring alerts trigger
- **Manual**: User reports issue
- **Source**: Error logs, metrics, user feedback

### 2. Triage
- **Assess**: Determine severity level
- **Assign**: Assign to on-call engineer
- **Document**: Create incident ticket

### 3. Investigation
- **Check**: Error logs, metrics dashboard
- **Identify**: Root cause
- **Isolate**: Determine scope of impact

### 4. Resolution
- **Fix**: Implement solution
- **Verify**: Confirm fix works
- **Deploy**: Roll out fix (if needed)

### 5. Post-Incident
- **Document**: Incident report
- **Review**: Post-mortem meeting
- **Improve**: Update runbooks, add monitoring

## Common Incidents & Solutions

### Issue: Agent Not Responding

**Symptoms**:
- Users report agent not speaking
- Conversation state stuck
- High latency

**Investigation**:
```bash
# Check logs
tail -f logs/app/voice-agent.log | grep ERROR

# Check service status
curl https://backend-url/health

# Check metrics
# Look at STT/LLM/TTS latency metrics
```

**Common Causes**:
1. STT service failure → Check OpenAI API status
2. LLM service timeout → Check Ollama/GPT connectivity
3. TTS service failure → Check OpenAI API
4. LiveKit connection issue → Check LiveKit Cloud status

**Resolution**:
- Restart affected service
- Switch to fallback LLM provider
- Check API rate limits
- Scale up resources if needed

### Issue: High Error Rate

**Symptoms**:
- Error rate > 10%
- Multiple error types in logs
- User complaints increase

**Investigation**:
```bash
# Check error logs
grep -i error logs/app/*.log | tail -100

# Check error types
# Group by error_type in error_logs table
```

**Resolution**:
- Identify most common error
- Check if dependency issue (API, database)
- Implement fix or workaround
- Add retry logic if transient errors

### Issue: Database Connection Lost

**Symptoms**:
- Cannot save conversations
- Database query errors
- High database latency

**Investigation**:
```bash
# Check database connection
psql -h db-host -U user -d voice_agent -c "SELECT 1"

# Check connection pool
# Review database metrics
```

**Resolution**:
- Restart database connection pool
- Check database server status
- Verify credentials
- Scale database if needed

### Issue: Rate Limiting Triggered

**Symptoms**:
- 429 errors in logs
- Users cannot generate tokens
- API quota exceeded

**Investigation**:
```bash
# Check rate limit logs
grep "rate limit" logs/app/*.log

# Check API usage
# Review OpenAI/Groq usage dashboard
```

**Resolution**:
- Increase rate limit temporarily
- Add more API keys (load balance)
- Implement exponential backoff
- Upgrade API tier if needed

## Escalation Path

1. **L1**: On-call engineer (initial response)
2. **L2**: Senior engineer (complex issues)
3. **L3**: Engineering lead (critical issues)
4. **L4**: CTO/VP Engineering (business-critical)

## Communication Template

### Internal Alert (Slack)
```
 [P1] Voice Agent Service Down
Status: Investigating
Impact: All users affected
On-call: @engineer-name
Incident: INC-12345
```

### Status Update
```
 [P1] Voice Agent Service Down - UPDATE
Status: Mitigated
Root Cause: OpenAI API outage
Resolution: Switched to Ollama fallback
ETA: 5 minutes
```

### Resolution
```
 [P1] Voice Agent Service Down - RESOLVED
Duration: 15 minutes
Root Cause: OpenAI API outage
Resolution: Switched to Ollama fallback
Post-mortem: Scheduled for tomorrow
```

## Monitoring & Alerting

### Critical Alerts
- Service down > 1 minute
- Error rate > 10% for 5 minutes
- Database connection lost
- API quota exceeded

### Warning Alerts
- Latency > 3 seconds (P95)
- Error rate > 5% for 15 minutes
- High retry rate
- Resource usage > 80%

## Post-Incident Checklist

- [ ] Document incident in incident log
- [ ] Create incident report
- [ ] Schedule post-mortem meeting
- [ ] Update runbooks with learnings
- [ ] Add monitoring for detected issue
- [ ] Implement preventive measures
