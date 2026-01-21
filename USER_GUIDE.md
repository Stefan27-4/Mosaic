# Mosaic - RLM Framework User Guide

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

**Mosaic** is a Python implementation of the Recursive Language Models (RLM) framework, which enables large language models to process arbitrarily long prompts by treating them as part of an external environment that the LLM can programmatically interact with.

Instead of feeding long prompts directly into the LLM's context window, RLMs:
- Store the prompt as a variable in a Python REPL environment
- Provide metadata about the context (type, length, structure)
- Allow the LLM to write code to examine and process the context
- Enable recursive sub-LLM calls for semantic analysis
- Build answers iteratively through multiple REPL interactions

## Key Benefits

- **🚀 Infinite Context**: Process prompts 2+ orders of magnitude beyond context windows (tested up to 1M+ tokens)
- **💰 Cost Efficient**: Comparable or cheaper than long-context models by using cheaper sub-LLMs
- **🎯 Better Quality**: Outperforms base LLMs even on shorter prompts through careful decomposition
- **🔧 Flexible**: Works with OpenAI, Anthropic, and any LLM provider
- **📊 Observable**: Full trajectory tracking for analysis and debugging
- **🎛️ Intelligent Routing**: Automatic model selection based on content type (NEW!)

## Installation

```bash
# Clone the repository
git clone https://github.com/Stefan27-4/Mosaic.git
cd Mosaic

# Install dependencies
pip install -r requirements.txt
```

**Requirements:**
- Python 3.8+
- `openai>=1.0.0` (for OpenAI models)
- `anthropic>=0.18.0` (for Anthropic models)

## Quick Start

### Basic Usage with OpenAI

```python
from rlm import RLM, OpenAIInterface

# Initialize LLM interfaces
root_llm = OpenAIInterface(model="gpt-4o", max_tokens=4096)
sub_llm = OpenAIInterface(model="gpt-4o-mini", max_tokens=16384)

# Create RLM instance
rlm = RLM(root_llm=root_llm, sub_llm=sub_llm)

# Prepare context (can be string, list, or dict)
context = [
    "Document 1: The Eiffel Tower is 330 meters tall...",
    "Document 2: It was designed by Gustave Eiffel...",
    # ... many more documents
]

# Execute query
query = "What is the height of the Eiffel Tower?"
answer, trajectory = rlm.query(query, context, verbose=True)

print(f"Answer: {answer}")
```

### Using Anthropic Models

```python
from rlm import RLM, AnthropicInterface

root_llm = AnthropicInterface(model="claude-3-5-sonnet-20241022")
sub_llm = AnthropicInterface(model="claude-3-5-haiku-20241022")

rlm = RLM(root_llm=root_llm, sub_llm=sub_llm)
answer, trajectory = rlm.query(query, context)
```

### API Keys

Set your API keys as environment variables:

```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

Or pass them directly:

```python
root_llm = OpenAIInterface(api_key="your-key", model="gpt-4o")
```

## Usage Modes

### Standard Mode (Default)

Full RLM capabilities with recursive sub-LLM calls:

```python
rlm = RLM(root_llm=root_llm, sub_llm=sub_llm, prompt_mode="standard")
```

The LLM can use `llm_query()` to recursively call itself on context snippets.

### Conservative Mode

For models that over-use sub-calls (e.g., Qwen):

```python
rlm = RLM(root_llm=root_llm, sub_llm=sub_llm, prompt_mode="conservative")
```

Adds warnings about sub-call costs and encourages batching.

### No Subcalls Mode (Ablation)

Disables recursive sub-calls - only REPL code execution:

```python
rlm = RLM(root_llm=root_llm, prompt_mode="no_subcalls")
```

Useful for simpler tasks or comparison studies.

## Configuration

### RLM Parameters

```python
rlm = RLM(
    root_llm=root_llm,           # Main LLM for reasoning
    sub_llm=sub_llm,             # LLM for sub-calls (optional, defaults to root_llm)
    max_iterations=20,           # Maximum REPL iterations
    max_recursion_depth=5,       # Maximum depth for nested sub-calls
    max_output_length=10000,     # Maximum chars in REPL output
    prompt_mode="standard"       # "standard", "conservative", or "no_subcalls"
)
```

### LLM Interface Parameters

```python
# OpenAI
llm = OpenAIInterface(
    model="gpt-4o",              # Model name
    api_key=None,                # API key (or use env var)
    max_tokens=4096,             # Max tokens to generate
    temperature=0.0              # Sampling temperature
)

# Anthropic
llm = AnthropicInterface(
    model="claude-3-5-sonnet-20241022",
    api_key=None,
    max_tokens=4096,
    temperature=0.0
)
```

## Examples

Run the included examples:

```bash
# Set API key
export OPENAI_API_KEY="your-key"

# Run example
python examples/basic_usage.py
```

The example demonstrates:
- OpenAI integration
- Anthropic integration  
- No subcalls mode
- Different context types

## How It Works

1. **Context Storage**: The prompt is stored as a variable in a Python REPL, not fed to the LLM
2. **LLM Query**: The LLM receives metadata and writes Python code to explore the context
3. **Code Execution**: Code runs in the REPL, results are returned to the LLM
4. **Recursive Calls**: The LLM can invoke `llm_query()` to analyze context snippets
5. **Iteration**: Process repeats until LLM provides `FINAL(answer)` or `FINAL_VAR(variable)`

### Example LLM Interaction

```python
# LLM writes code:
```repl
# Check context structure
print(f"Context has {len(context)} documents")

# Search for relevant documents
relevant = [doc for doc in context if "Eiffel" in doc]
print(f"Found {len(relevant)} relevant documents")

# Use sub-LLM to analyze
answer = llm_query(f"What is the height mentioned in: {relevant[0]}")
```

# LLM provides final answer:
FINAL(The Eiffel Tower is 330 meters tall)
```

## Trajectory Analysis

The `trajectory` returned by `query()` contains detailed execution information:

```python
answer, trajectory = rlm.query(query, context)

for iteration in trajectory:
    print(f"Iteration {iteration['iteration']}:")
    print(f"  Code blocks: {len(iteration.get('code_blocks', []))}")
    print(f"  Execution results: {iteration.get('execution_results', [])}")
    print(f"  Sub-calls: {iteration.get('subcalls', 0)}")
```

## Testing

Run the test suite to verify your installation:

```bash
python test_implementation.py
```

This tests all core functionality without requiring API keys.

## Documentation

- **[Implementation Guide](docs/IMPLEMENTATION_GUIDE.md)**: Detailed architecture and design decisions
- **[Research Paper](README.md)**: Original RLM paper (Zhang et al., 2025)

## Architecture

```
rlm/
├── __init__.py          # Package exports
├── core.py              # Main RLM orchestrator
├── repl.py              # REPL environment
├── llm_interface.py     # LLM provider interfaces
├── prompts.py           # System prompts
└── utils.py             # Utility functions
```

## Use Cases

### 1. Long Document Analysis
Process documents beyond context windows:
```python
context = load_document("very_long_book.txt")
query = "Summarize the main themes"
answer, _ = rlm.query(query, context)
```

### 2. Multi-Document QA
Answer questions across many documents:
```python
context = [doc1, doc2, ..., doc100]
query = "Which documents mention climate change?"
answer, _ = rlm.query(query, context)
```

### 3. Code Analysis
Analyze large codebases:
```python
context = {"file1.py": code1, "file2.py": code2, ...}
query = "Find all functions that use the database"
answer, _ = rlm.query(query, context)
```

### 4. Data Processing
Process structured data:
```python
context = large_json_data
query = "What is the average age of users?"
answer, _ = rlm.query(query, context)
```

## Intelligent Routing (NEW!)

The Heuristic Routing Engine automatically selects the optimal AI model based on text content using keyword-density scoring.

### Quick Start with Routing

```python
from rlm import route_text

# Automatic model selection
code_text = "class MyApp: def process(): return data"
model_id = route_text(code_text)  # Returns: "claude-opus-4.5"

sql_text = "SELECT * FROM users WHERE active = true"
model_id = route_text(sql_text)  # Returns: "gpt-5.2"
```

### Detailed Routing

```python
from rlm import HeuristicRoutingEngine

engine = HeuristicRoutingEngine(threshold=0.3)

result = engine.route_with_details(text)
print(f"Model: {result['model_id']}")
print(f"Profile: {result['profile_name']}")
print(f"Confidence: {result['confidence']}")
```

### 5 Specialist Profiles

The router automatically detects:
1. **Architect** (Claude Opus 4.5) - Code, legal documents
2. **Project Manager** (GPT-5.2) - SQL, planning, data structures
3. **Creative Director** (Gemini 3) - Stories, research, visuals
4. **News Analyst** (Grok 4.1) - Current events, social media
5. **Efficiency Expert** (DeepSeek 3.2) - Math, logic, default fallback

For complete routing documentation, see [docs/ROUTING_GUIDE.md](docs/ROUTING_GUIDE.md)

## Best Practices

1. **Use Cheaper Sub-LLMs**: Save costs by using GPT-4o-mini or Claude Haiku for sub-calls
2. **Choose Right Mode**: Use conservative mode for models that over-use sub-calls
3. **Monitor Trajectory**: Check trajectory for optimization opportunities
4. **Batch Context**: Group related documents for more efficient processing
5. **Set Limits**: Configure max_iterations and max_recursion_depth appropriately

## Limitations

- Requires API keys for OpenAI or Anthropic
- Sub-calls add latency (can be parallelized in future)
- REPL environment is not sandboxed (use trusted contexts only)
- Token estimation is approximate (uses 4 chars/token heuristic)

## Future Improvements

See [Implementation Guide](docs/IMPLEMENTATION_GUIDE.md) for planned enhancements:
- Sandboxed execution
- Response caching
- Parallel sub-calls
- Multi-modal support
- Better token estimation

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Citation

If you use this framework in your research, please cite:

```bibtex
@article{zhang2025recursive,
  title={Recursive Language Models},
  author={Zhang, Alex L. and Kraska, Tim and Khattab, Omar},
  journal={arXiv preprint arXiv:2512.24601},
  year={2025}
}
```

## License

MIT License - see LICENSE file for details

## Support

- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/Stefan27-4/Mosaic/issues)
- **Documentation**: See [docs/](docs/) directory
- **Examples**: See [examples/](examples/) directory

## Acknowledgments

This implementation is based on the research paper "Recursive Language Models" by Zhang et al. (2025) from MIT CSAIL.
