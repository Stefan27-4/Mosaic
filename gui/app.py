"""
Mosaic Application

Main application orchestrator that handles the flow between SetupView and MainChatView.
"""

import customtkinter as ctk
from .setup_view import SetupView
from .main_chat_view import MainChatView


class MosaicApp:
    """
    Main application class for Mosaic.
    
    Orchestrates the flow:
    1. Show SetupView to collect API keys and budget
    2. On completion, launch MainChatView with the configuration
    """
    
    def __init__(self):
        """Initialize the Mosaic application."""
        # Set appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.config = None
        self.main_window = None
        
        # Start with setup view
        self._show_setup()
    
    def _show_setup(self):
        """Show the setup/configuration window."""
        # Create hidden root window
        root = ctk.CTk()
        root.withdraw()
        
        # Show setup view as modal
        setup = SetupView(root, on_complete=self._on_setup_complete)
        
        # Run the event loop
        root.mainloop()
    
    def _on_setup_complete(self, config: dict):
        """
        Called when setup is complete.
        
        Args:
            config: Configuration dict with 'api_keys' and 'budget_limit'
        """
        self.config = config
        
        # Launch main chat window
        self.main_window = MainChatView(config)
        self.main_window.mainloop()
    
    def run(self):
        """
        Run the application.
        
        This is called externally to start the app.
        The flow is handled internally via _show_setup.
        """
        # The setup is already shown in __init__
        pass


def main():
    """Entry point for the Mosaic GUI application."""
    app = MosaicApp()
    app.run()


if __name__ == "__main__":
    main()
