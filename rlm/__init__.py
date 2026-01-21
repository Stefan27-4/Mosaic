"""
RLM (Recursive Language Models) Framework

A framework for enabling LLMs to process arbitrarily long prompts by treating
them as part of an external environment that the LLM can programmatically interact with.
"""

from .core import RLM
from .repl import REPLEnvironment
from .llm_interface import LLMInterface, OpenAIInterface, AnthropicInterface
from .prompts import RLM_SYSTEM_PROMPT, RLM_SYSTEM_PROMPT_CONSERVATIVE, RLM_NO_SUBCALLS_PROMPT
from .utils import chunk_text, estimate_tokens, format_context_info, load_document

__version__ = "0.1.0"

__all__ = [
    "RLM",
    "REPLEnvironment",
    "LLMInterface",
    "OpenAIInterface",
    "AnthropicInterface",
    "RLM_SYSTEM_PROMPT",
    "RLM_SYSTEM_PROMPT_CONSERVATIVE",
    "RLM_NO_SUBCALLS_PROMPT",
    "chunk_text",
    "estimate_tokens",
    "format_context_info",
    "load_document",
]
