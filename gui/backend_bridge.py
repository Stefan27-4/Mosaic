"""
Backend Bridge - Async RLM Integration with GUI

Provides thread-safe bridge between async RLM backend and synchronous customtkinter GUI.
"""

import threading
import queue
import asyncio
from typing import Optional, Dict, Any, Callable, Union, List
import traceback


class MosaicBridge:
    """
    Thread-safe bridge between async RLM backend and sync GUI.
    
    Handles:
    - Running async RLM operations in background thread
    - Message queue for thread-safe GUI updates
    - Budget tracking and cost updates
    - Hive memory state synchronization
    - Debug logging and error handling
    """
    
    def __init__(self, config: dict, message_callback: Callable[[tuple], None]):
        """
        Initialize the Mosaic backend bridge.
        
        Args:
            config: Configuration dict with 'api_keys' and 'budget_limit'
            message_callback: Callback function to receive messages from backend
                             Called with tuples: ("TYPE", data)
        """
        self.config = config
        self.message_callback = message_callback
        
        # Thread-safe message queue
        self.message_queue = queue.Queue()
        
        # Backend components (lazy init)
        self.rlm = None
        self.model_map = None
        
        # Track current request
        self.current_thread = None
        self.is_processing = False
        
        # Initialize backend
        self._initialize_backend()
    
    def _initialize_backend(self):
        """Initialize the RLM backend components."""
        try:
            # Import RLM components
            from rlm import RLM, create_model_map, get_available_models
            from rlm.llm_interface import OpenAIInterface, AnthropicInterface, GeminiInterface
            
            # Extract API keys from config
            api_keys = self.config.get("api_keys", {})
            
            # Create model map
            self.model_map = create_model_map(
                openai_api_key=api_keys.get("openai"),
                anthropic_api_key=api_keys.get("anthropic"),
                google_api_key=api_keys.get("google")
            )
            
            # Get available models
            available_models = get_available_models(self.model_map)
            
            # Determine which models to use
            if "gpt-5.2" in available_models:
                root_model_id = "gpt-5.2"
                sub_model_id = "deepseek-3.2" if "deepseek-3.2" in available_models else "gpt-5.2"
            elif "claude-opus-4.5" in available_models:
                root_model_id = "claude-opus-4.5"
                sub_model_id = "deepseek-3.2" if "deepseek-3.2" in available_models else "claude-opus-4.5"
            elif "gemini-3" in available_models:
                root_model_id = "gemini-3"
                sub_model_id = "deepseek-3.2" if "deepseek-3.2" in available_models else "gemini-3"
            else:
                # Fallback to first available
                root_model_id = list(available_models)[0]
                sub_model_id = root_model_id
            
            root_llm = self.model_map[root_model_id]
            sub_llm = self.model_map[sub_model_id]
            
            # Create RLM instance
            self.rlm = RLM(
                root_llm=root_llm,
                sub_llm=sub_llm,
                prompt_mode="standard",
                max_iterations=10,
                max_parallel_calls=10
            )
            
            self._send_message(("LOG", f"Backend initialized with {root_model_id} (root) and {sub_model_id} (sub)"))
            self._send_message(("LOG", f"Available models: {', '.join(available_models)}"))
            
        except Exception as e:
            error_msg = f"Failed to initialize backend: {str(e)}"
            self._send_message(("ERROR", error_msg))
            self._send_message(("LOG", f"[ERROR] {traceback.format_exc()}"))
    
    def _send_message(self, message: tuple):
        """
        Send a message to the GUI via callback.
        
        Args:
            message: Tuple of (type, data)
        """
        try:
            if self.message_callback:
                self.message_callback(message)
        except Exception as e:
            print(f"Error sending message to GUI: {e}")
    
    def run_query(self, user_prompt: str, context: Optional[list] = None, use_router: bool = True):
        """
        Run an RLM query in a background thread.
        
        Args:
            user_prompt: The user's query
            context: Optional list of context documents
            use_router: Whether to use smart routing
        """
        if self.is_processing:
            self._send_message(("ERROR", "Another query is already in progress"))
            return
        
        if not self.rlm:
            self._send_message(("ERROR", "Backend not initialized"))
            return
        
        self.is_processing = True
        
        # Start background thread
        self.current_thread = threading.Thread(
            target=self._run_query_thread,
            args=(user_prompt, context, use_router),
            daemon=True
        )
        self.current_thread.start()
    
    def _run_query_thread(self, user_prompt: str, context: Optional[list], use_router: bool):
        """
        Run the query in a background thread with its own event loop.
        
        Args:
            user_prompt: The user's query
            context: Optional list of context documents
            use_router: Whether to use smart routing
        """
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Send initial messages
            self._send_message(("LOG", f"[QUERY] Starting: {user_prompt[:100]}..."))
            self._send_message(("LOG", f"[CONFIG] Smart Router: {'ENABLED' if use_router else 'DISABLED'}"))
            
            if context:
                self._send_message(("LOG", f"[CONTEXT] {len(context)} documents loaded"))
            
            # Run the query
            try:
                # Use RLM's query method
                answer, trajectory = self.rlm.query(
                    user_prompt,
                    context=context or []
                )
                
                # Process trajectory for debug info
                self._process_trajectory(trajectory)
                
                # Send final answer
                self._send_message(("DONE", answer))
                self._send_message(("LOG", "[QUERY] Completed successfully"))
                
            except Exception as e:
                error_msg = f"Query failed: {str(e)}"
                self._send_message(("ERROR", error_msg))
                self._send_message(("LOG", f"[ERROR] {traceback.format_exc()}"))
            
        except Exception as e:
            error_msg = f"Thread error: {str(e)}"
            self._send_message(("ERROR", error_msg))
            self._send_message(("LOG", f"[THREAD ERROR] {traceback.format_exc()}"))
        
        finally:
            self.is_processing = False
            # Clean up event loop
            try:
                loop.close()
            except:
                pass
    
    def _process_trajectory(self, trajectory: Union[List[Dict[str, Any]], Dict[str, Any]]):
        """
        Process the RLM trajectory and send relevant messages to GUI.
        
        Args:
            trajectory: The trajectory from RLM (can be list or dict)
        """
        try:
            # Handle both list and dict formats
            if isinstance(trajectory, list):
                iterations = trajectory
                # Get subcall count from the last iteration if it exists
                subcall_count = 0
                if iterations and isinstance(iterations[-1], dict):
                    subcall_count = iterations[-1].get("subcalls", 0)
                # Cost tracking isn't available in the list format
                cost = 0
            else:
                # Existing logic for dict
                iterations = trajectory.get("iterations", [])
                subcall_count = trajectory.get("subcall_count", 0)
                cost = trajectory.get("estimated_cost", 0)
            
            # Send iteration count
            self._send_message(("LOG", f"[TRAJECTORY] {len(iterations)} iterations"))
            
            # Send subcall count
            if subcall_count > 0:
                self._send_message(("LOG", f"[SUB-CALLS] {subcall_count} recursive calls made"))
            
            # Track hive memory if present
            for i, iteration in enumerate(iterations, 1):
                # Log iteration
                self._send_message(("LOG", f"[ITERATION {i}] Processing..."))
                
                # Check for code execution
                if "code" in iteration:
                    code_lines = len(iteration["code"].split("\n"))
                    self._send_message(("LOG", f"[REPL] Executing {code_lines} lines of code"))
                
                # Check for results
                if "result" in iteration:
                    result_preview = str(iteration["result"])[:100]
                    self._send_message(("LOG", f"[RESULT] {result_preview}..."))
            
            # Send cost estimate if available
            if cost > 0:
                self._send_message(("BUDGET", cost))
        
        except Exception as e:
            self._send_message(("LOG", f"[WARNING] Error processing trajectory: {e}"))
    
    def get_hive_state(self) -> dict:
        """
        Get current hive memory state.
        
        Returns:
            Dict of hive memory contents
        """
        try:
            if self.rlm and hasattr(self.rlm, 'repl_env') and hasattr(self.rlm.repl_env, 'hive'):
                return self.rlm.repl_env.hive.get_all()
        except:
            pass
        
        return {}
    
    def is_busy(self) -> bool:
        """Check if backend is currently processing a query."""
        return self.is_processing
