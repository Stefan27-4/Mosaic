"""
Hive Memory for shared state across parallel sub-agents.

This module provides the HiveMemory class that enables parallel sub-agents
to share state (facts, findings) instantly instead of being isolated.
"""

import threading
from typing import Any, Dict, Optional


class HiveMemory:
    """
    Thread-safe shared memory for parallel sub-agents (Hive Mind).
    
    Allows multiple agents running in parallel to share facts, findings,
    and intermediate results instantly. Uses a lock to ensure thread-safety
    when accessed from parallel_query operations.
    """
    
    def __init__(self):
        """Initialize the hive memory with an empty state and a thread lock."""
        self._data: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def set(self, key: str, value: Any) -> None:
        """
        Thread-safe write operation.
        
        Args:
            key: The key to store the value under
            value: The value to store (can be any type)
        """
        with self._lock:
            self._data[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Thread-safe read operation.
        
        Args:
            key: The key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            The value associated with the key, or default if not found
        """
        with self._lock:
            return self._data.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """
        Thread-safe operation to get a snapshot of the entire memory.
        
        Returns:
            A copy of the entire memory dictionary
        """
        with self._lock:
            return self._data.copy()
    
    def clear(self) -> None:
        """
        Thread-safe operation to wipe all memory.
        
        Useful for starting a new session with a clean slate.
        """
        with self._lock:
            self._data.clear()
    
    def __repr__(self) -> str:
        """String representation of the hive memory."""
        with self._lock:
            return f"HiveMemory({self._data})"
    
    def __str__(self) -> str:
        """String representation for display."""
        with self._lock:
            if not self._data:
                return "HiveMemory(empty)"
            items = [f"{k}={repr(v)}" for k, v in self._data.items()]
            return f"HiveMemory({', '.join(items)})"
