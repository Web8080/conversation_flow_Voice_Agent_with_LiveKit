# ` xw  4z y7o p;]n Approach to Voice Agent

## Executive Summary

This document outlines how i would approach building and optimizing this voice agent system, with emphasis on **evaluation, experimentation, and production ML practices**.

---

## 1. Evaluation Framework

### 1.1 Key Metrics to Track

**Conversation Quality Metrics:**
- **Success Rate**: % of conversations that complete the full flow
- **Task Completion Rate**: % of appointments successfully scheduled
- **Average Turns**: Number of exchanges needed to complete task
- **User Satisfaction**: Explicit feedback + implicit signals (retries, abandonments)

**Model Performance Metrics:**
- **Intent Accuracy**: Correct intent classification rate
- **Slot Extraction F1**: Precision/Recall for entity extraction
- **Response Relevance**: Semantic similarity to expected response
- **Confidence Scores**: Distribution of model confidence per prediction

**Latency Metrics:**
- **STT Latency** (p50, p95, p99): Speech-to-text processing time
- **LLM Latency** (p50, p95, p99): Model inference time
- **TTS Latency** (p50, p95, p99): Text-to-speech generation time
- **End-to-End Latency**: Total user utterance → agent response

**Cost Metrics:**
- **Tokens per Conversation**: Input + output tokens
- **Cost per Conversation**: Total API costs
- **Cost per Successful Task**: Normalized by completion rate

**Error Metrics:**
- **STT Error Rate**: Transcription failures or low confidence
- **LLM Error Rate**: API failures, timeouts, invalid responses
- **State Transition Errors**: Invalid state jumps or stuck states
- **Fallback Rate**: Frequency of fallback state usage

### 1.2 Evaluation Dataset

**Gold Standard Dataset:**
```python
{
 "conversations": [
 {
 "user_utterances": ["I want to schedule an appointment", "Tomorrow at 2pm"],
 "expected_slots": {"date": "2025-01-11", "time": "14:00"},
 "expected_states": ["greeting", "collect_date", "collect_time", "confirmation"],
 "ground_truth_response": "Great! I've scheduled your appointment for tomorrow at 2pm. Is that correct?",
 "conversation_outcome": "success"
 }
 ]
}
```

**Test Scenarios:**
- Happy path conversations
- Edge cases (ambiguous dates, invalid times)
- Error recovery (interruptions, corrections)
- Out-of-scope requests (chit-chat, unrelated queries)

---

## 2. Model Selection & Optimization

### 2.1 LLM Model Comparison

**Models to Evaluate:**
1. **Ollama (Local)**: `llama3.2`, `mistral`, `phi-3`
 - Pros: Free, fast, privacy-preserving
 - Cons: Lower quality than cloud models
 - Use Case: Primary for cost-sensitive deployments

2. **Groq**: `llama-3.1-70b-versatile`
 - Pros: Very fast, high quality
 - Cons: API costs
 - Use Case: Primary for production quality

3. **OpenAI**: `gpt-4o-mini`, `gpt-4o`
 - Pros: Highest quality, reliable
 - Cons: Highest cost, latency
 - Use Case: Fallback, critical conversations

**Evaluation Strategy:**
- A/B test models with same prompts
- Compare: latency, cost, accuracy, user satisfaction
- Select based on cost/quality tradeoff for use case

### 2.2 Prompt Engineering & Versioning

**Prompt Versioning System:**
```python
PROMPT_VERSIONS = {
 "v1.0": "Basic appointment scheduling prompt",
 "v1.1": "Enhanced with few-shot examples",
 "v2.0": "Added chain-of-thought reasoning",
 "v2.1": "Optimized for shorter responses"
}
```

**Prompt Optimization Process:**
1. **Baseline**: Start with clear, concise instructions
2. **Few-Shot Learning**: Add examples of good conversations
3. **Chain-of-Thought**: For complex slot extraction
4. **Output Format**: Structure JSON for reliable parsing
5. **Iterative Refinement**: Test → Measure → Refine

**Prompt Template:**
```
System: You are a professional appointment scheduling assistant.

Your goal: Collect the following information in this order:
1. User's name
2. Preferred date (extract and normalize: YYYY-MM-DD)
3. Preferred time (extract and normalize: HH:MM)

Guidelines:
- Be concise and natural
- Confirm understanding when uncertain
- Use fallback responses for unclear input

Example conversation:
User: "Can I book something next Tuesday at 3?"
Assistant: "I'd be happy to schedule that for you. What's your name?"
[Continue with date confirmation...]

Current state: {state}
Collected information: {slots}

User says: "{user_input}"

Respond with JSON:
{
 "response": "Your natural language response",
 "extracted_slots": {"date": "2025-01-14", "time": "15:00"},
 "confidence": 0.95,
 "next_state": "collect_time",
 "needs_clarification": false
}
```

---

## 3. Feature Engineering & Slot Extraction

### 3.1 Enhanced Entity Extraction

**Current Approach**: LLM-based extraction (flexible but inconsistent)

**Improved Approach**: Hybrid system
1. **Rule-based Pre-processing**: Handle common patterns
 - Date patterns: "tomorrow", "next week", "Jan 15"
 - Time patterns: "2pm", "14:00", "afternoon"
 - Name patterns: Validate against common names DB

2. **LLM-based Extraction**: For ambiguous cases
 - Use LLM with structured output (JSON)
 - Confidence scoring per entity

3. **Validation Layer**: Post-extraction checks
 - Date range validation (not in past, within business hours)
 - Time slot availability check
 - Format normalization

**Confidence Scoring:**
```python
{
 "date": {"value": "2025-01-15", "confidence": 0.95, "source": "llm"},
 "time": {"value": "14:00", "confidence": 0.88, "source": "rules"},
 "name": {"value": "John Doe", "confidence": 0.72, "source": "llm", "needs_confirmation": true}
}
```

### 3.2 Intent Classification

**Intent Classes:**
- `SCHEDULE_APPOINTMENT`: Primary task
- `CHANGE_APPOINTMENT`: Modify existing
- `CANCEL_APPOINTMENT`: Cancel
- `GREETING`: Hello, hi, etc.
- `CLARIFY`: Requesting clarification
- `OUT_OF_SCOPE`: Unrelated queries

**Classification Strategy:**
- Lightweight classifier (few-shot LLM call)
- Fallback to state-based heuristics
- Log for model improvement

---

## 4. Cost Optimization

### 4.1 Token Counting & Budgeting

**Token Tracking:**
```python
class TokenTracker:
 def track_usage(self, provider: str, input_tokens: int, output_tokens: int):
 cost = self.calculate_cost(provider, input_tokens, output_tokens)
 self.metrics.record("token_usage", {
 "provider": provider,
 "input_tokens": input_tokens,
 "output_tokens": output_tokens,
 "cost": cost,
 "conversation_id": self.conversation_id
 })
```

**Cost Calculation:**
- OpenAI GPT-4o-mini: $0.15/1M input, $0.60/1M output tokens
- Groq: Free tier, then pricing
- Ollama: $0 (local compute)

**Budget Controls:**
- Max tokens per conversation
- Automatic fallback to cheaper model if approaching limit
- Daily/monthly budget caps

### 4.2 Response Caching

**Cache Strategy:**
```python
# Cache common responses (greetings, confirmations)
CACHE_KEY = f"llm_response:{hash(user_input + state + slots)}"

if cached_response:= cache.get(CACHE_KEY):
 return cached_response

response = await llm.generate(user_input, context)
cache.set(CACHE_KEY, response, ttl=3600) # 1 hour
```

**Cache Hit Rate Target**: 20-30% (greetings, common confirmations)

### 4.3 Smart Fallback Strategy

**Fallback Decision Tree:**
1. **Primary Model Fails** → Try fallback model (Ollama → Groq → OpenAI)
2. **High Latency** → Switch to faster model (Groq preferred)
3. **Low Confidence** → Use more expensive, higher-quality model
4. **Budget Exceeded** → Force to cheapest option

---

## 5. Experimentation Framework

### 5.1 A/B Testing Infrastructure

**Experiment Configuration:**
```python
experiments = {
 "prompt_v2_vs_v1": {
 "variant_a": {"prompt_version": "v1.0", "model": "gpt-4o-mini"},
 "variant_b": {"prompt_version": "v2.0", "model": "gpt-4o-mini"},
 "traffic_split": 0.5, # 50/50 split
 "metrics": ["success_rate", "avg_turns", "cost_per_conversation"],
 "duration_days": 7
 }
}
```

**Tracking:**
- Assign users to variants consistently (by session_id hash)
- Log all predictions with variant label
- Compare metrics after experiment period
- Statistical significance testing (t-test, chi-square)

### 5.2 Model Performance Comparison

**Comparative Evaluation:**
```python
results = {
 "ollama_llama3.2": {
 "success_rate": 0.72,
 "avg_latency_ms": 450,
 "cost_per_conversation": 0.0,
 "user_satisfaction": 0.68
 },
 "groq_llama70b": {
 "success_rate": 0.89,
 "avg_latency_ms": 320,
 "cost_per_conversation": 0.002,
 "user_satisfaction": 0.85
 },
 "openai_gpt4mini": {
 "success_rate": 0.94,
 "avg_latency_ms": 850,
 "cost_per_conversation": 0.015,
 "user_satisfaction": 0.91
 }
}
```

**Decision Matrix:**
- **Cost-sensitive**: Ollama (best cost, acceptable quality)
- **Balanced**: Groq (good quality, reasonable cost)
- **Quality-critical**: OpenAI (best quality, higher cost)

---

## 6. Production ML Patterns

### 6.1 Model Registry & Versioning

**Model Registry:**
```python
models = {
 "llm/ollama/llama3.2/v1": {
 "model_id": "llama3.2",
 "provider": "ollama",
 "version": "v1",
 "prompt_version": "v2.0",
 "performance": {"accuracy": 0.85, "latency_p95": 600},
 "deployed_at": "2025-01-10",
 "status": "production"
 }
}
```

**Deployment Strategy:**
- **Canary Deployment**: 10% traffic → 50% → 100%
- **Rollback Plan**: Automatic rollback if error rate > threshold
- **Blue-Green**: Maintain two versions, switch instantly

### 6.2 Feature Store

**Features to Track:**
```python
features = {
 "user_features": {
 "conversation_count": int, # Historical context
 "preferred_time_range": str, # Personalization
 "average_response_time": float # Behavioral signal
 },
 "context_features": {
 "current_state": str,
 "collected_slots": dict,
 "conversation_length": int,
 "time_of_day": str
 },
 "model_features": {
 "model_version": str,
 "prompt_version": str,
 "temperature": float
 }
}
```

### 6.3 Prediction Logging & Observability

**Prediction Log Schema:**
```python
prediction_log = {
 "conversation_id": "uuid",
 "timestamp": "iso8601",
 "model": "ollama/llama3.2",
 "prompt_version": "v2.0",
 "input": {
 "user_text": "I want to book tomorrow at 2pm",
 "state": "collect_date",
 "slots": {}
 },
 "output": {
 "response": "I'd be happy to help...",
 "extracted_slots": {"date": "2025-01-11", "time": "14:00"},
 "confidence": 0.92,
 "next_state": "confirmation"
 },
 "metadata": {
 "latency_ms": 450,
 "tokens_input": 120,
 "tokens_output": 45,
 "cost": 0.0
 }
}
```

**Monitoring:**
- **Drift Detection**: Compare prediction distributions over time
- **Performance Degradation**: Track accuracy/latency trends
- **Anomaly Detection**: Flag unusual patterns (high latency, low confidence)

---

## 7. Data Quality & Validation

### 7.1 Input Validation

**Validation Rules:**
- Audio quality check (signal-to-noise ratio)
- Minimum utterance length (avoid accidental triggers)
- Maximum utterance length (prevent rambling)
- Language detection (filter non-English if required)

### 7.2 Output Validation

**Response Quality Checks:**
- JSON structure validation (if structured output)
- Slot value format validation (dates, times)
- Response length (too short/long flagged)
- Toxicity detection (filter inappropriate responses)
- Confidence threshold (flag low-confidence predictions)

### 7.3 Data Quality Metrics

**Quality Score:**
```python
quality_score = (
 0.3 * slot_extraction_accuracy +
 0.2 * response_relevance +
 0.2 * confidence_score +
 0.15 * latency_score + # Lower is better
 0.15 * cost_efficiency_score # Lower is better
)
```

---

## 8. Performance Optimization

### 8.1 Streaming Responses

**Streaming LLM Responses:**
```python
# Instead of waiting for full response, stream tokens
async for token in llm.stream_response(user_input, context):
 # Start TTS synthesis early (with partial text)
 # Reduce perceived latency
 pass
```

**Benefits**: 30-50% reduction in perceived latency

### 8.2 Request Batching

**Batch Similar Requests:**
```python
# If multiple users in same state, batch LLM calls
batched_requests = [
 {"user_id": "u1", "input": "tomorrow", "state": "collect_date"},
 {"user_id": "u2", "input": "next week", "state": "collect_date"}
]
responses = await llm.batch_generate(batched_requests)
```

**Use Case**: Multi-user scenarios, reduces API overhead

### 8.3 Pre-computation

**Pre-compute Common Responses:**
- Greeting messages (state-independent)
- Confirmation prompts (template-based)
- Error messages (static)

**Cache Warm-up**: Pre-generate common responses on startup

---

## 9. Continuous Improvement Loop

### 9.1 Feedback Collection

**Explicit Feedback:**
- Post-conversation survey: "Was the agent helpful?" (1-5 scale)
- Task completion confirmation: "Did we schedule your appointment correctly?"

**Implicit Signals:**
- Retry rate (user rephrasing indicates misunderstanding)
- Abandonment rate (user leaving mid-conversation)
- Time to completion (faster = better UX)

### 9.2 Model Retraining Pipeline

**Data Collection:**
1. Log all conversations with outcomes
2. Flag high-quality vs low-quality interactions
3. Build training dataset from successful conversations

**Retraining Schedule:**
- **Weekly**: Prompt optimization based on recent data
- **Monthly**: Model fine-tuning (if using trainable models)
- **Quarterly**: Full model evaluation and potential replacement

### 9.3 Error Analysis

**Error Categorization:**
- **STT Errors**: Misheard words → improve audio quality or model
- **Intent Errors**: Wrong classification → improve prompt/examples
- **Slot Errors**: Missed entities → enhance extraction logic
- **State Errors**: Invalid transitions → fix state machine logic

**Root Cause Analysis:**
- Group errors by category
- Identify patterns (common failure modes)
- Prioritize fixes by impact (frequency × severity)

---

## 10. MLOps Integration

### 10.1 CI/CD for ML

**Pipeline Stages:**
1. **Data Validation**: Check quality of training data
2. **Model Training**: Train/fine-tune model
3. **Model Evaluation**: Run on test set, check metrics
4. **Model Registry**: Version and store model
5. **A/B Test Setup**: Configure experiment
6. **Deployment**: Deploy to staging → production
7. **Monitoring**: Track performance metrics

### 10.2 Model Monitoring Dashboard

**Key Metrics to Display:**
- Real-time: Latency (p50, p95, p99), error rate, throughput
- Daily: Success rate, cost per conversation, user satisfaction
- Weekly: Model comparison, A/B test results, drift detection

**Alerts:**
- Latency > threshold (p95 > 2s)
- Error rate spike (> 5% in 5 minutes)
- Cost anomaly (50% increase)
- Model drift detected

---

## 11. Talking Points

When presenting this approach:

1. **"I focused on evaluation first"**: Can't improve what you don't measure
2. **"I used a hybrid approach"**: Rules + LLM for reliability + flexibility
3. **"Cost optimization was critical"**: Token tracking, caching, smart fallbacks
4. **"I implemented experimentation"**: A/B testing for data-driven decisions
5. **"Production ML patterns"**: Model registry, versioning, monitoring
6. **"Continuous improvement loop"**: Feedback → analysis → refinement


