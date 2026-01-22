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
- **🎛️ Intelligent Routing**: Automatic model selection based on content type
- **⚡ Parallel Processing**: 10-20x speedup with asynchronous MapReduce (NEW!)
- **🧠 Hive Mind**: Shared state across parallel sub-agents for collaborative processing (NEW!)
- **🛡️ Adaptive Validation**: Tiered validation with peer review and self-correction (NEW!)
- **💾 Smart Caching**: SQLite-based response caching to reduce costs and improve performance (NEW!)

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

# Run examples
python examples/basic_usage.py
python examples/parallel_processing_example.py  # Async MapReduce demo
python examples/hive_memory_example.py          # Hive Mind demo
```

The examples demonstrate:
- OpenAI and Anthropic integration  
- No subcalls mode
- Different context types
- Parallel processing with async MapReduce
- Hive memory for shared state

## Hive Memory (Shared Intuition)

**NEW**: Enable parallel sub-agents to share findings instantly rather than working in isolation.

### Overview

The `hive` object provides thread-safe shared memory that persists across REPL iterations and is accessible to all parallel sub-agents. This creates a "hive mind" effect where agents can collaborate.

### Basic Usage

```repl
# Store findings
hive.set("suspect", "butler")
hive.set("weapon", "candlestick")

# Retrieve values
suspect = hive.get("suspect")
all_findings = hive.get_all()

# Clear for new session
hive.clear()
```

### Integration with Parallel Processing

When you use `parallel_query()`, the current hive state is automatically injected into each sub-agent's prompt:

```repl
# Set shared context
hive.set("search_topic", "climate change")

# Sub-agents see hive state automatically
results = parallel_query("Find mentions of the topic in: {chunk}", documents)

# Accumulate results
hive.set("total_mentions", len(results))
```

### Common Patterns

**Pattern 1: Fact Accumulation**
```repl
hive.set("important_facts", [])

for doc in context[:10]:
    facts = extract_key_points(doc)
    current = hive.get("important_facts", [])
    hive.set("important_facts", current + facts)
```

**Pattern 2: Progressive Refinement**
```repl
# First pass
candidates = parallel_query("Find potential answers in: {chunk}", context)
hive.set("candidates", candidates)

# Second pass (in next iteration)
best = llm_query(f"Best answer from: {hive.get('candidates')}")
```

**Pattern 3: Investigation Workflow**
```repl
# Initialize
hive.set("suspects", [])
hive.set("evidence", [])

# Build case
hive.set("suspects", hive.get("suspects") + ["butler"])
hive.set("evidence", hive.get("evidence") + ["candlestick"])

# Solve
solution = llm_query(f"Analyze: {hive.get_all()}")
```

### API

- `hive.set(key, value)` - Store a value (thread-safe)
- `hive.get(key, default=None)` - Retrieve a value (thread-safe)
- `hive.get_all()` - Get snapshot of all data (thread-safe)
- `hive.clear()` - Wipe all memory (thread-safe)

**Note**: Each query session gets its own fresh hive memory instance.

See `docs/HIVE_MEMORY.md` for complete documentation and `examples/hive_memory_example.py` for working examples.

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

### Integrated Model Mapping (NEW!)

Pre-configured model mappings - just add your API keys:

```python
from rlm import route_text, create_model_map

# Set API keys via environment variables or pass directly
# export OPENAI_API_KEY='your-key'
# export ANTHROPIC_API_KEY='your-key'
# export GOOGLE_API_KEY='your-key'

# Create model map (automatically uses env vars)
model_map = create_model_map()

# Or pass API keys directly
model_map = create_model_map(
    openai_api_key="your-openai-key",
    anthropic_api_key="your-anthropic-key",
    google_api_key="your-google-key"
)

# Route and use
text = "SELECT users.name FROM users WHERE active = true"
model_id = route_text(text)  # Returns: "gpt-5.2"
llm = model_map[model_id]
response = llm.query("Explain this SQL query")
```

**Model Mappings:**
- `claude-opus-4.5` → Anthropic Claude 3.5 Sonnet
- `gpt-5.2` → OpenAI GPT-4o
- `gemini-3` → Google Gemini 1.5 Pro
- `grok-4.1` → OpenAI GPT-4o-mini (Grok API not available yet)
- `deepseek-3.2` → OpenAI GPT-4o-mini (DeepSeek API not available yet)

### Smart Routing with Fallbacks (NEW!)

Automatic optimization and fallback handling:

```python
from rlm import classify_chunk, get_available_models, create_model_map

# Create model map (only provide keys you have)
model_map = create_model_map(
    openai_api_key="your-key"
    # No Anthropic or Google keys
)

# Detect available models
available = get_available_models(model_map)

# Smart routing with fallbacks
text = "class MyApp: def process(): return data"
model_id, details = classify_chunk(text, available_models=available)

llm = model_map[model_id]
response = llm.query("your prompt")

# Check routing details
if details.get('fallback_used'):
    print(f"Fallback: {details['ideal_model']} → {model_id}")
```

**Key Optimizations:**

1. **Single-Key Bypass**: If you only have one API key, routing skips all scoring for maximum efficiency
2. **Fallback Chains**: When ideal model unavailable, automatically uses next best option:
   - Architect (Claude) → Project Manager (GPT) → Efficiency (default)
   - Creative (Gemini) → Project Manager (GPT) → Efficiency (default)
   - News (Grok) → Project Manager (GPT) → Efficiency (default)
3. **Logging**: Warnings logged when fallbacks are triggered

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

## Resilience Layer - Adaptive Validation

The resilience layer provides intelligent quality assurance through tiered validation:

### Quick Start

```python
from rlm import ResilientAgent, CriticRouter, TaskType, OpenAIInterface

# Setup LLM and critic router
llm = OpenAIInterface(model="gpt-4o")
available_models = {"claude-opus-4.5", "gpt-5.2"}
router = CriticRouter(available_models)

# Create resilient agent with validation
agent = ResilientAgent(
    llm_interface=llm,
    critic_router=router,
    max_retries=3,
    enable_semantic_validation=True,
    validation_cost_limit=1.0  # Max $1 on validation
)

# Execute with automatic validation and retry
result, validation_history = agent.execute_with_retry(
    task_prompt="Write a function to process user data",
    task_type=TaskType.CODE,
    output_format="python",
    task_description="Data processing function"
)

print(f"Result: {result}")
print(f"Validation attempts: {len(validation_history)}")
```

### Two-Tier Validation

**Tier 1: Instant Checks (Free & Fast)**
- Python syntax validation
- JSON format validation  
- Zero cost, <1ms speed
- Immediate retry on failure

**Tier 2: Semantic Checks (Smart Critics)**
- Logic error detection
- Security vulnerability checks
- Peer review or self-correction
- ~$0.01 per check, 1-3 seconds

### Peer Review vs Self-Correction

The system automatically adapts based on available models:

```python
# Multiple models available → Peer Review
available = {"claude-opus-4.5", "gpt-5.2", "gemini-3"}
router = CriticRouter(available)

critic, is_peer = router.get_critic(TaskType.CODE, "gpt-5.2")
# Returns: ("claude-opus-4.5", True) - Different model reviews!

# Single model available → Self-Correction
available_single = {"gpt-5.2"}
router_single = CriticRouter(available_single)

critic, is_peer = router_single.get_critic(TaskType.CODE, "gpt-5.2")
# Returns: ("gpt-5.2", False) - Same model reviews itself
```

### Task Types and Critic Routing

Different task types route to optimal critics:

- **CODE**: Claude Opus > Claude Sonnet > GPT-4
- **LOGIC_MATH**: DeepSeek > GPT-4 > Claude
- **WRITING**: GPT-4 > Gemini > Claude
- **GENERAL**: GPT-4 > Claude > Gemini > DeepSeek

```python
from rlm import detect_task_type

# Auto-detect task type
task = detect_task_type("Write a function to calculate primes")
# Returns: TaskType.CODE

task = detect_task_type("Solve: x^2 + 3x - 4 = 0")
# Returns: TaskType.LOGIC_MATH
```

### Cost Control

Validation costs are automatically tracked and limited:

```python
agent = ResilientAgent(
    llm,
    router,
    enable_semantic_validation=True,
    validation_cost_limit=0.50  # Max $0.50
)

result, history = agent.execute_with_retry(...)

print(f"Validation cost: ${agent.validation_cost_spent:.2f}")
# Automatically stops semantic validation if budget exceeded
```

### Complete Documentation

For detailed information, see:
- **[Resilience Guide](docs/RESILIENCE_GUIDE.md)** - Complete documentation
- **[Examples](examples/resilience_example.py)** - Working code examples

## 7. Caching Layer (Smart Memorization)

The Mosaic Caching Layer provides SQLite-based response caching to optimize performance and reduce API costs by avoiding duplicate calls.

### Basic Caching

```python
from rlm import get_cache

cache = get_cache()

# Responses are automatically cached on first call
# Subsequent identical calls return cached responses instantly

# View cache statistics
savings = cache.get_total_savings()
print(f"Tokens saved: {savings['total_tokens_saved']:,}")
print(f"Cost savings: ${savings['estimated_cost_savings_usd']:.2f}")
```

### How It Works

The cache uses consistent SHA256 hashing of request parameters:

- **Normalized Inputs**: Whitespace and formatting differences don't affect caching
- **Smart Keys**: Hashes based on prompt + model + temperature + system_prompt
- **Persistent Storage**: SQLite database at `~/.mosaic/cache.db`
- **Automatic Updates**: Last accessed timestamp tracked for analytics

### Integration with LLM Interfaces

Caching works automatically with all LLM calls:

```python
from rlm import OpenAIInterface

llm = OpenAIInterface(model="gpt-4o")

# First call - hits API and caches response
response1 = llm.query("Explain quantum computing", use_cache=True)

# Second call - returns cached response instantly (no API call!)
response2 = llm.query("Explain quantum computing", use_cache=True)

# Disable caching for specific calls
response3 = llm.query("Explain quantum computing", use_cache=False)
```

### Temperature Considerations

Different temperatures create different cache entries:

```python
# These are cached separately
response_deterministic = llm.query("Hello", temperature=0.0)
response_creative = llm.query("Hello", temperature=0.7)

# Use temperature=0.0 for maximum cache hits
```

### Cache Management

```python
from rlm import get_cache

cache = get_cache()

# Get detailed statistics
stats = cache.get_cache_stats()
print(f"Total entries: {stats['total_cache_entries']}")
print(f"Unique models: {stats['unique_models']}")

# Per-model breakdown
for model_stat in stats['per_model_stats']:
    print(f"{model_stat['model_id']}: {model_stat['entry_count']} entries")

# Clear old entries
deleted = cache.clear_cache(older_than_days=30)
print(f"Deleted {deleted} old entries")

# Optimize database
cache.vacuum()
```

### Performance Benefits

The cache provides significant performance improvements:

- **Speed**: Instant responses for cached queries (<1ms vs 1-3s API call)
- **Cost**: Avoid duplicate API calls, reducing token costs
- **Reliability**: Cached responses available even during API outages
- **Consistency**: Same query returns same result (with temperature=0.0)

### Best Practices

1. **Use temperature=0.0** for deterministic responses and maximum cache hits
2. **Monitor savings** regularly with `cache.get_total_savings()`
3. **Periodic cleanup** to remove old entries and optimize database
4. **Disable selectively** when you need fresh responses

### Complete Documentation

For detailed information, see:
- **[Caching Guide](docs/CACHING_GUIDE.md)** - Complete documentation
- **[Examples](examples/cache_example.py)** - Working code examples

## Token Optimization

Accurate token counting and dynamic chunk size calculation for optimal performance.

### Features

- **Precise Token Counting**: Uses `tiktoken` for accurate counts
- **Cost Estimation**: Calculate projected API costs before processing
- **Dynamic Chunking**: Automatically optimizes chunk sizes based on model capacity
- **Task-Specific Tuning**: Different strategies for code, summarization, and general tasks

### Basic Token Counting

```python
from rlm import count_tokens, estimate_cost, get_model_limit

# Count tokens accurately
text = "Hello, world! This is a sample document."
tokens = count_tokens(text, model="gpt-4o")
print(f"Tokens: {tokens}")

# Estimate cost
cost = estimate_cost(text, model="gpt-4o")
print(f"Cost: ${cost:.6f}")

# Get model context limit
limit = get_model_limit("gpt-4o")
print(f"GPT-4o limit: {limit:,} tokens")
```

### Dynamic Chunk Sizing

```python
from rlm import smart_chunk_text, OptTaskType

# Load document
with open("large_document.txt") as f:
    document = f.read()

# Smart chunking for summarization (smaller chunks)
chunks = smart_chunk_text(
    text=document,
    model="gpt-4o",
    task_type=OptTaskType.SUMMARIZATION,
    overlap_ratio=0.1  # 10% overlap
)

print(f"Split into {len(chunks)} optimized chunks")
```

### Task Types

```python
from rlm import OptTaskType, calculate_chunk_size

# Different task types optimize differently
models = ["gpt-4o", "claude-opus-4.5", "gemini-1.5-pro"]

for model in models:
    code_size = calculate_chunk_size(model, OptTaskType.CODE_ANALYSIS)
    summ_size = calculate_chunk_size(model, OptTaskType.SUMMARIZATION)
    gen_size = calculate_chunk_size(model, OptTaskType.GENERAL)
    
    print(f"{model}:")
    print(f"  Code Analysis: {code_size:,} tokens (80% of capacity)")
    print(f"  Summarization: {summ_size:,} tokens (20% of capacity)")
    print(f"  General: {gen_size:,} tokens (40% of capacity)")
```

### Supported Models

| Model ID | Context Limit | Cost per 1M Tokens |
|----------|--------------|-------------------|
| claude-opus-4.5 | 200,000 | $15.00 |
| gpt-5.2 (gpt-4o) | 128,000 | $5.00 |
| gemini-3 (gemini-1.5-pro) | 2,000,000 | $1.25 |
| grok-4.1 | 128,000 | $2.00 |
| deepseek-3.2 | 64,000 | $0.50 |

### Advanced Usage

```python
from rlm import TokenGatekeeper, ChunkAutoTuner, OptTaskType

# Get singleton instances
gatekeeper = TokenGatekeeper()
tuner = ChunkAutoTuner()

# Accurate token counting
tokens = gatekeeper.count(text, model="gpt-4o")

# Calculate optimal chunk size
chunk_size = tuner.calculate_optimal_chunk_size(
    model_id="gpt-4o",
    task_type=OptTaskType.CODE_ANALYSIS
)

# Get optimally-sized chunks with custom overlap
chunks = tuner.get_optimal_chunks(
    text=document,
    model_id="gpt-4o",
    task_type=OptTaskType.GENERAL,
    overlap_ratio=0.15  # 15% overlap
)
```

### Cost-Aware Processing

```python
from rlm import count_tokens, estimate_cost, get_model_limit

document = "...large document..."
budget = 1.00  # $1 budget

# Find cheapest model within budget
models = ["gpt-4o", "gpt-4o-mini", "claude-opus-4.5", "deepseek-3.2"]

for model in models:
    tokens = count_tokens(document, model)
    cost = estimate_cost(document, model)
    limit = get_model_limit(model)
    
    fits = tokens <= limit
    within_budget = cost <= budget
    
    if fits and within_budget:
        print(f"✓ {model}: {tokens:,} tokens, ${cost:.4f}")
    elif not fits:
        print(f"✗ {model}: Too large ({tokens:,} > {limit:,})")
    elif not within_budget:
        print(f"✗ {model}: Over budget (${cost:.4f} > ${budget:.2f})")
```

### Best Practices

1. **Always use accurate token counting** for production workloads
2. **Match task type to your use case**:
   - `CODE_ANALYSIS`: Large context for code review
   - `SUMMARIZATION`: Small chunks for parallel processing
   - `GENERAL`: Balanced approach
3. **Test different overlap ratios** (5-30%) to find the sweet spot
4. **Monitor costs** before processing large documents
5. **Use smart_chunk_text()** for convenience in most cases

### Complete Documentation

For detailed information, see:
- **[Token Optimization Guide](docs/TOKEN_OPTIMIZATION_GUIDE.md)** - Complete documentation
- **[Examples](examples/token_optimization_example.py)** - Working code examples




## Persona System

The Persona System provides specialized system prompts for each specialist role, with intelligent model resolution for single or multi-key scenarios.

### Basic Usage

```python
from rlm import PromptManager, ModelResolver, map_routing_profile_to_persona

# Initialize
pm = PromptManager()
available = {"gpt-5.2", "claude-opus-4.5"}
resolver = ModelResolver(available)

# Get specialized prompt for a role
system_prompt = pm.get_system_message(
    role_id="architect",
    context_type="Python codebase",
    context_total_length=100000,
    hive_state={}
)
```

### The 5 Core Personas

1. **Architect** (Claude Opus 4.5) - Code architecture, design patterns, legal documents
2. **Project Manager** (GPT-5.2) - SQL, data structures, planning, workflows
3. **Creative Director** (Gemini 3) - Narrative writing, research synthesis
4. **News Analyst** (Grok 4.1) - Fact-checking, social media, current events
5. **Efficiency Expert** (DeepSeek 3.2) - Math, logic, general tasks

### Model Resolution (Critical for Single-Key Users)

```python
# Multi-key: Uses fallback chains
available = {"gpt-5.2", "claude-opus-4.5", "deepseek-3.2"}
resolver = ModelResolver(available)
resolved, fallback = resolver.resolve_model("gemini-3")
# Result: ("gpt-5.2", True) - fallback to next best

# Single-key: Bypasses all logic
available = {"gpt-5.2"}
resolver = ModelResolver(available)
resolved, fallback = resolver.resolve_model("claude-opus-4.5")
# Result: ("gpt-5.2", True) - uses what's available
```

### Complete Workflow

```python
from rlm import route_text, get_prompt_manager, get_model_resolver

# 1. Route to determine profile
text = "class User: pass"
profile = route_text(text)  # Routing logic

# 2. Map to persona
role_id = map_routing_profile_to_persona(profile)

# 3. Get preferred model
pm = get_prompt_manager()
preferred = pm.get_model_preference(role_id)

# 4. Resolve to available model
available = {"gpt-5.2"}
resolver = get_model_resolver(available)
resolved, _ = resolver.resolve_model(preferred)

# 5. Get specialized prompt
prompt = pm.get_system_message(role_id, ...)

# 6. Query with resolved model and specialized prompt
# response = llm.query(user_query, system_prompt=prompt)
```

### Custom Personas

Add custom personas in `rlm/personas.yaml`:

```yaml
personas:
  data_scientist:
    role_id: "data_scientist"
    display_name: "Data Scientist"
    model_preference: "gpt-5.2"
    system_prompt: |
      You are a Data Scientist...
    tools:
      - llm_query
      - parallel_query
      - hive
```

### Best Practices

1. **Always use ModelResolver** - Don't assume preferred models are available
2. **Single-key mode is default** - Most users have only 1 API key
3. **Provide rich context** - Include context_type, lengths, hive_state
4. **Log fallbacks** - Set `log_fallback=True` for debugging

### Complete Documentation

For detailed information, see:
- **[Persona System Guide](docs/PERSONA_SYSTEM_GUIDE.md)** - Complete documentation
- **[Examples](examples/persona_system_example.py)** - Working code examples

