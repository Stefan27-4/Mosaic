# GUI Integration Guide

## Overview

The Mosaic GUI is now fully integrated with the RLM backend, providing a complete desktop application for infinite context processing. This guide explains the integration architecture and how to use the integrated features.

## Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Mosaic GUI (Main Thread)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  SetupView   │→ │ MainChatView │ ←│ MosaicBridge │  │
│  └──────────────┘  └──────────────┘  └──────┬───────┘  │
│                                               │          │
└───────────────────────────────────────────────┼──────────┘
                                                │
                          Message Queue (Thread-Safe)
                                                │
┌───────────────────────────────────────────────┼──────────┐
│                Background Thread               │          │
│  ┌──────────────────────────────────────────┐ │          │
│  │   Async Event Loop                       │ │          │
│  │  ┌────────────────────────────────────┐  │ │          │
│  │  │  RLM Core                          │  │ │          │
│  │  │  - REPL Environment                │  │ │          │
│  │  │  - parallel_query()                │  │ │          │
│  │  │  - Hive Memory                     │  │ │          │
│  │  │  - Resilience Layer                │  │ │          │
│  │  └────────────────────────────────────┘  │ │          │
│  └──────────────────────────────────────────┘ │          │
└────────────────────────────────────────────────┘          │
                                                             │
┌────────────────────────────────────────────────┘          │
│  LLM APIs (OpenAI, Anthropic, Google)                     │
└────────────────────────────────────────────────────────────┘
```

### Thread-Safe Communication

The GUI uses a **queue-based message passing system** to safely communicate between the background thread (running async RLM) and the main GUI thread:

**Message Types:**
- `("LOG", "text")` - Debug log messages
- `("BUDGET", float)` - Cost updates
- `("DONE", "answer")` - Final answer from RLM
- `("ERROR", "message")` - Error notifications
- `("HIVE", dict)` - Hive memory state updates

**Flow:**
1. User sends message in GUI
2. MainChatView calls `backend.run_query()`
3. MosaicBridge creates background thread with new async event loop
4. RLM processes query asynchronously
5. Backend sends messages via callback → message queue
6. GUI's `_check_queue()` method (runs every 100ms) processes messages
7. GUI updates in main thread (thread-safe)

## Features

### 1. Real LLM Backend Integration

The GUI now connects to actual LLM APIs instead of simulated responses:

```python
# Backend automatically initializes with available API keys
backend = MosaicBridge(config={"api_keys": {...}, "budget_limit": 5.0})

# Runs actual RLM query
backend.run_query(
    user_prompt="Summarize these documents",
    context=[doc1, doc2, ...],
    use_router=True
)
```

### 2. Live Budget Monitoring

Real-time cost tracking with visual indicators:
- **Green** (<50%): Healthy budget
- **Yellow** (50-79%): Warning zone
- **Red** (80-100%): Critical
- **Auto-halt** at limit

### 3. Debug Log (Matrix Mode)

Enable "Show Debug Log" to see:
- Query initiation
- Router decisions
- REPL code execution
- Sub-LLM calls
- Iteration progress
- Hive memory updates
- Error messages with stack traces

### 4. Hive Memory Visualization

When parallel processing uses Hive Memory, the debug log shows:
```
[HIVE] Memory state: {"suspect": "butler", "weapon": "candlestick"}
```

### 5. Smart Routing

Toggle smart routing on/off:
- **ON**: Automatic model selection based on task type
- **OFF**: Manual model selection from dropdown

### 6. Parallel Processing

The backend automatically uses `parallel_query()` when the LLM determines it's beneficial:
```
[SUB-CALLS] 10 recursive calls made
[LOG] [ITERATION 1] Processing...
[REPL] Executing 5 lines of code
```

## Usage

### Basic Usage

```python
from gui import MosaicApp

# Launch GUI
app = MosaicApp()
app.run()
```

Or from command line:
```bash
python mosaic_gui.py
```

### With Pre-configured API Keys

```python
from gui import MainChatView

config = {
    "api_keys": {
        "openai": "sk-...",
        "anthropic": "sk-ant-...",
        "google": "AI..."
    },
    "budget_limit": 10.0
}

# Skip setup, go straight to chat
app = MainChatView(config)
app.mainloop()
```

### Environment Variables

Set API keys via environment:
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="AI..."

python mosaic_gui.py
```

## Example Queries

### Simple Query
```
User: What is 2+2?
Mosaic: 4

Debug Log:
[QUERY] Starting: What is 2+2?
[CONFIG] Smart Router: ENABLED
[ROUTER] Selected model: deepseek-3.2
[REPL] Executing 1 lines of code
[QUERY] Completed successfully
```

### Multi-Document Analysis
```
User: Summarize all documents
[Load 100 documents first]

Debug Log:
[QUERY] Starting: Summarize all documents
[CONTEXT] 100 documents loaded
[SUB-CALLS] 10 recursive calls made (parallel processing)
[ITERATION 1] Processing...
[REPL] Executing 3 lines of code
[RESULT] summaries = parallel_query(...)
[ITERATION 2] Processing...
[QUERY] Completed successfully
```

### Investigation with Hive Memory
```
User: Investigate the crime scene documents

Debug Log:
[QUERY] Starting: Investigate...
[ITERATION 1] Processing...
[REPL] Executing code: hive.set("suspect", "butler")
[HIVE] Memory state: {"suspect": "butler"}
[SUB-CALLS] 5 recursive calls made
[HIVE] Updated: {"suspect": "butler", "weapon": "candlestick", "location": "library"}
[ITERATION 2] Processing...
[QUERY] Completed successfully
```

## Error Handling

The GUI gracefully handles errors:

**Backend Initialization Failure:**
```
⚠️ Backend initialization failed: No API keys provided
```

**Query Error:**
```
❌ Error: Rate limit exceeded
[ERROR] openai.RateLimitError: ...
```

**Budget Exceeded:**
```
⚠️ BUDGET LIMIT REACHED - Processing halted!
[CIRCUIT BREAKER] Budget limit exceeded - shutting down
```

## Customization

### Custom Backend Configuration

```python
from gui import MainChatView, MosaicBridge

# Custom backend setup
backend = MosaicBridge(
    config={
        "api_keys": {...},
        "budget_limit": 20.0
    },
    message_callback=custom_handler
)

# Use in GUI
view = MainChatView(config)
view.backend = backend
```

### Custom Message Handling

```python
def custom_message_handler(message):
    msg_type, data = message
    
    if msg_type == "LOG":
        print(f"Backend: {data}")
    elif msg_type == "BUDGET":
        print(f"Cost update: ${data:.2f}")
    # ... handle other types
```

## Performance Tips

1. **Enable Debug Log**: See what's happening under the hood
2. **Use Smart Router**: Optimal model selection saves cost
3. **Load Context Once**: Don't reload same documents repeatedly
4. **Monitor Budget**: Set appropriate limits
5. **Check Hive Memory**: See accumulated findings between parallel calls

## Troubleshooting

### GUI Not Responding
- Background thread is processing
- Check debug log for progress
- Wait for "Completed successfully" message

### "Backend Not Initialized"
- Check API keys in setup
- Verify keys are valid
- Check network connection

### Budget Warning Appears Immediately
- Previous session costs carried over
- Restart GUI for fresh budget
- Increase budget limit in setup

### Slow Performance
- Large context requires more processing
- Multiple parallel calls take time
- Check debug log for iteration count

## Integration with Resilience Layer

When enabled, the Resilience Layer provides automatic validation:

```
Debug Log:
[RESILIENCE] Tier 1 validation: PASS
[RESILIENCE] Tier 2 critic review: Peer review mode
[RESILIENCE] Critic (claude-opus-4.5) reviewing worker (gpt-5.2)
[RESILIENCE] Validation: PASS
```

On retry:
```
⚠️ Agent failed validation - retrying (attempt 2/3)
[RESILIENCE] Applying critic feedback...
```

## Future Enhancements

Planned improvements:
- PDF document loading UI
- Hive memory visualization panel
- Real-time streaming responses
- Query history and bookmarks
- Export conversation to file
- Advanced settings panel
- Multi-tab support

## See Also

- [USER_GUIDE.md](../USER_GUIDE.md) - Complete RLM framework guide
- [ASYNC_MAPREDUCE.md](ASYNC_MAPREDUCE.md) - Parallel processing documentation
- [HIVE_MEMORY.md](HIVE_MEMORY.md) - Shared state documentation
- [RESILIENCE_GUIDE.md](RESILIENCE_GUIDE.md) - Validation layer guide
- [GUI_DESIGN.md](GUI_DESIGN.md) - UI design specifications
