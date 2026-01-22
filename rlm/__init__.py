"""
RLM (Recursive Language Models) Framework

A framework for enabling LLMs to process arbitrarily long prompts by treating
them as part of an external environment that the LLM can programmatically interact with.
"""

from .core import RLM
from .repl import REPLEnvironment
from .hive_memory import HiveMemory
from .llm_interface import (
    LLMInterface,
    OpenAIInterface,
    AnthropicInterface,
    GeminiInterface,
    create_model_map,
)
from .prompts import RLM_SYSTEM_PROMPT, RLM_SYSTEM_PROMPT_CONSERVATIVE, RLM_NO_SUBCALLS_PROMPT
from .utils import chunk_text, estimate_tokens, format_context_info, load_document
from .routing import (
    HeuristicRoutingEngine,
    route_text,
    classify_chunk,
    get_available_models,
    ProfileConfig,
    PROFILE_ARCHITECT,
    PROFILE_PROJECT_MANAGER,
    PROFILE_CREATIVE_DIRECTOR,
    PROFILE_NEWS_ANALYST,
    PROFILE_EFFICIENCY_EXPERT,
    FALLBACK_CHAINS,
)
from .resilience import (
    CriticRouter,
    ResilientAgent,
    TaskType,
    ValidationResult,
    detect_task_type,
)
from .cache import (
    MosaicCache,
    get_cache,
    with_cache,
    cache_context,
)

__version__ = "0.1.0"

__all__ = [
    "RLM",
    "REPLEnvironment",
    "HiveMemory",
    "LLMInterface",
    "OpenAIInterface",
    "AnthropicInterface",
    "GeminiInterface",
    "create_model_map",
    "RLM_SYSTEM_PROMPT",
    "RLM_SYSTEM_PROMPT_CONSERVATIVE",
    "RLM_NO_SUBCALLS_PROMPT",
    "chunk_text",
    "estimate_tokens",
    "format_context_info",
    "load_document",
    "HeuristicRoutingEngine",
    "route_text",
    "classify_chunk",
    "get_available_models",
    "ProfileConfig",
    "PROFILE_ARCHITECT",
    "PROFILE_PROJECT_MANAGER",
    "PROFILE_CREATIVE_DIRECTOR",
    "PROFILE_NEWS_ANALYST",
    "PROFILE_EFFICIENCY_EXPERT",
    "FALLBACK_CHAINS",
    "CriticRouter",
    "ResilientAgent",
    "TaskType",
    "ValidationResult",
    "detect_task_type",
    "MosaicCache",
    "get_cache",
    "with_cache",
    "cache_context",
]
