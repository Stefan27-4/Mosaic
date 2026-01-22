"""
Token optimization and efficiency layer for RLM framework.

This module provides accurate token counting with tiktoken and dynamic
chunk size calculation based on model capacity.
"""

import tiktoken
from typing import Dict, Tuple
from enum import Enum


class TaskType(Enum):
    """Task types for chunk size optimization."""
    CODE_ANALYSIS = "CODE_ANALYSIS"
    SUMMARIZATION = "SUMMARIZATION"
    GENERAL = "GENERAL"


# Model specifications: (context_limit, cost_per_million_tokens)
MODEL_SPECS: Dict[str, Tuple[int, float]] = {
    "claude-opus-4.5": (200000, 15.00),
    "claude-3-5-sonnet-20241022": (200000, 15.00),  # Actual model name
    "gpt-5.2": (128000, 5.00),
    "gpt-4o": (128000, 5.00),  # Actual model name
    "gpt-4o-mini": (128000, 0.50),
    "gemini-3": (2000000, 1.25),
    "gemini-1.5-pro": (2000000, 1.25),  # Actual model name
    "grok-4.1": (128000, 2.00),
    "deepseek-3.2": (64000, 0.50),
}


class TokenGatekeeper:
    """
    Accurate token counting and cost estimation using tiktoken.
    
    Singleton pattern to load encoders once for efficiency.
    """
    
    _instance = None
    _encoders: Dict[str, tiktoken.Encoding] = {}
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the token gatekeeper."""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._load_default_encoder()
    
    def _load_default_encoder(self):
        """Load the default cl100k_base encoder for fallback."""
        try:
            self._default_encoder = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            print(f"Warning: Could not load tiktoken encoder: {e}")
            self._default_encoder = None
    
    def _get_encoder(self, model: str) -> tiktoken.Encoding:
        """
        Get the tiktoken encoder for a specific model.
        
        Args:
            model: Model identifier
            
        Returns:
            tiktoken.Encoding instance
        """
        # Check cache
        if model in self._encoders:
            return self._encoders[model]
        
        # Try to get model-specific encoder
        try:
            # Map our model IDs to tiktoken model names
            model_mapping = {
                "gpt-5.2": "gpt-4o",
                "gpt-4o": "gpt-4o",
                "gpt-4o-mini": "gpt-4o",
                "claude-opus-4.5": "cl100k_base",
                "claude-3-5-sonnet-20241022": "cl100k_base",
                "gemini-3": "cl100k_base",
                "gemini-1.5-pro": "cl100k_base",
                "grok-4.1": "cl100k_base",
                "deepseek-3.2": "cl100k_base",
            }
            
            tiktoken_model = model_mapping.get(model, "cl100k_base")
            
            if tiktoken_model in ["gpt-4o", "gpt-4o-mini"]:
                encoder = tiktoken.encoding_for_model(tiktoken_model)
            else:
                encoder = tiktoken.get_encoding(tiktoken_model)
            
            self._encoders[model] = encoder
            return encoder
        except Exception:
            # Fallback to default encoder
            if self._default_encoder is not None:
                self._encoders[model] = self._default_encoder
                return self._default_encoder
            else:
                raise RuntimeError(f"Could not load encoder for model {model}")
    
    def count(self, text: str, model: str = "cl100k_base") -> int:
        """
        Count tokens in text using the appropriate encoder.
        
        Args:
            text: Text to count tokens for
            model: Model identifier
            
        Returns:
            Precise token count
        """
        if not text:
            return 0
        
        try:
            encoder = self._get_encoder(model)
            tokens = encoder.encode(text)
            return len(tokens)
        except Exception as e:
            print(f"Warning: Token counting failed for model {model}: {e}")
            # Fallback to heuristic (4 chars per token)
            return len(text) // 4
    
    def get_limit(self, model: str) -> int:
        """
        Get the context limit for a model.
        
        Args:
            model: Model identifier
            
        Returns:
            Context limit in tokens
        """
        return MODEL_SPECS.get(model, (128000, 5.00))[0]
    
    def estimate_cost(self, text: str, model: str) -> float:
        """
        Estimate the cost of processing text with a model.
        
        Args:
            text: Text to estimate cost for
            model: Model identifier
            
        Returns:
            Estimated cost in USD
        """
        token_count = self.count(text, model)
        cost_per_million = MODEL_SPECS.get(model, (128000, 5.00))[1]
        return (token_count / 1_000_000) * cost_per_million


class ChunkAutoTuner:
    """
    Dynamic chunk size calculation based on model capacity and task type.
    
    Automatically optimizes chunk sizes to match model capabilities.
    """
    
    def __init__(self):
        """Initialize the chunk auto-tuner."""
        self.gatekeeper = TokenGatekeeper()
    
    def calculate_optimal_chunk_size(
        self,
        model_id: str,
        task_type: TaskType = TaskType.GENERAL
    ) -> int:
        """
        Calculate the optimal chunk size for a model and task.
        
        Args:
            model_id: Model identifier
            task_type: Type of task (CODE_ANALYSIS, SUMMARIZATION, GENERAL)
            
        Returns:
            Optimal chunk size in tokens
        """
        # Step 1: Get the model's context limit
        context_limit = self.gatekeeper.get_limit(model_id)
        
        # Step 2: Reserve safety buffer for system prompt + response
        SAFETY_BUFFER = 4000
        available_tokens = context_limit - SAFETY_BUFFER
        
        # Step 3: Apply task-specific multiplier
        if task_type == TaskType.CODE_ANALYSIS:
            # Code analysis needs large context (80%)
            chunk_size = int(available_tokens * 0.80)
        elif task_type == TaskType.SUMMARIZATION:
            # Summarization works better with smaller chunks (20%)
            chunk_size = int(available_tokens * 0.20)
        else:  # TaskType.GENERAL
            # General tasks use moderate chunks (40%)
            chunk_size = int(available_tokens * 0.40)
        
        # Step 4: Clamp to reasonable limits
        MIN_CHUNK_SIZE = 1000
        MAX_CHUNK_SIZE = 100000
        
        chunk_size = max(MIN_CHUNK_SIZE, min(chunk_size, MAX_CHUNK_SIZE))
        
        return chunk_size
    
    def get_optimal_chunks(
        self,
        text: str,
        model_id: str,
        task_type: TaskType = TaskType.GENERAL,
        overlap_ratio: float = 0.1
    ) -> list:
        """
        Split text into optimally-sized chunks.
        
        Args:
            text: Text to split
            model_id: Model identifier
            task_type: Type of task
            overlap_ratio: Overlap between chunks (0.0 to 0.5)
            
        Returns:
            List of text chunks
        """
        optimal_size = self.calculate_optimal_chunk_size(model_id, task_type)
        
        # Calculate overlap in tokens
        overlap_tokens = int(optimal_size * min(overlap_ratio, 0.5))
        
        # Use tiktoken to split accurately
        encoder = self.gatekeeper._get_encoder(model_id)
        tokens = encoder.encode(text)
        
        chunks = []
        start = 0
        total_tokens = len(tokens)
        
        while start < total_tokens:
            end = min(start + optimal_size, total_tokens)
            chunk_tokens = tokens[start:end]
            chunk_text = encoder.decode(chunk_tokens)
            chunks.append(chunk_text)
            
            if end == total_tokens:
                break
            
            # Move forward with overlap
            start = end - overlap_tokens
        
        return chunks


# Global instances for convenience
_gatekeeper = None
_auto_tuner = None


def get_token_gatekeeper() -> TokenGatekeeper:
    """Get the global TokenGatekeeper instance."""
    global _gatekeeper
    if _gatekeeper is None:
        _gatekeeper = TokenGatekeeper()
    return _gatekeeper


def get_chunk_auto_tuner() -> ChunkAutoTuner:
    """Get the global ChunkAutoTuner instance."""
    global _auto_tuner
    if _auto_tuner is None:
        _auto_tuner = ChunkAutoTuner()
    return _auto_tuner


# Convenience functions
def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """
    Count tokens in text.
    
    Args:
        text: Text to count
        model: Model identifier
        
    Returns:
        Token count
    """
    return get_token_gatekeeper().count(text, model)


def estimate_cost(text: str, model: str) -> float:
    """
    Estimate cost of processing text.
    
    Args:
        text: Text to estimate
        model: Model identifier
        
    Returns:
        Estimated cost in USD
    """
    return get_token_gatekeeper().estimate_cost(text, model)


def get_model_limit(model: str) -> int:
    """
    Get context limit for a model.
    
    Args:
        model: Model identifier
        
    Returns:
        Context limit in tokens
    """
    return get_token_gatekeeper().get_limit(model)


def calculate_chunk_size(model: str, task_type: TaskType = TaskType.GENERAL) -> int:
    """
    Calculate optimal chunk size.
    
    Args:
        model: Model identifier
        task_type: Type of task
        
    Returns:
        Optimal chunk size in tokens
    """
    return get_chunk_auto_tuner().calculate_optimal_chunk_size(model, task_type)


def smart_chunk_text(
    text: str,
    model: str,
    task_type: TaskType = TaskType.GENERAL,
    overlap_ratio: float = 0.1
) -> list:
    """
    Split text into optimally-sized chunks.
    
    Args:
        text: Text to split
        model: Model identifier
        task_type: Type of task
        overlap_ratio: Overlap ratio (0.0 to 0.5)
        
    Returns:
        List of text chunks
    """
    return get_chunk_auto_tuner().get_optimal_chunks(text, model, task_type, overlap_ratio)
