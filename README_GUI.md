# Mosaic - Graphical User Interface

The Mosaic RLM framework now includes a beautiful customtkinter-based GUI with **full backend integration**!

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Launch the GUI
python mosaic_gui.py
```

## Features

### ✅ Backend Integration (NEW!)
- **Real RLM Engine**: Fully integrated async RLM backend
- **Parallel Processing**: Automatic use of parallel_query() for speed
- **Hive Memory**: Shared state visualization in debug log
- **Resilience Layer**: Automatic validation and retry feedback
- **Thread-Safe**: Queue-based message passing between backend and GUI

### 🎨 "Lovable Software" Design
- Dark mode with deep midnight blue background (#0F172A)
- Vivid purple accents (#8B5CF6)
- Clean, modern typography (Segoe UI)
- Rounded corners and smooth animations

### 🔧 Setup Window
- Configure API keys for AI providers (OpenAI, Anthropic, Google)
- Set financial circuit breaker (budget limit)
- Secure password-masked input fields
- Automatic backend initialization

### 💬 Chat Interface
- **Budget Health Dashboard**: Real-time spend tracking with color-coded progress
  - Green: < 50% of budget
  - Yellow: 50-80% of budget
  - Red: > 80% of budget
  - Auto-halt at limit
- **Smart Router**: Automatic model selection based on content
- **Manual Override**: Select specific models when needed
- **Debug Log**: "Matrix Mode" showing:
  - REPL execution
  - Sub-agent activity
  - Hive memory updates
  - Resilience layer feedback
  - Error messages with stack traces
- **Document Loading**: PDF ingestion (coming soon)

## Backend Integration

### Architecture

The GUI runs in the main thread while the RLM backend runs in a background thread with its own async event loop:

```
Main Thread (GUI)  ←→  Message Queue  ←→  Background Thread (RLM)
     │                                              │
     ├─ customtkinter UI                           ├─ Async Event Loop
     ├─ User interaction                           ├─ RLM Core
     ├─ Budget updates                             ├─ REPL Environment
     ├─ Debug log                                  ├─ parallel_query()
     └─ Message processing                         ├─ Hive Memory
                                                    └─ Resilience Layer
```

### Message Types

The backend sends messages to the GUI:
- `("LOG", "text")` - Debug log messages
- `("BUDGET", float)` - Cost updates
- `("DONE", "answer")` - Final answer
- `("ERROR", "message")` - Errors
- `("HIVE", dict)` - Hive memory state

### Real-Time Feedback

Enable debug log to see:
```
[QUERY] Starting: Summarize these documents
[CONFIG] Smart Router: ENABLED
[CONTEXT] 100 documents loaded
[ROUTER] Selected model: gpt-4o
[SUB-CALLS] 10 recursive calls made
[REPL] Executing 3 lines of code
[HIVE] Memory state: {"suspect": "butler"}
[QUERY] Completed successfully
```

## Usage Examples

### Basic Query
```python
# Just launch and chat!
from gui import MosaicApp
app = MosaicApp()
app.run()
```

### With API Keys Pre-Configured
```python
from gui import MainChatView

config = {
    "api_keys": {
        "openai": "sk-...",
        "anthropic": "sk-ant-..."
    },
    "budget_limit": 10.0
}

app = MainChatView(config)
app.mainloop()
```

## Screenshots

### Setup View
The configuration window collects API keys and sets budget limits:
- API key fields for OpenAI, Anthropic, Google Gemini, xAI (Grok), and DeepSeek
- Budget limit input with circuit breaker protection
- "Initialize Engine" button to launch the chat
- Backend automatically initializes with available keys

### Main Chat View
The primary interface features:
- **Left Sidebar** (25% width):
  - Budget health dashboard at top (real-time updates)
  - Load document button
  - Smart router toggle switch
  - Model selector dropdown
- **Chat Area** (75% width):
  - Scrollable message history
  - User messages (right-aligned)
  - AI responses (purple cards, powered by real LLMs!)
  - System notifications (gray, italic)
  - Input field with send button
- **Debug Log** (bottom, collapsible):
  - Matrix-style green text on dark background
  - Real REPL execution traces
  - Actual sub-agent activity logs
  - Hive memory state updates
  - Resilience layer feedback

## Architecture

```
gui/
├── __init__.py          # Package exports
├── app.py               # Application orchestrator
├── setup_view.py        # Window 1: Configuration
├── main_chat_view.py    # Window 2: Chat interface
├── backend_bridge.py    # NEW: Thread-safe backend integration
└── README.md            # Detailed GUI documentation
```

## Integration with RLM

The GUI now uses the actual RLM backend:

```python
from rlm import classify_chunk, get_available_models, create_model_map

# Get available models from API keys
model_map = create_model_map(**api_keys)
available = get_available_models(model_map)

# Route messages intelligently
model_id, details = classify_chunk(message, available)
llm = model_map[model_id]
response = llm.query(message)
```

## Requirements

- Python 3.8+
- customtkinter >= 5.2.0
- All RLM framework dependencies (see requirements.txt)

## Documentation

For detailed GUI documentation, see [gui/README.md](gui/README.md)

For RLM framework documentation, see [USER_GUIDE.md](USER_GUIDE.md)

---

**Note**: The GUI provides a visual interface to the powerful RLM framework described in the main README.md research paper.
