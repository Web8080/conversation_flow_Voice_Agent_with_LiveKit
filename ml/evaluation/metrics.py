from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
from collections import defaultdict


@dataclass
class ConversationMetrics:
    conversation_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    task_completed: bool = False
    total_turns: int = 0
    final_state: Optional[str] = None
    user_satisfaction: Optional[float] = None
    abandoned: bool = False


@dataclass
class ModelPerformanceMetrics:
    model_name: str
    provider: str
    prompt_version: str
    
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    
    latency_ms: List[float] = field(default_factory=list)
    input_tokens: List[int] = field(default_factory=list)
    output_tokens: List[int] = field(default_factory=list)
    total_cost: float = 0.0
    
    intent_accuracy: Optional[float] = None
    slot_extraction_f1: Optional[float] = None
    avg_confidence: float = 0.0


@dataclass
class ServiceMetrics:
    service_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    latency_ms: List[float] = field(default_factory=list)
    error_rate: float = 0.0


class MetricsCollector:
    def __init__(self):
        self.conversations: Dict[str, ConversationMetrics] = {}
        self.model_metrics: Dict[str, ModelPerformanceMetrics] = {}
        self.service_metrics: Dict[str, ServiceMetrics] = {}
        self.experiments: Dict[str, Dict[str, Any]] = defaultdict(dict)
    
    def start_conversation(self, conversation_id: str) -> ConversationMetrics:
        metrics = ConversationMetrics(
            conversation_id=conversation_id,
            start_time=datetime.now()
        )
        self.conversations[conversation_id] = metrics
        return metrics
    
    def end_conversation(
        self,
        conversation_id: str,
        success: bool,
        task_completed: bool,
        total_turns: int,
        final_state: Optional[str] = None,
        user_satisfaction: Optional[float] = None,
        abandoned: bool = False
    ):
        if conversation_id not in self.conversations:
            return
        
        metrics = self.conversations[conversation_id]
        metrics.end_time = datetime.now()
        metrics.success = success
        metrics.task_completed = task_completed
        metrics.total_turns = total_turns
        metrics.final_state = final_state
        metrics.user_satisfaction = user_satisfaction
        metrics.abandoned = abandoned
    
    def record_model_request(
        self,
        model_name: str,
        provider: str,
        prompt_version: str,
        latency_ms: float,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        success: bool,
        confidence: Optional[float] = None
    ):
        key = f"{provider}/{model_name}/{prompt_version}"
        
        if key not in self.model_metrics:
            self.model_metrics[key] = ModelPerformanceMetrics(
                model_name=model_name,
                provider=provider,
                prompt_version=prompt_version
            )
        
        metrics = self.model_metrics[key]
        metrics.total_requests += 1
        
        if success:
            metrics.successful_requests += 1
            metrics.latency_ms.append(latency_ms)
            metrics.input_tokens.append(input_tokens)
            metrics.output_tokens.append(output_tokens)
            metrics.total_cost += cost
            
            if confidence is not None:
                current_avg = metrics.avg_confidence
                count = metrics.successful_requests
                metrics.avg_confidence = ((current_avg * (count - 1)) + confidence) / count
        else:
            metrics.failed_requests += 1
    
    def record_service_request(
        self,
        service_name: str,
        latency_ms: float,
        success: bool
    ):
        if service_name not in self.service_metrics:
            self.service_metrics[service_name] = ServiceMetrics(service_name=service_name)
        
        metrics = self.service_metrics[service_name]
        metrics.total_requests += 1
        
        if success:
            metrics.successful_requests += 1
            metrics.latency_ms.append(latency_ms)
        else:
            metrics.failed_requests += 1
        
        if metrics.total_requests > 0:
            metrics.error_rate = metrics.failed_requests / metrics.total_requests
    
    def get_summary(self) -> Dict[str, Any]:
        conversation_metrics = []
        for conv in self.conversations.values():
            if conv.end_time:
                duration = (conv.end_time - conv.start_time).total_seconds()
                conversation_metrics.append({
                    "id": conv.conversation_id,
                    "duration_seconds": duration,
                    "success": conv.success,
                    "task_completed": conv.task_completed,
                    "total_turns": conv.total_turns,
                    "final_state": conv.final_state,
                    "abandoned": conv.abandoned
                })
        
        model_summaries = {}
        for key, metrics in self.model_metrics.items():
            latency_p50 = self._percentile(metrics.latency_ms, 50) if metrics.latency_ms else None
            latency_p95 = self._percentile(metrics.latency_ms, 95) if metrics.latency_ms else None
            latency_p99 = self._percentile(metrics.latency_ms, 99) if metrics.latency_ms else None
            
            model_summaries[key] = {
                "total_requests": metrics.total_requests,
                "success_rate": metrics.successful_requests / metrics.total_requests if metrics.total_requests > 0 else 0,
                "latency_p50_ms": latency_p50,
                "latency_p95_ms": latency_p95,
                "latency_p99_ms": latency_p99,
                "avg_input_tokens": sum(metrics.input_tokens) / len(metrics.input_tokens) if metrics.input_tokens else 0,
                "avg_output_tokens": sum(metrics.output_tokens) / len(metrics.output_tokens) if metrics.output_tokens else 0,
                "total_cost": metrics.total_cost,
                "avg_cost_per_request": metrics.total_cost / metrics.successful_requests if metrics.successful_requests > 0 else 0,
                "avg_confidence": metrics.avg_confidence
            }
        
        service_summaries = {}
        for name, metrics in self.service_metrics.items():
            latency_p50 = self._percentile(metrics.latency_ms, 50) if metrics.latency_ms else None
            latency_p95 = self._percentile(metrics.latency_ms, 95) if metrics.latency_ms else None
            
            service_summaries[name] = {
                "total_requests": metrics.total_requests,
                "success_rate": metrics.successful_requests / metrics.total_requests if metrics.total_requests > 0 else 0,
                "error_rate": metrics.error_rate,
                "latency_p50_ms": latency_p50,
                "latency_p95_ms": latency_p95
            }
        
        completed_conversations = [c for c in conversation_metrics if c.get("success") is not None]
        success_rate = sum(1 for c in completed_conversations if c["success"]) / len(completed_conversations) if completed_conversations else 0
        task_completion_rate = sum(1 for c in completed_conversations if c["task_completed"]) / len(completed_conversations) if completed_conversations else 0
        avg_turns = sum(c["total_turns"] for c in completed_conversations) / len(completed_conversations) if completed_conversations else 0
        
        return {
            "conversations": {
                "total": len(conversation_metrics),
                "completed": len(completed_conversations),
                "success_rate": success_rate,
                "task_completion_rate": task_completion_rate,
                "avg_turns": avg_turns,
                "abandonment_rate": sum(1 for c in completed_conversations if c["abandoned"]) / len(completed_conversations) if completed_conversations else 0
            },
            "models": model_summaries,
            "services": service_summaries
        }
    
    def _percentile(self, data: List[float], percentile: int) -> Optional[float]:
        if not data:
            return None
        sorted_data = sorted(data)
        index = int(len(sorted_data) * (percentile / 100))
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]


_global_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    return _global_collector


