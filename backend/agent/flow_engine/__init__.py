"""
Flow Engine - Retell-style Conversational Flow System

This module provides a JSON-driven conversational flow engine with:
- Node-based conversation flow (conversation, function, logic_split, end, transfer)
- Edge transitions with prompt-based and equation-based conditions
- Dynamic variable extraction and interpolation
- Voice Activity Detection (VAD) for proper end-of-speech detection
"""

from .schema import (
    FlowDefinition,
    NodeType,
    NodeBase,
    ConversationNode,
    FunctionNode,
    LogicSplitNode,
    EndNode,
    TransferNode,
    Edge,
    TransitionCondition,
    TransitionConditionType,
    GlobalSettings,
    load_flow_from_json,
    load_flow_from_dict,
    flow_to_dict,
)
from .engine import FlowEngine, FlowState, ConversationTurn, create_flow_engine
from .nodes import NodeExecutor, NodeResult, NodeResultType
from .dynamic_variables import DynamicVariableStore, interpolate_template
from .vad_processor import VADProcessor, VADConfig, VADResult, SpeechState

__all__ = [
    # Schema
    "FlowDefinition",
    "NodeType",
    "NodeBase",
    "ConversationNode",
    "FunctionNode",
    "LogicSplitNode",
    "EndNode",
    "TransferNode",
    "Edge",
    "TransitionCondition",
    "TransitionConditionType",
    "GlobalSettings",
    "load_flow_from_json",
    "load_flow_from_dict",
    "flow_to_dict",
    
    # Engine
    "FlowEngine",
    "FlowState",
    "ConversationTurn",
    "create_flow_engine",
    
    # Nodes
    "NodeExecutor",
    "NodeResult",
    "NodeResultType",
    
    # Dynamic Variables
    "DynamicVariableStore",
    "interpolate_template",
    
    # VAD
    "VADProcessor",
    "VADConfig",
    "VADResult",
    "SpeechState",
]
