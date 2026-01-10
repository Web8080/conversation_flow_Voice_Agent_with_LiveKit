import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from ml.cost_tracker import get_cost_tracker
    from ml.evaluation import get_metrics_collector
except ImportError:
    get_cost_tracker = None
    get_metrics_collector = None


class PredictionLogger:
    def __init__(self, log_dir: str = "logs/predictions"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.cost_tracker = get_cost_tracker() if get_cost_tracker else None
        self.metrics_collector = get_metrics_collector() if get_metrics_collector else None
    
    def log_prediction(
        self,
        conversation_id: str,
        model: str,
        provider: str,
        prompt_version: str,
        user_input: str,
        state: str,
        slots: Dict[str, Any],
        response: str,
        extracted_slots: Dict[str, Any],
        confidence: float,
        next_state: str,
        latency_ms: float,
        input_tokens: int,
        output_tokens: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        prediction_log = {
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "model": {
                "name": model,
                "provider": provider,
                "prompt_version": prompt_version
            },
            "input": {
                "user_text": user_input,
                "state": state,
                "slots": slots
            },
            "output": {
                "response": response,
                "extracted_slots": extracted_slots,
                "confidence": confidence,
                "next_state": next_state
            },
            "metadata": {
                "latency_ms": latency_ms,
                "tokens": {
                    "input": input_tokens,
                    "output": output_tokens,
                    "total": input_tokens + output_tokens
                },
                **(metadata or {})
            }
        }
        
        cost = 0.0
        if self.cost_tracker:
            cost = self.cost_tracker.record_token_usage(
                conversation_id=conversation_id,
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
        
        prediction_log["metadata"]["cost"] = cost
        
        if self.metrics_collector:
            self.metrics_collector.record_model_request(
                model_name=model,
                provider=provider,
                prompt_version=prompt_version,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                success=True,
                confidence=confidence
            )
        
        log_file = self.log_dir / f"predictions_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(prediction_log) + "\n")
        
        return prediction_log
    
    def log_error(
        self,
        conversation_id: str,
        model: str,
        provider: str,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        error_log = {
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "error": {
                "type": error_type,
                "message": error_message,
                "model": model,
                "provider": provider
            },
            "context": context or {}
        }
        
        if self.metrics_collector:
            self.metrics_collector.record_model_request(
                model_name=model,
                provider=provider,
                prompt_version="unknown",
                latency_ms=0,
                input_tokens=0,
                output_tokens=0,
                cost=0.0,
                success=False
            )
        
        log_file = self.log_dir / f"errors_{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(error_log) + "\n")


_global_prediction_logger: Optional[PredictionLogger] = None


def get_prediction_logger(log_dir: str = "logs/predictions") -> PredictionLogger:
    global _global_prediction_logger
    if _global_prediction_logger is None:
        _global_prediction_logger = PredictionLogger(log_dir=log_dir)
    return _global_prediction_logger

