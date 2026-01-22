# Mosaic Caching Layer Guide

## Overview

The Mosaic Caching Layer provides intelligent response caching to optimize performance and reduce API costs. By storing and retrieving responses for identical requests, the system can avoid expensive duplicate API calls while maintaining full functionality.

## Architecture

### MosaicCache Class

The caching system uses SQLite for lightweight, file-based persistent storage at `~/.mosaic/cache.db`.

**Database Schema:**
```sql
CREATE TABLE api_responses (
    request_hash TEXT PRIMARY KEY,      -- SHA256 hash of request parameters
    response_data TEXT NOT NULL,        -- Full JSON response from LLM
    created_at REAL NOT NULL,           -- Unix timestamp of creation
    last_accessed REAL,                 -- Unix timestamp of last access
    model_id TEXT NOT NULL,             -- Model identifier (e.g., "gpt-4o")
    tokens_saved INTEGER NOT NULL       -- Total tokens this response represents
);
```

### Hashing Logic

The system generates consistent SHA256 hashes by normalizing inputs before hashing:

**Normalized Components:**
- Prompt text (whitespace stripped)
- Model ID
- Temperature
- System prompt (if provided)
- Additional kwargs (JSON-sorted)

**Hash Formula:**
```
SHA256("{normalized_prompt}|{normalized_model}|{temperature}|{system_prompt}|{kwargs}")
```

This ensures that slightly different formatting doesn't cause cache misses.

## Usage

### Basic Usage

```python
from rlm import MosaicCache

# Initialize cache
cache = MosaicCache()

# Store a response
cache.set(
    prompt="What is the capital of France?",
    model_id="gpt-4o",
    response_data="The capital of France is Paris.",
    tokens_count=50,
    temperature=0.0
)

# Retrieve a cached response
result = cache.get(
    prompt="What is the capital of France?",
    model_id="gpt-4o",
    temperature=0.0
)

if result:
    print(f"Cached response: {result['response']}")
    print(f"Tokens saved: {result['tokens_saved']}")
else:
    print("Not in cache")
```

### Global Cache Instance

Use the global cache instance for convenience:

```python
from rlm import get_cache

cache = get_cache()

# Get total savings
savings = cache.get_total_savings()
print(f"Total tokens saved: {savings['total_tokens_saved']}")
print(f"Estimated savings: ${savings['estimated_cost_savings_usd']}")
```

### Decorator Integration

The `@with_cache` decorator automatically adds caching to LLM query methods:

```python
from rlm import with_cache, OpenAIInterface

class MyLLMWrapper:
    def __init__(self):
        self.model = "gpt-4o"
        self.temperature = 0.0
        self.llm = OpenAIInterface(model=self.model)
    
    @with_cache
    def query(self, prompt: str, system_prompt=None, use_cache=True):
        return self.llm.query(prompt, system_prompt)

# First call - hits API
wrapper = MyLLMWrapper()
response1 = wrapper.query("Explain quantum computing")

# Second call - returns cached response (no API call!)
response2 = wrapper.query("Explain quantum computing")

# Disable cache for specific call
response3 = wrapper.query("Explain quantum computing", use_cache=False)
```

### Context Manager

Control caching behavior with context managers:

```python
from rlm import cache_context, OpenAIInterface

llm = OpenAIInterface(model="gpt-4o")

# Normal operation - caching enabled
response1 = llm.query("Hello")

# Temporarily disable caching
with cache_context(enabled=False):
    response2 = llm.query("Hello")  # Bypasses cache
```

## Cache Management

### View Statistics

```python
from rlm import get_cache

cache = get_cache()

# Get detailed statistics
stats = cache.get_cache_stats()
print(f"Total cache entries: {stats['total_cache_entries']}")
print(f"Unique models: {stats['unique_models']}")
print(f"Estimated savings: ${stats['estimated_cost_savings_usd']}")

# Per-model statistics
for model_stat in stats['per_model_stats']:
    print(f"Model: {model_stat['model_id']}")
    print(f"  Entries: {model_stat['entry_count']}")
    print(f"  Tokens: {model_stat['total_tokens']}")
```

### Clear Cache

```python
from rlm import get_cache

cache = get_cache()

# Clear all cache entries
deleted_count = cache.clear_cache()
print(f"Deleted {deleted_count} entries")

# Clear entries older than 30 days
deleted_count = cache.clear_cache(older_than_days=30)
print(f"Deleted {deleted_count} old entries")
```

### Optimize Database

```python
from rlm import get_cache

cache = get_cache()

# Run VACUUM to optimize database
cache.vacuum()
```

## Performance Metrics

### Cache Hit Rate

Monitor cache effectiveness:

```python
from rlm import get_cache

cache = get_cache()
stats = cache.get_cache_stats()

total_entries = stats['total_cache_entries']
total_tokens = stats['total_tokens_saved']

if total_entries > 0:
    avg_tokens_per_entry = total_tokens / total_entries
    print(f"Average tokens per cached entry: {avg_tokens_per_entry:.0f}")
```

### Cost Savings Calculation

The cache estimates cost savings based on token counts:

**Estimation Formula:**
```
estimated_savings_usd = (total_tokens_saved / 1000) * $0.002
```

This is a rough average across different models. Actual savings vary by model:
- GPT-4o: ~$0.0025/1K tokens (input)
- GPT-4o-mini: ~$0.00015/1K tokens (input)
- Claude 3.5 Sonnet: ~$0.003/1K tokens (input)

## Integration with RLM

### Automatic Caching in LLM Interfaces

The caching layer integrates seamlessly with LLM interfaces:

```python
from rlm import OpenAIInterface, get_cache

# Initialize LLM with caching enabled
llm = OpenAIInterface(model="gpt-4o")

# First query - hits API and caches response
response1 = llm.query("Explain recursion", use_cache=True)

# Second query - returns cached response instantly
response2 = llm.query("Explain recursion", use_cache=True)

# Check savings
cache = get_cache()
savings = cache.get_total_savings()
print(f"You saved ${savings['estimated_cost_savings_usd']:.2f}!")
```

### Caching with Parallel Queries

The cache works automatically with `parallel_query`:

```python
from rlm import RLM, OpenAIInterface

root_llm = OpenAIInterface(model="gpt-4o")
sub_llm = OpenAIInterface(model="gpt-4o-mini")

rlm = RLM(root_llm=root_llm, sub_llm=sub_llm)

# Process documents - sub-calls are automatically cached
context = [doc1, doc2, doc3, doc4, doc5]
answer, trajectory = rlm.query("Summarize these documents", context)

# If you run again with same documents, cached responses are used!
answer2, trajectory2 = rlm.query("Summarize these documents", context)
```

## Best Practices

### 1. Cache Warming

Pre-populate cache with common queries:

```python
from rlm import OpenAIInterface, get_cache

llm = OpenAIInterface(model="gpt-4o")

# Warm up cache with common queries
common_queries = [
    "Explain this code",
    "Summarize this text",
    "Find the main points"
]

for query in common_queries:
    llm.query(query, use_cache=True)

cache = get_cache()
print(f"Cache warmed with {len(common_queries)} entries")
```

### 2. Regular Maintenance

Set up periodic cache maintenance:

```python
from rlm import get_cache
import schedule
import time

def maintain_cache():
    cache = get_cache()
    
    # Clear entries older than 90 days
    deleted = cache.clear_cache(older_than_days=90)
    print(f"Deleted {deleted} old entries")
    
    # Optimize database
    cache.vacuum()
    print("Database optimized")

# Run maintenance weekly
schedule.every().week.do(maintain_cache)

while True:
    schedule.run_pending()
    time.sleep(3600)  # Check every hour
```

### 3. Monitor Savings

Track and report cache effectiveness:

```python
from rlm import get_cache

cache = get_cache()
stats = cache.get_cache_stats()

print("=== Cache Performance Report ===")
print(f"Total Entries: {stats['total_cache_entries']}")
print(f"Tokens Saved: {stats['total_tokens_saved']:,}")
print(f"Estimated Savings: ${stats['estimated_cost_savings_usd']:.2f}")
print(f"Unique Models: {stats['unique_models']}")
print("\nPer-Model Breakdown:")
for model_stat in stats['per_model_stats']:
    print(f"  {model_stat['model_id']}: {model_stat['entry_count']} entries, "
          f"{model_stat['total_tokens']:,} tokens")
```

### 4. Temperature Considerations

Be aware that different temperatures create different cache entries:

```python
from rlm import OpenAIInterface

llm = OpenAIInterface(model="gpt-4o")

# These create separate cache entries
response1 = llm.query("Hello", temperature=0.0)   # Cached separately
response2 = llm.query("Hello", temperature=0.7)   # Different cache entry
response3 = llm.query("Hello", temperature=0.0)   # Uses response1's cache
```

For consistent caching, use temperature=0.0 for deterministic responses.

## Troubleshooting

### Cache Not Working

**Issue:** Queries not being cached

**Solutions:**
1. Check that `use_cache=True` is set (default)
2. Verify the cache directory is writable: `~/.mosaic/`
3. Check for SQLite errors in logs
4. Ensure identical parameters (prompt, model, temperature, system_prompt)

### Large Cache Database

**Issue:** Cache database growing too large

**Solutions:**
1. Clear old entries: `cache.clear_cache(older_than_days=30)`
2. Optimize database: `cache.vacuum()`
3. Consider setting up automated maintenance

### Inconsistent Cache Hits

**Issue:** Expected cache hits not happening

**Cause:** Input normalization differences

**Solutions:**
1. Ensure consistent formatting (extra whitespace doesn't matter)
2. Use exact same model IDs
3. Match temperature precisely
4. Check system prompts match exactly

## Advanced Usage

### Custom Cache Location

```python
from rlm import MosaicCache

# Use custom cache directory
cache = MosaicCache(cache_dir="/path/to/custom/cache")
```

### Manual Cache Management

```python
from rlm import MosaicCache

cache = MosaicCache()

# Manually hash and retrieve
request_hash = cache._generate_hash(
    prompt="Test",
    model_id="gpt-4o",
    temperature=0.0
)
print(f"Hash: {request_hash}")

# Direct database access (advanced)
import sqlite3
conn = sqlite3.connect(cache.db_path)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM api_responses")
count = cursor.fetchone()[0]
print(f"Total entries: {count}")
conn.close()
```

### Integration with Monitoring

```python
from rlm import get_cache
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cache = get_cache()

# Log cache usage
def log_cache_stats():
    stats = cache.get_cache_stats()
    logger.info(f"Cache entries: {stats['total_cache_entries']}")
    logger.info(f"Tokens saved: {stats['total_tokens_saved']}")
    logger.info(f"Savings: ${stats['estimated_cost_savings_usd']:.2f}")

# Call periodically
log_cache_stats()
```

## Summary

The Mosaic Caching Layer provides:

✅ **Automatic Response Caching** - Transparent caching for all LLM calls
✅ **Cost Optimization** - Reduce API costs by avoiding duplicate calls
✅ **Performance Improvement** - Instant responses for cached queries
✅ **Persistent Storage** - SQLite-based caching survives restarts
✅ **Smart Hashing** - Consistent cache keys with input normalization
✅ **Analytics** - Track savings and cache effectiveness
✅ **Flexible Control** - Enable/disable caching as needed

For more examples, see `examples/cache_example.py`.
