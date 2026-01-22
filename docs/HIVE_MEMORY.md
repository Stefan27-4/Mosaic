# Hive Memory: Shared Intuition for Parallel Sub-Agents

## Overview

The **Hive Memory** feature enables parallel sub-agents in the RLM framework to share state (facts, findings, intermediate results) instantly, rather than being isolated. This creates a "hive mind" effect where agents can collaborate and build on each other's discoveries.

## Motivation

When using `parallel_query()` to process multiple chunks simultaneously, each sub-agent typically works in isolation. However, many tasks benefit from agents being aware of what others have found:

- **Detective work**: One agent finds a clue that helps others interpret their evidence
- **Fact extraction**: Agents accumulate facts without duplication
- **Progressive refinement**: Each agent builds on previous findings
- **State aggregation**: Collect statistics or summaries across all parallel operations

## Architecture

### HiveMemory Class

```python
from rlm import HiveMemory

# Automatically injected as 'hive' in REPL environment
hive = HiveMemory()

# Thread-safe operations
hive.set(key, value)         # Store a value
value = hive.get(key, default=None)  # Retrieve a value
all_data = hive.get_all()     # Get snapshot of all data
hive.clear()                  # Wipe all memory
```

**Thread Safety**: All operations use `threading.Lock()` to ensure safety when accessed from parallel sub-agents running in different threads.

### Integration with RLM

The hive memory is:
1. **Automatically created** for each query session
2. **Injected into REPL** as the global variable `hive`
3. **Shared with parallel_query** - sub-agents receive current hive state in their prompts
4. **Persistent across iterations** - accumulates state throughout the entire query

## Usage Patterns

### Pattern 1: Accumulating Facts

```repl
# LLM can use hive to accumulate findings across iterations
hive.set("total_documents", len(context))
hive.set("important_facts", [])

# Process documents
for doc in context[:10]:
    facts = extract_facts(doc)  # Custom function
    current_facts = hive.get("important_facts", [])
    hive.set("important_facts", current_facts + facts)

print(f"Accumulated {len(hive.get('important_facts'))} facts")
```

### Pattern 2: Parallel Processing with Shared Context

```repl
# Set up shared context before parallel processing
hive.set("search_term", "climate change")
hive.set("found_count", 0)

# Parallel agents automatically see hive state
results = parallel_query(
    "Search for mentions of the topic. Check the hive for the search term. Report if found in: {chunk}",
    context
)

# Aggregate results
total_mentions = sum(1 for r in results if "found" in r.lower())
print(f"Total mentions: {total_mentions}")
```

### Pattern 3: Progressive Refinement

```repl
# First pass: Collect candidate answers
candidates = parallel_query("Find potential answers in: {chunk}", context)
hive.set("candidates", candidates)

# Second pass: Verify using shared candidates
# (In a subsequent iteration)
all_candidates = hive.get("candidates", [])
verification = llm_query(f"Which of these candidates is most accurate? {all_candidates}")
hive.set("verified_answer", verification)
```

### Pattern 4: Detective/Investigation Workflow

```repl
# Initialize investigation
hive.set("suspects", [])
hive.set("evidence", [])
hive.set("timeline", {})

# Analyze clues (could be done in parallel)
# Each analysis updates shared state
hive.set("suspects", hive.get("suspects") + ["butler"])
hive.set("evidence", hive.get("evidence") + ["candlestick"])

# Final synthesis uses accumulated state
all_suspects = hive.get("suspects")
all_evidence = hive.get("evidence")
solution = llm_query(f"Who done it? Suspects: {all_suspects}, Evidence: {all_evidence}")
```

## How It Works with parallel_query

When you call `parallel_query()`, the RLM framework:

1. **Takes a snapshot** of the current hive state
2. **Injects it into each sub-agent's prompt** as "Shared Context (Hive Memory)"
3. **Processes chunks in parallel** - all sub-agents can see the shared state
4. **Returns results** in the original order

### Example of Injected Context

When a sub-agent receives its prompt, it looks like:

```
Shared Context (Hive Memory):
  suspect: 'butler'
  weapon: 'candlestick'
  location: 'library'

[Your prompt template with {chunk} replaced]
```

This allows sub-agents to make decisions informed by accumulated findings.

## API Reference

### HiveMemory Class

```python
class HiveMemory:
    """Thread-safe shared memory for parallel sub-agents."""
    
    def set(self, key: str, value: Any) -> None:
        """
        Store a value (thread-safe).
        
        Args:
            key: The key to store under
            value: Any Python object
        """
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a value (thread-safe).
        
        Args:
            key: The key to retrieve
            default: Value to return if key doesn't exist
            
        Returns:
            The stored value or default
        """
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get a snapshot of all memory (thread-safe).
        
        Returns:
            Copy of the entire memory dictionary
        """
    
    def clear(self) -> None:
        """Wipe all memory (thread-safe)."""
```

### REPLEnvironment Integration

```python
from rlm import REPLEnvironment, HiveMemory

# Create your own hive (optional)
hive = HiveMemory()

# Pass to REPL
repl_env = REPLEnvironment(
    context=my_context,
    hive_memory=hive  # Optional: auto-created if None
)

# Access in code executed in REPL
code = """
hive.set("finding", "important discovery")
print(hive.get_all())
"""
output, success = repl_env.execute(code)
```

### RLM Integration

```python
from rlm import RLM, OpenAIInterface

# Hive memory is automatically managed per query
rlm = RLM(
    root_llm=OpenAIInterface(model="gpt-4o"),
    sub_llm=OpenAIInterface(model="gpt-4o-mini")
)

# Each query gets its own fresh hive memory
answer1, trajectory1 = rlm.query("Query 1", context)  # Hive 1
answer2, trajectory2 = rlm.query("Query 2", context)  # Hive 2 (fresh)
```

## Complete Example

```python
from rlm import RLM, OpenAIInterface

# Setup
root_llm = OpenAIInterface(model="gpt-4o")
sub_llm = OpenAIInterface(model="gpt-4o-mini")
rlm = RLM(root_llm=root_llm, sub_llm=sub_llm)

# Documents about a mystery
context = [
    "The butler was seen near the library at 9 PM",
    "A candlestick was found in the study",
    "The victim was last seen at 8:30 PM",
    "The library window was broken from inside"
]

# Query (LLM can use hive to track findings)
answer, trajectory = rlm.query(
    "Who is the most likely suspect and why?",
    context
)

# LLM might write code like:
"""
```repl
# Initialize investigation
hive.set("suspects", [])
hive.set("evidence", [])

# Process clues
for doc in context:
    if "butler" in doc:
        suspects = hive.get("suspects", [])
        hive.set("suspects", suspects + ["butler"])
    if "candlestick" in doc:
        evidence = hive.get("evidence", [])
        hive.set("evidence", evidence + ["candlestick"])

# Analyze
suspects = hive.get("suspects")
evidence = hive.get("evidence")
print(f"Suspects: {suspects}")
print(f"Evidence: {evidence}")

# Final answer
FINAL("The butler is the most likely suspect based on proximity to the scene")
```
"""
```

## Best Practices

### DO:
- ✅ Use hive for accumulating facts across iterations
- ✅ Store intermediate results that later iterations might need
- ✅ Track progress and statistics (e.g., processed count)
- ✅ Share context between parallel operations
- ✅ Clear hive state when starting a new logical phase

### DON'T:
- ❌ Store massive objects (keep data lean for efficiency)
- ❌ Assume hive persists between different `rlm.query()` calls
- ❌ Use hive as a replacement for proper return values
- ❌ Rely on write ordering in parallel operations (use atomic patterns)

## Performance Considerations

- **Thread-safe but lightweight**: Uses `threading.Lock()`, minimal overhead
- **Memory scope**: Lives for one query session, garbage collected after
- **Snapshot model**: `parallel_query` takes a snapshot, so updates during parallel execution don't propagate between sub-agents
- **Read-heavy optimization**: Multiple threads can read efficiently; writes serialize

## Comparison to Alternatives

| Approach | Pros | Cons |
|----------|------|------|
| **Hive Memory** | Instant sharing, thread-safe, simple API | Snapshot model (no inter-agent updates during parallel execution) |
| **Return values** | Explicit, functional | Requires aggregation step, no sharing during execution |
| **Global variables** | Simple | Not thread-safe, risky |
| **External DB** | Persistent, scalable | Slow, complex, overkill for session state |

## Examples

See `examples/hive_memory_example.py` for complete working examples demonstrating:
- Basic usage
- Integration with REPL
- Parallel processing scenarios
- Detective workflow pattern

## Troubleshooting

**Q: My hive data disappeared between queries**
- A: Each `rlm.query()` call gets a fresh hive. This is intentional for isolation.

**Q: Sub-agents in parallel_query aren't seeing each other's updates**
- A: Correct. parallel_query uses a snapshot. Sub-agents see the hive state from *before* parallel execution starts.

**Q: Can I share hive between different RLM instances?**
- A: No. Each query session has its own hive. Create a custom shared object if needed.

**Q: Thread safety with asyncio?**
- A: HiveMemory uses `threading.Lock()` which works with asyncio's thread pool executor.

## Future Enhancements

Potential future features:
- Async locks for pure asyncio environments
- Update propagation during parallel execution
- Hive snapshots/history for debugging
- Cross-query persistence (optional)
- Distributed hive for multi-machine setups

## License

Part of the RLM framework. See main LICENSE file.
