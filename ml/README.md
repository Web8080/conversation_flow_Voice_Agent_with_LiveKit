# ML/AI Scientist Enhancements

## Overview

This directory contains enhancements from a **senior ML/AI scientist perspective**, focusing on evaluation, experimentation, cost optimization, and production ML practices.

---

## Structure

```
ml/
├── ML_APPROACH.md              # Comprehensive ML strategy document
├── evaluation/
│   ├── metrics.py              # Metrics collection and tracking
│   └── __init__.py
├── cost_tracker.py             # Token usage and cost tracking
├── prediction_logger.py        # Prediction logging for observability
├── experiments/
│   ├── ab_test.py              # A/B testing framework
│   └── __init__.py
├── slot_extraction/
│   └── enhanced_extractor.py   # Hybrid rule-based + LLM slot extraction
└── README.md                   # This file
```

---

## Key Improvements

### 1. Evaluation Framework (`evaluation/metrics.py`)

**What it does:**
- Tracks conversation-level metrics (success rate, task completion, turns)
- Tracks model performance (latency, accuracy, cost, confidence)
- Tracks service performance (STT, LLM, TTS error rates)

**Usage:**
```python
from ml.evaluation import get_metrics_collector

collector = get_metrics_collector()

# Start conversation
conv_metrics = collector.start_conversation("conv-123")

# Record model request
collector.record_model_request(
    model_name="llama3.2",
    provider="ollama",
    prompt_version="v2.0",
    latency_ms=450,
    input_tokens=120,
    output_tokens=45,
    cost=0.0,
    success=True,
    confidence=0.92
)

# End conversation
collector.end_conversation(
    conversation_id="conv-123",
    success=True,
    task_completed=True,
    total_turns=5,
    final_state="terminal",
    user_satisfaction=4.5
)

# Get summary
summary = collector.get_summary()
```

**Metrics Collected:**
- Conversation: success rate, task completion rate, avg turns, abandonment rate
- Model: latency (p50, p95, p99), token usage, cost, confidence scores
- Service: error rates, latency percentiles

---

### 2. Cost Tracking (`cost_tracker.py`)

**What it does:**
- Tracks token usage per conversation
- Calculates costs based on provider pricing
- Monitors daily/monthly budgets
- Provides cost summaries

**Usage:**
```python
from ml.cost_tracker import get_cost_tracker

tracker = get_cost_tracker(daily_budget=10.0, monthly_budget=300.0)

# Start conversation
tracker.start_conversation("conv-123")

# Record token usage
cost = tracker.record_token_usage(
    conversation_id="conv-123",
    provider="openai",
    model="gpt-4o-mini",
    input_tokens=150,
    output_tokens=75
)

# Check budget
exceeded, message = tracker.check_budget_limit()

# Get summary
summary = tracker.get_summary()
```

**Supported Providers:**
- OpenAI: GPT-4o-mini, GPT-4o, GPT-3.5-turbo
- Groq: Llama-3.1-70b (free tier pricing)
- Ollama: Free (local compute)

---

### 3. Prediction Logging (`prediction_logger.py`)

**What it does:**
- Logs all predictions to JSONL files
- Tracks input/output, confidence, latency, cost
- Enables model debugging and analysis
- Integrates with metrics and cost tracking

**Usage:**
```python
from ml.prediction_logger import get_prediction_logger

logger = get_prediction_logger()

logger.log_prediction(
    conversation_id="conv-123",
    model="llama3.2",
    provider="ollama",
    prompt_version="v2.0",
    user_input="I want to schedule tomorrow at 2pm",
    state="collect_date",
    slots={},
    response="I'd be happy to help...",
    extracted_slots={"date": "2025-01-11", "time": "14:00"},
    confidence=0.92,
    next_state="confirmation",
    latency_ms=450,
    input_tokens=120,
    output_tokens=45,
    metadata={"experiment": "prompt_v2_vs_v1", "variant": "v2.0"}
)
```

**Log Format:**
```json
{
  "conversation_id": "conv-123",
  "timestamp": "2025-01-10T10:30:00",
  "model": {"name": "llama3.2", "provider": "ollama", "prompt_version": "v2.0"},
  "input": {"user_text": "...", "state": "collect_date", "slots": {}},
  "output": {"response": "...", "extracted_slots": {}, "confidence": 0.92, "next_state": "confirmation"},
  "metadata": {"latency_ms": 450, "tokens": {"input": 120, "output": 45}, "cost": 0.0}
}
```

---

### 4. A/B Testing Framework (`experiments/ab_test.py`)

**What it does:**
- Manages A/B experiments (prompts, models, configs)
- Assigns users to variants consistently
- Tracks metrics per variant
- Provides experiment results

**Usage:**
```python
from ml.experiments import get_ab_test_manager, ExperimentVariant

manager = get_ab_test_manager()

# Register experiment
experiment = manager.register_experiment(
    experiment_name="prompt_v2_vs_v1",
    variants=[
        ExperimentVariant("v1.0", {"prompt_version": "v1.0"}, traffic_percentage=0.5),
        ExperimentVariant("v2.0", {"prompt_version": "v2.0"}, traffic_percentage=0.5)
    ],
    metrics=["success_rate", "avg_turns", "cost_per_conversation"]
)

# Get variant for user
variant = manager.get_variant_for_user("prompt_v2_vs_v1", "user-123")
# Returns: ExperimentVariant with config {"prompt_version": "v2.0"}

# Record metrics
manager.record_conversation_metric(
    experiment_name="prompt_v2_vs_v1",
    variant_name="v2.0",
    conversation_id="conv-123",
    metrics={"success_rate": 1.0, "avg_turns": 5, "cost_per_conversation": 0.002}
)

# Get results
results = manager.get_experiment_results("prompt_v2_vs_v1")
```

---

### 5. Enhanced Slot Extraction (`slot_extraction/enhanced_extractor.py`)

**What it does:**
- Hybrid rule-based + LLM extraction
- Higher confidence for rule-based matches
- Confidence scoring per slot
- Needs-confirmation flagging

**Usage:**
```python
from ml.slot_extraction.enhanced_extractor import EnhancedSlotExtractor

extractor = EnhancedSlotExtractor()

# Extract date
date_slot = extractor.extract_date("I want to schedule tomorrow at 2pm")
# Returns: ExtractedSlot(value="2025-01-11", confidence=0.95, source="rules", needs_confirmation=False)

# Extract time
time_slot = extractor.extract_time("I want to schedule tomorrow at 2pm")
# Returns: ExtractedSlot(value="14:00", confidence=0.95, source="rules", needs_confirmation=False)

# Extract all slots
slots = extractor.extract_all_slots("My name is John Doe, schedule tomorrow at 2pm", ["name", "date", "time"])
# Returns: {
#   "name": ExtractedSlot(value="John Doe", confidence=0.9, ...),
#   "date": ExtractedSlot(value="2025-01-11", confidence=0.95, ...),
#   "time": ExtractedSlot(value="14:00", confidence=0.95, ...)
# }
```

**Supported Patterns:**
- Dates: "tomorrow", "next week", "Monday", "Jan 15", "12/31/2025"
- Times: "2pm", "14:00", "afternoon", "morning"
- Names: "my name is X", "I'm X", "it's X"

---

## Integration with Backend

### Step 1: Update LLM Service

Add metrics tracking to `backend/agent/services/llm_service.py`:

```python
from ml.evaluation import get_metrics_collector
from ml.prediction_logger import get_prediction_logger
from ml.cost_tracker import get_cost_tracker
import time

class OllamaLLMService(LLMService):
    async def generate_response(self, user_text: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        start_time = time.time()
        collector = get_metrics_collector()
        logger = get_prediction_logger()
        
        try:
            # ... existing LLM call ...
            latency_ms = (time.time() - start_time) * 1000
            
            # Track metrics
            collector.record_model_request(
                model_name=self.model,
                provider="ollama",
                prompt_version="v2.0",
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=0.0,
                success=True,
                confidence=0.92
            )
            
            return text.strip()
        except Exception as e:
            # Track failure
            collector.record_model_request(...success=False)
            logger.log_error(...)
            return None
```

### Step 2: Update State Machine

Add confidence scoring to slot extraction:

```python
from ml.slot_extraction.enhanced_extractor import EnhancedSlotExtractor

class CollectDateState(ConversationState):
    def __init__(self):
        self.extractor = EnhancedSlotExtractor()
    
    async def handle_input(self, user_text: str, context: ConversationContext, llm_service: LLMService) -> StateResponse:
        # Try rule-based first
        date_slot = self.extractor.extract_date(user_text)
        
        if date_slot and date_slot.confidence > 0.8:
            context.slots["date"] = date_slot.value
            # Use LLM for natural response generation
            response_text = await llm_service.generate_response(...)
            return StateResponse(next_state="collect_time", response_text=response_text, ...)
        
        # Fallback to LLM extraction
        # ...
```

### Step 3: Add Experimentation

Enable A/B testing in main agent:

```python
from ml.experiments import get_ab_test_manager

manager = get_ab_test_manager()
variant = manager.get_variant_for_user("prompt_v2_vs_v1", user_id)

# Use variant.config["prompt_version"] in prompt
```

---

## Production Considerations

### 1. Log Storage
- Store prediction logs in S3/GCS for long-term analysis
- Rotate logs daily (current: JSONL per day)
- Use log aggregation (ELK, Datadog) for querying

### 2. Metrics Dashboard
- Export metrics to Prometheus
- Build Grafana dashboards
- Set up alerts for anomalies

### 3. Cost Monitoring
- Set up budget alerts (email/Slack)
- Monitor cost trends (daily/weekly reports)
- Implement automatic fallback to cheaper models

### 4. Experiment Analysis
- Statistical significance testing (t-test, chi-square)
- Power analysis for experiment sizing
- Automated experiment reports

### 5. Model Registry
- Version control for prompts/configs
- Track model performance over time
- Canary deployments with gradual rollout

---

## Interview Talking Points

When presenting this ML approach:

1. **"I focused on evaluation first"**: Can't improve what you don't measure
2. **"Hybrid extraction system"**: Rules for reliability, LLM for flexibility
3. **"Cost optimization"**: Token tracking, budget limits, smart fallbacks
4. **"Experimentation framework"**: A/B testing for data-driven decisions
5. **"Production ML patterns"**: Prediction logging, model registry, monitoring
6. **"Continuous improvement loop"**: Feedback → analysis → refinement

This demonstrates **senior ML/AI thinking**: Not just building models, but building **systems** that improve over time.

---

## Next Steps

1. **Integrate ML components** into backend services
2. **Add monitoring dashboards** (Grafana + Prometheus)
3. **Set up experiment tracking** (MLflow, Weights & Biases)
4. **Implement model registry** (version control for prompts/models)
5. **Add automated testing** (evaluate on gold standard dataset)

---

## References

- `ML_APPROACH.md`: Comprehensive ML strategy document
- `backend/agent/services/llm_service.py`: LLM service implementation
- `backend/agent/state_machine/state_machine.py`: State machine logic

