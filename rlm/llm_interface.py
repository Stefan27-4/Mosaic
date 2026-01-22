"""
LLM Interface for RLM framework.

This module provides an abstract LLM interface and implementations for
OpenAI, Anthropic, and Google Gemini models.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

# Set up logging
logger = logging.getLogger(__name__)


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
    async def query_async(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Query the LLM asynchronously with a prompt.
        
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
            from openai import OpenAI, AsyncOpenAI
        except ImportError:
            raise ImportError("openai package is required. Install with: pip install openai>=1.0.0")
        
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        # Cache async client for reuse
        self._async_client = AsyncOpenAI(api_key=api_key) if api_key else AsyncOpenAI()
    
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
    
    async def query_async(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Query the OpenAI model asynchronously.
        
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
        
        response = await self._async_client.chat.completions.create(
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
            from anthropic import Anthropic, AsyncAnthropic
        except ImportError:
            raise ImportError("anthropic package is required. Install with: pip install anthropic>=0.18.0")
        
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.client = Anthropic(api_key=api_key) if api_key else Anthropic()
        # Cache async client for reuse
        self._async_client = AsyncAnthropic(api_key=api_key) if api_key else AsyncAnthropic()
    
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
    
    async def query_async(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Query the Anthropic model asynchronously.
        
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
        
        response = await self._async_client.messages.create(**kwargs)
        
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
        model: str = "gemini-1.5-flash",
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
            from google import genai
        except ImportError:
            raise ImportError("google-genai package is required. Install with: pip install google-genai")
        
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # Initialize client with API key
        # The new client handles the API key directly
        self.client = genai.Client(api_key=api_key)
    
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
        config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_tokens,
        }
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=full_prompt,
            config=config
        )
        
        return response.text
    
    async def query_async(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Query the Gemini model asynchronously.
        
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
        config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_tokens,
        }
        
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=full_prompt,
            config=config
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
    
    Only initializes models for which API keys are available. If a provider's
    initialization fails (e.g., missing API key), it logs a warning and skips
    that provider instead of crashing.
    
    Args:
        openai_api_key: OpenAI API key (optional, uses env var if None)
        anthropic_api_key: Anthropic API key (optional, uses env var if None)
        google_api_key: Google API key (optional, uses env var if None)
        
    Returns:
        Dictionary mapping routing model IDs to LLM interface instances
        
    Raises:
        RuntimeError: If no models could be initialized successfully
        
    Example:
        >>> from rlm import route_text, create_model_map
        >>> model_map = create_model_map()
        >>> model_id = route_text("SELECT * FROM users")
        >>> llm = model_map[model_id]
        >>> response = llm.query("Explain this SQL query")
    """
    model_map = {}
    initialized_providers = []
    failed_providers = []
    
    # Try to initialize Anthropic interface
    try:
        if not anthropic_api_key or not anthropic_api_key.strip():
            raise ValueError("Anthropic API Key is missing")
        anthropic_interface = AnthropicInterface(
            model="claude-3-5-sonnet-20241022",
            api_key=anthropic_api_key,
            max_tokens=8192
        )
        # Profile A: Architect - Claude for complex code/legal
        model_map["claude-opus-4.5"] = anthropic_interface
        initialized_providers.append("Anthropic (claude-opus-4.5)")
        logger.info("Successfully initialized Anthropic interface")
    except (ImportError, ValueError, Exception) as e:
        logger.warning(f"Failed to initialize Anthropic interface: {e}")
        failed_providers.append(f"Anthropic ({type(e).__name__}: {str(e)})")
    
    # Try to initialize OpenAI interface
    try:
        if not openai_api_key or not openai_api_key.strip():
            raise ValueError("OpenAI API Key is missing")
        openai_interface_gpt4o = OpenAIInterface(
            model="gpt-4o",
            api_key=openai_api_key,
            max_tokens=16384
        )
        openai_interface_gpt4o_mini = OpenAIInterface(
            model="gpt-4o-mini",
            api_key=openai_api_key,
            max_tokens=8192
        )
        # Profile B: Project Manager - GPT-4o for SQL/planning
        model_map["gpt-5.2"] = openai_interface_gpt4o
        # Profile D: News Analyst - GPT-4o-mini for news/social (Grok not publicly available)
        model_map["grok-4.1"] = openai_interface_gpt4o_mini
        # Profile E: Efficiency Expert - GPT-4o-mini for math/default (DeepSeek not publicly available)
        model_map["deepseek-3.2"] = openai_interface_gpt4o_mini
        initialized_providers.append("OpenAI (gpt-5.2, grok-4.1, deepseek-3.2)")
        logger.info("Successfully initialized OpenAI interface")
    except (ImportError, ValueError, Exception) as e:
        logger.warning(f"Failed to initialize OpenAI interface: {e}")
        failed_providers.append(f"OpenAI ({type(e).__name__}: {str(e)})")
    
    # Try to initialize Gemini interface
    try:
        if not google_api_key or not google_api_key.strip():
            raise ValueError("Google API Key is missing")
        gemini_interface = GeminiInterface(
            model="gemini-1.5-flash",
            api_key=google_api_key,
            max_tokens=8192
        )
        # Profile C: Creative Director - Gemini for creative/research
        model_map["gemini-3"] = gemini_interface
        initialized_providers.append("Google Gemini (gemini-3)")
        logger.info("Successfully initialized Google Gemini interface")
    except (ImportError, ValueError, Exception) as e:
        logger.warning(f"Failed to initialize Google Gemini interface: {e}")
        failed_providers.append(f"Google Gemini ({type(e).__name__}: {str(e)})")
    
    # Ensure at least one model was initialized
    if not model_map:
        error_msg = (
            "Failed to initialize any LLM providers. Please ensure you have at least one valid API key configured.\n"
            f"Failed providers:\n" + "\n".join(f"  - {p}" for p in failed_providers)
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Log summary
    logger.info(f"Model map initialized with {len(model_map)} models from {len(initialized_providers)} provider(s)")
    logger.info(f"Successfully initialized: {', '.join(initialized_providers)}")
    if failed_providers:
        logger.info(f"Skipped providers: {', '.join(failed_providers)}")
    
    return model_map


