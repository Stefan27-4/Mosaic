# Mosaic GUI

CustomTkinter-based graphical user interface for the Mosaic RLM framework.

## Features

### Window 1: Setup View
- **API Key Configuration**: Secure input fields for 5 AI providers
  - OpenAI
  - Anthropic (Claude)
  - Google Gemini
  - xAI (Grok)
  - DeepSeek
- **Financial Circuit Breaker**: Set budget limits to prevent overspending
- **Clean Interface**: "Lovable Software" aesthetic with dark mode

### Window 2: Main Chat View
- **Budget Health Dashboard**: Real-time monitoring with color-coded progress bar
  - Green: < 50% of budget
  - Yellow: 50-80% of budget
  - Red: > 80% of budget
- **Chat Interface**: Full-featured chat with message history
- **Smart Router**: Automatic model selection based on content analysis
- **Manual Model Selection**: Override router with manual selection
- **Document Loading**: PDF document ingestion (coming soon)
- **Debug Log**: "Matrix Mode" showing REPL execution and sub-agent activity

## Installation

```bash
pip install customtkinter>=5.2.0
```

## Usage

### Launch the GUI

```bash
python mosaic_gui.py
```

### Programmatic Usage

```python
from gui import MosaicApp

app = MosaicApp()
app.run()
```

### Standalone Testing

Each component can be tested independently:

```bash
# Test Setup View
python gui/setup_view.py

# Test Main Chat View
python gui/main_chat_view.py
```

## Design Specifications

### Color Palette (Lovable Software Theme)
- **Background**: `#0F172A` (Deep Midnight Blue)
- **Card/Surface**: `#1E293B` (Dark Slate)
- **Accent**: `#8B5CF6` (Vivid Purple)
- **Text**: `#F8FAFC` (Off-white)
- **Secondary Text**: `#94A3B8` (Slate Gray)

### Typography
- **Primary Font**: Segoe UI (fallback: Inter, Roboto)
- **Debug Log Font**: Consolas (monospace)

### Key Measurements
- **Window Sizes**: 
  - Setup: 600x700px
  - Main Chat: 1200x800px
- **Corner Radius**: 10-15px
- **Padding**: 15-30px

## Architecture

```
gui/
├── __init__.py          # Package initialization
├── app.py               # Application orchestrator
├── setup_view.py        # Window 1: Configuration
├── main_chat_view.py    # Window 2: Chat interface
└── README.md            # This file
```

## Integration with RLM Framework

The GUI integrates with the core RLM framework:

```python
from rlm import classify_chunk, get_available_models, create_model_map

# In MainChatView
config = {...}  # From SetupView
model_map = create_model_map(**config['api_keys'])
available = get_available_models(model_map)

# Route messages
model_id, details = classify_chunk(user_message, available)
llm = model_map[model_id]
response = llm.query(user_message)
```

## Future Enhancements

- [ ] PDF document loading and processing
- [ ] Real RLM integration (currently simulated)
- [ ] Cost tracking per model
- [ ] Export chat history
- [ ] Custom theme editor
- [ ] Multi-document context management
- [ ] Sub-agent visualization
- [ ] Performance metrics dashboard
