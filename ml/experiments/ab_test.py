import hashlib
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict


@dataclass
class ExperimentVariant:
    name: str
    config: Dict[str, Any]
    traffic_percentage: float = 0.5


@dataclass
class Experiment:
    name: str
    variants: List[ExperimentVariant]
    start_date: datetime
    end_date: Optional[datetime] = None
    active: bool = True
    metrics: List[str] = field(default_factory=lambda: ["success_rate", "avg_turns", "cost_per_conversation"])
    results: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class ABTestManager:
    def __init__(self):
        self.experiments: Dict[str, Experiment] = {}
        self.user_assignments: Dict[str, Dict[str, str]] = defaultdict(dict)
        self.conversation_metrics: Dict[str, Dict[str, Any]] = {}
    
    def register_experiment(
        self,
        experiment_name: str,
        variants: List[ExperimentVariant],
        metrics: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Experiment:
        if experiment_name in self.experiments:
            raise ValueError(f"Experiment '{experiment_name}' already exists")
        
        experiment = Experiment(
            name=experiment_name,
            variants=variants,
            start_date=start_date or datetime.now(),
            end_date=end_date,
            active=True,
            metrics=metrics
        )
        
        self.experiments[experiment_name] = experiment
        return experiment
    
    def get_variant_for_user(self, experiment_name: str, user_id: str) -> Optional[ExperimentVariant]:
        if experiment_name not in self.experiments:
            return None
        
        experiment = self.experiments[experiment_name]
        
        if not experiment.active:
            return experiment.variants[0]
        
        if experiment.end_date and datetime.now() > experiment.end_date:
            experiment.active = False
            return experiment.variants[0]
        
        if user_id in self.user_assignments and experiment_name in self.user_assignments[user_id]:
            assigned_variant_name = self.user_assignments[user_id][experiment_name]
            return next((v for v in experiment.variants if v.name == assigned_variant_name), experiment.variants[0])
        
        variant = self._assign_variant(experiment, user_id)
        if user_id not in self.user_assignments:
            self.user_assignments[user_id] = {}
        self.user_assignments[user_id][experiment_name] = variant.name
        
        return variant
    
    def _assign_variant(self, experiment: Experiment, user_id: str) -> ExperimentVariant:
        hash_input = f"{experiment.name}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        cumulative_percentage = 0.0
        for variant in experiment.variants:
            cumulative_percentage += variant.traffic_percentage
            if (hash_value % 100) / 100.0 < cumulative_percentage:
                return variant
        
        return experiment.variants[0]
    
    def record_conversation_metric(
        self,
        experiment_name: str,
        variant_name: str,
        conversation_id: str,
        metrics: Dict[str, Any]
    ):
        if experiment_name not in self.experiments:
            return
        
        if conversation_id not in self.conversation_metrics:
            self.conversation_metrics[conversation_id] = {}
        
        key = f"{experiment_name}:{variant_name}"
        if key not in self.conversation_metrics[conversation_id]:
            self.conversation_metrics[conversation_id][key] = {}
        
        self.conversation_metrics[conversation_id][key].update(metrics)
    
    def get_experiment_results(self, experiment_name: str) -> Dict[str, Any]:
        if experiment_name not in self.experiments:
            return {}
        
        experiment = self.experiments[experiment_name]
        results = {}
        
        for variant in experiment.variants:
            variant_conversations = []
            
            for conv_id, conv_metrics in self.conversation_metrics.items():
                key = f"{experiment_name}:{variant.name}"
                if key in conv_metrics:
                    variant_conversations.append(conv_metrics[key])
            
            if not variant_conversations:
                results[variant.name] = {"status": "no_data"}
                continue
            
            variant_results = {}
            for metric_name in experiment.metrics:
                values = [conv.get(metric_name) for conv in variant_conversations if conv.get(metric_name) is not None]
                if values:
                    variant_results[metric_name] = {
                        "count": len(values),
                        "mean": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values)
                    }
            
            results[variant.name] = variant_results
        
        experiment.results = results
        return results
    
    def end_experiment(self, experiment_name: str):
        if experiment_name not in self.experiments:
            return
        
        experiment = self.experiments[experiment_name]
        experiment.active = False
        experiment.end_date = datetime.now()
        
        return self.get_experiment_results(experiment_name)


_global_ab_test_manager: Optional[ABTestManager] = None


def get_ab_test_manager() -> ABTestManager:
    global _global_ab_test_manager
    if _global_ab_test_manager is None:
        _global_ab_test_manager = ABTestManager()
    return _global_ab_test_manager

