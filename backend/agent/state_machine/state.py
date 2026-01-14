from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from agent.state_machine.context import ConversationContext, Turn
from utils.logger import logger


@dataclass
class StateResponse:
    next_state: Optional[str]
    response_text: str
    should_continue: bool = True
    extracted_slots: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.extracted_slots is None:
            self.extracted_slots = {}


class ConversationState(ABC):
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.required_slots: List[str] = []
        self.optional_slots: List[str] = []
        self.max_retries: int = 3
        self.fallback_state: str = "fallback"
    
    @abstractmethod
    def get_prompt(self, context: ConversationContext) -> str:
        pass
    
    @abstractmethod
    async def handle_input(
        self, 
        user_text: str, 
        context: ConversationContext,
        llm_service
    ) -> StateResponse:
        pass
    
    def can_transition_to(self, target_state: str) -> bool:
        return True
    
    def extract_slots(self, user_text: str, context: ConversationContext, llm_service) -> Dict[str, Any]:
        return {}


class GreetingState(ConversationState):
    def __init__(self):
        super().__init__("greeting", "Initial greeting and introduction")
    
    def get_prompt(self, context: ConversationContext) -> str:
        return "Hello! I'm your appointment scheduling assistant. I can help you book an appointment. What's your name?"
    
    async def handle_input(
        self, 
        user_text: str, 
        context: ConversationContext,
        llm_service
    ) -> StateResponse:
        context.add_turn(Turn(role="user", text=user_text))
        
        extracted_slots = await self._extract_name(user_text, context, llm_service)
        
        if extracted_slots.get("name"):
            context.update_slot("name", extracted_slots["name"])
            response_text = f"Nice to meet you, {extracted_slots['name']}! When would you like to schedule your appointment? Please provide a date."
            context.add_turn(Turn(role="agent", text=response_text))
            return StateResponse(
                next_state="collect_date",
                response_text=response_text,
                extracted_slots=extracted_slots
            )
        else:
            response_text = "I didn't catch your name. Could you please tell me your name?"
            context.add_turn(Turn(role="agent", text=response_text))
            return StateResponse(
                next_state="greeting",
                response_text=response_text
            )
    
    async def _extract_name(self, user_text: str, context: ConversationContext, llm_service) -> Dict[str, Any]:
        prompt = f"""Extract the person's name from this text. If no name is mentioned, return empty string.
Text: "{user_text}"
Return only the name, nothing else."""
        
        try:
            response = await llm_service.generate_response(prompt)
            if response and len(response.strip()) > 0:
                return {"name": response.strip()}
        except Exception as e:
            logger.error("Name extraction failed", error=str(e))
        
        return {}


class CollectDateState(ConversationState):
    def __init__(self):
        super().__init__("collect_date", "Collect appointment date")
        self.required_slots = ["date"]
    
    def get_prompt(self, context: ConversationContext) -> str:
        name = context.get_slot("name") or "there"
        return f"Hi {name}, when would you like to schedule your appointment? Please provide a date."
    
    async def handle_input(
        self, 
        user_text: str, 
        context: ConversationContext,
        llm_service
    ) -> StateResponse:
        context.add_turn(Turn(role="user", text=user_text))
        
        extracted_slots = await self._extract_date(user_text, context, llm_service)
        
        if extracted_slots.get("date"):
            context.update_slot("date", extracted_slots["date"])
            response_text = f"Great! I have you scheduled for {extracted_slots['date']}. What time would you prefer?"
            context.add_turn(Turn(role="agent", text=response_text))
            context.reset_retry_count()
            return StateResponse(
                next_state="collect_time",
                response_text=response_text,
                extracted_slots=extracted_slots
            )
        else:
            context.increment_retry_count()
            if context.retry_count >= self.max_retries:
                response_text = "I'm having trouble understanding the date. Let me connect you with a human agent who can help."
                context.add_turn(Turn(role="agent", text=response_text))
                return StateResponse(
                    next_state="fallback",
                    response_text=response_text,
                    should_continue=False
                )
            else:
                response_text = "I didn't catch the date. Could you please provide a specific date? For example, 'January 15th' or 'next Monday'."
                context.add_turn(Turn(role="agent", text=response_text))
                return StateResponse(
                    next_state="collect_date",
                    response_text=response_text
                )
    
    async def _extract_date(self, user_text: str, context: ConversationContext, llm_service) -> Dict[str, Any]:
        prompt = f"""Extract the date from this text. Convert relative dates like "tomorrow" or "next week" to specific dates.
Today is {context.created_at.strftime('%Y-%m-%d')}.
Text: "{user_text}"
Return only the date in YYYY-MM-DD format, or empty string if no date found."""
        
        try:
            response = await llm_service.generate_response(prompt)
            if response and len(response.strip()) > 0:
                date_str = response.strip()
                if len(date_str) >= 10:
                    return {"date": date_str[:10]}
        except Exception as e:
            logger.error("Date extraction failed", error=str(e))
        
        return {}


class CollectTimeState(ConversationState):
    def __init__(self):
        super().__init__("collect_time", "Collect appointment time")
        self.required_slots = ["time"]
    
    def get_prompt(self, context: ConversationContext) -> str:
        date = context.get_slot("date") or "your selected date"
        return f"What time would you prefer for your appointment on {date}? Please provide a time, for example '2 PM' or '14:00'."
    
    async def handle_input(
        self, 
        user_text: str, 
        context: ConversationContext,
        llm_service
    ) -> StateResponse:
        context.add_turn(Turn(role="user", text=user_text))
        
        extracted_slots = await self._extract_time(user_text, context, llm_service)
        
        if extracted_slots.get("time"):
            context.update_slot("time", extracted_slots["time"])
            date = context.get_slot("date") or "the selected date"
            response_text = f"Perfect! I have {extracted_slots['time']} on {date}. Is this correct?"
            context.add_turn(Turn(role="agent", text=response_text))
            context.reset_retry_count()
            return StateResponse(
                next_state="confirmation",
                response_text=response_text,
                extracted_slots=extracted_slots
            )
        else:
            context.increment_retry_count()
            if context.retry_count >= self.max_retries:
                response_text = "I'm having trouble understanding the time. Let me connect you with a human agent."
                context.add_turn(Turn(role="agent", text=response_text))
                return StateResponse(
                    next_state="fallback",
                    response_text=response_text,
                    should_continue=False
                )
            else:
                response_text = "I didn't catch the time. Could you please provide a specific time? For example, '2 PM' or '14:00'."
                context.add_turn(Turn(role="agent", text=response_text))
                return StateResponse(
                    next_state="collect_time",
                    response_text=response_text
                )
    
    async def _extract_time(self, user_text: str, context: ConversationContext, llm_service) -> Dict[str, Any]:
        prompt = f"""Extract the time from this text. Convert to 24-hour format (HH:MM).
Text: "{user_text}"
Return only the time in HH:MM format (e.g., "14:00" for 2 PM), or empty string if no time found."""
        
        try:
            response = await llm_service.generate_response(prompt)
            if response and len(response.strip()) > 0:
                time_str = response.strip()
                return {"time": time_str}
        except Exception as e:
            logger.error("Time extraction failed", error=str(e))
        
        return {}


class ConfirmationState(ConversationState):
    def __init__(self):
        super().__init__("confirmation", "Confirm appointment details")
        self.calendar_service = None
    
    def set_calendar_service(self, calendar_service):
        """Set calendar service for booking appointments"""
        self.calendar_service = calendar_service
    
    def get_prompt(self, context: ConversationContext) -> str:
        name = context.get_slot("name") or "you"
        date = context.get_slot("date") or "the selected date"
        time = context.get_slot("time") or "the selected time"
        appointment_type = context.get_slot("appointment_type") or "appointment"
        return f"Just to confirm: {name}, you want to schedule a {appointment_type} on {date} at {time}. Is this correct? Please say yes or no."
    
    async def handle_input(
        self, 
        user_text: str, 
        context: ConversationContext,
        llm_service
    ) -> StateResponse:
        context.add_turn(Turn(role="user", text=user_text))
        
        confirmed = await self._extract_confirmation(user_text, context, llm_service)
        
        if confirmed:
            # Book the appointment
            appointment_booked = False
            event_details = None
            
            if self.calendar_service and self.calendar_service.is_enabled():
                try:
                    from datetime import date as date_type, time as time_type
                    import dateutil.parser
                    
                    date_str = context.get_slot("date")
                    time_str = context.get_slot("time")
                    name = context.get_slot("name") or "Guest"
                    appointment_type = context.get_slot("appointment_type") or "Appointment"
                    
                    if date_str and time_str:
                        # Parse date and time
                        appointment_date = dateutil.parser.parse(date_str).date() if isinstance(date_str, str) else date_str
                        appointment_time = dateutil.parser.parse(time_str).time() if isinstance(time_str, str) else time_str
                        
                        # Create appointment in calendar
                        event_details = await self.calendar_service.create_appointment(
                            appointment_date=appointment_date,
                            appointment_time=appointment_time,
                            summary=f"{appointment_type} - {name}",
                            description=f"Appointment scheduled via voice agent for {name}",
                            duration_minutes=30
                        )
                        
                        if event_details:
                            appointment_booked = True
                            context.update_slot("event_id", event_details.get('event_id'))
                            context.update_slot("calendar_link", event_details.get('html_link'))
                            logger.info("Appointment booked successfully", event_id=event_details.get('event_id'))
                except Exception as e:
                    logger.error("Failed to book appointment", error=str(e))
            
            # Generate response
            name = context.get_slot("name") or "you"
            date = context.get_slot("date") or "the selected date"
            time = context.get_slot("time") or "the selected time"
            
            if appointment_booked and event_details:
                response_text = f"Perfect! Your appointment is confirmed for {name} on {date} at {time}. I've added it to your calendar. Thank you, and have a great day!"
            else:
                response_text = f"Perfect! Your appointment is confirmed for {name} on {date} at {time}. Thank you, and have a great day!"
            
            context.add_turn(Turn(role="agent", text=response_text))
            return StateResponse(
                next_state="terminal",
                response_text=response_text,
                should_continue=False,
                extracted_slots={"appointment_booked": appointment_booked, "event_details": event_details}
            )
        else:
            response_text = "No problem. Let's start over. What date would you like to schedule your appointment?"
            context.add_turn(Turn(role="agent", text=response_text))
            context.slots.pop("date", None)
            context.slots.pop("time", None)
            context.reset_retry_count()
            return StateResponse(
                next_state="collect_date",
                response_text=response_text
            )
    
    async def _extract_confirmation(self, user_text: str, context: ConversationContext, llm_service) -> bool:
        prompt = f"""Determine if this text is a confirmation (yes/affirmative) or rejection (no/negative).
Text: "{user_text}"
Return only "yes" or "no"."""
        
        try:
            response = await llm_service.generate_response(prompt)
            if response:
                response_lower = response.strip().lower()
                return response_lower.startswith("yes") or response_lower.startswith("y") or "correct" in response_lower or "right" in response_lower
        except Exception as e:
            logger.error("Confirmation extraction failed", error=str(e))
        
        return False


class FallbackState(ConversationState):
    def __init__(self):
        super().__init__("fallback", "Handle unclear input or errors")
        self.max_retries = 3
    
    def get_prompt(self, context: ConversationContext) -> str:
        retry_count = context.retry_count
        if retry_count >= self.max_retries:
            return "I'm having trouble understanding. Let me connect you with a human agent who can better assist you."
        return f"I'm having trouble understanding. Could you please repeat that? (Attempt {retry_count + 1} of {self.max_retries})"
    
    async def handle_input(
        self, 
        user_text: str, 
        context: ConversationContext,
        llm_service
    ) -> StateResponse:
        context.add_turn(Turn(role="user", text=user_text))
        context.increment_retry_count()
        
        # If max retries reached, go to terminal
        if context.retry_count >= self.max_retries:
            response_text = "I'm having trouble understanding. Let me connect you with a human agent who can better assist you. Thank you for your patience."
            context.add_turn(Turn(role="agent", text=response_text))
            return StateResponse(
                next_state="terminal",
                response_text=response_text,
                should_continue=False
            )
        
        # Try to return to previous state
        previous_state = context.current_state or "greeting"
        if previous_state == "fallback":
            previous_state = "greeting"  # Default fallback
        
        response_text = self.get_prompt(context)
        context.add_turn(Turn(role="agent", text=response_text))
        
        return StateResponse(
            next_state=previous_state,
            response_text=response_text,
            should_continue=True
        )


class TerminalState(ConversationState):
    def __init__(self):
        super().__init__("terminal", "End conversation")
    
    def get_prompt(self, context: ConversationContext) -> str:
        # Check if appointment was successfully booked
        appointment_booked = context.get_slot("appointment_booked")
        if appointment_booked:
            return "Thank you for using our service. Your appointment has been confirmed. Goodbye!"
        return "Thank you for using our service. Goodbye!"
    
    async def handle_input(
        self, 
        user_text: str, 
        context: ConversationContext,
        llm_service
    ) -> StateResponse:
        # Terminal state - conversation has ended
        # Check if user is trying to restart
        user_lower = user_text.lower().strip()
        restart_keywords = ["restart", "start over", "new appointment", "again", "reset"]
        
        if any(keyword in user_lower for keyword in restart_keywords):
            # Reset conversation and go back to greeting
            context.slots.clear()
            context.reset_retry_count()
            response_text = "Sure! Let's start over. How can I help you schedule an appointment today?"
            return StateResponse(
                next_state="greeting",
                response_text=response_text,
                should_continue=True
            )
        
        # Otherwise, confirm conversation has ended
        response_text = "The conversation has ended. Thank you! If you need to schedule another appointment, please start a new conversation."
        return StateResponse(
            next_state=None,
            response_text=response_text,
            should_continue=False
        )

