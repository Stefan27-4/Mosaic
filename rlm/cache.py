"""
Caching Layer for Mosaic RLM framework.

This module provides SQLite-based caching to optimize performance and reduce API costs
by storing and retrieving responses for identical requests.
"""

import hashlib
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from functools import wraps


class MosaicCache:
    """
    SQLite-based caching system for LLM responses.
    
    This class provides persistent caching of API responses to reduce costs
    and improve performance by avoiding duplicate API calls.
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the caching system.
        
        Args:
            cache_dir: Directory to store the cache database.
                      Defaults to ~/.mosaic/
        """
        if cache_dir is None:
            cache_dir = os.path.expanduser("~/.mosaic")
        
        # Create directory if it doesn't exist
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        
        self.db_path = os.path.join(cache_dir, "cache.db")
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create the api_responses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_responses (
                request_hash TEXT PRIMARY KEY,
                response_data TEXT NOT NULL,
                created_at REAL NOT NULL,
                last_accessed REAL,
                model_id TEXT NOT NULL,
                tokens_saved INTEGER NOT NULL
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_model_id 
            ON api_responses(model_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_created_at 
            ON api_responses(created_at)
        """)
        
        conn.commit()
        conn.close()
    
    def _normalize_input(self, data: Any) -> str:
        """
        Normalize input data for consistent hashing.
        
        Args:
            data: Input data to normalize
            
        Returns:
            Normalized string representation
        """
        if isinstance(data, dict):
            # Sort keys for consistent ordering
            return json.dumps(data, sort_keys=True, separators=(',', ':'))
        elif isinstance(data, str):
            # Strip whitespace and normalize
            return data.strip()
        else:
            return str(data)
    
    def _generate_hash(
        self,
        prompt: str,
        model_id: str,
        temperature: float = 0.0,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate a consistent SHA256 hash for the request parameters.
        
        Args:
            prompt: The prompt text
            model_id: The model identifier
            temperature: Temperature parameter
            system_prompt: Optional system prompt
            **kwargs: Additional parameters to include in hash
            
        Returns:
            SHA256 hash as hex string
        """
        # Normalize all inputs
        normalized_prompt = self._normalize_input(prompt)
        normalized_model = self._normalize_input(model_id)
        normalized_system = self._normalize_input(system_prompt) if system_prompt else ""
        normalized_temp = str(temperature)
        
        # Sort kwargs for consistency
        normalized_kwargs = self._normalize_input(kwargs) if kwargs else ""
        
        # Combine all components
        hash_input = f"{normalized_prompt}|{normalized_model}|{normalized_temp}|{normalized_system}|{normalized_kwargs}"
        
        # Generate SHA256 hash
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
    
    def get(
        self,
        prompt: str,
        model_id: str,
        temperature: float = 0.0,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a cached response if it exists.
        
        Args:
            prompt: The prompt text
            model_id: The model identifier
            temperature: Temperature parameter
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
            
        Returns:
            Cached response data as dictionary, or None if not found
        """
        request_hash = self._generate_hash(prompt, model_id, temperature, system_prompt, **kwargs)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT response_data, tokens_saved
            FROM api_responses
            WHERE request_hash = ?
            """,
            (request_hash,)
        )
        
        result = cursor.fetchone()
        
        if result:
            # Update last_accessed timestamp
            current_time = time.time()
            cursor.execute(
                """
                UPDATE api_responses
                SET last_accessed = ?
                WHERE request_hash = ?
                """,
                (current_time, request_hash)
            )
            conn.commit()
            conn.close()
            
            # Deserialize and return the response
            response_data, tokens_saved = result
            return {
                'response': json.loads(response_data),
                'tokens_saved': tokens_saved,
                'from_cache': True
            }
        
        conn.close()
        return None
    
    def set(
        self,
        prompt: str,
        model_id: str,
        response_data: Any,
        tokens_count: int,
        temperature: float = 0.0,
        system_prompt: Optional[str] = None,
        **kwargs
    ):
        """
        Store a response in the cache.
        
        Args:
            prompt: The prompt text
            model_id: The model identifier
            response_data: The response to cache
            tokens_count: Number of tokens in the response
            temperature: Temperature parameter
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
        """
        request_hash = self._generate_hash(prompt, model_id, temperature, system_prompt, **kwargs)
        current_time = time.time()
        
        # Serialize response_data
        serialized_response = json.dumps(response_data)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Insert or replace the cache entry
        cursor.execute(
            """
            INSERT OR REPLACE INTO api_responses
            (request_hash, response_data, created_at, last_accessed, model_id, tokens_saved)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (request_hash, serialized_response, current_time, current_time, model_id, tokens_count)
        )
        
        conn.commit()
        conn.close()
    
    def get_total_savings(self) -> Dict[str, Any]:
        """
        Calculate total savings from cached responses.
        
        Returns:
            Dictionary with total tokens saved and estimated cost savings
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get total tokens saved
        cursor.execute(
            """
            SELECT 
                SUM(tokens_saved) as total_tokens,
                COUNT(*) as total_entries,
                COUNT(DISTINCT model_id) as unique_models
            FROM api_responses
            """
        )
        
        result = cursor.fetchone()
        conn.close()
        
        total_tokens, total_entries, unique_models = result
        total_tokens = total_tokens or 0
        total_entries = total_entries or 0
        unique_models = unique_models or 0
        
        # Estimate cost savings (rough estimate: $0.002 per 1K tokens average)
        estimated_savings = (total_tokens / 1000) * 0.002
        
        return {
            'total_tokens_saved': total_tokens,
            'total_cache_entries': total_entries,
            'unique_models': unique_models,
            'estimated_cost_savings_usd': round(estimated_savings, 2)
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get detailed cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get per-model statistics
        cursor.execute(
            """
            SELECT 
                model_id,
                COUNT(*) as entry_count,
                SUM(tokens_saved) as total_tokens
            FROM api_responses
            GROUP BY model_id
            """
        )
        
        model_stats = []
        for row in cursor.fetchall():
            model_id, entry_count, total_tokens = row
            model_stats.append({
                'model_id': model_id,
                'entry_count': entry_count,
                'total_tokens': total_tokens or 0
            })
        
        conn.close()
        
        # Get overall savings
        savings = self.get_total_savings()
        
        return {
            **savings,
            'per_model_stats': model_stats
        }
    
    def clear_cache(self, older_than_days: Optional[int] = None):
        """
        Clear cache entries.
        
        Args:
            older_than_days: If specified, only clear entries older than this many days.
                            If None, clears all entries.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if older_than_days is None:
            cursor.execute("DELETE FROM api_responses")
        else:
            cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
            cursor.execute(
                "DELETE FROM api_responses WHERE created_at < ?",
                (cutoff_time,)
            )
        
        conn.commit()
        deleted_count = cursor.rowcount
        conn.close()
        
        return deleted_count
    
    def vacuum(self):
        """Optimize the database by running VACUUM."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("VACUUM")
        conn.close()


# Global cache instance
_global_cache: Optional[MosaicCache] = None


def get_cache() -> MosaicCache:
    """
    Get the global cache instance.
    
    Returns:
        The global MosaicCache instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = MosaicCache()
    return _global_cache


def with_cache(func):
    """
    Decorator to add caching to LLM query methods.
    
    This decorator intercepts LLM calls and returns cached responses when available.
    """
    @wraps(func)
    def wrapper(self, prompt: str, system_prompt: Optional[str] = None, use_cache: bool = True, **kwargs):
        if not use_cache:
            return func(self, prompt, system_prompt, **kwargs)
        
        cache = get_cache()
        
        # Try to get from cache
        model_id = getattr(self, 'model', 'unknown')
        temperature = getattr(self, 'temperature', 0.0)
        
        cached_result = cache.get(
            prompt=prompt,
            model_id=model_id,
            temperature=temperature,
            system_prompt=system_prompt,
            **kwargs
        )
        
        if cached_result:
            # Return cached response
            return cached_result['response']
        
        # Call the actual function
        response = func(self, prompt, system_prompt, **kwargs)
        
        # Estimate tokens (rough estimate based on response length)
        tokens_count = len(response.split()) * 1.3  # Rough approximation
        
        # Cache the response
        cache.set(
            prompt=prompt,
            model_id=model_id,
            response_data=response,
            tokens_count=int(tokens_count),
            temperature=temperature,
            system_prompt=system_prompt,
            **kwargs
        )
        
        return response
    
    return wrapper


@contextmanager
def cache_context(enabled: bool = True):
    """
    Context manager for controlling cache behavior.
    
    Args:
        enabled: Whether caching should be enabled in this context
        
    Example:
        with cache_context(enabled=False):
            # Caching disabled for these calls
            result = llm.query(prompt)
    """
    # This is a simple context manager that can be extended
    # to temporarily disable caching or change cache settings
    yield
