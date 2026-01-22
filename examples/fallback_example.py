"""
Example demonstrating the single-key bypass and fallback chain optimization.

This shows how the routing engine automatically handles:
1. Single-key bypass when only one model is available
2. Fallback chains when ideal models are unavailable
"""

import sys
import os
import logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rlm import classify_chunk, get_available_models, FALLBACK_CHAINS

# Enable logging to see fallback warnings
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')


def example_single_key_bypass():
    """Demonstrate single-key bypass optimization."""
    print("=" * 80)
    print("Example 1: Single-Key Bypass Optimization")
    print("=" * 80)
    
    print("\nScenario: User only has OpenAI API key")
    print("-" * 80)
    
    # Simulate having only OpenAI models available
    available_models = {"gpt-5.2", "deepseek-3.2"}  # Both use OpenAI
    
    # But let's test with truly single model
    single_model = {"gpt-5.2"}
    
    texts = [
        "class DataProcessor: def process(self): return self.data",
        "SELECT users.name FROM users WHERE active = true",
        "Once upon a time in a faraway land...",
    ]
    
    print(f"\nAvailable model: {single_model}")
    print("\nResults:")
    
    for text in texts:
        model_id, details = classify_chunk(text, available_models=single_model)
        print(f"\n  Text: {text[:50]}...")
        print(f"  Routed to: {model_id}")
        print(f"  Bypass used: {details['bypass']}")
        print(f"  Reason: {details.get('reason', 'N/A')}")
    
    print("\n✓ With single key, all routing decisions skip scoring for efficiency!")


def example_fallback_chains():
    """Demonstrate fallback chain functionality."""
    print("\n" + "=" * 80)
    print("Example 2: Fallback Chains")
    print("=" * 80)
    
    print("\nScenario: User has OpenAI but not Anthropic or Google")
    print("-" * 80)
    
    # Only OpenAI models available
    available_models = {"gpt-5.2", "grok-4.1", "deepseek-3.2"}
    
    print(f"\nAvailable models: {available_models}")
    print("\nFallback chains:")
    for model, chain in FALLBACK_CHAINS.items():
        print(f"  {model:20s} → {' → '.join(chain)}")
    
    test_cases = [
        ("class MyApp: def __init__(self): pass", "Code", "claude-opus-4.5"),
        ("Once upon a time in a magical forest...", "Story", "gemini-3"),
        ("Breaking news: viral trend on Twitter!", "News", "grok-4.1"),
    ]
    
    print("\n" + "-" * 80)
    print("Routing results:")
    
    for text, category, ideal_model in test_cases:
        model_id, details = classify_chunk(text, available_models=available_models)
        
        print(f"\n  Category: {category}")
        print(f"  Text: {text[:50]}...")
        print(f"  Ideal model: {ideal_model}")
        print(f"  Actual model: {model_id}")
        
        if details.get('fallback_used'):
            print(f"  ⚠️  Fallback used: {ideal_model} → {model_id}")
        else:
            print(f"  ✓ Direct match")


def example_comprehensive_availability():
    """Show behavior with different availability scenarios."""
    print("\n" + "=" * 80)
    print("Example 3: Different Availability Scenarios")
    print("=" * 80)
    
    text = "class DataProcessor:\n    def process(self):\n        return self.data"
    
    scenarios = [
        ("Full access", {"claude-opus-4.5", "gpt-5.2", "gemini-3", "grok-4.1", "deepseek-3.2"}),
        ("OpenAI only", {"gpt-5.2", "grok-4.1", "deepseek-3.2"}),
        ("Anthropic only", {"claude-opus-4.5"}),
        ("Google only", {"gemini-3"}),
        ("Minimal (default)", {"deepseek-3.2"}),
    ]
    
    print(f"\nText: Code snippet")
    print(f"Ideal model: claude-opus-4.5 (Architect profile)")
    print("\n" + "-" * 80)
    
    for scenario_name, available in scenarios:
        model_id, details = classify_chunk(text, available_models=available)
        
        print(f"\n{scenario_name}:")
        print(f"  Available: {len(available)} model(s)")
        print(f"  Routed to: {model_id}")
        
        if details.get('bypass'):
            print(f"  Status: Single-key bypass")
        elif details.get('fallback_used'):
            print(f"  Status: Fallback from {details['ideal_model']}")
        else:
            print(f"  Status: Direct match")


def example_model_map_integration():
    """Show how to integrate with create_model_map."""
    print("\n" + "=" * 80)
    print("Example 4: Integration with Model Map")
    print("=" * 80)
    
    print("\nPractical usage pattern:")
    print("-" * 80)
    
    code = """
from rlm import classify_chunk, create_model_map, get_available_models

# Create model map with your API keys
model_map = create_model_map(
    openai_api_key="your-openai-key",
    # anthropic_api_key not provided
    # google_api_key not provided
)

# Detect which models are actually available
available = get_available_models(model_map)
print(f"Available models: {available}")

# Route text to best available model
text = "SELECT users.name FROM users WHERE active = true"
model_id, details = classify_chunk(text, available_models=available)

# Get the LLM and use it
llm = model_map[model_id]
response = llm.query("Explain this SQL query")

# Check if fallback was used
if details.get('fallback_used'):
    print(f"Note: Fallback from {details['ideal_model']} to {model_id}")
"""
    
    print(code)
    
    print("\nKey benefits:")
    print("  ✓ Automatic detection of available models")
    print("  ✓ Single-key bypass for efficiency")
    print("  ✓ Fallback chains ensure always available")
    print("  ✓ Warnings logged when using fallbacks")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SINGLE-KEY BYPASS & FALLBACK CHAIN EXAMPLES")
    print("=" * 80)
    
    example_single_key_bypass()
    example_fallback_chains()
    example_comprehensive_availability()
    example_model_map_integration()
    
    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80)
