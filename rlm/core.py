"""
Core RLM (Recursive Language Model) implementation.

This module implements the main RLM class that orchestrates the REPL
environment and LLM interactions.
"""

import re
import asyncio
from typing import Optional, Any, List, Dict, Tuple
from .repl import REPLEnvironment
from .llm_interface import LLMInterface
from .prompts import RLM_SYSTEM_PROMPT, RLM_SYSTEM_PROMPT_CONSERVATIVE, RLM_NO_SUBCALLS_PROMPT
from .utils import format_context_info


class RLM:
    """
    Recursive Language Model.
    
    Orchestrates the REPL environment and LLM interactions to enable
    processing of arbitrarily long prompts through recursive sub-calls.
    """
    
    def __init__(
        self,
        root_llm: LLMInterface,
        sub_llm: Optional[LLMInterface] = None,
        max_iterations: int = 20,
        max_recursion_depth: int = 5,
        max_output_length: int = 10000,
        prompt_mode: str = "standard",
        max_parallel_calls: int = 10
    ):
        """
        Initialize the RLM.
        
        Args:
            root_llm: LLM interface for the root/main LLM
            sub_llm: LLM interface for sub-calls (if None, uses root_llm)
            max_iterations: Maximum number of REPL iterations
            max_recursion_depth: Maximum depth for recursive sub-calls
            max_output_length: Maximum length of REPL output
            prompt_mode: Prompt mode - "standard", "conservative", or "no_subcalls"
            max_parallel_calls: Maximum concurrent API calls in parallel_query
        """
        self.root_llm = root_llm
        self.sub_llm = sub_llm if sub_llm is not None else root_llm
        self.max_iterations = max_iterations
        self.max_recursion_depth = max_recursion_depth
        self.max_output_length = max_output_length
        self.prompt_mode = prompt_mode
        self.max_parallel_calls = max_parallel_calls
        
        # Select system prompt based on mode
        if prompt_mode == "conservative":
            self.system_prompt_template = RLM_SYSTEM_PROMPT_CONSERVATIVE
        elif prompt_mode == "no_subcalls":
            self.system_prompt_template = RLM_NO_SUBCALLS_PROMPT
        else:  # standard
            self.system_prompt_template = RLM_SYSTEM_PROMPT
        
        # Trajectory tracking
        self.trajectory: List[Dict[str, Any]] = []
        self.subcall_count = 0
        self.current_recursion_depth = 0
    
    def query(
        self,
        query: str,
        context: Any,
        verbose: bool = False
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Execute an RLM query.
        
        Args:
            query: The query/question to answer
            context: The context to use (can be string, list, dict, etc.)
            verbose: If True, print iteration details
            
        Returns:
            Tuple of (final_answer, trajectory):
                - final_answer: The final answer string
                - trajectory: List of iteration dictionaries with execution details
        """
        # Reset trajectory
        self.trajectory = []
        self.subcall_count = 0
        self.current_recursion_depth = 0
        
        # Create llm_query function for sub-calls
        def llm_query_fn(prompt: str) -> str:
            if self.prompt_mode == "no_subcalls":
                return "Error: llm_query is not available in no_subcalls mode"
            
            if self.current_recursion_depth >= self.max_recursion_depth:
                return "Error: Maximum recursion depth reached"
            
            self.subcall_count += 1
            self.current_recursion_depth += 1
            
            try:
                response = self.sub_llm.query(prompt)
                return response
            finally:
                self.current_recursion_depth -= 1
        
        # Create parallel_query function for parallel sub-calls
        def parallel_query_fn(prompt_template: str, context_chunks: List[str]) -> List[str]:
            """
            Process multiple chunks in parallel using async LLM calls.
            
            Args:
                prompt_template: Template string with {chunk} placeholder
                context_chunks: List of text chunks to process
                
            Returns:
                List of responses in the same order as input chunks
            """
            if self.prompt_mode == "no_subcalls":
                return ["Error: parallel_query is not available in no_subcalls mode"] * len(context_chunks)
            
            if self.current_recursion_depth >= self.max_recursion_depth:
                return ["Error: Maximum recursion depth reached"] * len(context_chunks)
            
            # Run async query in the synchronous context
            return asyncio.run(self._parallel_query_async(prompt_template, context_chunks))
        
        # Initialize REPL environment
        repl_env = REPLEnvironment(
            context=context,
            llm_query_fn=llm_query_fn if self.prompt_mode != "no_subcalls" else None,
            parallel_query_fn=parallel_query_fn if self.prompt_mode != "no_subcalls" else None,
            max_output_length=self.max_output_length
        )
        
        # Format context info for system prompt
        context_info = format_context_info(context)
        system_prompt = self.system_prompt_template.format(**context_info)
        
        # Build conversation history
        conversation_history = []
        
        # Initial prompt
        initial_message = f"Query: {query}\n\nPlease solve this query using the REPL environment."
        conversation_history.append({"role": "user", "content": initial_message})
        
        final_answer = None
        
        for iteration in range(self.max_iterations):
            if verbose:
                print(f"\n--- Iteration {iteration + 1} ---")
            
            # Build full prompt from conversation history
            prompt = self._build_prompt_from_history(conversation_history)
            
            # Query the root LLM
            response = self.root_llm.query(prompt, system_prompt=system_prompt)
            
            if verbose:
                print(f"LLM Response:\n{response[:500]}...")
            
            # Add to conversation history
            conversation_history.append({"role": "assistant", "content": response})
            
            # Check for final answer
            final_answer = self._extract_final_answer(response, repl_env)
            if final_answer is not None:
                if verbose:
                    print(f"\nFinal answer found: {final_answer[:200]}...")
                
                # Record iteration
                self.trajectory.append({
                    "iteration": iteration + 1,
                    "response": response,
                    "final_answer": final_answer,
                    "subcalls": self.subcall_count
                })
                break
            
            # Extract and execute code blocks
            code_blocks = self._extract_code_blocks(response)
            
            if not code_blocks:
                # No code to execute, ask for clarification
                if verbose:
                    print("No code blocks found")
                
                self.trajectory.append({
                    "iteration": iteration + 1,
                    "response": response,
                    "code_blocks": [],
                    "execution_results": []
                })
                
                conversation_history.append({
                    "role": "user",
                    "content": "Please provide Python code in a ```repl or ```python code block, or provide your final answer using FINAL() or FINAL_VAR()."
                })
                continue
            
            # Execute code blocks
            execution_results = []
            for code in code_blocks:
                output, success = repl_env.execute(code)
                execution_results.append({
                    "code": code,
                    "output": output,
                    "success": success
                })
                
                if verbose:
                    print(f"\nCode executed:\n{code[:200]}...")
                    print(f"Output:\n{output[:200]}...")
            
            # Record iteration
            self.trajectory.append({
                "iteration": iteration + 1,
                "response": response,
                "code_blocks": code_blocks,
                "execution_results": execution_results,
                "subcalls": self.subcall_count
            })
            
            # Add execution results to conversation
            results_message = self._format_execution_results(execution_results)
            conversation_history.append({
                "role": "user",
                "content": f"REPL execution results:\n{results_message}"
            })
        
        if final_answer is None:
            final_answer = "Error: Maximum iterations reached without final answer"
            if verbose:
                print(f"\n{final_answer}")
        
        return final_answer, self.trajectory
    
    async def _parallel_query_async(
        self,
        prompt_template: str,
        context_chunks: List[str]
    ) -> List[str]:
        """
        Process multiple chunks in parallel using async LLM calls.
        
        Uses a semaphore to limit concurrency and prevent API rate limits.
        
        Args:
            prompt_template: Template string with {chunk} placeholder
            context_chunks: List of text chunks to process
            
        Returns:
            List of responses in the same order as input chunks
        """
        # Create a semaphore to limit concurrent API calls
        semaphore = asyncio.Semaphore(self.max_parallel_calls)
        
        async def process_chunk(chunk: str, index: int) -> Tuple[int, str]:
            """Process a single chunk with semaphore protection."""
            async with semaphore:
                # Format the prompt with the chunk
                prompt = prompt_template.format(chunk=chunk)
                
                # Increment subcall count (thread-safe in async context)
                self.subcall_count += 1
                
                try:
                    # Call async query method
                    response = await self.sub_llm.query_async(prompt)
                    return (index, response)
                except Exception as e:
                    # Return error message but continue processing other chunks
                    return (index, f"Error processing chunk {index}: {str(e)}")
        
        # Create tasks for all chunks
        tasks = [process_chunk(chunk, i) for i, chunk in enumerate(context_chunks)]
        
        # Run all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        # Sort by index to maintain original order
        sorted_results = sorted(results, key=lambda x: x[0])
        
        # Return just the responses
        return [response for _, response in sorted_results]
    
    def _build_prompt_from_history(self, history: List[Dict[str, str]]) -> str:
        """Build a single prompt string from conversation history."""
        # For the first message, just return it
        if len(history) == 1:
            return history[0]["content"]
        
        # Build conversation history
        parts = []
        for msg in history:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                parts.append(f"User: {content}")
            else:
                parts.append(f"Assistant: {content}")
        
        return "\n\n".join(parts)
    
    def _extract_code_blocks(self, response: str) -> List[str]:
        """
        Extract code blocks from LLM response.
        
        Looks for ```repl or ```python code blocks.
        
        Args:
            response: LLM response text
            
        Returns:
            List of code strings
        """
        # Pattern to match ```repl or ```python code blocks
        # Newline after language identifier is optional to handle edge cases
        # where LLM might generate inline code blocks
        pattern = r'```(?:repl|python)\n?(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        return [match.strip() for match in matches]
    
    def _extract_final_answer(self, response: str, repl_env: REPLEnvironment) -> Optional[str]:
        """
        Extract final answer from response.
        
        Looks for FINAL(answer) or FINAL_VAR(variable_name) patterns.
        
        Args:
            response: LLM response text
            repl_env: REPL environment to get variables from
            
        Returns:
            Final answer string if found, None otherwise
        """
        # Check for FINAL(answer)
        final_pattern = r'FINAL\((.*?)\)'
        final_match = re.search(final_pattern, response, re.DOTALL)
        if final_match:
            return final_match.group(1).strip()
        
        # Check for FINAL_VAR(variable_name)
        final_var_pattern = r'FINAL_VAR\((\w+)\)'
        final_var_match = re.search(final_var_pattern, response)
        if final_var_match:
            var_name = final_var_match.group(1).strip()
            if repl_env.has_variable(var_name):
                return str(repl_env.get_variable(var_name))
            else:
                return f"Error: Variable '{var_name}' not found in REPL environment"
        
        return None
    
    def _format_execution_results(self, results: List[Dict[str, Any]]) -> str:
        """Format execution results for conversation history."""
        if not results:
            return "No code was executed."
        
        formatted = []
        for i, result in enumerate(results):
            status = "Success" if result["success"] else "Failed"
            formatted.append(f"Code block {i+1} ({status}):\n{result['output']}")
        
        return "\n\n".join(formatted)
