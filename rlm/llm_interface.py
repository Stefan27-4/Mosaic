"""
LLM Interface for RLM framework.

This module provides an abstract LLM interface and implementations for
OpenAI and Anthropic models.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class LLMInterface(ABC):
    """
    Abstract base class for LLM interfaces.
    """
    
    @abstractmethod
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Query the LLM with a prompt.
        
        Args:
            prompt: The prompt to send to the LLM
            system_prompt: Optional system prompt to use
            
        Returns:
            The LLM's response as a string
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.
        
        Returns:
            Dictionary with model information (name, max_tokens, etc.)
        """
        pass


class OpenAIInterface(LLMInterface):
    """
    LLM interface for OpenAI models.
    """
    
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        max_tokens: int = 16384,
        temperature: float = 0.0
    ):
        """
        Initialize the OpenAI interface.
        
        Args:
            model: Model name (e.g., "gpt-4o-mini", "gpt-4o")
            api_key: OpenAI API key (if None, uses environment variable)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package is required. Install with: pip install openai>=1.0.0")
        
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
    
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Query the OpenAI model.
        
        Args:
            prompt: The prompt to send to the model
            system_prompt: Optional system prompt
            
        Returns:
            The model's response
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        
        return response.choices[0].message.content
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "provider": "openai",
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }


class AnthropicInterface(LLMInterface):
    """
    LLM interface for Anthropic models.
    """
    
    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        api_key: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.0
    ):
        """
        Initialize the Anthropic interface.
        
        Args:
            model: Model name (e.g., "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022")
            api_key: Anthropic API key (if None, uses environment variable)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        """
        try:
            from anthropic import Anthropic
        except ImportError:
            raise ImportError("anthropic package is required. Install with: pip install anthropic>=0.18.0")
        
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.client = Anthropic(api_key=api_key) if api_key else Anthropic()
    
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Query the Anthropic model.
        
        Args:
            prompt: The prompt to send to the model
            system_prompt: Optional system prompt
            
        Returns:
            The model's response
        """
        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        response = self.client.messages.create(**kwargs)
        
        return response.content[0].text
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "provider": "anthropic",
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
