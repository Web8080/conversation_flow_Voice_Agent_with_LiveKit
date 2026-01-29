"""
JSON Schema Definitions for Conversational Flows

Defines the structure for:
- Flow definitions (nodes, edges, global settings)
- Node types (conversation, function, logic_split, end, transfer)
- Edge transitions (prompt-based and equation-based conditions)
- Dynamic variables
"""

from typing import Dict, List, Optional, Any, Union, Literal
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path


class NodeType(str, Enum):
    """Types of nodes in the conversation flow"""
    CONVERSATION = "conversation"      # Dialogue with user, can extract variables
    FUNCTION = "function"              # Execute a function (API call, calendar, etc.)
    LOGIC_SPLIT = "logic_split"        # Conditional branching based on variables
    END = "end"                        # Terminal node, ends conversation
    TRANSFER = "transfer"              # Transfer to human agent
    EXTRACT_VARIABLE = "extract_variable"  # Extract dynamic variable from conversation


class TransitionConditionType(str, Enum):
    """Types of transition conditions"""
    PROMPT = "prompt"      # LLM evaluates if condition is met
    EQUATION = "equation"  # Mathematical/logical equation on variables


@dataclass
class TransitionCondition:
    """A condition for transitioning between nodes"""
    type: TransitionConditionType
    condition: str  # The prompt or equation
    description: Optional[str] = None  # Human-readable description


@dataclass
class Edge:
    """Connection between nodes with transition conditions"""
    id: str
    target_node_id: str
    conditions: List[TransitionCondition] = field(default_factory=list)
    is_default: bool = False  # If true, this edge is taken when no other conditions match
    priority: int = 0  # Lower number = higher priority (evaluated first)


@dataclass
class NodeBase:
    """Base class for all node types"""
    id: str
    type: NodeType
    name: str
    description: Optional[str] = None
    edges: List[Edge] = field(default_factory=list)
    
    # Global node settings (can override flow-level settings)
    llm_model: Optional[str] = None
    temperature: Optional[float] = None


@dataclass
class ConversationNode(NodeBase):
    """Node for handling dialogue with user"""
    type: NodeType = field(default=NodeType.CONVERSATION)
    
    # The instruction/prompt for this conversation turn
    instruction: str = ""
    
    # Variables to extract from user response
    extract_variables: List[str] = field(default_factory=list)
    
    # Response template (supports variable interpolation with {{var_name}})
    response_template: Optional[str] = None
    
    # Whether agent should speak immediately on entering this node
    auto_respond: bool = True
    
    # Fine-tune examples for this node
    examples: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class FunctionNode(NodeBase):
    """Node for executing functions/API calls"""
    type: NodeType = field(default=NodeType.FUNCTION)
    
    # Function to call (registered function name)
    function_name: str = ""
    
    # Parameters to pass (supports variable interpolation)
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Variable to store result in
    result_variable: Optional[str] = None
    
    # Message to say while function executes (optional)
    pending_message: Optional[str] = None
    
    # Message on success (supports {{result}} interpolation)
    success_message: Optional[str] = None
    
    # Message on failure
    failure_message: Optional[str] = None


@dataclass
class LogicSplitNode(NodeBase):
    """Node for conditional branching"""
    type: NodeType = field(default=NodeType.LOGIC_SPLIT)
    
    # Note: Logic split uses edges with equation conditions
    # The node itself just evaluates which edge to take


@dataclass
class EndNode(NodeBase):
    """Terminal node that ends the conversation"""
    type: NodeType = field(default=NodeType.END)
    
    # Final message to user
    message: str = "Thank you for using our service. Goodbye!"
    
    # Reason for ending (for analytics)
    end_reason: str = "completed"


@dataclass
class TransferNode(NodeBase):
    """Node for transferring to human agent"""
    type: NodeType = field(default=NodeType.TRANSFER)
    
    # Message before transfer
    message: str = "Let me connect you with a human agent."
    
    # Transfer destination (phone number, queue name, etc.)
    destination: Optional[str] = None
    
    # Reason for transfer
    transfer_reason: str = "user_request"


@dataclass
class ExtractVariableNode(NodeBase):
    """Node for extracting variables from conversation"""
    type: NodeType = field(default=NodeType.EXTRACT_VARIABLE)
    
    # Variables to extract
    variables: List[Dict[str, str]] = field(default_factory=list)
    # Each dict has: name, description, type (string, number, date, time, boolean)
    
    # Extraction prompt (optional, uses default if not provided)
    extraction_prompt: Optional[str] = None


@dataclass
class GlobalSettings:
    """Global settings for the entire flow"""
    # Agent personality/instructions
    system_prompt: str = "You are a helpful voice assistant."
    
    # Default LLM settings
    llm_model: str = "gemini-1.5-flash"
    temperature: float = 0.7
    max_tokens: int = 500
    
    # Voice settings
    voice: str = "default"
    language: str = "en"
    
    # Conversation settings
    max_retries: int = 3
    fallback_node_id: Optional[str] = None
    
    # VAD settings
    vad_enabled: bool = True
    silence_threshold_ms: int = 500  # Silence duration to detect end of speech
    min_speech_duration_ms: int = 250  # Minimum speech duration to process
    
    # Interruption handling
    allow_interruptions: bool = True
    
    # Variables available at flow start (can be passed in)
    initial_variables: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FlowDefinition:
    """Complete definition of a conversation flow"""
    id: str
    name: str
    version: str = "1.0.0"
    description: Optional[str] = None
    
    # Global settings
    global_settings: GlobalSettings = field(default_factory=GlobalSettings)
    
    # Starting node
    start_node_id: str = ""
    
    # All nodes in the flow
    nodes: Dict[str, NodeBase] = field(default_factory=dict)
    
    # Metadata
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def get_node(self, node_id: str) -> Optional[NodeBase]:
        """Get a node by ID"""
        return self.nodes.get(node_id)
    
    def get_start_node(self) -> Optional[NodeBase]:
        """Get the starting node"""
        return self.nodes.get(self.start_node_id)
    
    def validate(self) -> List[str]:
        """Validate the flow definition, return list of errors"""
        errors = []
        
        # Check start node exists
        if not self.start_node_id:
            errors.append("start_node_id is required")
        elif self.start_node_id not in self.nodes:
            errors.append(f"start_node_id '{self.start_node_id}' does not exist in nodes")
        
        # Check all edge targets exist
        for node_id, node in self.nodes.items():
            for edge in node.edges:
                if edge.target_node_id not in self.nodes:
                    errors.append(f"Node '{node_id}' has edge to non-existent node '{edge.target_node_id}'")
        
        # Check fallback node exists
        if self.global_settings.fallback_node_id:
            if self.global_settings.fallback_node_id not in self.nodes:
                errors.append(f"fallback_node_id '{self.global_settings.fallback_node_id}' does not exist")
        
        return errors


# Type alias for any node type
AnyNode = Union[ConversationNode, FunctionNode, LogicSplitNode, EndNode, TransferNode, ExtractVariableNode]


def parse_node_from_dict(data: Dict[str, Any]) -> AnyNode:
    """Parse a node from a dictionary (from JSON)"""
    node_type = NodeType(data.get("type", "conversation"))
    
    # Parse edges
    edges = []
    for edge_data in data.get("edges", []):
        conditions = []
        for cond_data in edge_data.get("conditions", []):
            conditions.append(TransitionCondition(
                type=TransitionConditionType(cond_data.get("type", "prompt")),
                condition=cond_data.get("condition", ""),
                description=cond_data.get("description")
            ))
        edges.append(Edge(
            id=edge_data.get("id", ""),
            target_node_id=edge_data.get("target_node_id", ""),
            conditions=conditions,
            is_default=edge_data.get("is_default", False),
            priority=edge_data.get("priority", 0)
        ))
    
    # Common fields
    base_fields = {
        "id": data.get("id", ""),
        "name": data.get("name", ""),
        "description": data.get("description"),
        "edges": edges,
        "llm_model": data.get("llm_model"),
        "temperature": data.get("temperature"),
    }
    
    if node_type == NodeType.CONVERSATION:
        return ConversationNode(
            **base_fields,
            instruction=data.get("instruction", ""),
            extract_variables=data.get("extract_variables", []),
            response_template=data.get("response_template"),
            auto_respond=data.get("auto_respond", True),
            examples=data.get("examples", [])
        )
    elif node_type == NodeType.FUNCTION:
        return FunctionNode(
            **base_fields,
            function_name=data.get("function_name", ""),
            parameters=data.get("parameters", {}),
            result_variable=data.get("result_variable"),
            pending_message=data.get("pending_message"),
            success_message=data.get("success_message"),
            failure_message=data.get("failure_message")
        )
    elif node_type == NodeType.LOGIC_SPLIT:
        return LogicSplitNode(**base_fields)
    elif node_type == NodeType.END:
        return EndNode(
            **base_fields,
            message=data.get("message", "Thank you for using our service. Goodbye!"),
            end_reason=data.get("end_reason", "completed")
        )
    elif node_type == NodeType.TRANSFER:
        return TransferNode(
            **base_fields,
            message=data.get("message", "Let me connect you with a human agent."),
            destination=data.get("destination"),
            transfer_reason=data.get("transfer_reason", "user_request")
        )
    elif node_type == NodeType.EXTRACT_VARIABLE:
        return ExtractVariableNode(
            **base_fields,
            variables=data.get("variables", []),
            extraction_prompt=data.get("extraction_prompt")
        )
    else:
        # Default to conversation node
        return ConversationNode(**base_fields)


def load_flow_from_json(json_path: Union[str, Path]) -> FlowDefinition:
    """Load a flow definition from a JSON file"""
    path = Path(json_path)
    with open(path, 'r') as f:
        data = json.load(f)
    
    return load_flow_from_dict(data)


def load_flow_from_dict(data: Dict[str, Any]) -> FlowDefinition:
    """Load a flow definition from a dictionary"""
    # Parse global settings
    global_data = data.get("global_settings", {})
    global_settings = GlobalSettings(
        system_prompt=global_data.get("system_prompt", "You are a helpful voice assistant."),
        llm_model=global_data.get("llm_model", "gemini-1.5-flash"),
        temperature=global_data.get("temperature", 0.7),
        max_tokens=global_data.get("max_tokens", 500),
        voice=global_data.get("voice", "default"),
        language=global_data.get("language", "en"),
        max_retries=global_data.get("max_retries", 3),
        fallback_node_id=global_data.get("fallback_node_id"),
        vad_enabled=global_data.get("vad_enabled", True),
        silence_threshold_ms=global_data.get("silence_threshold_ms", 500),
        min_speech_duration_ms=global_data.get("min_speech_duration_ms", 250),
        allow_interruptions=global_data.get("allow_interruptions", True),
        initial_variables=global_data.get("initial_variables", {})
    )
    
    # Parse nodes
    nodes = {}
    for node_data in data.get("nodes", []):
        node = parse_node_from_dict(node_data)
        nodes[node.id] = node
    
    return FlowDefinition(
        id=data.get("id", ""),
        name=data.get("name", ""),
        version=data.get("version", "1.0.0"),
        description=data.get("description"),
        global_settings=global_settings,
        start_node_id=data.get("start_node_id", ""),
        nodes=nodes,
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at")
    )


def flow_to_dict(flow: FlowDefinition) -> Dict[str, Any]:
    """Convert a flow definition to a dictionary (for JSON serialization)"""
    # Convert global settings
    global_settings = {
        "system_prompt": flow.global_settings.system_prompt,
        "llm_model": flow.global_settings.llm_model,
        "temperature": flow.global_settings.temperature,
        "max_tokens": flow.global_settings.max_tokens,
        "voice": flow.global_settings.voice,
        "language": flow.global_settings.language,
        "max_retries": flow.global_settings.max_retries,
        "fallback_node_id": flow.global_settings.fallback_node_id,
        "vad_enabled": flow.global_settings.vad_enabled,
        "silence_threshold_ms": flow.global_settings.silence_threshold_ms,
        "min_speech_duration_ms": flow.global_settings.min_speech_duration_ms,
        "allow_interruptions": flow.global_settings.allow_interruptions,
        "initial_variables": flow.global_settings.initial_variables
    }
    
    # Convert nodes
    nodes = []
    for node in flow.nodes.values():
        node_dict = {
            "id": node.id,
            "type": node.type.value,
            "name": node.name,
            "description": node.description,
            "edges": [
                {
                    "id": edge.id,
                    "target_node_id": edge.target_node_id,
                    "conditions": [
                        {
                            "type": cond.type.value,
                            "condition": cond.condition,
                            "description": cond.description
                        }
                        for cond in edge.conditions
                    ],
                    "is_default": edge.is_default,
                    "priority": edge.priority
                }
                for edge in node.edges
            ],
            "llm_model": node.llm_model,
            "temperature": node.temperature
        }
        
        # Add type-specific fields
        if isinstance(node, ConversationNode):
            node_dict.update({
                "instruction": node.instruction,
                "extract_variables": node.extract_variables,
                "response_template": node.response_template,
                "auto_respond": node.auto_respond,
                "examples": node.examples
            })
        elif isinstance(node, FunctionNode):
            node_dict.update({
                "function_name": node.function_name,
                "parameters": node.parameters,
                "result_variable": node.result_variable,
                "pending_message": node.pending_message,
                "success_message": node.success_message,
                "failure_message": node.failure_message
            })
        elif isinstance(node, EndNode):
            node_dict.update({
                "message": node.message,
                "end_reason": node.end_reason
            })
        elif isinstance(node, TransferNode):
            node_dict.update({
                "message": node.message,
                "destination": node.destination,
                "transfer_reason": node.transfer_reason
            })
        elif isinstance(node, ExtractVariableNode):
            node_dict.update({
                "variables": node.variables,
                "extraction_prompt": node.extraction_prompt
            })
        
        nodes.append(node_dict)
    
    return {
        "id": flow.id,
        "name": flow.name,
        "version": flow.version,
        "description": flow.description,
        "global_settings": global_settings,
        "start_node_id": flow.start_node_id,
        "nodes": nodes,
        "created_at": flow.created_at,
        "updated_at": flow.updated_at
    }
