from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict


PROVIDER_PRICING = {
    "openai": {
        "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
        "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
        "gpt-3.5-turbo": {"input": 0.50 / 1_000_000, "output": 1.50 / 1_000_000},
    },
    "groq": {
        "llama-3.1-70b-versatile": {"input": 0.0, "output": 0.0},  # Free tier
        "default": {"input": 0.27 / 1_000_000, "output": 0.27 / 1_000_000},
    },
    "ollama": {
        "default": {"input": 0.0, "output": 0.0},  # Local, free
    }
}


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    provider: str = ""
    model: str = ""


@dataclass
class ConversationCost:
    conversation_id: str
    start_time: datetime
    token_usages: list[TokenUsage] = field(default_factory=list)
    total_cost: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0


class CostTracker:
    def __init__(self, daily_budget: Optional[float] = None, monthly_budget: Optional[float] = None):
        self.conversations: Dict[str, ConversationCost] = {}
        self.daily_costs: Dict[str, float] = defaultdict(float)
        self.monthly_costs: Dict[str, float] = defaultdict(float)
        self.daily_budget = daily_budget
        self.monthly_budget = monthly_budget
    
    def start_conversation(self, conversation_id: str) -> ConversationCost:
        cost = ConversationCost(
            conversation_id=conversation_id,
            start_time=datetime.now()
        )
        self.conversations[conversation_id] = cost
        return cost
    
    def record_token_usage(
        self,
        conversation_id: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        if conversation_id not in self.conversations:
            self.start_conversation(conversation_id)
        
        cost = self._calculate_cost(provider, model, input_tokens, output_tokens)
        
        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost,
            provider=provider,
            model=model
        )
        
        conv_cost = self.conversations[conversation_id]
        conv_cost.token_usages.append(usage)
        conv_cost.total_cost += cost
        conv_cost.total_input_tokens += input_tokens
        conv_cost.total_output_tokens += output_tokens
        
        today = datetime.now().strftime("%Y-%m-%d")
        this_month = datetime.now().strftime("%Y-%m")
        
        self.daily_costs[today] += cost
        self.monthly_costs[this_month] += cost
        
        return cost
    
    def _calculate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        pricing = PROVIDER_PRICING.get(provider, {}).get(model)
        
        if pricing is None:
            pricing = PROVIDER_PRICING.get(provider, {}).get("default", {"input": 0.0, "output": 0.0})
        
        input_cost = pricing["input"] * input_tokens
        output_cost = pricing["output"] * output_tokens
        
        return input_cost + output_cost
    
    def get_conversation_cost(self, conversation_id: str) -> Optional[ConversationCost]:
        return self.conversations.get(conversation_id)
    
    def get_daily_cost(self, date: Optional[str] = None) -> float:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        return self.daily_costs.get(date, 0.0)
    
    def get_monthly_cost(self, month: Optional[str] = None) -> float:
        if month is None:
            month = datetime.now().strftime("%Y-%m")
        return self.monthly_costs.get(month, 0.0)
    
    def check_budget_limit(self) -> tuple[bool, str]:
        daily_cost = self.get_daily_cost()
        monthly_cost = self.get_monthly_cost()
        
        if self.daily_budget and daily_cost >= self.daily_budget:
            return True, f"Daily budget exceeded: ${daily_cost:.4f} / ${self.daily_budget:.4f}"
        
        if self.monthly_budget and monthly_cost >= self.monthly_budget:
            return True, f"Monthly budget exceeded: ${monthly_cost:.4f} / ${self.monthly_budget:.4f}"
        
        return False, ""
    
    def get_summary(self) -> Dict:
        total_conversations = len(self.conversations)
        total_cost = sum(conv.total_cost for conv in self.conversations.values())
        avg_cost_per_conversation = total_cost / total_conversations if total_conversations > 0 else 0
        
        total_input_tokens = sum(conv.total_input_tokens for conv in self.conversations.values())
        total_output_tokens = sum(conv.total_output_tokens for conv in self.conversations.values())
        
        return {
            "total_conversations": total_conversations,
            "total_cost": total_cost,
            "avg_cost_per_conversation": avg_cost_per_conversation,
            "daily_cost": self.get_daily_cost(),
            "monthly_cost": self.get_monthly_cost(),
            "total_tokens": {
                "input": total_input_tokens,
                "output": total_output_tokens,
                "total": total_input_tokens + total_output_tokens
            },
            "budget_status": {
                "daily_limit": self.daily_budget,
                "daily_usage": self.get_daily_cost(),
                "daily_remaining": (self.daily_budget - self.get_daily_cost()) if self.daily_budget else None,
                "monthly_limit": self.monthly_budget,
                "monthly_usage": self.get_monthly_cost(),
                "monthly_remaining": (self.monthly_budget - self.get_monthly_cost()) if self.monthly_budget else None
            }
        }


_global_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker(daily_budget: Optional[float] = None, monthly_budget: Optional[float] = None) -> CostTracker:
    global _global_cost_tracker
    if _global_cost_tracker is None:
        _global_cost_tracker = CostTracker(daily_budget=daily_budget, monthly_budget=monthly_budget)
    return _global_cost_tracker

