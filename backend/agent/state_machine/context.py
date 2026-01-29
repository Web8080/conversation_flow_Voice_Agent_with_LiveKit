from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from utils.logger import logger


@dataclass
class Turn:
    role: str  # "user" or "agent"
    text: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationContext:
    def __init__(self, user_id: Optional[str] = None, session_id: Optional[str] = None):
        self.user_id = user_id
        self.session_id = session_id
        self.current_state: Optional[str] = None
        self.slots: Dict[str, Any] = {}
        self.history: List[Turn] = []
        self.retry_count: int = 0
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()
        logger.info("Conversation context created", session_id=session_id)
    
    def update_slot(self, slot_name: str, value: Any) -> bool:
        old_value = self.slots.get(slot_name)
        self.slots[slot_name] = value
        self.updated_at = datetime.now()
        logger.info("Slot updated", slot=slot_name, old_value=old_value, new_value=value)
        return True
    
    def get_slot(self, slot_name: str) -> Optional[Any]:
        return self.slots.get(slot_name)
    
    def are_required_slots_filled(self, required_slots: List[str]) -> bool:
        return all(self.slots.get(slot) is not None for slot in required_slots)
    
    def get_missing_slots(self, required_slots: List[str]) -> List[str]:
        return [slot for slot in required_slots if self.slots.get(slot) is None]
    
    def add_turn(self, turn: Turn):
        self.history.append(turn)
        self.updated_at = datetime.now()
        logger.debug("Turn added to history", role=turn.role, text_length=len(turn.text))
    
    def get_recent_turns(self, limit: int = 5) -> List[Turn]:
        return self.history[-limit:] if len(self.history) > limit else self.history
    
    def get_conversation_history_for_llm(self) -> List[Dict[str, str]]:
        return [
            {"role": turn.role, "content": turn.text}
            for turn in self.history[-10:]  # Last 10 turns for LLM context
        ]
    
    def increment_retry_count(self):
        self.retry_count += 1
        self.updated_at = datetime.now()
        logger.info("Retry count incremented", count=self.retry_count)
    
    def reset_retry_count(self):
        self.retry_count = 0
        self.updated_at = datetime.now()
        logger.info("Retry count reset")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "current_state": self.current_state,
            "slots": self.slots,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "turn_count": len(self.history),
        }


