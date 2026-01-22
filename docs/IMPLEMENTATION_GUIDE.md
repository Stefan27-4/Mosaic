# RLM Framework Implementation Guide

## Overview

The Recursive Language Models (RLM) framework enables large language models to process arbitrarily long prompts by treating them as part of an external environment that the LLM can programmatically interact with. Instead of feeding long prompts directly into the neural network, RLMs store the prompt as a variable in a Python REPL environment and allow the LLM to write code to examine, decompose, and recursively query itself over snippets of the prompt.

## Key Concepts

### 1. Context as Environment
Rather than passing long context directly to the LLM's context window, RLMs store it as a variable in a REPL environment. The LLM receives only:
- Metadata about the context (type, length, structure)
- The ability to programmatically access and manipulate the context
- Results from code execution

### 2. Recursive Sub-calls
The LLM can invoke itself recursively via an `llm_query()` function available in the REPL. This allows:
- Processing chunks of the context independently
- Aggregating results from multiple sub-queries
- Building up answers iteratively

### 3. Iterative REPL Interaction
The RLM operates in iterations:
1. LLM receives context metadata and previous execution results
2. LLM writes Python code to explore the context
3. Code is executed in the REPL environment
4. Results are fed back to the LLM
5. Process repeats until LLM provides a final answer

## Core Components

### REPLEnvironment (`rlm/repl.py`)

The REPL environment provides:
- **Context Storage**: Stores the prompt/context as a variable
- **Code Execution**: Safely executes Python code
- **State Persistence**: Maintains variables across iterations
- **Output Truncation**: Prevents context overflow by limiting output length
- **Sub-LLM Access**: Provides `llm_query()` function for recursive calls

Key methods:
- `execute(code)`: Execute Python code and return output
- `get_variable(var_name)`: Retrieve a variable from the namespace
- `has_variable(var_name)`: Check if a variable exists

### LLMInterface (`rlm/llm_interface.py`)

Abstract interface for LLM providers with implementations for:

**OpenAIInterface**:
- Supports GPT-4o, GPT-4o-mini, etc.
- Configurable max_tokens, temperature
- Uses OpenAI's chat completions API

**AnthropicInterface**:
- Supports Claude 3.5 Sonnet, Haiku, etc.
- Configurable max_tokens, temperature
- Uses Anthropic's messages API

Key methods:
- `query(prompt, system_prompt)`: Send a query to the LLM
- `get_model_info()`: Get model metadata

### System Prompts (`rlm/prompts.py`)

Three prompt variants:

**RLM_SYSTEM_PROMPT** (Standard):
- Full sub-call capabilities
- Encourages use of `llm_query()` for semantic analysis
- Provides examples of chunking and recursive strategies

**RLM_SYSTEM_PROMPT_CONSERVATIVE**:
- Same as standard but adds warning about sub-call costs
- Encourages batching to minimize calls
- Useful for models that over-use sub-calls (e.g., Qwen)

**RLM_NO_SUBCALLS_PROMPT** (Ablation):
- Removes `llm_query()` function
- LLM must solve using only REPL code
- Useful for comparison and simpler tasks

### Core RLM (`rlm/core.py`)

The main orchestrator that:

1. **Initialization**:
   - Accepts root LLM (for main reasoning) and sub-LLM (for recursive calls)
   - Configures max iterations, recursion depth, output length
   - Selects system prompt based on mode

2. **Query Execution**:
   - Formats context metadata for system prompt
   - Manages conversation history across iterations
   - Extracts and executes code blocks from LLM responses
   - Detects final answers via `FINAL()` or `FINAL_VAR()` tags
   - Tracks trajectory for analysis

3. **Code Extraction**:
   - Looks for ` ```repl ` or ` ```python ` code blocks
   - Extracts code content for execution

4. **Final Answer Detection**:
   - `FINAL(answer)`: Direct answer in text
   - `FINAL_VAR(variable_name)`: Answer stored in REPL variable

5. **Trajectory Tracking**:
   - Records each iteration's response and execution results
   - Counts sub-LLM calls
   - Enables analysis and debugging

### Utilities (`rlm/utils.py`)

Helper functions:
- `chunk_text(text, chunk_size, overlap)`: Split text into overlapping chunks
- `estimate_tokens(text)`: Estimate token count (4 chars/token heuristic)
- `format_context_info(context)`: Format context metadata for prompts
- `load_document(file_path)`: Load text from file
- `truncate_output(text, max_length)`: Truncate with indicator

## Usage Patterns

### Basic Usage

```python
from rlm import RLM, OpenAIInterface

# Initialize LLM interfaces
root_llm = OpenAIInterface(model="gpt-4o")
sub_llm = OpenAIInterface(model="gpt-4o-mini")

# Create RLM
rlm = RLM(root_llm=root_llm, sub_llm=sub_llm)

# Query with context
context = ["Document 1...", "Document 2...", ...]
query = "What is the main topic discussed?"

answer, trajectory = rlm.query(query, context, verbose=True)
print(f"Answer: {answer}")
```

### Without Sub-calls

```python
# Use no_subcalls mode for ablation studies
rlm = RLM(root_llm=root_llm, prompt_mode="no_subcalls")
answer, trajectory = rlm.query(query, context)
```

### Conservative Mode

```python
# Use conservative mode for models that over-use sub-calls
rlm = RLM(root_llm=root_llm, sub_llm=sub_llm, prompt_mode="conservative")
answer, trajectory = rlm.query(query, context)
```

### With Anthropic

```python
from rlm import AnthropicInterface

root_llm = AnthropicInterface(model="claude-3-5-sonnet-20241022")
sub_llm = AnthropicInterface(model="claude-3-5-haiku-20241022")

rlm = RLM(root_llm=root_llm, sub_llm=sub_llm)
answer, trajectory = rlm.query(query, context)
```

## Key Observations from the Paper

1. **Context Length Scaling**: RLMs successfully handle inputs up to 2 orders of magnitude beyond model context windows (tested up to 1M+ tokens).

2. **Quality Improvement**: Even for prompts within context windows, RLMs outperform base LLMs by decomposing and processing context more carefully.

3. **Cost Efficiency**: Despite using multiple sub-calls, total cost is comparable to or cheaper than long-context models due to:
   - Using cheaper models for sub-calls (e.g., GPT-4o-mini vs GPT-4o)
   - Only processing relevant portions of context
   - Avoiding full context in every call

4. **Model Differences**: Different models exhibit different behaviors:
   - GPT models effectively use sub-calls when needed
   - Qwen models tend to over-use sub-calls and benefit from conservative prompts
   - Smaller models can be effective for sub-calls with proper orchestration

5. **Task Complexity**: RLMs show increasing benefits as tasks get more complex:
   - Simple needle-in-haystack: Moderate improvement
   - Complex reasoning over long context: Significant improvement
   - Multi-hop queries: Dramatic improvement

## Architecture Decisions

### Why Separate Root and Sub-LLM?
- **Cost optimization**: Use powerful model for reasoning, cheaper model for context processing
- **Specialization**: Different models may excel at different aspects
- **Flexibility**: Easy to experiment with model combinations

### Why REPL Environment?
- **Familiar paradigm**: Developers understand REPL interactions
- **Rich functionality**: Full Python available for context manipulation
- **State management**: Variables persist across iterations
- **Safe execution**: Isolated namespace prevents interference

### Why Multiple Prompt Modes?
- **Standard**: Best for most models and tasks
- **Conservative**: Prevents wasteful sub-calls in eager models
- **No subcalls**: Enables ablation studies and simpler tasks

## Future Improvements

1. **Enhanced Safety**: Sandboxed execution environment for untrusted contexts
2. **Caching**: Memoize sub-LLM responses for identical queries
3. **Parallel Sub-calls**: Execute independent sub-calls concurrently
4. **Better Token Estimation**: Use tiktoken for accurate counting
5. **Streaming**: Stream responses for better user experience
6. **Error Recovery**: Automatic retry with different strategies on failures
7. **Context Preprocessing**: Automatic chunking and indexing strategies
8. **Multi-modal**: Support for images, PDFs, etc. in context
9. **Observability**: Better logging, metrics, and debugging tools
10. **Optimization**: Automatic tuning of chunk sizes and sub-call strategies

## References

Zhang, A. L., Kraska, T., & Khattab, O. (2025). Recursive Language Models. arXiv:2512.24601
