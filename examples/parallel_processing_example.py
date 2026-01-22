"""
Example demonstrating parallel processing with the RLM framework.

This example shows how to use the parallel_query() function to process
multiple chunks simultaneously for dramatic speed improvements.
"""

from rlm import RLM, OpenAIInterface

def mock_llm_query(prompt: str) -> str:
    """Mock LLM for demonstration (replace with real API in production)."""
    # Simulate processing
    import time
    time.sleep(0.1)  # Simulate API latency
    
    if "summarize" in prompt.lower():
        return "This chunk discusses various topics."
    elif "magic number" in prompt.lower():
        return "The magic number is 42."
    else:
        return "Processed successfully."


def demonstrate_sequential_vs_parallel():
    """
    Compare sequential processing with parallel processing.
    """
    print("=" * 80)
    print("PARALLEL PROCESSING DEMONSTRATION")
    print("=" * 80)
    
    # Create sample context with multiple documents
    documents = [
        f"Document {i}: This is a sample document with content about topic {i}. " * 100
        for i in range(20)
    ]
    
    print(f"\nProcessing {len(documents)} documents...")
    print(f"Each document is approximately {len(documents[0])} characters")
    
    # Note: In a real scenario, you would initialize with actual API keys
    # For this example, we're demonstrating the structure
    
    print("\n" + "=" * 80)
    print("APPROACH 1: Sequential Processing (OLD WAY - SLOW)")
    print("=" * 80)
    print("""
```repl
# OLD APPROACH: Process one at a time
summaries = []
for i, doc in enumerate(context):
    summary = llm_query(f"Summarize this document: {{doc}}")
    summaries.append(summary)
    print(f"Processed document {{i+1}}/{{len(context)}}")
```

This approach processes 20 documents sequentially:
- If each API call takes 2 seconds
- Total time: 20 × 2 = 40 seconds
- Uses sequential loop (slow)
""")
    
    print("\n" + "=" * 80)
    print("APPROACH 2: Parallel Processing (NEW WAY - FAST)")
    print("=" * 80)
    print("""
```repl
# NEW APPROACH: Process all documents simultaneously
summaries = parallel_query("Summarize this document: {chunk}", context)
print(f"Processed all {{len(summaries)}} documents in parallel!")
```

This approach processes 20 documents in parallel:
- All 20 API calls happen simultaneously
- Total time: ~2 seconds (just one batch)
- 20x faster for this workload!
- Concurrency limit prevents rate limiting (default: 10 concurrent calls)
""")
    
    print("\n" + "=" * 80)
    print("REAL-WORLD EXAMPLE: Analyzing Research Papers")
    print("=" * 80)
    print("""
Scenario: You have 100 research papers and need to extract key findings.

OLD WAY (Sequential):
```repl
findings = []
for paper in context:
    finding = llm_query(f"Extract key findings from this paper: {{paper}}")
    findings.append(finding)
# Time: 100 papers × 2 sec/paper = 200 seconds (3+ minutes)
```

NEW WAY (Parallel):
```repl
findings = parallel_query("Extract key findings from this paper: {chunk}", context)
# Time: ~20 seconds (10 concurrent calls × 2 batches)
# 10x faster!
```
""")
    
    print("\n" + "=" * 80)
    print("ADVANCED USAGE: Multi-Stage Parallel Processing")
    print("=" * 80)
    print("""
You can combine parallel processing with aggregation:

```repl
# Stage 1: Parallel processing of all documents
summaries = parallel_query("Summarize this: {chunk}", context)

# Stage 2: Parallel analysis of summaries (if needed)
# Group summaries into batches
batch_size = 10
batches = [summaries[i:i+batch_size] for i in range(0, len(summaries), batch_size)]
batch_texts = ["\\n".join(batch) for batch in batches]

# Parallel aggregation
aggregations = parallel_query("Synthesize these summaries: {chunk}", batch_texts)

# Final synthesis
final_answer = llm_query(f"Provide final answer based on: {{aggregations}}")
```

This handles even massive datasets efficiently!
""")
    
    print("\n" + "=" * 80)
    print("CONCURRENCY CONTROL")
    print("=" * 80)
    print("""
The parallel_query() function automatically manages concurrency:

- Default limit: 10 concurrent API calls
- Prevents hitting rate limits (HTTP 429 errors)
- Configure via RLM initialization: RLM(..., max_parallel_calls=20)
- Automatic semaphore ensures safety

Example with custom concurrency:
```python
from rlm import RLM, OpenAIInterface

rlm = RLM(
    root_llm=OpenAIInterface(model="gpt-4o"),
    sub_llm=OpenAIInterface(model="gpt-4o-mini"),
    max_parallel_calls=20  # Allow 20 concurrent calls
)
```
""")
    
    print("\n" + "=" * 80)
    print("WHEN TO USE PARALLEL_QUERY")
    print("=" * 80)
    print("""
✅ USE parallel_query() when:
- Processing multiple independent chunks
- Same operation on each chunk
- Need to analyze 10+ documents/sections
- Speed is important

❌ DON'T USE parallel_query() when:
- Sequential processing is required (state depends on previous results)
- Only 1-2 chunks to process
- Need to build up context iteratively
- Chunks have dependencies

BEST PRACTICE:
- Use parallel_query() for the "map" phase (process each independently)
- Use llm_query() for the "reduce" phase (aggregate results)
""")
    
    print("\n" + "=" * 80)
    print("Example complete!")
    print("=" * 80)


if __name__ == "__main__":
    demonstrate_sequential_vs_parallel()
