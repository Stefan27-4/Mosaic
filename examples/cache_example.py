"""
Mosaic Caching Layer Example

This example demonstrates the caching system for optimizing performance
and reducing API costs.
"""

from rlm import MosaicCache, get_cache


def example_basic_usage():
    """Demonstrate basic cache operations."""
    print("=== Basic Cache Usage ===\n")
    
    cache = MosaicCache()
    
    # Store a response
    print("Storing response in cache...")
    cache.set(
        prompt="What is the capital of France?",
        model_id="gpt-4o",
        response_data="The capital of France is Paris.",
        tokens_count=50,
        temperature=0.0
    )
    
    # Retrieve cached response
    print("Retrieving from cache...")
    result = cache.get(
        prompt="What is the capital of France?",
        model_id="gpt-4o",
        temperature=0.0
    )
    
    if result:
        print(f"✓ Cache hit!")
        print(f"  Response: {result['response']}")
        print(f"  Tokens saved: {result['tokens_saved']}")
    else:
        print("✗ Cache miss")
    
    print()


def example_hash_consistency():
    """Demonstrate that formatting doesn't affect cache hits."""
    print("=== Hash Consistency ===\n")
    
    cache = MosaicCache()
    
    # Store with specific formatting
    cache.set(
        prompt="  What is Python?  \n",
        model_id="gpt-4o",
        response_data="Python is a programming language.",
        tokens_count=40,
        temperature=0.0
    )
    
    # Try to retrieve with different formatting - should still hit cache
    result = cache.get(
        prompt="What is Python?",  # No extra whitespace
        model_id="gpt-4o",
        temperature=0.0
    )
    
    if result:
        print("✓ Cache hit despite different whitespace!")
        print(f"  Response: {result['response']}")
    else:
        print("✗ Unexpected cache miss")
    
    print()


def example_cache_stats():
    """Demonstrate cache statistics and savings tracking."""
    print("=== Cache Statistics ===\n")
    
    cache = MosaicCache()
    
    # Add some sample entries
    samples = [
        ("Explain recursion", "gpt-4o", "Recursion is...", 100),
        ("What is AI?", "gpt-4o-mini", "AI is...", 80),
        ("Summarize this", "claude-3-5-sonnet", "Summary...", 120),
        ("Code review", "gpt-4o", "The code...", 200),
    ]
    
    print("Adding sample cache entries...")
    for prompt, model, response, tokens in samples:
        cache.set(
            prompt=prompt,
            model_id=model,
            response_data=response,
            tokens_count=tokens,
            temperature=0.0
        )
    
    # Get total savings
    savings = cache.get_total_savings()
    print(f"\nTotal Savings:")
    print(f"  Tokens saved: {savings['total_tokens_saved']:,}")
    print(f"  Cache entries: {savings['total_cache_entries']}")
    print(f"  Unique models: {savings['unique_models']}")
    print(f"  Estimated cost savings: ${savings['estimated_cost_savings_usd']:.2f}")
    
    # Get detailed statistics
    stats = cache.get_cache_stats()
    print(f"\nPer-Model Breakdown:")
    for model_stat in stats['per_model_stats']:
        print(f"  {model_stat['model_id']}:")
        print(f"    Entries: {model_stat['entry_count']}")
        print(f"    Tokens: {model_stat['total_tokens']:,}")
    
    print()


def example_temperature_sensitivity():
    """Demonstrate how temperature affects caching."""
    print("=== Temperature Sensitivity ===\n")
    
    cache = MosaicCache()
    
    prompt = "Tell me a joke"
    
    # Cache with temperature 0.0
    cache.set(
        prompt=prompt,
        model_id="gpt-4o",
        response_data="Why did the chicken cross the road?",
        tokens_count=50,
        temperature=0.0
    )
    
    # Try to retrieve with same temperature - should hit
    result1 = cache.get(prompt=prompt, model_id="gpt-4o", temperature=0.0)
    print(f"Temperature 0.0: {'✓ Cache hit' if result1 else '✗ Cache miss'}")
    
    # Try to retrieve with different temperature - should miss
    result2 = cache.get(prompt=prompt, model_id="gpt-4o", temperature=0.7)
    print(f"Temperature 0.7: {'✓ Cache hit' if result2 else '✗ Cache miss (expected)'}")
    
    print()


def example_global_cache():
    """Demonstrate using the global cache instance."""
    print("=== Global Cache Instance ===\n")
    
    # Get global cache
    cache = get_cache()
    
    # Store some data
    cache.set(
        prompt="Global cache test",
        model_id="gpt-4o",
        response_data="Testing global cache",
        tokens_count=30,
        temperature=0.0
    )
    
    # Retrieve from anywhere using global cache
    result = get_cache().get(
        prompt="Global cache test",
        model_id="gpt-4o",
        temperature=0.0
    )
    
    if result:
        print("✓ Global cache works!")
        print(f"  Response: {result['response']}")
    
    print()


def example_cache_clearing():
    """Demonstrate cache clearing operations."""
    print("=== Cache Clearing ===\n")
    
    cache = MosaicCache()
    
    # Add entries with different timestamps (simulated)
    import time
    
    entries_before = cache.get_cache_stats()['total_cache_entries']
    print(f"Entries before: {entries_before}")
    
    # Add some test entries
    for i in range(5):
        cache.set(
            prompt=f"Test query {i}",
            model_id="gpt-4o",
            response_data=f"Response {i}",
            tokens_count=50,
            temperature=0.0
        )
    
    entries_after = cache.get_cache_stats()['total_cache_entries']
    print(f"Entries after adding: {entries_after}")
    
    # Clear specific old entries (0 days = all)
    deleted = cache.clear_cache(older_than_days=0)
    print(f"Deleted {deleted} entries")
    
    entries_final = cache.get_cache_stats()['total_cache_entries']
    print(f"Entries remaining: {entries_final}")
    
    print()


def example_with_system_prompt():
    """Demonstrate caching with system prompts."""
    print("=== System Prompt Caching ===\n")
    
    cache = MosaicCache()
    
    prompt = "Explain AI"
    system1 = "You are a helpful assistant."
    system2 = "You are an expert in AI."
    
    # Cache with first system prompt
    cache.set(
        prompt=prompt,
        model_id="gpt-4o",
        response_data="AI explained (assistant)",
        tokens_count=60,
        temperature=0.0,
        system_prompt=system1
    )
    
    # Try with same system prompt - should hit
    result1 = cache.get(
        prompt=prompt,
        model_id="gpt-4o",
        temperature=0.0,
        system_prompt=system1
    )
    print(f"Same system prompt: {'✓ Cache hit' if result1 else '✗ Cache miss'}")
    
    # Try with different system prompt - should miss
    result2 = cache.get(
        prompt=prompt,
        model_id="gpt-4o",
        temperature=0.0,
        system_prompt=system2
    )
    print(f"Different system prompt: {'✓ Cache hit' if result2 else '✗ Cache miss (expected)'}")
    
    print()


def example_performance_comparison():
    """Demonstrate performance benefits of caching."""
    print("=== Performance Comparison ===\n")
    
    cache = MosaicCache()
    
    # Simulate storing responses
    queries = [
        "What is Python?",
        "Explain machine learning",
        "How does caching work?",
        "Define recursion",
        "What is a database?"
    ]
    
    print("Simulating cache population...")
    for i, query in enumerate(queries):
        cache.set(
            prompt=query,
            model_id="gpt-4o",
            response_data=f"Response to: {query}",
            tokens_count=100,
            temperature=0.0
        )
    
    # Simulate cache hits
    print(f"\nSimulating {len(queries)} cache hits...")
    hits = 0
    for query in queries:
        result = cache.get(
            prompt=query,
            model_id="gpt-4o",
            temperature=0.0
        )
        if result:
            hits += 1
    
    print(f"✓ Cache hits: {hits}/{len(queries)}")
    print(f"✓ Cache hit rate: {(hits/len(queries)*100):.0f}%")
    
    savings = cache.get_total_savings()
    print(f"✓ Total tokens saved: {savings['total_tokens_saved']:,}")
    print(f"✓ Estimated savings: ${savings['estimated_cost_savings_usd']:.2f}")
    
    print()


def run_all_examples():
    """Run all cache examples."""
    print("╔════════════════════════════════════════════════════╗")
    print("║    Mosaic Caching Layer - Examples                ║")
    print("╚════════════════════════════════════════════════════╝")
    print()
    
    example_basic_usage()
    example_hash_consistency()
    example_cache_stats()
    example_temperature_sensitivity()
    example_global_cache()
    example_cache_clearing()
    example_with_system_prompt()
    example_performance_comparison()
    
    print("╔════════════════════════════════════════════════════╗")
    print("║    All examples completed successfully!           ║")
    print("╚════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    run_all_examples()
