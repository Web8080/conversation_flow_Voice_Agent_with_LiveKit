"""
Node Execution Module

Handles execution of different node types in the conversation flow.
Each node type has specific execution logic.
"""

from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum

from .schema import (
    NodeType, NodeBase, ConversationNode, FunctionNode,
    LogicSplitNode, EndNode, TransferNode, ExtractVariableNode,
    Edge, TransitionConditionType
)
from .dynamic_variables import DynamicVariableStore
from utils.logger import logger


class NodeResultType(str, Enum):
    """Type of node execution result"""
    RESPONSE = "response"          # Node produced a response to speak
    CONTINUE = "continue"          # Continue to next node immediately (no response)
    END = "end"                    # Conversation ended
    TRANSFER = "transfer"          # Transfer to human agent
    ERROR = "error"                # Error occurred
    WAIT_INPUT = "wait_input"      # Wait for user input


@dataclass
class NodeResult:
    """Result from executing a node"""
    result_type: NodeResultType
    response_text: Optional[str] = None
    next_node_id: Optional[str] = None
    extracted_variables: Dict[str, Any] = field(default_factory=dict)
    should_wait_for_input: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class NodeExecutor:
    """
    Executes nodes in the conversation flow.
    
    Usage:
        executor = NodeExecutor(llm_service, function_registry)
        result = await executor.execute(node, user_input, variables)
    """
    
    def __init__(
        self, 
        llm_service,
        function_registry: Optional[Dict[str, callable]] = None,
        system_prompt: str = ""
    ):
        self.llm_service = llm_service
        self.function_registry = function_registry or {}
        self.system_prompt = system_prompt
    
    def register_function(self, name: str, func: callable):
        """Register a function for FunctionNode execution"""
        self.function_registry[name] = func
        logger.info("Function registered", name=name)
    
    async def execute(
        self,
        node: NodeBase,
        user_input: Optional[str],
        variables: DynamicVariableStore,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> NodeResult:
        """Execute a node and return the result"""
        
        logger.info("Executing node", 
                   node_id=node.id, 
                   node_type=node.type.value,
                   has_user_input=user_input is not None)
        
        try:
            if node.type == NodeType.CONVERSATION:
                return await self._execute_conversation(
                    node, user_input, variables, conversation_history
                )
            elif node.type == NodeType.FUNCTION:
                return await self._execute_function(node, variables)
            elif node.type == NodeType.LOGIC_SPLIT:
                return await self._execute_logic_split(node, variables)
            elif node.type == NodeType.END:
                return self._execute_end(node, variables)
            elif node.type == NodeType.TRANSFER:
                return self._execute_transfer(node, variables)
            elif node.type == NodeType.EXTRACT_VARIABLE:
                return await self._execute_extract_variable(
                    node, user_input, variables, conversation_history
                )
            else:
                logger.error("Unknown node type", node_type=node.type)
                return NodeResult(
                    result_type=NodeResultType.ERROR,
                    error_message=f"Unknown node type: {node.type}"
                )
        except Exception as e:
            logger.error("Node execution failed", 
                        node_id=node.id, 
                        error=str(e))
            return NodeResult(
                result_type=NodeResultType.ERROR,
                error_message=str(e)
            )
    
    async def _execute_conversation(
        self,
        node: ConversationNode,
        user_input: Optional[str],
        variables: DynamicVariableStore,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> NodeResult:
        """Execute a conversation node"""
        
        # If this is the first visit (no user input), generate initial response
        if user_input is None and node.auto_respond:
            response_text = variables.interpolate(
                node.response_template or node.instruction
            )
            return NodeResult(
                result_type=NodeResultType.RESPONSE,
                response_text=response_text,
                should_wait_for_input=True
            )
        
        # Extract variables from user input if configured
        extracted = {}
        if user_input and node.extract_variables:
            extracted = await self._extract_variables_from_input(
                user_input, 
                node.extract_variables,
                variables,
                conversation_history
            )
            for var_name, value in extracted.items():
                variables.set(var_name, value, source=node.id)
        
        # Generate response using LLM
        prompt = self._build_conversation_prompt(
            node, user_input, variables, conversation_history
        )
        
        response = await self.llm_service.generate_response(
            prompt,
            context={
                "system_prompt": self.system_prompt,
                "history": conversation_history or []
            }
        )
        
        # Evaluate transitions
        next_node_id = await self._evaluate_transitions(
            node.edges, user_input, variables
        )
        
        return NodeResult(
            result_type=NodeResultType.RESPONSE,
            response_text=response,
            next_node_id=next_node_id,
            extracted_variables=extracted,
            should_wait_for_input=next_node_id is None  # Wait if no transition
        )
    
    async def _execute_function(
        self,
        node: FunctionNode,
        variables: DynamicVariableStore
    ) -> NodeResult:
        """Execute a function node"""
        
        func = self.function_registry.get(node.function_name)
        if func is None:
            logger.error("Function not found", function_name=node.function_name)
            return NodeResult(
                result_type=NodeResultType.ERROR,
                error_message=f"Function not found: {node.function_name}",
                response_text=variables.interpolate(node.failure_message) if node.failure_message else None
            )
        
        # Interpolate parameters
        params = {}
        for key, value in node.parameters.items():
            if isinstance(value, str):
                params[key] = variables.interpolate(value)
            else:
                params[key] = value
        
        # Say pending message if configured
        response_text = None
        if node.pending_message:
            response_text = variables.interpolate(node.pending_message)
        
        # Execute function
        try:
            import asyncio
            if asyncio.iscoroutinefunction(func):
                result = await func(**params)
            else:
                result = func(**params)
            
            # Store result in variable
            if node.result_variable:
                variables.set(node.result_variable, result, source=node.id)
            
            # Generate success response
            if node.success_message:
                variables.set("result", result, source=node.id)
                response_text = variables.interpolate(node.success_message)
            
            # Evaluate transitions
            next_node_id = await self._evaluate_transitions(
                node.edges, None, variables
            )
            
            return NodeResult(
                result_type=NodeResultType.RESPONSE if response_text else NodeResultType.CONTINUE,
                response_text=response_text,
                next_node_id=next_node_id,
                extracted_variables={"result": result} if node.result_variable else {},
                should_wait_for_input=False,
                metadata={"function_result": result}
            )
            
        except Exception as e:
            logger.error("Function execution failed", 
                        function_name=node.function_name,
                        error=str(e))
            
            failure_response = variables.interpolate(node.failure_message) if node.failure_message else f"Sorry, I encountered an error: {str(e)}"
            
            return NodeResult(
                result_type=NodeResultType.RESPONSE,
                response_text=failure_response,
                error_message=str(e)
            )
    
    async def _execute_logic_split(
        self,
        node: LogicSplitNode,
        variables: DynamicVariableStore
    ) -> NodeResult:
        """Execute a logic split node"""
        
        # Evaluate transitions - logic split just routes based on conditions
        next_node_id = await self._evaluate_transitions(
            node.edges, None, variables
        )
        
        return NodeResult(
            result_type=NodeResultType.CONTINUE,
            next_node_id=next_node_id,
            should_wait_for_input=False
        )
    
    def _execute_end(
        self,
        node: EndNode,
        variables: DynamicVariableStore
    ) -> NodeResult:
        """Execute an end node"""
        
        response_text = variables.interpolate(node.message)
        
        return NodeResult(
            result_type=NodeResultType.END,
            response_text=response_text,
            should_wait_for_input=False,
            metadata={"end_reason": node.end_reason}
        )
    
    def _execute_transfer(
        self,
        node: TransferNode,
        variables: DynamicVariableStore
    ) -> NodeResult:
        """Execute a transfer node"""
        
        response_text = variables.interpolate(node.message)
        
        return NodeResult(
            result_type=NodeResultType.TRANSFER,
            response_text=response_text,
            should_wait_for_input=False,
            metadata={
                "transfer_reason": node.transfer_reason,
                "destination": node.destination
            }
        )
    
    async def _execute_extract_variable(
        self,
        node: ExtractVariableNode,
        user_input: Optional[str],
        variables: DynamicVariableStore,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> NodeResult:
        """Execute a variable extraction node"""
        
        if not user_input:
            return NodeResult(
                result_type=NodeResultType.WAIT_INPUT,
                should_wait_for_input=True
            )
        
        # Extract each variable
        extracted = {}
        for var_def in node.variables:
            var_name = var_def.get("name", "")
            var_description = var_def.get("description", "")
            var_type = var_def.get("type", "string")
            
            value = await self._extract_single_variable(
                user_input, var_name, var_description, var_type, variables
            )
            
            if value is not None:
                extracted[var_name] = value
                variables.set(var_name, value, source=node.id)
        
        # Evaluate transitions
        next_node_id = await self._evaluate_transitions(
            node.edges, user_input, variables
        )
        
        return NodeResult(
            result_type=NodeResultType.CONTINUE,
            next_node_id=next_node_id,
            extracted_variables=extracted,
            should_wait_for_input=False
        )
    
    async def _extract_variables_from_input(
        self,
        user_input: str,
        variable_names: List[str],
        variables: DynamicVariableStore,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Extract multiple variables from user input using LLM"""
        
        if not variable_names:
            return {}
        
        # Build extraction prompt
        vars_desc = ", ".join(variable_names)
        prompt = f"""Extract the following information from the user's message.
Variables to extract: {vars_desc}

User said: "{user_input}"

For each variable, return the extracted value. If a variable is not found, return null.
Return as JSON object with variable names as keys.
Only return the JSON, no explanation."""

        try:
            response = await self.llm_service.generate_response(prompt)
            
            # Parse JSON response
            import json
            # Clean up response (remove markdown code blocks if present)
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            response = response.strip()
            
            extracted = json.loads(response)
            
            # Filter to only requested variables
            result = {}
            for var_name in variable_names:
                if var_name in extracted and extracted[var_name] is not None:
                    result[var_name] = extracted[var_name]
            
            logger.info("Variables extracted", 
                       extracted_count=len(result),
                       variables=list(result.keys()))
            
            return result
            
        except Exception as e:
            logger.error("Variable extraction failed", error=str(e))
            return {}
    
    async def _extract_single_variable(
        self,
        user_input: str,
        var_name: str,
        description: str,
        var_type: str,
        variables: DynamicVariableStore
    ) -> Optional[Any]:
        """Extract a single variable from user input"""
        
        prompt = f"""Extract the {description} from this text.
Expected type: {var_type}
Text: "{user_input}"

Return only the extracted value, nothing else. 
If not found, return exactly "null"."""

        try:
            response = await self.llm_service.generate_response(prompt)
            response = response.strip()
            
            if response.lower() == "null" or not response:
                return None
            
            # Type conversion
            if var_type == "number":
                try:
                    return float(response) if '.' in response else int(response)
                except ValueError:
                    return response
            elif var_type == "boolean":
                return response.lower() in ("true", "yes", "1")
            else:
                return response
                
        except Exception as e:
            logger.error("Single variable extraction failed",
                        var_name=var_name, error=str(e))
            return None
    
    def _build_conversation_prompt(
        self,
        node: ConversationNode,
        user_input: Optional[str],
        variables: DynamicVariableStore,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Build prompt for conversation node"""
        
        # Interpolate instruction with variables
        instruction = variables.interpolate(node.instruction)
        
        # Add examples if provided
        examples_text = ""
        if node.examples:
            examples_text = "\n\nExamples:\n"
            for ex in node.examples:
                examples_text += f"User: {ex.get('user', '')}\n"
                examples_text += f"Agent: {ex.get('agent', '')}\n\n"
        
        prompt = f"""{instruction}{examples_text}

User: {user_input}

Respond appropriately based on the instruction. Keep response concise for voice."""

        return prompt
    
    async def _evaluate_transitions(
        self,
        edges: List[Edge],
        user_input: Optional[str],
        variables: DynamicVariableStore
    ) -> Optional[str]:
        """Evaluate edge transitions and return next node ID"""
        
        if not edges:
            return None
        
        # Sort by priority
        sorted_edges = sorted(edges, key=lambda e: e.priority)
        
        # Evaluate equation conditions first (they're faster)
        for edge in sorted_edges:
            equation_conditions = [
                c for c in edge.conditions 
                if c.type == TransitionConditionType.EQUATION
            ]
            
            if equation_conditions:
                all_met = all(
                    variables.evaluate_equation(c.condition)
                    for c in equation_conditions
                )
                if all_met:
                    logger.debug("Equation transition matched",
                               edge_id=edge.id,
                               target=edge.target_node_id)
                    return edge.target_node_id
        
        # Evaluate prompt conditions (require LLM call)
        for edge in sorted_edges:
            prompt_conditions = [
                c for c in edge.conditions 
                if c.type == TransitionConditionType.PROMPT
            ]
            
            if prompt_conditions and user_input:
                # Build evaluation prompt
                conditions_text = "\n".join([
                    f"- {c.condition}" for c in prompt_conditions
                ])
                
                eval_prompt = f"""Determine if the user's message matches these conditions:
{conditions_text}

User said: "{user_input}"

Does the user's message satisfy ALL of these conditions?
Reply with only "yes" or "no"."""

                try:
                    response = await self.llm_service.generate_response(eval_prompt)
                    if response and response.strip().lower().startswith("yes"):
                        logger.debug("Prompt transition matched",
                                   edge_id=edge.id,
                                   target=edge.target_node_id)
                        return edge.target_node_id
                except Exception as e:
                    logger.warning("Transition evaluation failed", error=str(e))
        
        # Check for default edge
        for edge in sorted_edges:
            if edge.is_default:
                logger.debug("Using default transition",
                           edge_id=edge.id,
                           target=edge.target_node_id)
                return edge.target_node_id
        
        return None
