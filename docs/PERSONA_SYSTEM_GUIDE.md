# Persona System Guide

Complete guide to Mosaic's Persona System - specialized system prompts for each specialist role with intelligent model resolution.

## Overview

The Persona System provides role-specific system prompts tailored to each specialist profile identified by the Smart Router. Each persona has:

- **Specialized system prompts** optimized for their domain
- **Tool-specific access** (some personas see different tools)
- **Model preferences** (best model for each role)
- **Graceful degradation** (works even with single API key)

## Architecture

### Components

1. **personas.yaml** - Configuration file defining all specialist roles
2. **PromptManager** - Loads personas and generates specialized system prompts
3. **ModelResolver** - Maps persona preferences to available models
4. **Integration helpers** - Connect routing engine to personas

### The 5 Core Personas

#### 1. Architect (Senior Principal Engineer)
- **Model Preference:** Claude Opus 4.5
- **Specialization:** Code architecture, design patterns, legal documents
- **Focus:** SOLID principles, scalability, security, compliance
- **Use Cases:**
  - Large-scale code refactoring
  - Multi-file architecture analysis
  - Design pattern implementation
  - Contract and legal document analysis

#### 2. Project Manager (Technical PM)
- **Model Preference:** GPT-5.2
- **Specialization:** SQL, data structures, planning, workflows
- **Focus:** Structure, organization, step-by-step execution
- **Use Cases:**
  - Database schema design
  - JSON/YAML data validation
  - Project planning and milestones
  - Process documentation

#### 3. Creative Director (Research Analyst)
- **Model Preference:** Gemini 3
- **Specialization:** Narrative writing, research synthesis, visual content
- **Focus:** Storytelling, synthesis, engaging presentation
- **Use Cases:**
  - Creative writing and narratives
  - Research paper analysis
  - Multi-source information synthesis
  - Visual content description

#### 4. News Analyst (Fact-Checking Journalist)
- **Model Preference:** Grok 4.1
- **Specialization:** Current events, social media, fact-checking
- **Focus:** Source verification, temporal awareness, bias detection
- **Use Cases:**
  - Real-time event monitoring
  - Social media sentiment analysis
  - Fact-checking with source attribution
  - Timeline reconstruction

#### 5. Efficiency Expert (Logic & Math Specialist)
- **Model Preference:** DeepSeek 3.2
- **Specialization:** Mathematics, logic, algorithms, general tasks
- **Focus:** Precision, clarity, step-by-step reasoning
- **Use Cases:**
  - Mathematical problem-solving
  - Logical reasoning and proofs
  - Algorithm optimization
  - Default fallback for unknown tasks

## Usage

### Basic Usage

```python
from rlm import PromptManager, ModelResolver

# Initialize PromptManager
pm = PromptManager()

# Get specialized system prompt
system_prompt = pm.get_system_message(
    role_id="architect",
    context_type="Python codebase",
    context_total_length=100000,
    context_lengths="[5000, 4500, 6000, ...]",
    hive_state={"patterns": ["Singleton", "Factory"]}
)

# Use with your LLM
llm.query(user_prompt, system_prompt=system_prompt)
```

### Model Resolution (Critical for Single-Key Users)

The ModelResolver ensures graceful degradation when preferred models aren't available:

```python
from rlm import ModelResolver

# Multi-key scenario
available = {"claude-opus-4.5", "gpt-5.2", "deepseek-3.2"}
resolver = ModelResolver(available)

# Resolve preferred model
resolved, was_fallback = resolver.resolve_model("gemini-3")
# Result: ("gpt-5.2", True) - fallback to next best

# Single-key scenario (most users!)
available = {"gpt-5.2"}
resolver = ModelResolver(available)

# ALL requests resolve to the same model
resolved, _ = resolver.resolve_model("claude-opus-4.5")
# Result: ("gpt-5.2", True) - uses what's available
```

### Complete Workflow

```python
from rlm import (
    route_text,
    map_routing_profile_to_persona,
    get_prompt_manager,
    get_model_resolver,
)

# 1. Smart Router determines profile
text = "class User: def __init__(self): pass"
model_id = route_text(text)  # Returns routing model ID

# 2. Map to persona
from rlm.routing import HeuristicRoutingEngine
engine = HeuristicRoutingEngine()
profile_name = engine.classify(text)  # "Architect"
role_id = map_routing_profile_to_persona(profile_name)  # "architect"

# 3. Get preferred model
pm = get_prompt_manager()
preferred_model = pm.get_model_preference(role_id)  # "claude-opus-4.5"

# 4. Resolve to available model
available = {"gpt-5.2", "deepseek-3.2"}
resolver = get_model_resolver(available)
resolved, fallback = resolver.resolve_model(preferred_model)
# Result: "gpt-5.2" (Claude not available)

# 5. Get specialized prompt
system_prompt = pm.get_system_message(
    role_id=role_id,
    context_type="code",
    context_total_length=len(text),
    context_lengths=str(len(text))
)

# 6. Query with resolved model and specialized prompt
# llm = model_map[resolved]
# response = llm.query(user_query, system_prompt=system_prompt)
```

## Persona Configuration (personas.yaml)

### Structure

```yaml
personas:
  role_id:
    role_id: "string"
    display_name: "Human Readable Name"
    description: "Brief description"
    model_preference: "preferred-model-id"
    system_prompt: |
      Multi-line system prompt
      with specialized instructions
    tools:
      - tool1
      - tool2
```

### Adding Custom Personas

You can extend personas.yaml with custom roles:

```yaml
personas:
  # ... existing personas ...
  
  data_scientist:
    role_id: "data_scientist"
    display_name: "Data Scientist"
    description: "Statistical analysis, ML models, data visualization"
    model_preference: "gpt-5.2"
    
    system_prompt: |
      You are a Data Scientist specializing in statistical analysis.
      
      **Core Competencies:**
      - Statistical hypothesis testing
      - Machine learning model selection
      - Data visualization best practices
      - Feature engineering
      
      **Standards:**
      - Always state assumptions clearly
      - Validate models with appropriate metrics
      - Consider data quality and bias
      
      **Available Tools:**
      - llm_query() for complex calculations
      - parallel_query() for batch data processing
      - hive for storing intermediate results
    
    tools:
      - llm_query
      - parallel_query
      - hive
      - print
      - context
```

## Dynamic Prompt Injection

The PromptManager automatically injects:

### 1. Context Information
```
**Context Information:**
- Type: list of Python files
- Total Length: 100,000 characters
- Chunk Distribution: [5000, 4500, 6000, ...]
```

### 2. Hive Memory State
```
**Current Hive Memory State:**
{
  "patterns_found": ["Singleton", "Factory"],
  "violations": 3,
  "key_files": ["core.py", "utils.py"]
}

This state is automatically available to all parallel_query sub-agents.
```

### 3. Tool Function Signatures
```
**Available Tools & Functions:**

**llm_query(prompt: str) -> str**
Query a sub-LLM for semantic analysis...

**parallel_query(prompt_template: str, chunks: List[str]) -> List[str]**
Process multiple chunks in parallel...
```

### 4. Trajectory Tracking Note
```
**Execution Tracking:**
All of your REPL code execution is tracked...
Use FINAL(answer) or FINAL_VAR(variable) when ready.
```

## Model Resolution Strategies

### Fallback Chains

Each model has a predefined fallback chain:

```python
FALLBACK_CHAINS = {
    'claude-opus-4.5': ['claude-opus-4.5', 'gpt-5.2', 'deepseek-3.2'],
    'gpt-5.2': ['gpt-5.2', 'claude-opus-4.5', 'deepseek-3.2'],
    'gemini-3': ['gemini-3', 'gpt-5.2', 'deepseek-3.2'],
    'grok-4.1': ['grok-4.1', 'gpt-5.2', 'deepseek-3.2'],
    'deepseek-3.2': ['deepseek-3.2', 'gpt-5.2', 'claude-opus-4.5'],
}
```

### Single-Key Bypass

When only one API key is available, ModelResolver:
1. Detects single-key mode
2. Skips fallback chain logic
3. Returns the only available model for ALL requests
4. Logs the bypass for transparency

This ensures Mosaic works perfectly even with just one API key!

### Resolution Priority

1. **Direct Match**: Preferred model is available → use it
2. **Single-Key Bypass**: Only one model available → use it
3. **Fallback Chain**: Try models in preference order
4. **Emergency Fallback**: Use any available model

## Best Practices

### 1. Initialize Once
```python
# At application startup
from rlm import get_prompt_manager, get_model_resolver

pm = get_prompt_manager()
available_models = {"gpt-5.2", "deepseek-3.2"}
resolver = get_model_resolver(available_models)

# Reuse throughout application
# No need to recreate
```

### 2. Always Use ModelResolver
```python
# ❌ Bad: Assume model is available
system_prompt = pm.get_system_message("architect")
llm = model_map["claude-opus-4.5"]  # Might not exist!

# ✅ Good: Resolve to available model
preferred = pm.get_model_preference("architect")
resolved, _ = resolver.resolve_model(preferred)
llm = model_map[resolved]
```

### 3. Provide Context Info
```python
# ❌ Minimal prompt
prompt = pm.get_system_message("architect")

# ✅ Rich prompt with context
prompt = pm.get_system_message(
    role_id="architect",
    context_type="Python codebase",
    context_total_length=100000,
    context_lengths="[5000, 4500, 6000]",
    hive_state=current_hive.get_all()
)
```

### 4. Log Fallbacks
```python
# Enable fallback logging for debugging
resolved, was_fallback = resolver.resolve_model(
    preferred_model,
    log_fallback=True  # Will print warnings
)

if was_fallback:
    print(f"Note: Using {resolved} instead of {preferred_model}")
```

## Integration with Existing Systems

### With Routing Engine
```python
from rlm import HeuristicRoutingEngine, map_routing_profile_to_persona

engine = HeuristicRoutingEngine()
profile = engine.classify(text)  # Returns profile name
role_id = map_routing_profile_to_persona(profile)
# Now use role_id with PromptManager
```

### With RLM Core
```python
from rlm import RLM, get_prompt_manager

pm = get_prompt_manager()

# Override system prompt in RLM
rlm = RLM(root_llm=llm, sub_llm=sub_llm)
custom_prompt = pm.get_system_message("architect", ...)
# Use custom_prompt in your workflow
```

### With Caching
```python
from rlm import get_cache

# Personas don't affect caching
# Cache key includes full prompt, so different personas
# will naturally have different cache entries
cache = get_cache()
response = llm.query(prompt, use_cache=True)
```

## Troubleshooting

### Issue: "Unknown persona role_id"
**Cause:** Invalid role_id provided
**Solution:** Use `pm.list_personas()` to see available options

### Issue: "No models available"
**Cause:** Empty available_models set
**Solution:** Ensure at least one API key is configured

### Issue: "personas.yaml not found"
**Cause:** File missing or wrong location
**Solution:** Provide explicit path: `PromptManager(personas_file="/path/to/personas.yaml")`

### Issue: Persona always uses wrong model
**Cause:** Not using ModelResolver
**Solution:** Always resolve models before using them

## Performance

- **Prompt Generation**: ~1-5ms (including YAML parse cache)
- **Model Resolution**: <1ms (hash table lookups)
- **Memory Overhead**: ~100KB for loaded personas
- **Singleton Pattern**: PromptManager and ModelResolver cached globally

## Examples

See `examples/persona_system_example.py` for:
1. Loading personas and exploring configurations
2. Getting specialized system prompts
3. Model resolution with multiple keys
4. Single-key mode handling
5. Complete routing-to-persona workflow
6. Persona comparisons

## Summary

The Persona System ensures:
- ✅ Each task gets a specialized, expert-level system prompt
- ✅ Works seamlessly with single or multiple API keys
- ✅ Graceful fallback when preferred models unavailable
- ✅ Easy integration with routing engine
- ✅ Customizable via YAML configuration
- ✅ Production-ready with caching and error handling

The combination of specialized prompts + intelligent model resolution makes Mosaic powerful even for users with just one API key!
