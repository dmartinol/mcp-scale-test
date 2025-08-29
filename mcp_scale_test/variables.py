"""Variable substitution system for dynamic argument generation."""

import re
import time
from typing import Any, Dict


class VariableExpander:
    """Handles expansion of template variables in tool arguments."""

    def __init__(self) -> None:
        self._counter = 0
        # Pattern to match {{variable}} or {{function(args)}}
        self._pattern = re.compile(r"\{\{([^}]+)\}\}")

    def expand_arguments(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expand all variables in the arguments dictionary.

        Args:
            args: Dictionary containing potential template variables

        Returns:
            Dictionary with all variables expanded to actual values
        """
        if not args:
            return {}

        # Deep copy and expand the arguments
        result = self._expand_recursive(args)
        # Type checker doesn't know _expand_recursive preserves dict structure
        return result  # type: ignore[no-any-return]

    def _expand_recursive(self, obj: Any) -> Any:
        """Recursively expand variables in nested data structures."""
        if isinstance(obj, dict):
            return {key: self._expand_recursive(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_recursive(item) for item in obj]
        elif isinstance(obj, str):
            return self._expand_string(obj)
        else:
            return obj

    def _expand_string(self, text: str) -> Any:
        """
        Expand variables in a string.

        Args:
            text: String that may contain {{variable}} patterns

        Returns:
            String with variables replaced, or the actual value if the entire
            string is a single variable
        """
        # Check if the entire string is a single variable (for type preservation)
        full_match = re.fullmatch(r"\{\{([^}]+)\}\}", text)
        if full_match:
            return self._resolve_variable(full_match.group(1))

        # Replace all variables in the string
        def replace_var(match: re.Match[str]) -> str:
            value = self._resolve_variable(match.group(1))
            return str(value)

        return self._pattern.sub(replace_var, text)

    def _resolve_variable(self, variable: str) -> Any:
        """
        Resolve a single variable to its value.

        Args:
            variable: Variable name (without the {{ }})

        Returns:
            The resolved value
        """
        variable = variable.strip()

        if variable == "timestamp":
            return time.time()
        elif variable == "counter":
            self._counter += 1
            return self._counter
        elif variable.startswith("random.randint("):
            # Parse random.randint(min,max)
            return self._parse_randint(variable)
        else:
            # Unknown variable, return as-is with warning
            return f"{{{{unknown:{variable}}}}}"

    def _parse_randint(self, expr: str) -> int:
        """
        Parse and execute random.randint(min,max) expression.

        Args:
            expr: Expression like "random.randint(1,1000)"

        Returns:
            Random integer in the specified range
        """
        import random

        # Extract the arguments from random.randint(min,max)
        match = re.match(r"random\.randint\((\d+),(\d+)\)", expr)
        if not match:
            raise ValueError(f"Invalid randint expression: {expr}")

        min_val = int(match.group(1))
        max_val = int(match.group(2))

        return random.randint(min_val, max_val)

    def reset_counter(self) -> None:
        """Reset the counter to 0."""
        self._counter = 0
