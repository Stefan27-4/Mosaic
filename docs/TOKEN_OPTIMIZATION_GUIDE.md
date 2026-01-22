# Token Optimization Guide

## Overview

The Token Optimization Layer provides accurate token counting using `tiktoken` and dynamic chunk size calculation based on model capacity. This system automatically optimizes chunk sizes to match model capabilities, improving both performance and cost efficiency.

## Architecture

### Components

1. **TokenGatekeeper**: Accurate token counting and cost estimation
2. **ChunkAutoTuner**: Dynamic chunk size calculation
3. **Model Specifications**: Comprehensive model capacity database

## TokenGatekeeper

The `TokenGatekeeper` class provides precise token counting using OpenAI's `tiktoken` library and cost estimation based on model pricing.

### Features

- **Singleton Pattern**: Encoders loaded once for efficiency
- **Model-Specific Encoding**: Uses appropriate encoder for each model
- **Fallback Handling**: Defaults to `cl100k_base` for unknown models
- **Cost Estimation**: Calculates projected API costs

### Supported Models

| Model ID | Context Limit | Cost per 1M Tokens |
|----------|--------------|-------------------|
| claude-opus-4.5 | 200,000 | $15.00 |
| gpt-5.2 (gpt-4o) | 128,000 | $5.00 |
| gemini-3 (gemini-1.5-pro) | 2,000,000 | $1.25 |
| grok-4.1 | 128,000 | $2.00 |
| deepseek-3.2 | 64,000 | $0.50 |

### Usage

```python
from rlm import TokenGatekeeper, count_tokens, estimate_cost, get_model_limit

# Get the global instance
gatekeeper = TokenGatekeeper()

# Count tokens
text = "Hello, world! This is a test."
token_count = gatekeeper.count(text, model="gpt-4o")
print(f"Tokens: {token_count}")

# Or use convenience function
token_count = count_tokens(text, model="gpt-4o")

# Get model context limit
limit = gatekeeper.get_limit("gpt-4o")
print(f"GPT-4o context limit: {limit:,} tokens")

# Or use convenience function
limit = get_model_limit("gpt-4o")

# Estimate cost
cost = gatekeeper.estimate_cost(text, model="gpt-4o")
print(f"Estimated cost: ${cost:.6f}")

# Or use convenience function
cost = estimate_cost(text, model="gpt-4o")
```

### Methods

#### `count(text: str, model: str) -> int`

Count tokens in text using the appropriate encoder.

**Parameters:**
- `text`: Text to count tokens for
- `model`: Model identifier

**Returns:** Precise token count

**Example:**
```python
gatekeeper = TokenGatekeeper()
tokens = gatekeeper.count("Hello world", "gpt-4o")
```

#### `get_limit(model: str) -> int`

Get the context limit for a model.

**Parameters:**
- `model`: Model identifier

**Returns:** Context limit in tokens

**Example:**
```python
limit = gatekeeper.get_limit("claude-opus-4.5")
print(f"Claude Opus can handle {limit:,} tokens")
```

#### `estimate_cost(text: str, model: str) -> float`

Estimate the cost of processing text.

**Parameters:**
- `text`: Text to estimate cost for
- `model`: Model identifier

**Returns:** Estimated cost in USD

**Example:**
```python
cost = gatekeeper.estimate_cost(large_document, "gpt-4o")
print(f"Processing will cost approximately ${cost:.2f}")
```

## ChunkAutoTuner

The `ChunkAutoTuner` class calculates optimal chunk sizes based on model capacity and task type.

### Task Types

```python
from rlm import OptTaskType

# Available task types
OptTaskType.CODE_ANALYSIS    # 80% of available context
OptTaskType.SUMMARIZATION    # 20% of available context
OptTaskType.GENERAL          # 40% of available context
```

### Chunk Size Calculation

The auto-tuner follows this algorithm:

1. **Get Model Limit**: Fetch the model's context window size
2. **Reserve Buffer**: Subtract 4,000 tokens for system prompt + response
3. **Apply Task Multiplier**:
   - CODE_ANALYSIS: 80% (needs large context)
   - SUMMARIZATION: 20% (smaller chunks are faster)
   - GENERAL: 40% (balanced approach)
4. **Clamp Values**: Ensure 1,000 ≤ chunk_size ≤ 100,000

### Usage

```python
from rlm import ChunkAutoTuner, OptTaskType, calculate_chunk_size

# Get the global instance
tuner = ChunkAutoTuner()

# Calculate optimal chunk size
chunk_size = tuner.calculate_optimal_chunk_size(
    model_id="gpt-4o",
    task_type=OptTaskType.CODE_ANALYSIS
)
print(f"Optimal chunk size: {chunk_size:,} tokens")

# Or use convenience function
chunk_size = calculate_chunk_size("gpt-4o", OptTaskType.SUMMARIZATION)

# Get optimally-sized chunks
text = "...very long document..."
chunks = tuner.get_optimal_chunks(
    text=text,
    model_id="gpt-4o",
    task_type=OptTaskType.GENERAL,
    overlap_ratio=0.1  # 10% overlap
)
print(f"Split into {len(chunks)} chunks")
```

### Chunk Size Examples

For **GPT-4o** (128,000 token limit):

- Available after buffer: 124,000 tokens
- CODE_ANALYSIS: 99,200 tokens (80%)
- SUMMARIZATION: 24,800 tokens (20%)
- GENERAL: 49,600 tokens (40%)

For **Gemini 1.5 Pro** (2,000,000 token limit):

- Available after buffer: 1,996,000 tokens
- CODE_ANALYSIS: 100,000 tokens (clamped at max)
- SUMMARIZATION: 100,000 tokens (clamped at max)
- GENERAL: 100,000 tokens (clamped at max)

For **DeepSeek 3.2** (64,000 token limit):

- Available after buffer: 60,000 tokens
- CODE_ANALYSIS: 48,000 tokens (80%)
- SUMMARIZATION: 12,000 tokens (20%)
- GENERAL: 24,000 tokens (40%)

### Methods

#### `calculate_optimal_chunk_size(model_id: str, task_type: OptTaskType) -> int`

Calculate the optimal chunk size for a model and task.

**Parameters:**
- `model_id`: Model identifier
- `task_type`: Type of task

**Returns:** Optimal chunk size in tokens

**Example:**
```python
tuner = ChunkAutoTuner()
size = tuner.calculate_optimal_chunk_size("gpt-4o", OptTaskType.CODE_ANALYSIS)
```

#### `get_optimal_chunks(text: str, model_id: str, task_type: OptTaskType, overlap_ratio: float) -> list`

Split text into optimally-sized chunks.

**Parameters:**
- `text`: Text to split
- `model_id`: Model identifier
- `task_type`: Type of task
- `overlap_ratio`: Overlap between chunks (0.0 to 0.5)

**Returns:** List of text chunks

**Example:**
```python
chunks = tuner.get_optimal_chunks(
    text=document,
    model_id="gpt-4o",
    task_type=OptTaskType.SUMMARIZATION,
    overlap_ratio=0.15  # 15% overlap
)
```

## Convenience Functions

The module provides convenient top-level functions:

```python
from rlm import (
    count_tokens,
    estimate_cost,
    get_model_limit,
    calculate_chunk_size,
    smart_chunk_text,
)

# Count tokens
tokens = count_tokens("Hello world", "gpt-4o")

# Estimate cost
cost = estimate_cost(document, "gpt-4o")

# Get model limit
limit = get_model_limit("claude-opus-4.5")

# Calculate optimal chunk size
chunk_size = calculate_chunk_size("gpt-4o", OptTaskType.GENERAL)

# Smart chunking (all-in-one)
chunks = smart_chunk_text(
    text=document,
    model="gpt-4o",
    task_type=OptTaskType.SUMMARIZATION,
    overlap_ratio=0.1
)
```

## Integration Examples

### Example 1: Document Processing

```python
from rlm import smart_chunk_text, OptTaskType, count_tokens, estimate_cost

# Load document
with open("large_document.txt") as f:
    document = f.read()

# Check token count
total_tokens = count_tokens(document, "gpt-4o")
print(f"Document has {total_tokens:,} tokens")

# Estimate cost
cost = estimate_cost(document, "gpt-4o")
print(f"Direct processing would cost ~${cost:.2f}")

# Smart chunking for summarization
chunks = smart_chunk_text(
    text=document,
    model="gpt-4o",
    task_type=OptTaskType.SUMMARIZATION,
    overlap_ratio=0.1
)

print(f"Split into {len(chunks)} chunks")
print(f"Average chunk size: {total_tokens // len(chunks):,} tokens")
```

### Example 2: Code Analysis

```python
from rlm import ChunkAutoTuner, OptTaskType, count_tokens

# Load source code
with open("large_codebase.py") as f:
    code = f.read()

tuner = ChunkAutoTuner()

# Calculate optimal size for code analysis
optimal_size = tuner.calculate_optimal_chunk_size(
    model_id="claude-opus-4.5",
    task_type=OptTaskType.CODE_ANALYSIS
)

print(f"Optimal chunk size for code: {optimal_size:,} tokens")

# Split code into chunks
chunks = tuner.get_optimal_chunks(
    text=code,
    model_id="claude-opus-4.5",
    task_type=OptTaskType.CODE_ANALYSIS,
    overlap_ratio=0.05  # Small overlap for code
)

# Process each chunk
for i, chunk in enumerate(chunks):
    tokens = count_tokens(chunk, "claude-opus-4.5")
    print(f"Chunk {i+1}: {tokens:,} tokens")
```

### Example 3: Cost-Aware Processing

```python
from rlm import get_model_limit, count_tokens, estimate_cost

models = ["gpt-4o", "gpt-4o-mini", "claude-opus-4.5", "deepseek-3.2"]
document = "..." # Large document

print("Model Comparison:")
print("-" * 60)

for model in models:
    tokens = count_tokens(document, model)
    cost = estimate_cost(document, model)
    limit = get_model_limit(model)
    
    fits = tokens <= limit
    status = "✓ Fits" if fits else "✗ Too large"
    
    print(f"{model:20} | {tokens:8,} tokens | ${cost:8.4f} | {status}")
```

## Performance Tips

### 1. Reuse Encoders

The `TokenGatekeeper` uses a singleton pattern and caches encoders. Reuse the global instance:

```python
from rlm import get_token_gatekeeper

gatekeeper = get_token_gatekeeper()  # Reuses cached encoders
```

### 2. Batch Token Counting

When processing multiple texts, count them sequentially to leverage encoder caching:

```python
from rlm import count_tokens

documents = [doc1, doc2, doc3]
model = "gpt-4o"

total_tokens = sum(count_tokens(doc, model) for doc in documents)
```

### 3. Choose Appropriate Task Types

- Use `CODE_ANALYSIS` for large context needs (code review, architecture)
- Use `SUMMARIZATION` for parallel processing (many small chunks)
- Use `GENERAL` for balanced workloads

### 4. Optimize Overlap

- High overlap (20-30%): Better context continuity, more tokens/cost
- Low overlap (5-10%): Less redundancy, lower cost
- No overlap (0%): Maximum efficiency, may lose context

## Troubleshooting

### Issue: "Could not load tiktoken encoder"

**Cause:** tiktoken not installed or incompatible version

**Solution:**
```bash
pip install --upgrade tiktoken>=0.5.0
```

### Issue: Inaccurate token counts

**Cause:** Using wrong model identifier

**Solution:** Ensure you're using the actual model name:
```python
# Correct
count_tokens(text, "gpt-4o")

# Wrong
count_tokens(text, "gpt-5.2")  # Use actual model name
```

### Issue: Chunks too large/small

**Cause:** Wrong task type selected

**Solution:** Choose appropriate task type:
```python
from rlm import OptTaskType

# For code with large context needs
OptTaskType.CODE_ANALYSIS

# For parallel summarization
OptTaskType.SUMMARIZATION

# For general use
OptTaskType.GENERAL
```

## Best Practices

1. **Always use accurate token counting** for production workloads
2. **Match task type to your use case** for optimal chunking
3. **Test different overlap ratios** to find the sweet spot
4. **Monitor costs** using `estimate_cost()` before processing
5. **Check model limits** with `get_model_limit()` before chunking
6. **Use smart_chunk_text()** for convenience in most cases
7. **Cache tokenizer instances** by using the global functions

## API Reference Summary

### Classes

- `TokenGatekeeper`: Accurate token counting and cost estimation
- `ChunkAutoTuner`: Dynamic chunk size calculation

### Enums

- `OptTaskType`: CODE_ANALYSIS, SUMMARIZATION, GENERAL

### Functions

- `count_tokens(text, model)`: Count tokens
- `estimate_cost(text, model)`: Estimate cost
- `get_model_limit(model)`: Get context limit
- `calculate_chunk_size(model, task_type)`: Calculate optimal size
- `smart_chunk_text(text, model, task_type, overlap_ratio)`: Smart chunking
- `get_token_gatekeeper()`: Get global TokenGatekeeper
- `get_chunk_auto_tuner()`: Get global ChunkAutoTuner

### Constants

- `MODEL_SPECS`: Dictionary of (context_limit, cost_per_million) tuples
