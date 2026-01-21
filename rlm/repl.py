"""
REPL Environment for RLM framework.

This module provides a Python REPL environment that stores context as a variable
and provides an llm_query function for recursive sub-LM calls.
"""

import sys
import asyncio
from io import StringIO
from typing import Any, Dict, Optional, Callable, Tuple, List


class REPLEnvironment:
    """
    A Python REPL environment for RLM.
    
    Stores context as a variable accessible to the LLM, provides an llm_query
    function for recursive sub-LM calls, executes Python code safely, and
    maintains state across iterations.
    """
    
    def __init__(
        self,
        context: Any,
        llm_query_fn: Optional[Callable[[str], str]] = None,
        parallel_query_fn: Optional[Callable[[str, List[str]], List[str]]] = None,
        max_output_length: int = 10000
    ):
        """
        Initialize the REPL environment.
        
        Args:
            context: The context to store in the REPL environment
            llm_query_fn: Function to call for LLM queries (can be None for no-subcalls mode)
            parallel_query_fn: Function to call for parallel LLM queries (can be None)
            max_output_length: Maximum length of output to return (truncates if longer)
        """
        self.context = context
        self.max_output_length = max_output_length
        self.namespace: Dict[str, Any] = {
            'context': context,
        }
        
        # Add llm_query function if provided
        if llm_query_fn is not None:
            self.namespace['llm_query'] = llm_query_fn
        
        # Add parallel_query function if provided
        if parallel_query_fn is not None:
            self.namespace['parallel_query'] = parallel_query_fn
    
    def execute(self, code: str) -> Tuple[str, bool]:
        """
        Execute Python code in the REPL environment.
        
        Args:
            code: Python code to execute
            
        Returns:
            Tuple of (output, success):
                - output: String output from execution (stdout + any errors)
                - success: Boolean indicating if execution was successful
        """
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        success = True
        error_msg = ""
        
        try:
            # Execute the code in the namespace
            exec(code, self.namespace)
        except Exception as e:
            success = False
            error_msg = f"Error: {type(e).__name__}: {str(e)}"
        finally:
            # Restore stdout
            sys.stdout = old_stdout
        
        # Get the captured output
        output = captured_output.getvalue()
        
        # Add error message if execution failed
        if not success:
            output = output + "\n" + error_msg if output else error_msg
        
        # Truncate output if too long
        if len(output) > self.max_output_length:
            truncated_msg = f"\n\n[Output truncated. Showing first {self.max_output_length} characters of {len(output)} total]"
            output = output[:self.max_output_length] + truncated_msg
        
        return output, success
    
    def get_variable(self, var_name: str) -> Any:
        """
        Get a variable from the REPL namespace.
        
        Args:
            var_name: Name of the variable to retrieve
            
        Returns:
            The value of the variable
            
        Raises:
            KeyError: If variable doesn't exist
        """
        return self.namespace[var_name]
    
    def has_variable(self, var_name: str) -> bool:
        """
        Check if a variable exists in the REPL namespace.
        
        Args:
            var_name: Name of the variable to check
            
        Returns:
            True if variable exists, False otherwise
        """
        return var_name in self.namespace
