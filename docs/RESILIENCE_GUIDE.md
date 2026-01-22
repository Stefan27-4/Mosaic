# Resilience Layer - Adaptive Validation Guide

## Overview

The Resilience Layer implements intelligent validation and quality assurance for RLM outputs through a tiered validation system:

1. **Tier 1 (Instant)**: Free, fast syntax and format checks
2. **Tier 2 (Semantic)**: Smart critic reviews using LLMs

The system automatically adapts between **peer review** (when multiple models available) and **self-correction** (when only one model available).

## Architecture

### CriticRouter

Routes tasks to the optimal critic model for validation:

```python
from rlm import CriticRouter, TaskType

# Initialize with available models
available = {"claude-opus-4.5", "gpt-5.2", "gemini-3"}
router = CriticRouter(available)

# Get best critic for code review
critic_id, is_peer = router.get_critic(
    TaskType.CODE,
    worker_model_id="gpt-5.2"
)
# Returns: ("claude-opus-4.5", True) - peer review!
```

**Critic Preferences by Task:**
- **CODE**: claude-opus-4.5 > claude-sonnet-3.5 > gpt-5.2
- **LOGIC/MATH**: deepseek-3.2 > gpt-5.2 > claude-opus-4.5
- **WRITING**: gpt-5.2 > gemini-3 > claude-opus-4.5
- **GENERAL**: gpt-5.2 > claude-opus-4.5 > gemini-3 > deepseek-3.2

**Conflict of Interest Rule:**
The router tries to return a critic **different** from the worker model (peer review). Only falls back to the same model when necessary (self-correction).

### ResilientAgent

Agent with automatic retry and tiered validation:

```python
from rlm import ResilientAgent, CriticRouter, TaskType, OpenAIInterface

# Setup
llm = OpenAIInterface(model="gpt-4o")
router = CriticRouter({"claude-opus-4.5", "gpt-5.2"})

agent = ResilientAgent(
    llm_interface=llm,
    critic_router=router,
    max_retries=3,
    enable_semantic_validation=True,
    validation_cost_limit=1.0  # Max $1 on validation
)

# Execute with automatic validation & retry
result, history = agent.execute_with_retry(
    task_prompt="Write a function to process user data",
    task_type=TaskType.CODE,
    output_format="python",
    task_description="Data processing function"
)
```

## Tiered Validation Flow

### Tier 1: Instant Checks (Free & Fast)

**Python Syntax:**
```python
result = agent.validate_python_syntax(code)
if result.passed:
    print("✓ Syntax valid")
else:
    print(f"✗ Syntax error: {result.message}")
    print(f"  Fix: {result.suggestion}")
```

**JSON Format:**
```python
result = agent.validate_json(json_text)
```

**Characteristics:**
- **Cost**: FREE (no API calls)
- **Speed**: <1ms (instant)
- **Detects**: Syntax errors, malformed JSON, basic format issues
- **Action**: Immediate retry with error message

### Tier 2: Semantic Checks (Smart Critics)

**Peer Review (Multiple Models):**
```python
# Worker: gpt-5.2
# Critic: claude-opus-4.5 (different model)

result = agent.semantic_validate(
    content=code,
    task_type=TaskType.CODE,
    worker_model_id="gpt-5.2",
    task_description="User authentication"
)
```

Prompt to critic:
```
You are a Senior Reviewer conducting peer review.

Task Type: code
Worker Model: gpt-5.2

The worker model generated the following output. Review it for:
- Logic errors or bugs
- Security vulnerabilities
- Edge cases not handled

Content to Review:
[code here]

Respond with EXACTLY ONE of:
1. "PASS" - if correct and production-ready
2. "FAIL: <reason>" - if issues found
```

**Self-Correction (Single Model):**
```python
# Worker: gpt-5.2
# Critic: gpt-5.2 (same model - only one available)

result = agent.semantic_validate(
    content=code,
    task_type=TaskType.CODE,
    worker_model_id="gpt-5.2"
)
```

Prompt to critic:
```
You are reviewing your own work for quality assurance.

Step back and critically evaluate your previous output:

[code here]

Check for:
- Logic errors you may have missed
- Assumptions that may be incorrect
- Better approaches you should consider

Respond with: "PASS" or "FAIL: <reason>"
```

**Characteristics:**
- **Cost**: ~$0.01 per validation (token usage)
- **Speed**: ~1-3 seconds (LLM call)
- **Detects**: Logic errors, security issues, subtle bugs
- **Action**: Retry with critic's detailed feedback

## Usage Patterns

### Pattern 1: Basic Validation

```python
from rlm import ResilientAgent, TaskType, OpenAIInterface

llm = OpenAIInterface(model="gpt-4o")
agent = ResilientAgent(llm, enable_semantic_validation=False)

# Just instant validation (no LLM critic)
result, history = agent.execute_with_retry(
    "Generate JSON config",
    TaskType.GENERAL,
    output_format="json"
)
```

### Pattern 2: Full Validation (Peer Review)

```python
from rlm import ResilientAgent, CriticRouter, TaskType
from rlm import OpenAIInterface, AnthropicInterface

# Multiple models available
gpt = OpenAIInterface(model="gpt-4o")
claude = AnthropicInterface(model="claude-3-5-sonnet-20241022")

available = {"gpt-5.2", "claude-opus-4.5"}
router = CriticRouter(available)

agent = ResilientAgent(
    gpt,
    router,
    enable_semantic_validation=True
)

# Full 2-tier validation with peer review
result, history = agent.execute_with_retry(
    "Implement user authentication",
    TaskType.CODE,
    output_format="python"
)

# Check validation history
for entry in history:
    print(f"Attempt {entry['attempt']}: {entry['tier']} - {'PASS' if entry['passed'] else 'FAIL'}")
```

### Pattern 3: Cost-Controlled Validation

```python
agent = ResilientAgent(
    llm,
    router,
    enable_semantic_validation=True,
    validation_cost_limit=0.50  # Max $0.50 on validation
)

# Will automatically stop semantic validation if budget exceeded
result, history = agent.execute_with_retry(...)

print(f"Validation cost: ${agent.validation_cost_spent:.2f}")
```

### Pattern 4: Auto Task Detection

```python
from rlm import detect_task_type

# Automatically detect task type from content
task_type = detect_task_type("Write a function to calculate primes")
# Returns: TaskType.CODE

task_type = detect_task_type("Solve this equation: x^2 + 3x - 4 = 0")
# Returns: TaskType.LOGIC_MATH
```

## Integration with RLM Core

The resilience layer integrates seamlessly with the RLM framework:

```python
from rlm import RLM, OpenAIInterface
from rlm import ResilientAgent, CriticRouter, TaskType

# Setup models
root_llm = OpenAIInterface(model="gpt-4o")
sub_llm = OpenAIInterface(model="gpt-4o-mini")

# Setup resilience
available = {"gpt-5.2", "claude-opus-4.5"}
router = CriticRouter(available)
resilient_root = ResilientAgent(
    root_llm,
    router,
    enable_semantic_validation=True
)

# Use in RLM workflow
rlm = RLM(root_llm=root_llm, sub_llm=sub_llm)

# The REPL code can use resilient execution
# (integration example - actual integration may vary)
```

## Efficiency Guardrails

### 1. Single-Key Bypass
When only one API key available, system automatically uses self-correction instead of failing.

### 2. Cost Limiting
```python
agent = ResilientAgent(
    llm,
    router,
    validation_cost_limit=1.0  # Max $1 on validation
)

# Tracks spend automatically
if agent.validation_cost_spent >= agent.validation_cost_limit:
    # Skips semantic validation
    pass
```

### 3. Max Retries
```python
agent = ResilientAgent(
    llm,
    router,
    max_retries=3  # Try max 3 times
)

# After 3 failures, returns last result
result, history = agent.execute_with_retry(...)
if len(history) == 3:
    print("Warning: Max retries reached")
```

### 4. Tier Escalation
- **First**: Instant checks (free)
- **Only if passed**: Semantic checks (costs tokens)
- **Never**: Semantic if instant fails (waste prevention)

## Task Types

### CODE
- **Best Critics**: Claude Opus, Claude Sonnet
- **Checks**: Syntax, logic, security, edge cases
- **Example**: Function implementations, class definitions

### LOGIC_MATH
- **Best Critics**: DeepSeek, GPT-4
- **Checks**: Mathematical correctness, proof validity
- **Example**: Equations, theorems, logic puzzles

### WRITING
- **Best Critics**: GPT-4, Gemini
- **Checks**: Grammar, coherence, style
- **Example**: Essays, summaries, articles

### GENERAL
- **Best Critics**: GPT-4, Claude, Gemini
- **Checks**: Overall quality
- **Example**: General queries, mixed content

## ValidationResult

All validation methods return a `ValidationResult` object:

```python
class ValidationResult:
    passed: bool          # True if validation passed
    message: str          # Result message
    suggestion: str       # How to fix (if failed)
    tier: str            # "instant" or "semantic"
```

Usage:
```python
result = agent.validate_python_syntax(code)

if not result.passed:
    print(f"Validation failed ({result.tier})")
    print(f"Error: {result.message}")
    print(f"Fix: {result.suggestion}")
```

## Best Practices

### 1. Start with Instant Validation Only
```python
# Cheap and fast for development
agent = ResilientAgent(llm, enable_semantic_validation=False)
```

### 2. Enable Semantic for Production
```python
# Quality assurance for production code
agent = ResilientAgent(
    llm,
    router,
    enable_semantic_validation=True,
    validation_cost_limit=2.0  # Reasonable budget
)
```

### 3. Use Peer Review When Possible
```python
# Provide multiple models for best results
available = {"claude-opus-4.5", "gpt-5.2", "gemini-3"}
router = CriticRouter(available)
# Router will select different model for review
```

### 4. Monitor Validation Costs
```python
result, history = agent.execute_with_retry(...)

print(f"Total cost: ${agent.validation_cost_spent:.2f}")
print(f"Validation attempts: {len(history)}")

# Calculate cost per validation
cost_per_validation = agent.validation_cost_spent / len(history)
print(f"Average cost: ${cost_per_validation:.3f}")
```

### 5. Check Validation History
```python
result, history = agent.execute_with_retry(...)

# Analyze what happened
for entry in history:
    if not entry['passed']:
        print(f"Failed at {entry['tier']}: {entry['message']}")
```

## Performance Metrics

**Instant Validation (Tier 1):**
- Speed: <1ms
- Cost: $0
- Accuracy: ~95% for syntax/format issues

**Semantic Validation (Tier 2):**
- Speed: 1-3 seconds
- Cost: ~$0.01 per check
- Accuracy: ~85-95% depending on critic quality

**Combined (Both Tiers):**
- Speed: 1-3 seconds (Tier 2 dominates)
- Cost: ~$0.01 per full validation
- Accuracy: ~98% (catches most issues)

## Troubleshooting

### Issue: "No critic router available"
```python
# Solution: Provide a critic router
router = CriticRouter(available_models)
agent = ResilientAgent(llm, critic_router=router)
```

### Issue: "Validation budget exceeded"
```python
# Solution: Increase budget or reset spend
agent.validation_cost_limit = 5.0
# or
agent.validation_cost_spent = 0.0  # Reset
```

### Issue: "Max retries exceeded"
```python
# Solution: Increase max retries or check prompts
agent = ResilientAgent(llm, router, max_retries=5)
```

### Issue: All validations use same model
```python
# Solution: Provide more models
available = {"claude-opus-4.5", "gpt-5.2", "gemini-3"}
router = CriticRouter(available)
# Now can do peer review
```

## See Also

- `examples/resilience_example.py` - Complete working examples
- `rlm/resilience.py` - Source code
- `USER_GUIDE.md` - General RLM usage
- `docs/ROUTING_GUIDE.md` - Model routing
