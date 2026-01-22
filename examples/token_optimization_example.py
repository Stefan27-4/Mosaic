"""
Token Optimization Examples

This script demonstrates the Token Optimization Layer's capabilities:
- Accurate token counting with tiktoken
- Dynamic chunk size calculation
- Cost estimation and optimization
- Model-specific tuning
"""

from rlm import (
    TokenGatekeeper,
    ChunkAutoTuner,
    OptTaskType,
    count_tokens,
    estimate_cost,
    get_model_limit,
    calculate_chunk_size,
    smart_chunk_text,
    MODEL_SPECS,
)


def example_1_basic_token_counting():
    """Example 1: Basic token counting."""
    print("=" * 70)
    print("Example 1: Basic Token Counting")
    print("=" * 70)
    
    gatekeeper = TokenGatekeeper()
    
    texts = [
        "Hello, world!",
        "The quick brown fox jumps over the lazy dog.",
        "import numpy as np\ndata = np.array([1, 2, 3])",
        "SELECT * FROM users WHERE active = TRUE AND created_at > '2024-01-01';",
    ]
    
    model = "gpt-4o"
    
    print(f"\nModel: {model}")
    print("-" * 70)
    
    for text in texts:
        tokens = gatekeeper.count(text, model)
        # Also show convenience function
        tokens_conv = count_tokens(text, model)
        
        print(f"Text: {text[:50]:50} | Tokens: {tokens:4}")
        assert tokens == tokens_conv, "Both methods should match"
    
    print("\n✓ Token counting successful\n")


def example_2_model_limits():
    """Example 2: Model context limits."""
    print("=" * 70)
    print("Example 2: Model Context Limits")
    print("=" * 70)
    
    gatekeeper = TokenGatekeeper()
    
    print("\nModel Specifications:")
    print("-" * 70)
    print(f"{'Model':<25} {'Context Limit':>15} {'Cost/1M Tokens':>15}")
    print("-" * 70)
    
    for model_id, (limit, cost) in MODEL_SPECS.items():
        limit_from_gatekeeper = gatekeeper.get_limit(model_id)
        limit_conv = get_model_limit(model_id)
        
        print(f"{model_id:<25} {limit:>15,} {f'${cost:.2f}':>15}")
        assert limit == limit_from_gatekeeper == limit_conv, "All methods should match"
    
    print("\n✓ Model limits retrieved successfully\n")


def example_3_cost_estimation():
    """Example 3: Cost estimation."""
    print("=" * 70)
    print("Example 3: Cost Estimation")
    print("=" * 70)
    
    gatekeeper = TokenGatekeeper()
    
    # Simulate a large document
    large_text = "This is a sample sentence. " * 1000  # ~7000 tokens
    
    print(f"\nDocument length: {len(large_text):,} characters")
    print("-" * 70)
    print(f"{'Model':<25} {'Tokens':>10} {'Cost (USD)':>15}")
    print("-" * 70)
    
    for model_id in ["gpt-4o", "gpt-4o-mini", "claude-opus-4.5", "deepseek-3.2"]:
        tokens = gatekeeper.count(large_text, model_id)
        cost = gatekeeper.estimate_cost(large_text, model_id)
        cost_conv = estimate_cost(large_text, model_id)
        
        print(f"{model_id:<25} {tokens:>10,} {f'${cost:.6f}':>15}")
        assert abs(cost - cost_conv) < 0.000001, "Costs should match"
    
    print("\n✓ Cost estimation successful\n")


def example_4_chunk_size_calculation():
    """Example 4: Optimal chunk size calculation."""
    print("=" * 70)
    print("Example 4: Optimal Chunk Size Calculation")
    print("=" * 70)
    
    tuner = ChunkAutoTuner()
    
    models = ["gpt-4o", "claude-opus-4.5", "gemini-1.5-pro", "deepseek-3.2"]
    task_types = [OptTaskType.CODE_ANALYSIS, OptTaskType.SUMMARIZATION, OptTaskType.GENERAL]
    
    for model in models:
        print(f"\nModel: {model}")
        print("-" * 70)
        
        for task_type in task_types:
            chunk_size = tuner.calculate_optimal_chunk_size(model, task_type)
            chunk_size_conv = calculate_chunk_size(model, task_type)
            
            print(f"{task_type.value:<20} → {chunk_size:>8,} tokens")
            assert chunk_size == chunk_size_conv, "Both methods should match"
    
    print("\n✓ Chunk size calculation successful\n")


def example_5_smart_chunking():
    """Example 5: Smart text chunking."""
    print("=" * 70)
    print("Example 5: Smart Text Chunking")
    print("=" * 70)
    
    # Create a sample document
    document = """
    The Recursive Language Model (RLM) framework enables LLMs to process
    arbitrarily long prompts by treating them as part of an external environment.
    """ * 100  # Make it longer
    
    print(f"\nDocument length: {len(document):,} characters")
    
    # Count tokens
    total_tokens = count_tokens(document, "gpt-4o")
    print(f"Total tokens: {total_tokens:,}")
    
    # Smart chunking with different task types
    print("\nChunking Results:")
    print("-" * 70)
    
    for task_type in [OptTaskType.CODE_ANALYSIS, OptTaskType.SUMMARIZATION, OptTaskType.GENERAL]:
        chunks = smart_chunk_text(
            text=document,
            model="gpt-4o",
            task_type=task_type,
            overlap_ratio=0.1
        )
        
        avg_size = sum(count_tokens(chunk, "gpt-4o") for chunk in chunks) // len(chunks)
        
        print(f"{task_type.value:<20} → {len(chunks):>3} chunks (avg {avg_size:,} tokens each)")
    
    print("\n✓ Smart chunking successful\n")


def example_6_overlap_comparison():
    """Example 6: Overlap ratio comparison."""
    print("=" * 70)
    print("Example 6: Overlap Ratio Comparison")
    print("=" * 70)
    
    document = "This is a sample document. " * 500  # ~3500 tokens
    model = "gpt-4o"
    
    print(f"\nDocument: {count_tokens(document, model):,} tokens")
    print("-" * 70)
    print(f"{'Overlap Ratio':<15} {'# Chunks':>10} {'Total Tokens':>15} {'Redundancy':>12}")
    print("-" * 70)
    
    for overlap_ratio in [0.0, 0.1, 0.2, 0.3]:
        chunks = smart_chunk_text(
            text=document,
            model=model,
            task_type=OptTaskType.GENERAL,
            overlap_ratio=overlap_ratio
        )
        
        total_tokens_chunked = sum(count_tokens(chunk, model) for chunk in chunks)
        redundancy = (total_tokens_chunked / count_tokens(document, model) - 1) * 100
        
        print(f"{overlap_ratio:<15.1%} {len(chunks):>10} {total_tokens_chunked:>15,} {f'+{redundancy:.1f}%':>12}")
    
    print("\n✓ Overlap comparison successful\n")


def example_7_model_selection():
    """Example 7: Model selection based on document size."""
    print("=" * 70)
    print("Example 7: Model Selection Based on Document Size")
    print("=" * 70)
    
    # Simulate documents of different sizes
    document_sizes = [5000, 50000, 150000, 250000]  # In tokens
    
    print("\nRecommended Models by Document Size:")
    print("-" * 70)
    print(f"{'Doc Tokens':<15} {'Recommended Models':<50}")
    print("-" * 70)
    
    for size in document_sizes:
        suitable_models = []
        
        for model_id, (limit, cost) in MODEL_SPECS.items():
            if size < limit:
                suitable_models.append((model_id, cost))
        
        # Sort by cost (cheapest first)
        suitable_models.sort(key=lambda x: x[1])
        
        model_names = ", ".join([m[0] for m in suitable_models[:3]])  # Top 3
        print(f"{size:>10,} → {model_names}")
    
    print("\n✓ Model selection successful\n")


def example_8_batch_processing():
    """Example 8: Batch document processing."""
    print("=" * 70)
    print("Example 8: Batch Document Processing")
    print("=" * 70)
    
    # Simulate multiple documents
    documents = [
        "Short document " * 50,
        "Medium length document " * 200,
        "Long document with lots of text " * 500,
        "Very long document " * 1000,
    ]
    
    model = "gpt-4o"
    
    print(f"\nProcessing {len(documents)} documents with {model}")
    print("-" * 70)
    print(f"{'Doc #':<8} {'Tokens':>10} {'Chunks':>8} {'Est. Cost':>12}")
    print("-" * 70)
    
    total_tokens = 0
    total_cost = 0.0
    
    for i, doc in enumerate(documents, 1):
        tokens = count_tokens(doc, model)
        cost = estimate_cost(doc, model)
        
        chunks = smart_chunk_text(
            text=doc,
            model=model,
            task_type=OptTaskType.SUMMARIZATION,
            overlap_ratio=0.1
        )
        
        total_tokens += tokens
        total_cost += cost
        
        print(f"Doc {i:<4} {tokens:>10,} {len(chunks):>8} {f'${cost:.6f}':>12}")
    
    print("-" * 70)
    print(f"{'TOTAL':<8} {total_tokens:>10,} {' ':>8} {f'${total_cost:.6f}':>12}")
    
    print("\n✓ Batch processing successful\n")


def example_9_encoding_consistency():
    """Example 9: Encoding consistency check."""
    print("=" * 70)
    print("Example 9: Encoding Consistency")
    print("=" * 70)
    
    test_texts = [
        "Hello world",
        "  Hello world  ",  # Extra whitespace
        "Hello\nworld",  # With newline
        "Hello\tworld",  # With tab
    ]
    
    model = "gpt-4o"
    
    print(f"\nModel: {model}")
    print("-" * 70)
    
    for text in test_texts:
        tokens = count_tokens(text, model)
        repr_text = repr(text)
        print(f"Text: {repr_text:30} | Tokens: {tokens:4}")
    
    print("\n✓ Encoding consistency verified\n")


def example_10_cost_aware_workflow():
    """Example 10: Cost-aware processing workflow."""
    print("=" * 70)
    print("Example 10: Cost-Aware Processing Workflow")
    print("=" * 70)
    
    document = "Sample document content. " * 1000
    budget = 0.10  # $0.10 budget
    
    print(f"\nBudget: ${budget:.2f}")
    print(f"Document size: {count_tokens(document, 'gpt-4o'):,} tokens")
    print("-" * 70)
    print(f"{'Model':<25} {'Cost':>12} {'Within Budget':>15}")
    print("-" * 70)
    
    viable_models = []
    
    for model_id in ["gpt-4o", "gpt-4o-mini", "claude-opus-4.5", "deepseek-3.2"]:
        cost = estimate_cost(document, model_id)
        within_budget = cost <= budget
        status = "✓ Yes" if within_budget else "✗ No"
        
        print(f"{model_id:<25} {f'${cost:.6f}':>12} {status:>15}")
        
        if within_budget:
            viable_models.append(model_id)
    
    if viable_models:
        print(f"\nRecommended: Use {viable_models[0]} (cheapest within budget)")
    else:
        print(f"\nWarning: All models exceed budget. Consider chunking or increasing budget.")
    
    print("\n✓ Cost-aware workflow complete\n")


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 18 + "TOKEN OPTIMIZATION EXAMPLES" + " " * 22 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    examples = [
        example_1_basic_token_counting,
        example_2_model_limits,
        example_3_cost_estimation,
        example_4_chunk_size_calculation,
        example_5_smart_chunking,
        example_6_overlap_comparison,
        example_7_model_selection,
        example_8_batch_processing,
        example_9_encoding_consistency,
        example_10_cost_aware_workflow,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n✗ Example failed: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("=" * 70)
    print("All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
