"""
Integrated GUI Example

Demonstrates the fully integrated Mosaic GUI with RLM backend.

This example shows:
1. Backend integration with real LLM APIs
2. Thread-safe message passing
3. Real-time budget monitoring
4. Debug log with REPL operations
5. Hive memory visualization (when used)
6. Resilience layer feedback

Requirements:
- Set environment variables: OPENAI_API_KEY, ANTHROPIC_API_KEY (optional), GOOGLE_API_KEY (optional)
- Or enter API keys in the setup window

Usage:
    python examples/integrated_gui_example.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui import MosaicApp


def main():
    """Run the integrated Mosaic GUI."""
    print("=" * 60)
    print("Mosaic - Integrated GUI Example")
    print("=" * 60)
    print()
    print("Starting GUI application...")
    print()
    print("Features:")
    print("- Real RLM backend integration")
    print("- Live budget monitoring")
    print("- Debug log showing REPL operations")
    print("- Hive memory visualization")
    print("- Multi-model support with smart routing")
    print()
    print("Please configure your API keys in the setup window.")
    print("=" * 60)
    print()
    
    # Launch GUI
    app = MosaicApp()
    app.run()


if __name__ == "__main__":
    main()
