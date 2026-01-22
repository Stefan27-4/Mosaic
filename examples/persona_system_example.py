"""
Persona System Examples - Specialized system prompts for each role.

This example demonstrates:
1. Loading personas and getting specialized system prompts
2. Using ModelResolver for graceful model fallback
3. Mapping routing profiles to personas
4. Single-key mode handling
"""

from rlm import (
    PromptManager,
    ModelResolver,
    get_prompt_manager,
    get_model_resolver,
    map_routing_profile_to_persona,
)


def example_1_load_personas():
    """Example 1: Load and explore persona configurations."""
    print("=" * 60)
    print("Example 1: Loading Personas")
    print("=" * 60)
    
    # Get the global PromptManager instance
    pm = get_prompt_manager()
    
    # List all available personas
    personas = pm.list_personas()
    print(f"\nAvailable Personas: {personas}")
    
    # Get info for each persona
    for persona_id in personas:
        info = pm.get_persona_info(persona_id)
        print(f"\n{persona_id}:")
        print(f"  Display Name: {info['display_name']}")
        print(f"  Description: {info['description']}")
        print(f"  Preferred Model: {info['model_preference']}")
        print(f"  Tools: {', '.join(info['tools'])}")
    
    print("\n" + "=" * 60 + "\n")


def example_2_get_system_prompts():
    """Example 2: Get specialized system prompts."""
    print("=" * 60)
    print("Example 2: Getting System Prompts")
    print("=" * 60)
    
    pm = get_prompt_manager()
    
    # Get system prompt for the Architect persona
    architect_prompt = pm.get_system_message(
        role_id="architect",
        context_type="list of Python files",
        context_total_length=50000,
        context_lengths="[2000, 3000, 2500, ...]",
        hive_state={"pattern_found": "Singleton", "violations": 3}
    )
    
    print("\nArchitect System Prompt (truncated):")
    print(architect_prompt[:500] + "...\n")
    
    # Get system prompt for News Analyst
    news_prompt = pm.get_system_message(
        role_id="news_analyst",
        context_type="list of news articles",
        context_total_length=30000,
        context_lengths="[1500, 2000, 1800, ...]",
        hive_state={"verified_facts": 5, "unverified_claims": 2}
    )
    
    print("\nNews Analyst System Prompt (truncated):")
    print(news_prompt[:500] + "...\n")
    
    print("=" * 60 + "\n")


def example_3_model_resolver_multi_key():
    """Example 3: ModelResolver with multiple API keys."""
    print("=" * 60)
    print("Example 3: ModelResolver - Multi-Key Mode")
    print("=" * 60)
    
    # Simulate having 3 API keys available
    available = {"claude-opus-4.5", "gpt-5.2", "deepseek-3.2"}
    resolver = ModelResolver(available)
    
    print(f"\nAvailable Models: {resolver.list_available_models()}")
    print(f"Model Count: {resolver.get_available_count()}")
    print(f"Single-Key Mode: {resolver.is_single_key_mode()}")
    
    # Resolve various model requests
    test_requests = [
        "claude-opus-4.5",  # Available - direct match
        "gpt-5.2",          # Available - direct match
        "gemini-3",         # Not available - fallback
        "grok-4.1",         # Not available - fallback
    ]
    
    print("\nModel Resolution:")
    for requested in test_requests:
        resolved, was_fallback = resolver.resolve_model(requested, log_fallback=False)
        status = "FALLBACK" if was_fallback else "DIRECT"
        print(f"  {requested:20} → {resolved:20} [{status}]")
    
    print("\n" + "=" * 60 + "\n")


def example_4_model_resolver_single_key():
    """Example 4: ModelResolver with single API key (most common case)."""
    print("=" * 60)
    print("Example 4: ModelResolver - Single-Key Mode")
    print("=" * 60)
    
    # Simulate having only ONE API key (most users)
    available = {"gpt-5.2"}
    resolver = ModelResolver(available)
    
    print(f"\nAvailable Models: {resolver.list_available_models()}")
    print(f"Model Count: {resolver.get_available_count()}")
    print(f"Single-Key Mode: {resolver.is_single_key_mode()}")
    
    # All requests resolve to the single available model
    test_requests = [
        "claude-opus-4.5",  # Not available - uses GPT
        "gpt-5.2",          # Available
        "gemini-3",         # Not available - uses GPT
        "deepseek-3.2",     # Not available - uses GPT
    ]
    
    print("\nModel Resolution (Single-Key Bypass):")
    for requested in test_requests:
        resolved, was_fallback = resolver.resolve_model(requested, log_fallback=False)
        status = "FALLBACK" if was_fallback else "DIRECT"
        print(f"  {requested:20} → {resolved:20} [{status}]")
    
    print("\nNote: In single-key mode, ALL requests use the same model.")
    print("This ensures the system works regardless of which single API key you have.")
    
    print("\n" + "=" * 60 + "\n")


def example_5_routing_integration():
    """Example 5: Integrating Routing Engine with Personas."""
    print("=" * 60)
    print("Example 5: Routing Engine → Persona Integration")
    print("=" * 60)
    
    # Simulate routing engine profile names
    routing_profiles = [
        "Architect",
        "Project Manager",
        "Creative Director",
        "News Analyst",
        "Efficiency Expert",
    ]
    
    print("\nRouting Profile → Persona Role ID Mapping:")
    for profile in routing_profiles:
        role_id = map_routing_profile_to_persona(profile)
        print(f"  {profile:20} → {role_id}")
    
    print("\n" + "=" * 60 + "\n")


def example_6_complete_workflow():
    """Example 6: Complete workflow from routing to specialized prompt."""
    print("=" * 60)
    print("Example 6: Complete Workflow")
    print("=" * 60)
    
    # Step 1: Routing engine determines the profile
    detected_profile = "Architect"  # From HeuristicRoutingEngine
    print(f"\n1. Routing Engine detected profile: {detected_profile}")
    
    # Step 2: Map to persona role ID
    role_id = map_routing_profile_to_persona(detected_profile)
    print(f"2. Mapped to persona role_id: {role_id}")
    
    # Step 3: Get preferred model for this persona
    pm = get_prompt_manager()
    preferred_model = pm.get_model_preference(role_id)
    print(f"3. Persona prefers model: {preferred_model}")
    
    # Step 4: Resolve to available model
    available = {"gpt-5.2", "deepseek-3.2"}  # No Claude available
    resolver = ModelResolver(available)
    resolved_model, was_fallback = resolver.resolve_model(preferred_model, log_fallback=False)
    print(f"4. Resolved to available model: {resolved_model} (fallback: {was_fallback})")
    
    # Step 5: Get specialized system prompt
    system_prompt = pm.get_system_message(
        role_id=role_id,
        context_type="Python codebase",
        context_total_length=100000,
        context_lengths="[5000, 4500, 6000, ...]",
        hive_state={}
    )
    print(f"5. Generated specialized system prompt ({len(system_prompt)} chars)")
    
    # Step 6: Ready to query LLM
    print(f"\n6. Ready to query {resolved_model} with {role_id} persona!")
    print(f"   System prompt optimized for: {pm.get_persona_info(role_id)['display_name']}")
    
    print("\n" + "=" * 60 + "\n")


def example_7_persona_comparison():
    """Example 7: Compare system prompts across personas."""
    print("=" * 60)
    print("Example 7: Persona System Prompt Comparison")
    print("=" * 60)
    
    pm = get_prompt_manager()
    
    print("\nSystem Prompt Lengths by Persona:")
    print("-" * 60)
    
    for persona_id in pm.list_personas():
        prompt = pm.get_system_message(
            role_id=persona_id,
            context_type="mixed",
            context_total_length=10000,
            context_lengths="[1000, 1000, ...]"
        )
        info = pm.get_persona_info(persona_id)
        print(f"{info['display_name']:30} {len(prompt):6} chars")
    
    print("\n" + "=" * 60 + "\n")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("PERSONA SYSTEM EXAMPLES")
    print("=" * 60 + "\n")
    
    try:
        example_1_load_personas()
        example_2_get_system_prompts()
        example_3_model_resolver_multi_key()
        example_4_model_resolver_single_key()
        example_5_routing_integration()
        example_6_complete_workflow()
        example_7_persona_comparison()
        
        print("\n" + "=" * 60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
