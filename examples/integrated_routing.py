"""
Example demonstrating the integrated routing and model mapping.

This shows how to use the routing engine with pre-configured model mappings,
so users only need to provide API keys.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rlm import route_text, create_model_map


def example_with_model_map():
    """Example using the integrated model map."""
    print("=" * 80)
    print("Integrated Routing + Model Map Example")
    print("=" * 80)
    
    # Create model map - users only need to provide API keys
    # API keys can be passed directly or use environment variables
    # (OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY)
    model_map = create_model_map(
        # openai_api_key="your-openai-key",      # or set OPENAI_API_KEY env var
        # anthropic_api_key="your-anthropic-key", # or set ANTHROPIC_API_KEY env var
        # google_api_key="your-google-key",       # or set GOOGLE_API_KEY env var
    )
    
    print("\nAvailable models in map:")
    for model_id, llm in model_map.items():
        info = llm.get_model_info()
        print(f"  {model_id} → {info['provider']}/{info['model']}")
    
    # Example texts to route
    examples = [
        ("Code", "class DataProcessor:\n    def process(self):\n        return self.data"),
        ("SQL", "SELECT users.name FROM users WHERE active = true"),
        ("Story", "Once upon a time, there was a character who lived in a magical setting."),
        ("News", "Breaking news today: viral trend on Twitter gains momentum!"),
        ("Math", "Calculate the integral of x^2 from 0 to 1"),
    ]
    
    print("\n" + "=" * 80)
    print("Routing Examples:")
    print("=" * 80)
    
    for name, text in examples:
        # Route the text
        model_id = route_text(text)
        
        # Get the corresponding LLM
        llm = model_map[model_id]
        
        print(f"\n{name}:")
        print(f"  Text: {text[:60]}...")
        print(f"  Routed to: {model_id}")
        print(f"  Using: {llm.get_model_info()['provider']}/{llm.get_model_info()['model']}")
        
        # Now you can use llm.query() to actually call the model
        # response = llm.query("Analyze this: " + text)


def example_with_custom_mapping():
    """Example with custom model mapping."""
    print("\n" + "=" * 80)
    print("Custom Model Mapping Example")
    print("=" * 80)
    
    from rlm import OpenAIInterface, AnthropicInterface, GeminiInterface
    
    # Create your own custom mapping
    custom_map = {
        "claude-opus-4.5": AnthropicInterface(model="claude-3-5-sonnet-20241022"),
        "gpt-5.2": OpenAIInterface(model="gpt-4o"),
        "gemini-3": GeminiInterface(model="gemini-1.5-flash"),  # Use Flash instead of Pro
        "grok-4.1": OpenAIInterface(model="gpt-4o-mini"),
        "deepseek-3.2": OpenAIInterface(model="gpt-3.5-turbo"),  # Use cheaper model
    }
    
    text = "def calculate_fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"
    model_id = route_text(text)
    
    print(f"\nText: {text[:60]}...")
    print(f"Routed to: {model_id}")
    print(f"Custom mapping uses: {custom_map[model_id].get_model_info()}")


def example_with_rlm_integration():
    """Example integrating routing with RLM framework."""
    print("\n" + "=" * 80)
    print("RLM + Routing Integration Example")
    print("=" * 80)
    
    from rlm import RLM, OpenAIInterface
    
    # For this example, we'll use OpenAI for both root and sub-LLM
    # In production, you'd use the routing engine to select models dynamically
    root_llm = OpenAIInterface(model="gpt-4o")
    sub_llm = OpenAIInterface(model="gpt-4o-mini")
    
    rlm = RLM(root_llm=root_llm, sub_llm=sub_llm, prompt_mode="standard")
    
    # Example: Route sub-queries to specialized models
    # This is a conceptual example - actual implementation would require
    # modifying the RLM class to use the routing engine
    
    print("\nConceptual workflow:")
    print("1. User submits query with large context")
    print("2. RLM breaks it into chunks")
    print("3. Each chunk is routed to optimal model:")
    print("   - Code chunks → Claude Opus")
    print("   - SQL chunks → GPT-4o")
    print("   - Story chunks → Gemini")
    print("   - etc.")
    print("4. Results aggregated by RLM")


def check_api_keys():
    """Check which API keys are available."""
    print("\n" + "=" * 80)
    print("API Key Status Check")
    print("=" * 80)
    
    keys = {
        "OpenAI": os.getenv("OPENAI_API_KEY"),
        "Anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "Google": os.getenv("GOOGLE_API_KEY"),
    }
    
    for provider, key in keys.items():
        status = "✓ Set" if key else "✗ Not set"
        print(f"  {provider}: {status}")
    
    if not any(keys.values()):
        print("\n⚠️  No API keys found in environment variables.")
        print("   Set them before using the models:")
        print("   export OPENAI_API_KEY='your-key'")
        print("   export ANTHROPIC_API_KEY='your-key'")
        print("   export GOOGLE_API_KEY='your-key'")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("INTEGRATED ROUTING + MODEL EXAMPLES")
    print("=" * 80)
    
    check_api_keys()
    example_with_model_map()
    example_with_custom_mapping()
    example_with_rlm_integration()
    
    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80)
    print("\nNote: Actual API calls are commented out to avoid charges.")
    print("Uncomment llm.query() lines to make real API calls.")
