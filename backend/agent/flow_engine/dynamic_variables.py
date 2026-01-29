"""
Dynamic Variable Store

Manages dynamic variables extracted during conversation flow.
Supports:
- Variable interpolation in templates ({{var_name}})
- Equation evaluation for transition conditions
- Type validation
- Variable history tracking
"""

import re
import operator
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime
from utils.logger import logger


@dataclass
class VariableChange:
    """Record of a variable change"""
    variable_name: str
    old_value: Any
    new_value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""  # Which node made the change


class DynamicVariableStore:
    """
    Store for dynamic variables during conversation.
    
    Features:
    - Get/set variables with type coercion
    - Template interpolation: "Hello {{name}}, your appointment is on {{date}}"
    - Equation evaluation: "{{age}} >> 18", "{{status}} == 'active'"
    - Variable existence checks
    - Change history tracking
    """
    
    def __init__(self, initial_variables: Optional[Dict[str, Any]] = None):
        self._variables: Dict[str, Any] = initial_variables.copy() if initial_variables else {}
        self._history: List[VariableChange] = []
        self._variable_types: Dict[str, str] = {}  # Optional type hints
        
        logger.info("DynamicVariableStore initialized", 
                   initial_count=len(self._variables))
    
    def get(self, name: str, default: Any = None) -> Any:
        """Get a variable value"""
        return self._variables.get(name, default)
    
    def set(self, name: str, value: Any, source: str = "") -> None:
        """Set a variable value"""
        old_value = self._variables.get(name)
        self._variables[name] = value
        
        # Track change
        self._history.append(VariableChange(
            variable_name=name,
            old_value=old_value,
            new_value=value,
            source=source
        ))
        
        logger.debug("Variable set", name=name, value=value, source=source)
    
    def exists(self, name: str) -> bool:
        """Check if a variable exists and has a non-None value"""
        return name in self._variables and self._variables[name] is not None
    
    def delete(self, name: str) -> None:
        """Delete a variable"""
        if name in self._variables:
            old_value = self._variables.pop(name)
            self._history.append(VariableChange(
                variable_name=name,
                old_value=old_value,
                new_value=None,
                source="delete"
            ))
    
    def get_all(self) -> Dict[str, Any]:
        """Get all variables"""
        return self._variables.copy()
    
    def clear(self) -> None:
        """Clear all variables"""
        self._variables.clear()
        self._history.clear()
    
    def get_history(self, variable_name: Optional[str] = None) -> List[VariableChange]:
        """Get change history, optionally filtered by variable name"""
        if variable_name:
            return [h for h in self._history if h.variable_name == variable_name]
        return self._history.copy()
    
    def interpolate(self, template: str) -> str:
        """
        Interpolate variables into a template string.
        
        Template format: {{variable_name}}
        Example: "Hello {{name}}, your appointment is on {{date}}"
        
        If a variable doesn't exist, the placeholder is left as-is.
        """
        if not template:
            return template
        
        def replace_var(match):
            var_name = match.group(1).strip()
            value = self._variables.get(var_name)
            if value is not None:
                return str(value)
            return match.group(0)  # Keep original if not found
        
        # Match {{variable_name}} pattern
        pattern = r'\{\{([^}]+)\}\}'
        return re.sub(pattern, replace_var, template)
    
    def evaluate_equation(self, equation: str) -> bool:
        """
        Evaluate an equation condition against variables.
        
        Supported operators:
        - >> : greater than
        - << : less than
        - == : equals
        - != : not equals
        - >= : greater than or equal
        - <= : less than or equal
        - CONTAINS : string contains
        - NOT CONTAINS : string does not contain
        - exists : variable exists
        - not exists : variable does not exist
        - AND : logical and
        - OR : logical or
        
        Examples:
        - "{{age}} >> 18"
        - "{{status}} == 'active'"
        - "{{name}} exists"
        - "{{items}} CONTAINS 'apple'"
        - "{{age}} >> 18 AND {{status}} == 'active'"
        """
        if not equation:
            return True  # Empty equation is always true
        
        equation = equation.strip()
        
        # Handle logical operators (AND/OR) - split and evaluate recursively
        # Check for OR first (lower precedence)
        if ' OR ' in equation:
            parts = equation.split(' OR ', 1)
            return self.evaluate_equation(parts[0]) or self.evaluate_equation(parts[1])
        
        # Check for AND
        if ' AND ' in equation:
            parts = equation.split(' AND ', 1)
            return self.evaluate_equation(parts[0]) and self.evaluate_equation(parts[1])
        
        # Handle 'exists' and 'not exists' (both formats: "not exists" and "not_exists")
        exists_match = re.match(r'\{\{(\w+)\}\}\s+(exists|not exists|not_exists)', equation, re.IGNORECASE)
        if exists_match:
            var_name = exists_match.group(1)
            is_not = 'not' in exists_match.group(2).lower()
            result = self.exists(var_name)
            return not result if is_not else result
        
        # Also check for reversed format: "{{var}} not exists" vs "not {{var}} exists"
        not_exists_match = re.match(r'\{\{(\w+)\}\}\s+not\s+exists', equation, re.IGNORECASE)
        if not_exists_match:
            var_name = not_exists_match.group(1)
            return not self.exists(var_name)
        
        # Handle comparison operators
        # First, interpolate variables
        interpolated = self._interpolate_for_eval(equation)
        
        # Parse the comparison
        comparison_ops = [
            ('>=', operator.ge),
            ('<=', operator.le),
            ('>>', operator.gt),
            ('<<', operator.lt),
            ('!=', operator.ne),
            ('==', operator.eq),
            ('CONTAINS', self._contains),
            ('NOT CONTAINS', self._not_contains),
        ]
        
        for op_str, op_func in comparison_ops:
            if op_str in interpolated:
                parts = interpolated.split(op_str, 1)
                if len(parts) == 2:
                    left = self._parse_value(parts[0].strip())
                    right = self._parse_value(parts[1].strip())
                    try:
                        return op_func(left, right)
                    except (TypeError, ValueError) as e:
                        logger.warning("Equation evaluation failed", 
                                     equation=equation, error=str(e))
                        return False
        
        # If no operator found, try to evaluate as boolean
        try:
            value = self._parse_value(interpolated)
            return bool(value)
        except:
            return False
    
    def _interpolate_for_eval(self, template: str) -> str:
        """Interpolate variables for equation evaluation, preserving types"""
        if not template:
            return template
        
        def replace_var(match):
            var_name = match.group(1).strip()
            value = self._variables.get(var_name)
            if value is None:
                return '""'  # Empty string for missing values
            if isinstance(value, str):
                return f'"{value}"'
            if isinstance(value, bool):
                return str(value).lower()
            return str(value)
        
        pattern = r'\{\{([^}]+)\}\}'
        return re.sub(pattern, replace_var, template)
    
    def _parse_value(self, value_str: str) -> Any:
        """Parse a string value into appropriate type"""
        value_str = value_str.strip()
        
        # Remove quotes if present
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]
        
        # Try to parse as number
        try:
            if '.' in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass
        
        # Boolean
        if value_str.lower() == 'true':
            return True
        if value_str.lower() == 'false':
            return False
        
        # Return as string
        return value_str
    
    @staticmethod
    def _contains(haystack: Any, needle: Any) -> bool:
        """Check if haystack contains needle"""
        if isinstance(haystack, str) and isinstance(needle, str):
            return needle in haystack
        if isinstance(haystack, (list, tuple)):
            return needle in haystack
        return False
    
    @staticmethod
    def _not_contains(haystack: Any, needle: Any) -> bool:
        """Check if haystack does not contain needle"""
        return not DynamicVariableStore._contains(haystack, needle)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export variables as dictionary"""
        return {
            "variables": self._variables.copy(),
            "history_count": len(self._history)
        }
    
    def __repr__(self) -> str:
        return f"DynamicVariableStore({self._variables})"


# Convenience function for quick interpolation
def interpolate_template(template: str, variables: Dict[str, Any]) -> str:
    """Quick interpolation without creating a store"""
    store = DynamicVariableStore(variables)
    return store.interpolate(template)
