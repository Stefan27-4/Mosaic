# Asynchronous MapReduce (Parallel Execution)

## Overview

The RLM framework now supports **parallel processing** of multiple text chunks through the `parallel_query()` function. This enables dramatic speed improvements when analyzing large datasets by processing chunks simultaneously instead of sequentially.

## Key Features

### 1. Async Adapter Layer

All LLM interfaces now support asynchronous operations:

```python
# Synchronous (original)
response = llm.query("prompt")

# Asynchronous (new)
response = await llm.query_async("prompt")
```

**Supported Interfaces:**
- `OpenAIInterface` - Uses `AsyncOpenAI` client
- `AnthropicInterface` - Uses `AsyncAnthropic` client  
- `GeminiInterface` - Uses `generate_content_async` method

### 2. The `parallel_query()` Function

A new REPL environment function that processes multiple chunks in parallel:

```python
# Function signature
parallel_query(prompt_template: str, context_chunks: list[str]) -> list[str]
```

**Parameters:**
- `prompt_template`: Template string with `{chunk}` placeholder
- `context_chunks`: List of text chunks to process

**Returns:**
- List of responses in the same order as input chunks

**Example:**
```python
summaries = parallel_query("Summarize this: {chunk}", documents)
# Returns: ["Summary 1", "Summary 2", ...]
```

### 3. Automatic Concurrency Control

Built-in semaphore prevents API rate limiting:

```python
rlm = RLM(
    root_llm=OpenAIInterface(model="gpt-4o"),
    sub_llm=OpenAIInterface(model="gpt-4o-mini"),
    max_parallel_calls=10  # Default: 10 concurrent calls
)
```

**Benefits:**
- Prevents HTTP 429 (Rate Limit) errors
- Configurable concurrency limit
- Automatic batching for large datasets

## Performance Comparison

### Sequential Processing (Old Way)

```repl
# Process 100 documents one at a time
summaries = []
for doc in context:
    summary = llm_query(f"Summarize: {doc}")
    summaries.append(summary)

# Time: 100 × 2 seconds = 200 seconds (3+ minutes)
```

### Parallel Processing (New Way)

```repl
# Process 100 documents in parallel
summaries = parallel_query("Summarize: {chunk}", context)

# Time with max_parallel_calls=10:
# 10 batches × 2 seconds = 20 seconds
# 10x faster!
```

## Usage Patterns

### Pattern 1: Simple Parallel Processing

```repl
# Analyze multiple documents
analyses = parallel_query(
    "What is the main topic of this document? {chunk}",
    context
)
```

### Pattern 2: MapReduce Pattern

```repl
# Map: Process each chunk in parallel
summaries = parallel_query("Summarize this: {chunk}", context)

# Reduce: Aggregate results
final_answer = llm_query(
    f"Synthesize these summaries into one answer: {summaries}"
)
```

### Pattern 3: Multi-Stage Parallel Processing

```repl
# Stage 1: Parallel extraction
findings = parallel_query(
    "Extract key findings: {chunk}",
    research_papers
)

# Stage 2: Parallel categorization  
categories = parallel_query(
    "Categorize this finding: {chunk}",
    findings
)

# Stage 3: Sequential aggregation
final = llm_query(f"Synthesize by category: {categories}")
```

### Pattern 4: Chunking + Parallel Processing

```repl
# Create chunks
chunk_size = 100000
chunks = [context[i:i+chunk_size] 
          for i in range(0, len(context), chunk_size)]

# Process in parallel
results = parallel_query(
    "Answer the question based on this chunk: {chunk}",
    chunks
)

# Aggregate
answer = llm_query(f"Combine these answers: {results}")
```

## Architecture Details

### Async Flow

1. **User calls `parallel_query()` in REPL**
2. **REPL function bridges to async code**
   - Uses `asyncio.run()` to execute async function
   - Maintains synchronous interface for LLM
3. **Async coordinator creates tasks**
   - One task per chunk
   - Semaphore controls concurrency
4. **Tasks execute in parallel**
   - `asyncio.gather()` runs all tasks
   - Respects semaphore limit
5. **Results collected and returned**
   - Maintains original order
   - Handles errors gracefully

### Error Handling

If a chunk fails, the error is captured but other chunks continue:

```python
# Chunk 3 fails, but others succeed
results = parallel_query("Process: {chunk}", chunks)
# Results: ["Success", "Success", "Error: ...", "Success"]
```

### Thread Safety

The implementation is thread-safe:
- Semaphore controls concurrent access
- Subcall count incremented safely
- No race conditions in state

## When to Use Parallel Processing

### ✅ Good Use Cases

- **Multiple independent documents**: Analyze 100 research papers
- **Same operation on many chunks**: Summarize 50 sections
- **Extract structured data**: Pull names from 200 profiles
- **Batch translation**: Translate 30 documents
- **Parallel classification**: Categorize 100 articles

### ❌ Poor Use Cases

- **Sequential dependencies**: Each chunk builds on previous
- **Few chunks**: Only 1-2 items to process
- **Stateful iteration**: Need to accumulate context
- **Single long document**: Better to chunk differently

## Configuration

### Adjusting Concurrency

```python
# Conservative (low rate limits)
rlm = RLM(root_llm=llm, max_parallel_calls=5)

# Moderate (default)
rlm = RLM(root_llm=llm, max_parallel_calls=10)

# Aggressive (high rate limits)
rlm = RLM(root_llm=llm, max_parallel_calls=20)
```

### Model Selection

Use cheaper models for parallel sub-calls:

```python
rlm = RLM(
    root_llm=OpenAIInterface(model="gpt-4o"),      # Expensive, smart
    sub_llm=OpenAIInterface(model="gpt-4o-mini"),  # Cheap, fast
    max_parallel_calls=20
)
```

## System Prompt Updates

The LLM is now informed about `parallel_query()`:

> **NEW FEATURE: parallel_query() - Process Multiple Chunks Simultaneously**
> 
> You now have access to a powerful parallel processing tool:
> - Function signature: `parallel_query(prompt_template, list_of_chunks)`
> - This function processes all chunks in parallel and returns a list of results
> - Use this whenever you need to analyze multiple files or chunks - it's MUCH faster than loops
> - Example: `summaries = parallel_query("Summarize this: {chunk}", context)`
> - DO NOT iterate with for loops when you can use parallel_query

## Example: Complete Workflow

```python
from rlm import RLM, OpenAIInterface

# Initialize RLM with async support
root_llm = OpenAIInterface(model="gpt-4o")
sub_llm = OpenAIInterface(model="gpt-4o-mini")

rlm = RLM(
    root_llm=root_llm,
    sub_llm=sub_llm,
    max_parallel_calls=15,
    prompt_mode="standard"
)

# Query with large context
context = [... 100 research papers ...]
query = "What are the key trends in AI research?"

answer, trajectory = rlm.query(query, context, verbose=True)

# The LLM will use parallel_query() automatically:
# ```repl
# trends = parallel_query(
#     "Extract AI trends from this paper: {chunk}",
#     context
# )
# final = llm_query(f"Synthesize trends: {trends}")
# ```
```

## Monitoring Performance

Track parallel execution in trajectory:

```python
answer, trajectory = rlm.query(query, context)

for step in trajectory:
    if 'subcalls' in step:
        print(f"Iteration {step['iteration']}: {step['subcalls']} subcalls")
```

## Best Practices

1. **Use parallel_query for map phase**: Process independent chunks
2. **Use llm_query for reduce phase**: Aggregate/synthesize results
3. **Configure concurrency based on rate limits**: Start with 10, adjust as needed
4. **Use cheaper models for sub-calls**: Save costs on parallel operations
5. **Chunk appropriately**: ~100-200K chars per chunk for optimal performance
6. **Handle errors gracefully**: Check for "Error:" in results
7. **Monitor API costs**: Parallel calls can increase costs if not managed

## Troubleshooting

### Rate Limit Errors (HTTP 429)

**Solution**: Reduce `max_parallel_calls`

```python
rlm = RLM(root_llm=llm, max_parallel_calls=5)
```

### Slow Performance

**Check**: Are you using parallel_query?
- ❌ `for chunk in chunks: llm_query(...)`
- ✅ `parallel_query(..., chunks)`

### Out of Order Results

**Note**: Results are automatically sorted by input order
- No action needed - this is handled internally

### Memory Issues

**Solution**: Process in batches

```repl
# Instead of processing 1000 chunks at once
batch_size = 100
for i in range(0, len(context), batch_size):
    batch = context[i:i+batch_size]
    results = parallel_query("Process: {chunk}", batch)
    # Handle results
```

## Future Enhancements

- Budget tracking for parallel calls
- Progress callbacks
- Adaptive concurrency based on API response times
- Streaming results as they complete
- Automatic retry on transient failures

## See Also

- [examples/parallel_processing_example.py](../examples/parallel_processing_example.py)
- [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)
- [USER_GUIDE.md](../USER_GUIDE.md)
