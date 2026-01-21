"""
Example demonstrating the Hive Memory (Shared Intuition) feature.

This example shows how parallel sub-agents can share state using the hive memory,
enabling them to collaborate and build on each other's findings.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rlm import HiveMemory


def example_basic_usage():
    """Basic usage of HiveMemory."""
    print("="*60)
    print("Example 1: Basic HiveMemory Usage")
    print("="*60)
    
    # Create a hive memory instance
    hive = HiveMemory()
    
    # Store some findings
    hive.set("suspect", "butler")
    hive.set("weapon", "candlestick")
    hive.set("location", "library")
    
    # Retrieve values
    print(f"Suspect: {hive.get('suspect')}")
    print(f"Weapon: {hive.get('weapon')}")
    print(f"Missing clue: {hive.get('missing_clue', 'not found')}")
    
    # Get all findings
    print(f"\nAll findings: {hive.get_all()}")
    
    # Clear memory
    hive.clear()
    print(f"After clear: {hive.get_all()}")
    print()


def example_with_mock_rlm():
    """Example showing how HiveMemory integrates with RLM."""
    print("="*60)
    print("Example 2: HiveMemory with Mock RLM Workflow")
    print("="*60)
    
    from rlm import REPLEnvironment
    
    # Create a hive memory
    hive = HiveMemory()
    
    # Create REPL environment with hive
    repl_env = REPLEnvironment(
        context=["doc1", "doc2", "doc3"],
        hive_memory=hive
    )
    
    # Simulate LLM writing code that uses hive
    code1 = """
# First iteration: Store initial findings
hive.set("total_docs", len(context))
hive.set("analyzed_count", 0)
print(f"Initialized: {hive.get_all()}")
"""
    
    output1, success1 = repl_env.execute(code1)
    print(f"Iteration 1 Output:\n{output1}")
    print(f"Success: {success1}\n")
    
    # Second iteration: Update findings
    code2 = """
# Second iteration: Update analysis progress
current_count = hive.get("analyzed_count")
hive.set("analyzed_count", current_count + 1)
hive.set("current_topic", "climate change")
print(f"Updated: {hive.get_all()}")
"""
    
    output2, success2 = repl_env.execute(code2)
    print(f"Iteration 2 Output:\n{output2}")
    print(f"Success: {success2}\n")
    
    # Third iteration: Read accumulated state
    code3 = """
# Third iteration: Use accumulated findings
findings = hive.get_all()
print("Final accumulated findings:")
for key, value in findings.items():
    print(f"  {key}: {value}")
"""
    
    output3, success3 = repl_env.execute(code3)
    print(f"Iteration 3 Output:\n{output3}")
    print(f"Success: {success3}\n")


def example_parallel_scenario():
    """Simulate how hive memory would be used in parallel_query."""
    print("="*60)
    print("Example 3: Parallel Processing Scenario")
    print("="*60)
    
    import threading
    import time
    
    # Create shared hive
    hive = HiveMemory()
    
    # Initial state
    hive.set("total_found", 0)
    hive.set("important_findings", [])
    
    def simulate_parallel_agent(agent_id, chunk):
        """Simulate a parallel sub-agent processing a chunk."""
        print(f"Agent {agent_id} starting...")
        
        # Read current hive state
        current_findings = hive.get("important_findings", [])
        print(f"  Agent {agent_id} sees current findings: {current_findings}")
        
        # Simulate processing
        time.sleep(0.1)
        
        # Update hive with findings (thread-safe)
        if "important" in chunk:
            current_total = hive.get("total_found", 0)
            hive.set("total_found", current_total + 1)
            
            current_list = hive.get("important_findings", [])
            new_list = current_list + [f"Finding from chunk {chunk}"]
            hive.set("important_findings", new_list)
            
            print(f"  Agent {agent_id} found something important!")
        
        print(f"Agent {agent_id} finished")
    
    # Simulate parallel processing
    chunks = ["chunk1_important", "chunk2", "chunk3_important", "chunk4"]
    threads = []
    
    for i, chunk in enumerate(chunks):
        thread = threading.Thread(target=simulate_parallel_agent, args=(i, chunk))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    # Check final state
    print(f"\nFinal hive state:")
    print(f"  Total found: {hive.get('total_found')}")
    print(f"  Important findings: {hive.get('important_findings')}")
    print()


def example_detective_workflow():
    """Example: Detective solving a mystery using hive memory."""
    print("="*60)
    print("Example 4: Detective Mystery Workflow")
    print("="*60)
    
    from rlm import REPLEnvironment
    
    hive = HiveMemory()
    
    # Simulated documents about a mystery
    documents = [
        "The butler was seen near the library at 9 PM",
        "A candlestick was found in the study",
        "The victim was last seen at 8:30 PM",
        "The library window was broken from inside"
    ]
    
    repl_env = REPLEnvironment(
        context=documents,
        hive_memory=hive
    )
    
    # Iteration 1: Initialize investigation
    code1 = """
hive.set("case_status", "investigating")
hive.set("suspects", [])
hive.set("evidence", [])
hive.set("timeline", {})
print("Investigation started")
print(f"Initial state: {hive.get_all()}")
"""
    output1, _ = repl_env.execute(code1)
    print(f"Step 1:\n{output1}\n")
    
    # Iteration 2: Analyze first clue
    code2 = """
# Analyze butler sighting
hive.set("suspects", ["butler"])
hive.set("timeline", {"9:00 PM": "butler at library"})
print(f"After analyzing first clue: {hive.get_all()}")
"""
    output2, _ = repl_env.execute(code2)
    print(f"Step 2:\n{output2}\n")
    
    # Iteration 3: Add more evidence
    code3 = """
# Add weapon evidence
evidence_list = hive.get("evidence", [])
evidence_list.append("candlestick in study")
hive.set("evidence", evidence_list)

timeline = hive.get("timeline", {})
timeline["8:30 PM"] = "victim last seen"
hive.set("timeline", timeline)

print(f"Evidence accumulated: {hive.get('evidence')}")
print(f"Timeline: {hive.get('timeline')}")
"""
    output3, _ = repl_env.execute(code3)
    print(f"Step 3:\n{output3}\n")
    
    # Iteration 4: Final analysis
    code4 = """
# Synthesize all findings
suspects = hive.get("suspects", [])
evidence = hive.get("evidence", [])
timeline = hive.get("timeline", {})

print("="*40)
print("CASE SUMMARY")
print("="*40)
print(f"Suspects: {', '.join(suspects)}")
print(f"Evidence: {len(evidence)} items")
for item in evidence:
    print(f"  - {item}")
print(f"Timeline:")
for time, event in sorted(timeline.items()):
    print(f"  {time}: {event}")
"""
    output4, _ = repl_env.execute(code4)
    print(f"Final Analysis:\n{output4}\n")


if __name__ == "__main__":
    example_basic_usage()
    example_with_mock_rlm()
    example_parallel_scenario()
    example_detective_workflow()
    
    print("="*60)
    print("All examples completed successfully!")
    print("="*60)
