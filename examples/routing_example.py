"""
Example demonstrating the Heuristic Routing Engine for RLM framework.

This example shows how to use the routing engine to automatically select
the optimal AI model for different types of text chunks.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rlm.routing import (
    HeuristicRoutingEngine,
    route_text,
    PROFILE_ARCHITECT,
    PROFILE_PROJECT_MANAGER,
    PROFILE_CREATIVE_DIRECTOR,
    PROFILE_NEWS_ANALYST,
    PROFILE_EFFICIENCY_EXPERT,
)


def example_basic_routing():
    """Basic routing example."""
    print("=" * 80)
    print("Basic Routing Example")
    print("=" * 80)
    
    # Sample text chunks of different types
    texts = {
        "Code": """
        class DataProcessor:
            def __init__(self):
                import pandas as pd
                self.data = pd.DataFrame()
            
            async def process(self):
                return await self.fetch_data()
        """,
        
        "SQL Query": """
        SELECT users.name, COUNT(orders.id) as order_count
        FROM users
        LEFT JOIN orders ON users.id = orders.user_id
        WHERE orders.created_at >= '2026-01-01'
        GROUP BY users.name
        ORDER BY order_count DESC
        """,
        
        "Story": """
        In the final chapter, the character finally understood the theme
        that had been woven through the narrative. The plot reached its
        climax as the setting transformed from darkness to light.
        """,
        
        "News": """
        Breaking news today: The latest update from Twitter shows a viral
        trend gaining momentum. Current sentiment analysis indicates this
        could be the biggest story of 2026.
        """,
        
        "Math": """
        Theorem: The integral of f(x) over the interval [a,b] can be
        calculated using the fundamental theorem of calculus. To solve
        this equation, we need to find the derivative first.
        """,
        
        "Generic": """
        This is a simple piece of text that doesn't have many specific
        keywords. It's just a regular paragraph about general topics.
        """
    }
    
    # Route each text
    for name, text in texts.items():
        model_id = route_text(text)
        print(f"\n{name}:")
        print(f"  Routed to: {model_id}")


def example_detailed_routing():
    """Detailed routing with confidence scores."""
    print("\n" + "=" * 80)
    print("Detailed Routing Example (with confidence scores)")
    print("=" * 80)
    
    engine = HeuristicRoutingEngine(threshold=0.3)
    
    # Example: Project planning document
    planning_doc = """
    Project Roadmap for Q1 2026
    
    Phase 1: Database Schema Design
    - Milestone 1.1: Define schema structure
    - Step 1: Create tables with PRIMARY KEY and FOREIGN KEY constraints
    - Step 2: Write SQL INSERT and UPDATE statements
    - Deliverable: Complete database schema
    
    Phase 2: API Development
    - Workflow: Design JSON endpoints
    - Timeline: 4 weeks
    - Key deliverables include YAML configuration files
    """
    
    result = engine.route_with_details(planning_doc)
    
    print(f"\nText: Project Planning Document")
    print(f"Selected Model: {result['model_id']}")
    print(f"Profile: {result['profile_name']}")
    print(f"Confidence: {result['confidence']:.3f}")
    print(f"Is Fallback: {result['is_fallback']}")
    print(f"\nAll Profile Scores:")
    for profile, score in result['all_scores'].items():
        print(f"  {profile}: {score:.3f}")


def example_custom_profiles():
    """Example with custom profile configuration."""
    print("\n" + "=" * 80)
    print("Custom Profile Configuration Example")
    print("=" * 80)
    
    from rlm.routing import ProfileConfig
    
    # Create a custom profile for medical/healthcare text
    medical_profile = ProfileConfig(
        name="Medical Specialist",
        model_id="custom-medical-model",
        keywords={
            "patient": 2.0,
            "diagnosis": 2.0,
            "treatment": 2.0,
            "symptom": 1.5,
            "medical": 1.5,
            "doctor": 1.5,
            "prescription": 2.0,
            "clinical": 1.5,
        }
    )
    
    # Create engine with custom profile
    engine = HeuristicRoutingEngine(
        profiles=[
            medical_profile,
            PROFILE_ARCHITECT,
            PROFILE_PROJECT_MANAGER,
        ],
        threshold=0.25
    )
    
    medical_text = """
    The patient presented with symptoms of acute pain. After clinical
    examination, the doctor made a diagnosis and provided a treatment
    plan. A prescription was written for the medical condition.
    """
    
    result = engine.route_with_details(medical_text)
    
    print(f"\nMedical Text:")
    print(f"Selected Model: {result['model_id']}")
    print(f"Profile: {result['profile_name']}")
    print(f"Confidence: {result['confidence']:.3f}")


def example_batch_routing():
    """Example of routing multiple chunks."""
    print("\n" + "=" * 80)
    print("Batch Routing Example")
    print("=" * 80)
    
    engine = HeuristicRoutingEngine()
    
    chunks = [
        "def calculate_sum(a, b): return a + b",
        "SELECT * FROM users WHERE active = true",
        "Once upon a time, in a faraway land, there lived a character...",
        "Breaking: Latest news update from Twitter today!",
        "Solve this equation: ∫x²dx from 0 to 1",
    ]
    
    print(f"\nRouting {len(chunks)} text chunks:")
    for i, chunk in enumerate(chunks, 1):
        model_id, scores = engine.route(chunk)
        max_score = max(scores.values()) if scores else 0.0
        print(f"\n  Chunk {i}: {chunk[:50]}...")
        print(f"    → {model_id} (confidence: {max_score:.3f})")


def example_threshold_comparison():
    """Compare routing with different thresholds."""
    print("\n" + "=" * 80)
    print("Threshold Comparison Example")
    print("=" * 80)
    
    # Text with weak signals
    weak_text = "This document mentions SQL once but is mostly generic content."
    
    thresholds = [0.1, 0.3, 0.5, 0.7]
    
    print(f"\nText: '{weak_text}'")
    print(f"\nRouting with different thresholds:")
    
    for threshold in thresholds:
        engine = HeuristicRoutingEngine(threshold=threshold)
        result = engine.route_with_details(weak_text)
        print(f"\n  Threshold {threshold}:")
        print(f"    Model: {result['model_id']}")
        print(f"    Confidence: {result['confidence']:.3f}")
        print(f"    Fallback: {result['is_fallback']}")


def example_model_mapping():
    """Show how to map model IDs to actual LLM interfaces."""
    print("\n" + "=" * 80)
    print("Model Mapping Example")
    print("=" * 80)
    
    # This demonstrates how you would integrate routing with actual LLM calls
    # (Note: This is conceptual - actual implementation would require API keys)
    
    model_mapping = {
        "claude-opus-4.5": "Anthropic Claude Opus - For complex code/legal",
        "gpt-5.2": "OpenAI GPT-5.2 - For SQL/planning/data",
        "gemini-3": "Google Gemini 3 - For creative/research",
        "grok-4.1": "xAI Grok 4.1 - For news/social media",
        "deepseek-3.2": "DeepSeek 3.2 - For math/logic/default",
    }
    
    engine = HeuristicRoutingEngine()
    
    sample_texts = [
        "class MyApp: def __init__(self): pass",
        "SELECT * FROM database",
        "Write a story about adventure",
    ]
    
    print("\nMapping routed models to actual LLM services:")
    for text in sample_texts:
        model_id = route_text(text)
        llm_service = model_mapping.get(model_id, "Unknown")
        print(f"\n  Text: '{text}'")
        print(f"  Model ID: {model_id}")
        print(f"  Service: {llm_service}")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("HEURISTIC ROUTING ENGINE EXAMPLES")
    print("=" * 80)
    
    example_basic_routing()
    example_detailed_routing()
    example_custom_profiles()
    example_batch_routing()
    example_threshold_comparison()
    example_model_mapping()
    
    print("\n" + "=" * 80)
    print("Examples completed successfully!")
    print("=" * 80)
