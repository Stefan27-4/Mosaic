#!/usr/bin/env python3
"""
Mosaic GUI Launcher

Entry point for launching the Mosaic graphical user interface.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.app import main

if __name__ == "__main__":
    main()
