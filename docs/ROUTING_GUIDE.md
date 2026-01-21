# Heuristic Routing Engine Guide

## Overview

The Heuristic Routing Engine is a deterministic, keyword-density scoring algorithm that analyzes text chunks and automatically assigns them to the optimal AI model based on their "Feature Fingerprints." Unlike LLM-based routing, this system uses pure algorithmic analysis for fast, consistent, and cost-free routing decisions.

## Key Features

- **Deterministic**: Same input always produces the same output
- **Fast**: No API calls required - pure algorithmic processing
- **Cost-Free**: No additional LLM queries for routing decisions
- **Customizable**: Define your own profiles and keywords
- **Transparent**: Full visibility into scoring and confidence levels

## How It Works

### 1. Tokenization
Text is split into lowercase tokens for analysis, extracting meaningful words while ignoring punctuation.

### 2. Keyword Matching
Each specialist profile contains weighted keywords:
- **Strong indicators** (weight 2.0): High confidence signals like `class`, `def`, `SELECT`
- **Medium indicators** (weight 1.5): Moderate signals like `function`, `schema`
- **Weak indicators** (weight 0.5-1.0): Common words with lower confidence

### 3. Scoring
For each profile, the engine:
1. Counts keyword occurrences in the text
2. Multiplies counts by keyword weights
3. Normalizes by text length to get density
4. Produces a confidence score (0.0 to 1.0)

### 4. Routing Decision
- Profile with highest score wins
- If max score < threshold (default 0.3), falls back to default model
- Default is DeepSeek 3.2 (most cost-effective generalist)

## The 5 Specialist Profiles

### Profile A: "Architect" → Claude Opus 4.5

**Use Case**: Deep coding refactors, multi-file architecture, complex legal reasoning

**Feature Fingerprints**:
- **Coding**: `class`, `def`, `import`, `return`, `async`, `await`, `interface`
- **Legal**: `section`, `clause`, `agreement`, `hereby`, `terms`, `contract`
- **Indicators**: High density of indentation, brackets `{}`, structured code

**Example Text**:
```python
class DataProcessor:
    def __init__(self):
        import pandas as pd
        self.data = pd.DataFrame()
    
    async def process(self):
        return await self.fetch_data()
```

### Profile B: "Project Manager" → GPT-5.2

**Use Case**: SQL database management, JSON data structuring, step-by-step planning

**Feature Fingerprints**:
- **Database**: `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `JOIN`, `schema`, `table`
- **Data**: `json`, `yaml`, `xml`, key-value pairs
- **Planning**: `step`, `phase`, `milestone`, `deliverable`, `workflow`, `roadmap`

**Example Text**:
```sql
SELECT users.name, COUNT(orders.id)
FROM users
JOIN orders ON users.id = orders.user_id
GROUP BY users.name
```

### Profile C: "Creative Director" → Gemini 3

**Use Case**: Narrative writing, research summarization, visual/multimodal descriptions

**Feature Fingerprints**:
- **Narrative**: `story`, `character`, `plot`, `theme`, `chapter`, `scene`
- **Visuals**: `image`, `video`, `slide`, `presentation`, `graph`, `chart`
- **Research**: `study`, `findings`, `abstract`, `conclusion`, `literature review`

**Example Text**:
```
The narrative unfolds as the character discovers the main theme.
This chapter presents findings from the research study, with
visualizations including graphs and charts in the presentation.
```

### Profile D: "News Analyst" → Grok 4.1

**Use Case**: Real-time events, social media sentiment, conversational tasks

**Feature Fingerprints**:
- **Temporal**: `today`, `yesterday`, `current`, `breaking`, `live`, `2026`
- **Social**: `twitter`, `x.com`, `trend`, `viral`, `sentiment`, `hashtag`
- **Tone**: Conversational markers, slang, `roast`, `joke`

**Example Text**:
```
Breaking news today! Latest update went viral on Twitter.
Current sentiment shows this trend is the biggest story of 2026.
```

### Profile E: "Efficiency Expert" → DeepSeek 3.2

**Use Case**: Pure logic puzzles, math equations, text formatting, default fallback

**Feature Fingerprints**:
- **Math**: `latex`, `equation`, `theorem`, `proof`, `calculate`, `integral`
- **Logic**: `syllogism`, `logic puzzle`, `if...then` constructs
- **Default**: Used when no other profile matches strongly

**Example Text**:
```
Theorem: For all x, the equation holds. Proof: Calculate the
integral and solve for the derivative using this formula.
```

## Basic Usage

### Simple Routing

```python
from rlm import route_text

# Automatic routing
text = "SELECT * FROM users WHERE active = true"
model_id = route_text(text)  # Returns: "gpt-5.2"
```

### Detailed Routing

```python
from rlm import HeuristicRoutingEngine

engine = HeuristicRoutingEngine()

text = "class MyApp: def process(): return data"
result = engine.route_with_details(text)

print(f"Model: {result['model_id']}")           # "claude-opus-4.5"
print(f"Profile: {result['profile_name']}")     # "Architect"
print(f"Confidence: {result['confidence']}")    # 0.85
print(f"All scores: {result['all_scores']}")    # {...}
```

### Batch Routing

```python
from rlm import HeuristicRoutingEngine

engine = HeuristicRoutingEngine()

chunks = [
    "def calculate(): return sum",
    "SELECT * FROM table",
    "Once upon a time...",
]

for chunk in chunks:
    model_id, scores = engine.route(chunk)
    print(f"{chunk[:20]}... → {model_id}")
```

## Advanced Usage

### Custom Profiles

Create your own specialist profiles:

```python
from rlm import HeuristicRoutingEngine, ProfileConfig

# Define custom profile
medical_profile = ProfileConfig(
    name="Medical Specialist",
    model_id="custom-medical-gpt",
    keywords={
        "patient": 2.0,
        "diagnosis": 2.0,
        "treatment": 1.5,
        "symptom": 1.5,
        "prescription": 2.0,
    }
)

# Use custom profile
engine = HeuristicRoutingEngine(
    profiles=[medical_profile, PROFILE_ARCHITECT],
    threshold=0.3
)

text = "Patient diagnosis requires treatment and prescription"
result = engine.route_with_details(text)
# Routes to "custom-medical-gpt"
```

### Custom Thresholds

Adjust the confidence threshold:

```python
# Low threshold - more aggressive routing
engine_aggressive = HeuristicRoutingEngine(threshold=0.1)

# High threshold - more conservative, uses fallback more
engine_conservative = HeuristicRoutingEngine(threshold=0.7)

# Custom default fallback
engine_custom = HeuristicRoutingEngine(
    threshold=0.4,
    default_model_id="my-default-model"
)
```

### Integration with RLM

Use routing to select sub-LLMs dynamically:

```python
from rlm import RLM, HeuristicRoutingEngine
from rlm.llm_interface import OpenAIInterface

# Create model pool
models = {
    "gpt-5.2": OpenAIInterface(model="gpt-4o"),
    "claude-opus-4.5": AnthropicInterface(model="claude-3-opus"),
    "deepseek-3.2": OpenAIInterface(model="gpt-4o-mini"),
}

router = HeuristicRoutingEngine()

def smart_llm_query(text):
    """Route to optimal model based on content."""
    model_id = router.route(text)[0]
    llm = models.get(model_id, models["deepseek-3.2"])
    return llm.query(text)

# Use in RLM with routing
rlm = RLM(
    root_llm=models["gpt-5.2"],
    sub_llm=None  # Can override llm_query in REPL
)
```

## Configuration Examples

### Use Case: Multi-Domain Application

```python
from rlm import (
    HeuristicRoutingEngine,
    PROFILE_ARCHITECT,
    PROFILE_PROJECT_MANAGER,
    PROFILE_CREATIVE_DIRECTOR,
)

# Technical content only
tech_router = HeuristicRoutingEngine(
    profiles=[PROFILE_ARCHITECT, PROFILE_PROJECT_MANAGER],
    threshold=0.25
)

# Creative content only
creative_router = HeuristicRoutingEngine(
    profiles=[PROFILE_CREATIVE_DIRECTOR],
    threshold=0.2,
    default_model_id="gemini-3"  # Default to creative
)
```

### Use Case: Cost Optimization

```python
# Route aggressively to cheaper models
cost_optimizer = HeuristicRoutingEngine(
    threshold=0.5,  # Higher threshold
    default_model_id="deepseek-3.2"  # Cheapest default
)

# Only use expensive models for clear matches
result = cost_optimizer.route_with_details(text)
if not result['is_fallback']:
    # High confidence - use specialized model
    use_model(result['model_id'])
else:
    # Low confidence - use cheap default
    use_model("deepseek-3.2")
```

## Performance Characteristics

### Speed
- **~0.1-1ms** per routing decision
- **No network latency** (pure local computation)
- **Parallelizable** (no shared state)

### Accuracy
- **High precision** for texts with clear domain signals
- **Graceful fallback** for ambiguous content
- **Customizable** via threshold tuning

### Cost
- **Zero API costs** for routing
- **Deterministic** (cacheable results for identical inputs)

## Best Practices

### 1. Tune Thresholds for Your Use Case

```python
# Experiment with different thresholds
for threshold in [0.1, 0.3, 0.5, 0.7]:
    engine = HeuristicRoutingEngine(threshold=threshold)
    result = engine.route_with_details(sample_text)
    print(f"Threshold {threshold}: {result['model_id']}")
```

### 2. Monitor Confidence Scores

```python
result = engine.route_with_details(text)
if result['confidence'] < 0.2:
    # Very low confidence - might want human review
    log_uncertain_routing(text, result)
```

### 3. Use Appropriate Profiles

Only include profiles relevant to your domain:

```python
# For code-only application
code_router = HeuristicRoutingEngine(
    profiles=[PROFILE_ARCHITECT, PROFILE_PROJECT_MANAGER],
    threshold=0.3
)
```

### 4. Cache Routing Results

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_route(text: str) -> str:
    return route_text(text)
```

## Troubleshooting

### Issue: Always routing to fallback

**Solution**: Lower the threshold or add more keywords to profiles

```python
engine = HeuristicRoutingEngine(threshold=0.2)  # Lower threshold
```

### Issue: Wrong model selected

**Solution**: Check keyword weights and add domain-specific keywords

```python
# Add custom keywords for your domain
custom_profile = ProfileConfig(
    name="Custom",
    model_id="custom-model",
    keywords={
        "domain_keyword_1": 2.0,
        "domain_keyword_2": 1.5,
    }
)
```

### Issue: Ambiguous routing

**Solution**: Increase threshold or examine all scores

```python
result = engine.route_with_details(text)
print("All scores:", result['all_scores'])
# Review which profiles are competing
```

## Comparison with LLM-Based Routing

| Aspect | Heuristic Routing | LLM-Based Routing |
|--------|------------------|-------------------|
| Speed | ~1ms | ~500-2000ms |
| Cost | Free | $0.001-0.01 per route |
| Consistency | 100% deterministic | Variable |
| Customization | Keywords/weights | Prompt engineering |
| Transparency | Full score visibility | Black box |
| Context understanding | Keyword-based | Semantic |

**When to use Heuristic Routing:**
- Need fast, consistent decisions
- Cost is a concern
- Clear keyword-based domains
- Require transparency/auditability

**When to use LLM-Based Routing:**
- Need semantic understanding
- Ambiguous/nuanced content
- Willing to pay for better accuracy
- Complex multi-domain routing

## API Reference

### `route_text(text_chunk: str, threshold: float = 0.3) -> str`

Simple routing function.

**Returns**: Model identifier string

### `HeuristicRoutingEngine`

Main routing engine class.

**Methods**:
- `route(text_chunk) -> (model_id, scores_dict)`
- `route_with_details(text_chunk) -> dict`
- `calculate_score(text, profile) -> float`

### `ProfileConfig`

Profile configuration class.

**Parameters**:
- `name`: Profile name
- `model_id`: Target model identifier
- `keywords`: Dict of keyword -> weight

## Examples

See `examples/routing_example.py` for complete working examples.

## Future Enhancements

Potential improvements:
- N-gram keyword matching
- Regex pattern support
- Learning-based weight tuning
- Multi-language support
- Composite scoring (structure + keywords)
