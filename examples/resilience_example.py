"""
Example demonstrating the Resilience Layer with Adaptive Validation.

This example shows:
1. CriticRouter selecting optimal critics for different task types
2. ResilientAgent with tiered validation (instant + semantic)
3. Peer review vs self-correction based on available models
4. Automatic retry with validation feedback
"""

from rlm.resilience import (
    CriticRouter,
    ResilientAgent,
    TaskType,
    ValidationResult,
    detect_task_type
)


class MockLLM:
    """Mock LLM for testing (avoids real API calls)."""
    
    def __init__(self, model_name="mock-gpt"):
        self.model = model_name
        self.call_count = 0
    
    def query(self, prompt):
        """Mock query that returns simple responses."""
        self.call_count += 1
        
        # Simulate critic responses
        if "Senior Reviewer" in prompt or "reviewing your own work" in prompt:
            if "buggy code" in prompt.lower():
                return "FAIL: Found potential null pointer dereference"
            return "PASS"
        
        # Simulate task responses
        if self.call_count == 1:
            # First attempt - intentionally buggy
            return "def process(data):\n    return data.length()  # Bug: should be len()"
        else:
            # Second attempt - fixed
            return "def process(data):\n    return len(data)"


def example_1_critic_routing():
    """Example 1: CriticRouter selecting critics for different tasks."""
    print("=" * 60)
    print("Example 1: Critic Routing")
    print("=" * 60)
    
    # Scenario 1: Multiple models available (peer review)
    print("\n--- Scenario 1: Multiple Models (Peer Review) ---")
    available = {"claude-opus-4.5", "gpt-5.2", "gemini-3"}
    router = CriticRouter(available)
    
    # Code review
    critic, is_peer = router.get_critic(TaskType.CODE, "gpt-5.2")
    print(f"Code task by gpt-5.2:")
    print(f"  Critic: {critic}")
    print(f"  Peer review: {is_peer}")
    print(f"  (Prefers Claude for code)")
    
    # Logic/Math review
    critic, is_peer = router.get_critic(TaskType.LOGIC_MATH, "claude-opus-4.5")
    print(f"\nLogic/Math task by claude-opus-4.5:")
    print(f"  Critic: {critic}")
    print(f"  Peer review: {is_peer}")
    print(f"  (Prefers DeepSeek for logic, but uses GPT as fallback)")
    
    # Writing review
    critic, is_peer = router.get_critic(TaskType.WRITING, "gemini-3")
    print(f"\nWriting task by gemini-3:")
    print(f"  Critic: {critic}")
    print(f"  Peer review: {is_peer}")
    print(f"  (Prefers GPT for writing)")
    
    # Scenario 2: Only one model available (self-correction)
    print("\n--- Scenario 2: Single Model (Self-Correction) ---")
    available_single = {"gpt-5.2"}
    router_single = CriticRouter(available_single)
    
    critic, is_peer = router_single.get_critic(TaskType.CODE, "gpt-5.2")
    print(f"Code task by gpt-5.2 (only model):")
    print(f"  Critic: {critic}")
    print(f"  Peer review: {is_peer}")
    print(f"  (Falls back to self-correction)")


def example_2_instant_validation():
    """Example 2: Tier 1 instant validation (syntax, format)."""
    print("\n" + "=" * 60)
    print("Example 2: Tier 1 - Instant Validation")
    print("=" * 60)
    
    llm = MockLLM()
    router = CriticRouter({"gpt-5.2"})
    agent = ResilientAgent(llm, router, enable_semantic_validation=False)
    
    # Valid Python code
    print("\n--- Valid Python Code ---")
    code = """
def hello():
    print("Hello, World!")
    return True
"""
    result = agent.validate_python_syntax(code)
    print(f"Code:\n{code}")
    print(f"Result: {'PASS' if result.passed else 'FAIL'}")
    print(f"Message: {result.message}")
    
    # Invalid Python code
    print("\n--- Invalid Python Code ---")
    bad_code = """
def hello(:
    print("Missing parenthesis"
    return True
"""
    result = agent.validate_python_syntax(bad_code)
    print(f"Code:\n{bad_code}")
    print(f"Result: {'PASS' if result.passed else 'FAIL'}")
    print(f"Message: {result.message}")
    print(f"Suggestion: {result.suggestion}")
    
    # Valid JSON
    print("\n--- Valid JSON ---")
    json_text = '{"name": "Alice", "age": 30}'
    result = agent.validate_json(json_text)
    print(f"JSON: {json_text}")
    print(f"Result: {'PASS' if result.passed else 'FAIL'}")
    
    # Invalid JSON
    print("\n--- Invalid JSON ---")
    bad_json = '{"name": "Alice", age: 30}'  # Missing quotes
    result = agent.validate_json(bad_json)
    print(f"JSON: {bad_json}")
    print(f"Result: {'PASS' if result.passed else 'FAIL'}")
    print(f"Message: {result.message}")


def example_3_semantic_validation():
    """Example 3: Tier 2 semantic validation with critic."""
    print("\n" + "=" * 60)
    print("Example 3: Tier 2 - Semantic Validation")
    print("=" * 60)
    
    llm = MockLLM("gpt-5.2")
    router = CriticRouter({"claude-opus-4.5", "gpt-5.2"})
    agent = ResilientAgent(llm, router, enable_semantic_validation=True)
    
    # Good code (critic will pass)
    print("\n--- Good Code (Critic Approves) ---")
    good_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    result = agent.semantic_validate(
        good_code,
        TaskType.CODE,
        "gpt-5.2",
        "Implement Fibonacci function"
    )
    print(f"Code:\n{good_code}")
    print(f"Worker: gpt-5.2")
    print(f"Result: {'PASS' if result.passed else 'FAIL'}")
    print(f"Message: {result.message}")


def example_4_full_workflow():
    """Example 4: Complete workflow with retry logic."""
    print("\n" + "=" * 60)
    print("Example 4: Full Workflow with Retry")
    print("=" * 60)
    
    llm = MockLLM("gpt-5.2")
    router = CriticRouter({"claude-opus-4.5", "gpt-5.2"})
    agent = ResilientAgent(
        llm,
        router,
        max_retries=3,
        enable_semantic_validation=False  # Simplify for demo
    )
    
    print("\n--- Task: Generate Python function ---")
    print("(First attempt will have syntax error, second will pass)")
    
    result, history = agent.execute_with_retry(
        task_prompt="Write a function to process data",
        task_type=TaskType.CODE,
        output_format="python",
        task_description="Data processing function"
    )
    
    print(f"\nFinal Result:\n{result}")
    print(f"\nValidation History ({len(history)} attempts):")
    for i, entry in enumerate(history, 1):
        print(f"  Attempt {entry['attempt']}:")
        print(f"    Tier: {entry['tier']}")
        print(f"    Passed: {entry['passed']}")
        print(f"    Message: {entry['message']}")
        if 'feedback' in entry:
            print(f"    Feedback: {entry['feedback']}")


def example_5_task_detection():
    """Example 5: Automatic task type detection."""
    print("\n" + "=" * 60)
    print("Example 5: Task Type Detection")
    print("=" * 60)
    
    test_cases = [
        "Write a function to calculate fibonacci numbers",
        "Calculate the derivative of x^2 + 3x + 1",
        "Write an essay about climate change",
        "Analyze this data and provide insights"
    ]
    
    for text in test_cases:
        task_type = detect_task_type(text)
        print(f"\nText: {text}")
        print(f"Detected type: {task_type.value}")


def example_6_cost_limiting():
    """Example 6: Validation cost limiting."""
    print("\n" + "=" * 60)
    print("Example 6: Validation Cost Limiting")
    print("=" * 60)
    
    llm = MockLLM("gpt-5.2")
    router = CriticRouter({"claude-opus-4.5", "gpt-5.2"})
    
    # Set a low validation budget
    agent = ResilientAgent(
        llm,
        router,
        enable_semantic_validation=True,
        validation_cost_limit=0.05  # Only $0.05 for validation
    )
    
    print(f"\nValidation budget: ${agent.validation_cost_limit:.2f}")
    print(f"Spent so far: ${agent.validation_cost_spent:.2f}")
    
    # First validation (should work)
    print("\n--- Validation 1 ---")
    result = agent.semantic_validate(
        "def test(): pass",
        TaskType.CODE,
        "gpt-5.2"
    )
    print(f"Result: {'PASS' if result.passed else 'FAIL'}")
    print(f"Spent now: ${agent.validation_cost_spent:.2f}")
    
    # Simulate spending budget
    agent.validation_cost_spent = 0.06
    
    # Second validation (should be skipped due to budget)
    print("\n--- Validation 2 (budget exceeded) ---")
    result = agent.semantic_validate(
        "def test2(): pass",
        TaskType.CODE,
        "gpt-5.2"
    )
    print(f"Result: {'PASS' if result.passed else 'FAIL'}")
    print(f"Message: {result.message}")
    print(f"(Validation skipped to stay within budget)")


if __name__ == "__main__":
    print("\n" + "🛡️  RESILIENCE LAYER EXAMPLES  🛡️".center(60))
    print("\nDemonstrating Adaptive Validation with CriticRouter\n")
    
    # Run all examples
    example_1_critic_routing()
    example_2_instant_validation()
    example_3_semantic_validation()
    example_4_full_workflow()
    example_5_task_detection()
    example_6_cost_limiting()
    
    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("✓ Tier 1 (instant): Free, fast syntax/format checks")
    print("✓ Tier 2 (semantic): Smart critic reviews for quality")
    print("✓ Peer review: Different models review each other")
    print("✓ Self-correction: Same model when only one available")
    print("✓ Auto-retry: Fixes issues based on validation feedback")
    print("✓ Cost control: Budget limits prevent overspending")
    print()
