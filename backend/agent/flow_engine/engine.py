"""
Flow Engine - Main orchestrator for conversation flows

This is the central engine that:
1. Loads and validates flow definitions from JSON
2. Manages conversation state and transitions
3. Coordinates with VAD for speech detection
4. Executes nodes and handles transitions
"""

import asyncio
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .schema import (
    FlowDefinition, NodeBase, NodeType,
    load_flow_from_json, load_flow_from_dict
)
from .nodes import NodeExecutor, NodeResult, NodeResultType
from .dynamic_variables import DynamicVariableStore
from .vad_processor import VADProcessor, VADConfig, VADResult
from utils.logger import logger


@dataclass
class ConversationTurn:
    """A single turn in the conversation"""
    role: str  # "user" or "agent"
    text: str
    timestamp: datetime = field(default_factory=datetime.now)
    node_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowState:
    """Current state of a conversation flow"""
    flow_id: str
    session_id: str
    current_node_id: str
    variables: DynamicVariableStore
    history: List[ConversationTurn] = field(default_factory=list)
    retry_count: int = 0
    is_complete: bool = False
    end_reason: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_turn(self, role: str, text: str, node_id: Optional[str] = None, metadata: Dict[str, Any] = None):
        """Add a conversation turn"""
        self.history.append(ConversationTurn(
            role=role,
            text=text,
            node_id=node_id or self.current_node_id,
            metadata=metadata or {}
        ))
        self.updated_at = datetime.now()
    
    def get_history_for_llm(self, max_turns: int = 10) -> List[Dict[str, str]]:
        """Get conversation history formatted for LLM context"""
        recent = self.history[-max_turns:] if len(self.history) > max_turns else self.history
        return [
            {"role": turn.role, "content": turn.text}
            for turn in recent
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Export state as dictionary"""
        return {
            "flow_id": self.flow_id,
            "session_id": self.session_id,
            "current_node_id": self.current_node_id,
            "variables": self.variables.get_all(),
            "turn_count": len(self.history),
            "retry_count": self.retry_count,
            "is_complete": self.is_complete,
            "end_reason": self.end_reason,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class FlowEngine:
    """
    Main conversation flow engine.
    
    Usage:
        # Load flow
        engine = FlowEngine(llm_service)
        await engine.load_flow_from_file("flows/appointment.json")
        
        # Start conversation
        state = engine.create_session("session_123")
        response = await engine.start(state)
        
        # Process user input
        result = await engine.process_input(state, "My name is John")
        
        # With VAD
        engine.enable_vad(vad_config)
        result = await engine.process_audio_frame(state, audio_frame)
    """
    
    def __init__(
        self,
        llm_service,
        function_registry: Optional[Dict[str, Callable]] = None
    ):
        self.llm_service = llm_service
        self.flow: Optional[FlowDefinition] = None
        self.node_executor: Optional[NodeExecutor] = None
        self.function_registry = function_registry or {}
        
        # VAD processor (optional, for audio processing)
        self.vad_processor: Optional[VADProcessor] = None
        self.vad_enabled = False
        
        # Session management
        self._sessions: Dict[str, FlowState] = {}
        
        # Callbacks
        self._on_state_change: Optional[Callable] = None
        self._on_response: Optional[Callable] = None
        
        logger.info("FlowEngine initialized")
    
    def register_function(self, name: str, func: Callable):
        """Register a function for use in FunctionNodes"""
        self.function_registry[name] = func
        if self.node_executor:
            self.node_executor.register_function(name, func)
        logger.info("Function registered in engine", name=name)
    
    def set_callbacks(
        self,
        on_state_change: Optional[Callable] = None,
        on_response: Optional[Callable] = None
    ):
        """Set callbacks for flow events"""
        self._on_state_change = on_state_change
        self._on_response = on_response
    
    async def load_flow_from_file(self, path: str) -> FlowDefinition:
        """Load a flow definition from a JSON file"""
        self.flow = load_flow_from_json(path)
        
        # Validate flow
        errors = self.flow.validate()
        if errors:
            error_msg = "; ".join(errors)
            logger.error("Flow validation failed", errors=errors)
            raise ValueError(f"Invalid flow definition: {error_msg}")
        
        # Initialize node executor
        self.node_executor = NodeExecutor(
            self.llm_service,
            self.function_registry,
            self.flow.global_settings.system_prompt
        )
        
        # Register any pre-registered functions
        for name, func in self.function_registry.items():
            self.node_executor.register_function(name, func)
        
        logger.info("Flow loaded", 
                   flow_id=self.flow.id,
                   flow_name=self.flow.name,
                   node_count=len(self.flow.nodes))
        
        return self.flow
    
    async def load_flow_from_dict(self, data: Dict[str, Any]) -> FlowDefinition:
        """Load a flow definition from a dictionary"""
        self.flow = load_flow_from_dict(data)
        
        # Validate flow
        errors = self.flow.validate()
        if errors:
            error_msg = "; ".join(errors)
            logger.error("Flow validation failed", errors=errors)
            raise ValueError(f"Invalid flow definition: {error_msg}")
        
        # Initialize node executor
        self.node_executor = NodeExecutor(
            self.llm_service,
            self.function_registry,
            self.flow.global_settings.system_prompt
        )
        
        logger.info("Flow loaded from dict",
                   flow_id=self.flow.id,
                   node_count=len(self.flow.nodes))
        
        return self.flow
    
    def enable_vad(self, config: Optional[VADConfig] = None):
        """Enable Voice Activity Detection for audio processing"""
        if config is None and self.flow:
            # Use flow's VAD settings
            config = VADConfig(
                silence_threshold_ms=self.flow.global_settings.silence_threshold_ms,
                min_speech_duration_ms=self.flow.global_settings.min_speech_duration_ms
            )
        
        self.vad_processor = VADProcessor(config or VADConfig())
        self.vad_enabled = True
        logger.info("VAD enabled", config=config)
    
    async def initialize_vad(self):
        """Initialize VAD model (call this before processing audio)"""
        if self.vad_processor:
            await self.vad_processor.initialize()
    
    def create_session(
        self,
        session_id: str,
        initial_variables: Optional[Dict[str, Any]] = None
    ) -> FlowState:
        """Create a new conversation session"""
        if not self.flow:
            raise RuntimeError("No flow loaded. Call load_flow_from_file first.")
        
        # Merge initial variables with flow defaults
        variables = DynamicVariableStore(
            self.flow.global_settings.initial_variables.copy()
        )
        if initial_variables:
            for key, value in initial_variables.items():
                variables.set(key, value, source="initial")
        
        state = FlowState(
            flow_id=self.flow.id,
            session_id=session_id,
            current_node_id=self.flow.start_node_id,
            variables=variables
        )
        
        self._sessions[session_id] = state
        
        logger.info("Session created",
                   session_id=session_id,
                   flow_id=self.flow.id,
                   start_node=self.flow.start_node_id)
        
        return state
    
    def get_session(self, session_id: str) -> Optional[FlowState]:
        """Get an existing session"""
        return self._sessions.get(session_id)
    
    async def start(self, state: FlowState) -> NodeResult:
        """
        Start a conversation flow (enter the start node).
        Returns the initial response from the start node.
        """
        if not self.flow or not self.node_executor:
            raise RuntimeError("No flow loaded.")
        
        node = self.flow.get_node(state.current_node_id)
        if not node:
            raise ValueError(f"Start node not found: {state.current_node_id}")
        
        # Execute start node without user input
        result = await self.node_executor.execute(
            node,
            user_input=None,
            variables=state.variables,
            conversation_history=state.get_history_for_llm()
        )
        
        # Record agent response
        if result.response_text:
            state.add_turn("agent", result.response_text, node.id)
            
            if self._on_response:
                try:
                    await self._on_response(state, result.response_text)
                except Exception as e:
                    logger.warning("Response callback failed", error=str(e))
        
        # Notify state change
        if self._on_state_change:
            try:
                await self._on_state_change(state, node.id)
            except Exception as e:
                logger.warning("State change callback failed", error=str(e))
        
        return result
    
    async def process_input(
        self,
        state: FlowState,
        user_input: str
    ) -> NodeResult:
        """
        Process user text input through the flow.
        
        Args:
            state: Current conversation state
            user_input: User's text input
        
        Returns:
            NodeResult with response and state updates
        """
        if not self.flow or not self.node_executor:
            raise RuntimeError("No flow loaded.")
        
        if state.is_complete:
            logger.warning("Attempt to process input on completed flow",
                         session_id=state.session_id)
            return NodeResult(
                result_type=NodeResultType.END,
                response_text="The conversation has ended."
            )
        
        # Record user input
        state.add_turn("user", user_input)
        
        # Get current node
        node = self.flow.get_node(state.current_node_id)
        if not node:
            logger.error("Current node not found", node_id=state.current_node_id)
            return NodeResult(
                result_type=NodeResultType.ERROR,
                error_message=f"Node not found: {state.current_node_id}"
            )
        
        # Execute current node with user input
        result = await self.node_executor.execute(
            node,
            user_input=user_input,
            variables=state.variables,
            conversation_history=state.get_history_for_llm()
        )
        
        # Handle node result
        return await self._handle_node_result(state, result)
    
    async def process_audio_frame(
        self,
        state: FlowState,
        audio_frame: Any
    ) -> Optional[NodeResult]:
        """
        Process an audio frame through VAD.
        
        Returns NodeResult only when speech is complete and processed.
        Returns None while waiting for more audio.
        """
        if not self.vad_enabled or not self.vad_processor:
            raise RuntimeError("VAD not enabled. Call enable_vad() first.")
        
        # Process frame through VAD
        vad_result = await self.vad_processor.process_frame(audio_frame)
        
        if not vad_result.is_speech_complete:
            return None  # Still collecting audio
        
        if not vad_result.audio_data:
            return None  # No valid speech detected
        
        # Transcribe audio
        # This would typically call your STT service
        # For now, we return a placeholder result
        # The actual implementation should call:
        # user_text = await stt_service.transcribe(vad_result.audio_data)
        
        logger.info("Speech complete, ready for STT",
                   audio_size=len(vad_result.audio_data),
                   duration_ms=vad_result.speech_duration_ms)
        
        # Return a result indicating we need STT processing
        return NodeResult(
            result_type=NodeResultType.WAIT_INPUT,
            metadata={
                "audio_data": vad_result.audio_data,
                "speech_duration_ms": vad_result.speech_duration_ms
            }
        )
    
    async def process_transcribed_audio(
        self,
        state: FlowState,
        user_text: str,
        audio_metadata: Optional[Dict[str, Any]] = None
    ) -> NodeResult:
        """
        Process transcribed audio text.
        
        This is called after STT converts audio to text.
        """
        # Reset VAD for next utterance
        if self.vad_processor:
            self.vad_processor.reset()
        
        # Process as regular text input
        return await self.process_input(state, user_text)
    
    async def _handle_node_result(
        self,
        state: FlowState,
        result: NodeResult
    ) -> NodeResult:
        """Handle the result of node execution"""
        
        # Record agent response
        if result.response_text:
            state.add_turn("agent", result.response_text, state.current_node_id)
            
            if self._on_response:
                try:
                    await self._on_response(state, result.response_text)
                except Exception as e:
                    logger.warning("Response callback failed", error=str(e))
        
        # Handle different result types
        if result.result_type == NodeResultType.END:
            state.is_complete = True
            state.end_reason = result.metadata.get("end_reason", "completed")
            logger.info("Flow completed",
                       session_id=state.session_id,
                       reason=state.end_reason)
        
        elif result.result_type == NodeResultType.TRANSFER:
            state.is_complete = True
            state.end_reason = "transfer"
            logger.info("Flow transferred",
                       session_id=state.session_id,
                       destination=result.metadata.get("destination"))
        
        elif result.result_type == NodeResultType.ERROR:
            # Try fallback node if configured
            if self.flow.global_settings.fallback_node_id:
                state.retry_count += 1
                if state.retry_count <= self.flow.global_settings.max_retries:
                    state.current_node_id = self.flow.global_settings.fallback_node_id
                    logger.warning("Transitioning to fallback node",
                                 retry_count=state.retry_count)
                else:
                    state.is_complete = True
                    state.end_reason = "max_retries"
                    logger.error("Max retries reached",
                               session_id=state.session_id)
        
        # Handle transition to next node
        if result.next_node_id and not state.is_complete:
            old_node = state.current_node_id
            state.current_node_id = result.next_node_id
            state.retry_count = 0  # Reset retry count on successful transition
            
            logger.info("Node transition",
                       from_node=old_node,
                       to_node=result.next_node_id)
            
            if self._on_state_change:
                try:
                    await self._on_state_change(state, result.next_node_id)
                except Exception as e:
                    logger.warning("State change callback failed", error=str(e))
            
            # If the next node doesn't need user input, execute it immediately
            if not result.should_wait_for_input:
                next_node = self.flow.get_node(result.next_node_id)
                if next_node:
                    next_result = await self.node_executor.execute(
                        next_node,
                        user_input=None,
                        variables=state.variables,
                        conversation_history=state.get_history_for_llm()
                    )
                    # Recursively handle the next result
                    return await self._handle_node_result(state, next_result)
        
        return result
    
    def get_current_node(self, state: FlowState) -> Optional[NodeBase]:
        """Get the current node for a session"""
        if not self.flow:
            return None
        return self.flow.get_node(state.current_node_id)
    
    def get_flow_summary(self) -> Dict[str, Any]:
        """Get summary of loaded flow"""
        if not self.flow:
            return {"loaded": False}
        
        return {
            "loaded": True,
            "id": self.flow.id,
            "name": self.flow.name,
            "version": self.flow.version,
            "node_count": len(self.flow.nodes),
            "start_node": self.flow.start_node_id,
            "vad_enabled": self.vad_enabled
        }


# Convenience function to create a flow engine with common setup
async def create_flow_engine(
    llm_service,
    flow_path: str,
    functions: Optional[Dict[str, Callable]] = None,
    enable_vad: bool = True,
    vad_config: Optional[VADConfig] = None
) -> FlowEngine:
    """
    Create and initialize a flow engine.
    
    Args:
        llm_service: LLM service for generating responses
        flow_path: Path to flow JSON file
        functions: Dictionary of functions for FunctionNodes
        enable_vad: Whether to enable VAD
        vad_config: VAD configuration (uses flow settings if None)
    
    Returns:
        Initialized FlowEngine
    """
    engine = FlowEngine(llm_service, functions)
    await engine.load_flow_from_file(flow_path)
    
    if enable_vad:
        engine.enable_vad(vad_config)
        await engine.initialize_vad()
    
    return engine
