# Mosaic - Graphical User Interface

The Mosaic RLM framework now includes a beautiful customtkinter-based GUI!

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Launch the GUI
python mosaic_gui.py
```

## Features

### 🎨 "Lovable Software" Design
- Dark mode with deep midnight blue background (#0F172A)
- Vivid purple accents (#8B5CF6)
- Clean, modern typography (Segoe UI)
- Rounded corners and smooth animations

### 🔧 Setup Window
- Configure API keys for 5 AI providers
- Set financial circuit breaker (budget limit)
- Secure password-masked input fields

### 💬 Chat Interface
- **Budget Health Dashboard**: Real-time spend tracking with color-coded progress
  - Green: < 50% of budget
  - Yellow: 50-80% of budget
  - Red: > 80% of budget
- **Smart Router**: Automatic model selection based on content
- **Manual Override**: Select specific models when needed
- **Debug Log**: "Matrix Mode" showing REPL and sub-agent activity
- **Document Loading**: PDF ingestion (coming soon)

## Screenshots

### Setup View
The configuration window collects API keys and sets budget limits:
- API key fields for OpenAI, Anthropic, Google Gemini, xAI (Grok), and DeepSeek
- Budget limit input with circuit breaker protection
- "Initialize Engine" button to launch the chat

### Main Chat View
The primary interface features:
- **Left Sidebar** (25% width):
  - Budget health dashboard at top
  - Load document button
  - Smart router toggle switch
  - Model selector dropdown
- **Chat Area** (75% width):
  - Scrollable message history
  - User messages (right-aligned)
  - AI responses (purple cards)
  - System notifications (gray, italic)
  - Input field with send button
- **Debug Log** (bottom, collapsible):
  - Matrix-style green text on dark background
  - REPL execution traces
  - Sub-agent activity logs

## Architecture

```
gui/
├── __init__.py          # Package exports
├── app.py               # Application orchestrator
├── setup_view.py        # Window 1: Configuration
├── main_chat_view.py    # Window 2: Chat interface
└── README.md            # Detailed GUI documentation
```

## Integration with RLM

The GUI seamlessly integrates with the core RLM framework:

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
