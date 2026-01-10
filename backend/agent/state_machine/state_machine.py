from typing import Dict, Optional
from agent.state_machine.state import (
    ConversationState,
    StateResponse,
    GreetingState,
    CollectDateState,
    CollectTimeState,
    ConfirmationState,
    FallbackState,
    TerminalState
)
from agent.state_machine.context import ConversationContext
from utils.logger import logger


class StateMachine:
    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.states: Dict[str, ConversationState] = {
            "greeting": GreetingState(),
            "collect_date": CollectDateState(),
            "collect_time": CollectTimeState(),
            "confirmation": ConfirmationState(),
            "fallback": FallbackState(),
            "terminal": TerminalState(),
        }
        self.current_state_name: str = "greeting"
        logger.info("State machine initialized", initial_state=self.current_state_name)
    
    def get_current_state(self) -> ConversationState:
        return self.states.get(self.current_state_name, self.states["greeting"])
    
    def transition_to(self, state_name: str, context: ConversationContext) -> bool:
        if state_name not in self.states:
            logger.error("Invalid state transition", state=state_name, valid_states=list(self.states.keys()))
            return False
        
        previous_state = self.current_state_name
        self.current_state_name = state_name
        context.current_state = state_name
        
        logger.info("State transition", from_state=previous_state, to_state=state_name)
        return True
    
    def can_transition_to(self, target_state: str) -> bool:
        current_state = self.get_current_state()
        return current_state.can_transition_to(target_state)
    
    async def process_user_input(
        self, 
        user_text: str, 
        context: ConversationContext
    ) -> StateResponse:
        current_state = self.get_current_state()
        
        logger.info("Processing user input", 
                   current_state=self.current_state_name,
                   input_length=len(user_text))
        
        try:
            response = await current_state.handle_input(
                user_text=user_text,
                context=context,
                llm_service=self.llm_service
            )
            
            if response.next_state:
                if response.next_state != self.current_state_name:
                    self.transition_to(response.next_state, context)
            
            return response
        except Exception as e:
            logger.error("Error processing user input", error=str(e), state=self.current_state_name)
            return StateResponse(
                next_state="fallback",
                response_text="I encountered an error. Let me try again.",
                should_continue=True
            )
    
    def get_initial_prompt(self, context: ConversationContext) -> str:
        current_state = self.get_current_state()
        return current_state.get_prompt(context)
    
    def reset_to_initial_state(self, context: ConversationContext):
        self.current_state_name = "greeting"
        context.current_state = "greeting"
        context.retry_count = 0
        logger.info("State machine reset to initial state")

