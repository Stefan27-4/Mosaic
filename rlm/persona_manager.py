"""
Persona System - Specialized system prompts for each role with model resolution.

This module provides:
1. PromptManager - Loads and manages persona configurations
2. ModelResolver - Maps persona preferences to available models
"""

import os
import yaml
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path


class PromptManager:
    """
    Manages persona-specific system prompts and tool definitions.
    
    Loads persona configurations from personas.yaml and provides
    system prompts tailored to each specialist role.
    """
    
    def __init__(self, personas_file: Optional[str] = None):
        """
        Initialize the PromptManager.
        
        Args:
            personas_file: Path to personas.yaml. If None, uses default location.
        """
        if personas_file is None:
            # Default to personas.yaml in the same directory as this file
            personas_file = Path(__file__).parent / "personas.yaml"
        
        self.personas_file = personas_file
        self.personas = self._load_personas()
        
    def _load_personas(self) -> Dict:
        """Load persona configurations from YAML file."""
        try:
            with open(self.personas_file, 'r') as f:
                data = yaml.safe_load(f)
                return data.get('personas', {})
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Personas configuration file not found: {self.personas_file}"
            )
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing personas.yaml: {e}")
    
    def get_system_message(
        self,
        role_id: str,
        context_type: str = "list",
        context_total_length: int = 0,
        context_lengths: str = "",
        hive_state: Optional[Dict] = None,
        include_trajectory_note: bool = True
    ) -> str:
        """
        Get the complete system prompt for a specific persona.
        
        Args:
            role_id: The persona role ID (e.g., "architect", "news_analyst")
            context_type: Type of context data (e.g., "list", "dict", "string")
            context_total_length: Total character length of context
            context_lengths: String describing chunk lengths
            hive_state: Current state of Hive Memory (optional)
            include_trajectory_note: Whether to include trajectory tracking note
        
        Returns:
            Complete system prompt with dynamic injections
        """
        if role_id not in self.personas:
            raise ValueError(
                f"Unknown persona role_id: {role_id}. "
                f"Available: {list(self.personas.keys())}"
            )
        
        persona = self.personas[role_id]
        base_prompt = persona['system_prompt']
        
        # Dynamic context injection
        context_info = f"""
**Context Information:**
- Type: {context_type}
- Total Length: {context_total_length:,} characters
- Chunk Distribution: {context_lengths}
"""
        
        # Hive Memory state injection (if available)
        hive_info = ""
        if hive_state and hive_state:
            import json
            hive_json = json.dumps(hive_state, indent=2)
            hive_info = f"""
**Current Hive Memory State:**
{hive_json}

This state is automatically available to all parallel_query sub-agents.
"""
        
        # Tool function signatures
        tools_list = persona.get('tools', [])
        tools_info = self._format_tool_signatures(tools_list)
        
        # Trajectory tracking note
        trajectory_note = ""
        if include_trajectory_note:
            trajectory_note = """
**Execution Tracking:**
All of your REPL code execution is tracked for analysis and debugging.
Use `print()` statements liberally to show your reasoning process.
When you're ready to provide your final answer, use:
- `FINAL(your_answer_string)` for direct string answers, or
- `FINAL_VAR(variable_name)` to return a variable's value
"""
        
        # Assemble complete prompt
        complete_prompt = f"""{base_prompt}

{context_info}

{hive_info}

{tools_info}

{trajectory_note}

Remember: You are acting as {persona['display_name']}.
Focus on your core competencies and use the available tools effectively.
"""
        
        return complete_prompt.strip()
    
    def _format_tool_signatures(self, tools_list: List[str]) -> str:
        """Format tool function signatures for the system prompt."""
        if not tools_list:
            return ""
        
        signatures = {
            'llm_query': """
**llm_query(prompt: str) -> str**
Query a sub-LLM for semantic analysis. Use for complex reasoning on smaller chunks.
Example: `result = llm_query("Analyze this code for security issues: " + code_snippet)`
""",
            'parallel_query': """
**parallel_query(prompt_template: str, chunks: List[str]) -> List[str]**
Process multiple chunks in parallel. MUCH faster than loops.
The {chunk} placeholder in prompt_template is replaced with each chunk.
Returns results in the same order as input chunks.
Example: `summaries = parallel_query("Summarize: {chunk}", context)`
""",
            'hive': """
**hive (HiveMemory object)**
Thread-safe shared memory for accumulating findings across iterations and parallel operations.
Methods:
  - hive.set(key, value) - Store a finding
  - hive.get(key, default=None) - Retrieve a value
  - hive.get_all() - Get all stored data as dict
Example: `hive.set("key_finding", "important discovery")`
""",
            'print': """
**print(*args)**
Standard Python print function. Use to show your reasoning and intermediate results.
All print output is visible in the trajectory for debugging.
""",
            'context': """
**context (variable)**
The main data you're analyzing. Type and structure vary by task.
Always inspect it first: `print(type(context))`, `print(len(context))`
"""
        }
        
        available_tools = [signatures[tool] for tool in tools_list if tool in signatures]
        
        if available_tools:
            return """
**Available Tools & Functions:**
""" + "\n".join(available_tools)
        return ""
    
    def get_persona_info(self, role_id: str) -> Dict:
        """Get full persona information."""
        if role_id not in self.personas:
            raise ValueError(f"Unknown persona role_id: {role_id}")
        return self.personas[role_id]
    
    def list_personas(self) -> List[str]:
        """List all available persona role IDs."""
        return list(self.personas.keys())
    
    def get_model_preference(self, role_id: str) -> str:
        """Get the preferred model for a persona."""
        if role_id not in self.personas:
            raise ValueError(f"Unknown persona role_id: {role_id}")
        return self.personas[role_id].get('model_preference', 'deepseek-3.2')


class ModelResolver:
    """
    Resolves persona model preferences to actually available models.
    
    Ensures graceful degradation when preferred models aren't available,
    especially critical for users with only one API key.
    """
    
    # Fallback chains for each model (ordered by preference)
    FALLBACK_CHAINS = {
        'claude-opus-4.5': ['claude-opus-4.5', 'gpt-5.2', 'deepseek-3.2'],
        'gpt-5.2': ['gpt-5.2', 'claude-opus-4.5', 'deepseek-3.2'],
        'gemini-3': ['gemini-3', 'gpt-5.2', 'deepseek-3.2'],
        'grok-4.1': ['grok-4.1', 'gpt-5.2', 'deepseek-3.2'],
        'deepseek-3.2': ['deepseek-3.2', 'gpt-5.2', 'claude-opus-4.5'],
    }
    
    def __init__(self, available_models: Set[str]):
        """
        Initialize ModelResolver.
        
        Args:
            available_models: Set of model IDs that are currently available
                            (i.e., have valid API keys configured)
        """
        self.available_models = available_models
        
        if not available_models:
            raise ValueError(
                "No models available. At least one API key must be configured."
            )
    
    def resolve_model(
        self,
        requested_model: str,
        log_fallback: bool = True
    ) -> Tuple[str, bool]:
        """
        Resolve a requested model to an available model.
        
        Args:
            requested_model: The preferred model ID
            log_fallback: Whether to log when fallback is used
        
        Returns:
            Tuple of (resolved_model_id, was_fallback_used)
        """
        # Direct match - preferred model is available
        if requested_model in self.available_models:
            return requested_model, False
        
        # Single-key bypass: only one model available, use it
        if len(self.available_models) == 1:
            resolved = list(self.available_models)[0]
            if log_fallback:
                print(f"[ModelResolver] Single-key mode: Using {resolved} "
                      f"(requested: {requested_model})")
            return resolved, True
        
        # Multi-key: use fallback chain
        fallback_chain = self.FALLBACK_CHAINS.get(
            requested_model,
            ['gpt-5.2', 'claude-opus-4.5', 'deepseek-3.2']  # Default chain
        )
        
        for candidate in fallback_chain:
            if candidate in self.available_models:
                if log_fallback:
                    print(f"[ModelResolver] Fallback: {requested_model} → {candidate} "
                          f"(preferred model not available)")
                return candidate, True
        
        # Last resort: use any available model
        resolved = list(self.available_models)[0]
        if log_fallback:
            print(f"[ModelResolver] Emergency fallback: Using {resolved} "
                  f"(no preferred models available)")
        return resolved, True
    
    def get_available_count(self) -> int:
        """Get count of available models."""
        return len(self.available_models)
    
    def is_single_key_mode(self) -> bool:
        """Check if running in single-key mode (only one model available)."""
        return len(self.available_models) == 1
    
    def list_available_models(self) -> List[str]:
        """List all available model IDs."""
        return sorted(list(self.available_models))


# Global instances (can be initialized once and reused)
_prompt_manager = None
_model_resolver = None


def get_prompt_manager(personas_file: Optional[str] = None) -> PromptManager:
    """Get or create global PromptManager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager(personas_file)
    return _prompt_manager


def get_model_resolver(available_models: Optional[Set[str]] = None) -> ModelResolver:
    """
    Get or create global ModelResolver instance.
    
    Args:
        available_models: Set of available model IDs. If None, uses existing instance.
    
    Returns:
        ModelResolver instance
    """
    global _model_resolver
    if _model_resolver is None and available_models is None:
        raise ValueError(
            "ModelResolver not initialized. Provide available_models on first call."
        )
    if available_models is not None:
        _model_resolver = ModelResolver(available_models)
    return _model_resolver


def map_routing_profile_to_persona(profile_name: str) -> str:
    """
    Map routing engine profile names to persona role IDs.
    
    Args:
        profile_name: Profile from routing engine (e.g., "Architect", "Project Manager")
    
    Returns:
        Persona role_id (e.g., "architect", "project_manager")
    """
    mapping = {
        'Architect': 'architect',
        'Project Manager': 'project_manager',
        'Creative Director': 'creative_director',
        'News Analyst': 'news_analyst',
        'Efficiency Expert': 'efficiency_expert',
        # Also support lowercase/underscore versions
        'architect': 'architect',
        'project_manager': 'project_manager',
        'creative_director': 'creative_director',
        'news_analyst': 'news_analyst',
        'efficiency_expert': 'efficiency_expert',
    }
    
    return mapping.get(profile_name, 'efficiency_expert')  # Default to efficiency expert
