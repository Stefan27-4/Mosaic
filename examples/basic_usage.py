"""
Basic usage example for the RLM framework.

This example demonstrates how to:
1. Initialize LLM interfaces (root and sub-LLM)
2. Create an RLM instance
3. Execute a query with context
4. Display results
"""

import os
from rlm import RLM, OpenAIInterface, AnthropicInterface


def example_openai():
    """Example using OpenAI models."""
    print("=" * 80)
    print("RLM Example with OpenAI")
    print("=" * 80)
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        return
    
    # Initialize LLM interfaces
    # Use GPT-4o for root LLM and GPT-4o-mini for sub-LLM (cheaper for recursive calls)
    root_llm = OpenAIInterface(model="gpt-4o", max_tokens=4096, temperature=0.0)
    sub_llm = OpenAIInterface(model="gpt-4o-mini", max_tokens=16384, temperature=0.0)
    
    # Create RLM instance
    rlm = RLM(
        root_llm=root_llm,
        sub_llm=sub_llm,
        max_iterations=10,
        max_recursion_depth=5,
        prompt_mode="standard"  # Options: "standard", "conservative", "no_subcalls"
    )
    
    # Prepare context - a long list of documents
    context = [
        "Document 1: The Eiffel Tower is located in Paris, France. It was built in 1889.",
        "Document 2: The Great Wall of China is over 13,000 miles long.",
        "Document 3: The Statue of Liberty was a gift from France to the United States.",
        "Document 4: The Colosseum in Rome was built in 80 AD.",
        "Document 5: The Eiffel Tower is 330 meters tall and was designed by Gustave Eiffel.",
        "Document 6: Mount Everest is the tallest mountain in the world at 8,849 meters.",
        "Document 7: The Amazon River is the largest river by discharge volume of water in the world.",
        "Document 8: The Eiffel Tower receives about 7 million visitors per year.",
    ]
    
    # Execute query
    query = "What is the height of the Eiffel Tower and who designed it?"
    
    print(f"\nQuery: {query}")
    print(f"Context: {len(context)} documents\n")
    
    answer, trajectory = rlm.query(query, context, verbose=True)
    
    print("\n" + "=" * 80)
    print("FINAL ANSWER:")
    print("=" * 80)
    print(answer)
    
    print("\n" + "=" * 80)
    print("TRAJECTORY SUMMARY:")
    print("=" * 80)
    print(f"Total iterations: {len(trajectory)}")
    if trajectory:
        total_subcalls = trajectory[-1].get("subcalls", 0)
        print(f"Total sub-LLM calls: {total_subcalls}")


def example_anthropic():
    """Example using Anthropic models."""
    print("=" * 80)
    print("RLM Example with Anthropic")
    print("=" * 80)
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        return
    
    # Initialize LLM interfaces
    # Use Claude 3.5 Sonnet for root and Haiku for sub-calls
    root_llm = AnthropicInterface(model="claude-3-5-sonnet-20241022", max_tokens=4096)
    sub_llm = AnthropicInterface(model="claude-3-5-haiku-20241022", max_tokens=8192)
    
    # Create RLM instance
    rlm = RLM(
        root_llm=root_llm,
        sub_llm=sub_llm,
        max_iterations=10,
        max_recursion_depth=5,
        prompt_mode="standard"
    )
    
    # Prepare a simple context
    context = "The quick brown fox jumps over the lazy dog. " * 100  # Repeat to make it longer
    
    # Execute query
    query = "How many times does the word 'fox' appear in the context?"
    
    print(f"\nQuery: {query}")
    print(f"Context: {len(context)} characters\n")
    
    answer, trajectory = rlm.query(query, context, verbose=True)
    
    print("\n" + "=" * 80)
    print("FINAL ANSWER:")
    print("=" * 80)
    print(answer)
    
    print("\n" + "=" * 80)
    print("TRAJECTORY SUMMARY:")
    print("=" * 80)
    print(f"Total iterations: {len(trajectory)}")


def example_no_subcalls():
    """Example using RLM without sub-calls (ablation mode)."""
    print("=" * 80)
    print("RLM Example without Sub-calls (Ablation)")
    print("=" * 80)
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        return
    
    # Initialize LLM interface
    root_llm = OpenAIInterface(model="gpt-4o-mini", max_tokens=4096, temperature=0.0)
    
    # Create RLM instance without sub-calls
    rlm = RLM(
        root_llm=root_llm,
        max_iterations=10,
        prompt_mode="no_subcalls"  # This disables sub-LLM calls
    )
    
    # Prepare context
    context = [
        "Alice scored 95 on the math test.",
        "Bob scored 87 on the math test.",
        "Charlie scored 92 on the math test.",
        "Diana scored 88 on the math test.",
    ]
    
    # Execute query
    query = "What is the average score on the math test?"
    
    print(f"\nQuery: {query}")
    print(f"Context: {len(context)} items\n")
    
    answer, trajectory = rlm.query(query, context, verbose=True)
    
    print("\n" + "=" * 80)
    print("FINAL ANSWER:")
    print("=" * 80)
    print(answer)


if __name__ == "__main__":
    # Run examples based on available API keys
    if os.getenv("OPENAI_API_KEY"):
        example_openai()
        print("\n\n")
        example_no_subcalls()
    
    if os.getenv("ANTHROPIC_API_KEY"):
        print("\n\n")
        example_anthropic()
    
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("No API keys found. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.")
