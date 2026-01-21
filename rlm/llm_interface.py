"""
LLM Interface for RLM framework.

This module provides an abstract LLM interface and implementations for
OpenAI, Anthropic, and Google Gemini models.
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


class GeminiInterface(LLMInterface):
    """
    LLM interface for Google Gemini models.
    """
    
    def __init__(
        self,
        model: str = "gemini-1.5-pro",
        api_key: Optional[str] = None,
        max_tokens: int = 8192,
        temperature: float = 0.0
    ):
        """
        Initialize the Gemini interface.
        
        Args:
            model: Model name (e.g., "gemini-1.5-pro", "gemini-1.5-flash")
            api_key: Google API key (if None, uses environment variable)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("google-generativeai package is required. Install with: pip install google-generativeai")
        
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Configure API key
        if api_key:
            genai.configure(api_key=api_key)
        # If no api_key provided, will use GOOGLE_API_KEY environment variable
        
        self.client = genai.GenerativeModel(model)
    
    def query(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Query the Gemini model.
        
        Args:
            prompt: The prompt to send to the model
            system_prompt: Optional system prompt
            
        Returns:
            The model's response
        """
        # Combine system prompt with user prompt if provided
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt
        
        # Configure generation parameters
        generation_config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_tokens,
        }
        
        response = self.client.generate_content(
            full_prompt,
            generation_config=generation_config
        )
        
        return response.text
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "provider": "google",
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }


def create_model_map(
    openai_api_key: Optional[str] = None,
    anthropic_api_key: Optional[str] = None,
    google_api_key: Optional[str] = None
) -> Dict[str, LLMInterface]:
    """
    Create a mapping from routing model IDs to actual LLM interface instances.
    
    This helper function creates the default mapping used by the routing engine.
    Users can provide API keys or rely on environment variables.
    
    Args:
        openai_api_key: OpenAI API key (optional, uses env var if None)
        anthropic_api_key: Anthropic API key (optional, uses env var if None)
        google_api_key: Google API key (optional, uses env var if None)
        
    Returns:
        Dictionary mapping routing model IDs to LLM interface instances
        
    Example:
        >>> from rlm import route_text, create_model_map
        >>> model_map = create_model_map()
        >>> model_id = route_text("SELECT * FROM users")
        >>> llm = model_map[model_id]
        >>> response = llm.query("Explain this SQL query")
    """
    return {
        # Profile A: Architect - Claude Opus for complex code/legal
        "claude-opus-4.5": AnthropicInterface(
            model="claude-3-5-sonnet-20241022",
            api_key=anthropic_api_key,
            max_tokens=8192
        ),
        
        # Profile B: Project Manager - GPT-4o for SQL/planning
        "gpt-5.2": OpenAIInterface(
            model="gpt-4o",
            api_key=openai_api_key,
            max_tokens=16384
        ),
        
        # Profile C: Creative Director - Gemini for creative/research
        "gemini-3": GeminiInterface(
            model="gemini-1.5-pro",
            api_key=google_api_key,
            max_tokens=8192
        ),
        
        # Profile D: News Analyst - GPT-4o-mini for news/social (Grok not publicly available)
        # Note: Can be replaced with Grok API when available
        "grok-4.1": OpenAIInterface(
            model="gpt-4o-mini",
            api_key=openai_api_key,
            max_tokens=8192
        ),
        
        # Profile E: Efficiency Expert - GPT-4o-mini for math/default (DeepSeek not publicly available)
        # Note: Can be replaced with DeepSeek API when available
        "deepseek-3.2": OpenAIInterface(
            model="gpt-4o-mini",
            api_key=openai_api_key,
            max_tokens=8192
        ),
    }

