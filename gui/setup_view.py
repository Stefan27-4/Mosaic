"""
Setup View - Configuration and API Key Management

Window 1: Collects API keys and defines safety limits.
"""

import customtkinter as ctk
from typing import Optional, Callable, Dict


class SetupView(ctk.CTkToplevel):
    """
    Setup window for configuring API keys and budget limits.
    
    Features:
    - API key input fields for 5 providers
    - Budget limit (circuit breaker) configuration
    - Clean "Lovable Software" aesthetic
    """
    
    # Lovable Software Theme Colors
    BG_COLOR = "#0F172A"  # Deep Midnight Blue
    CARD_COLOR = "#1E293B"  # Dark Slate
    ACCENT_COLOR = "#8B5CF6"  # Vivid Purple
    TEXT_COLOR = "#F8FAFC"  # Off-white
    
    def __init__(self, parent: Optional[ctk.CTk] = None, on_complete: Optional[Callable] = None):
        """
        Initialize the setup view.
        
        Args:
            parent: Parent CTk window (if None, creates standalone)
            on_complete: Callback function called when setup is complete
                        Receives dict with 'api_keys' and 'budget_limit'
        """
        if parent:
            super().__init__(parent)
        else:
            super().__init__()
        
        self.on_complete = on_complete
        self.api_key_entries = {}
        
        # Window configuration
        self.title("Mosaic - Configuration")
        self.geometry("600x700")
        self.configure(fg_color=self.BG_COLOR)
        
        # Make window modal
        self.grab_set()
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create and layout all widgets."""
        # Main container with padding
        main_frame = ctk.CTkFrame(self, fg_color=self.BG_COLOR)
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Header
        header = ctk.CTkLabel(
            main_frame,
            text="Configure Mosaic Engine",
            font=("Segoe UI", 32, "bold"),
            text_color=self.TEXT_COLOR
        )
        header.pack(pady=(0, 30))
        
        # API Keys Section
        api_card = ctk.CTkFrame(main_frame, fg_color=self.CARD_COLOR, corner_radius=15)
        api_card.pack(fill="x", pady=(0, 20))
        
        api_header = ctk.CTkLabel(
            api_card,
            text="API Keys",
            font=("Segoe UI", 20, "bold"),
            text_color=self.TEXT_COLOR
        )
        api_header.pack(pady=(20, 15), padx=20, anchor="w")
        
        # API key providers
        providers = [
            ("OpenAI", "openai"),
            ("Anthropic (Claude)", "anthropic"),
            ("Google Gemini", "google"),
            ("xAI (Grok)", "xai"),
            ("DeepSeek", "deepseek")
        ]
        
        for display_name, key_name in providers:
            self._create_api_key_field(api_card, display_name, key_name)
        
        # Circuit Breaker Section
        circuit_card = ctk.CTkFrame(main_frame, fg_color=self.CARD_COLOR, corner_radius=15)
        circuit_card.pack(fill="x", pady=(0, 20))
        
        circuit_header = ctk.CTkLabel(
            circuit_card,
            text="Financial Circuit Breaker",
            font=("Segoe UI", 20, "bold"),
            text_color=self.TEXT_COLOR
        )
        circuit_header.pack(pady=(20, 5), padx=20, anchor="w")
        
        circuit_note = ctk.CTkLabel(
            circuit_card,
            text="⚠️ Process will auto-terminate if this limit is reached",
            font=("Segoe UI", 11),
            text_color="#94A3B8",
            wraplength=500,
            justify="left"
        )
        circuit_note.pack(pady=(0, 15), padx=20, anchor="w")
        
        # Budget limit field
        budget_frame = ctk.CTkFrame(circuit_card, fg_color="transparent")
        budget_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        budget_label = ctk.CTkLabel(
            budget_frame,
            text="Safety Limit (Max Spend):",
            font=("Segoe UI", 14),
            text_color=self.TEXT_COLOR
        )
        budget_label.pack(side="left", padx=(0, 10))
        
        self.budget_entry = ctk.CTkEntry(
            budget_frame,
            width=120,
            height=40,
            font=("Segoe UI", 14),
            fg_color="#1E293B",
            border_color=self.ACCENT_COLOR,
            border_width=2,
            text_color=self.TEXT_COLOR
        )
        self.budget_entry.pack(side="left")
        self.budget_entry.insert(0, "5.00")
        
        dollar_label = ctk.CTkLabel(
            budget_frame,
            text="USD",
            font=("Segoe UI", 14),
            text_color="#94A3B8"
        )
        dollar_label.pack(side="left", padx=(5, 0))
        
        # Initialize Engine Button
        init_button = ctk.CTkButton(
            main_frame,
            text="Initialize Engine",
            font=("Segoe UI", 16, "bold"),
            height=50,
            fg_color=self.ACCENT_COLOR,
            hover_color="#7C3AED",
            text_color=self.TEXT_COLOR,
            corner_radius=10,
            command=self._on_initialize
        )
        init_button.pack(fill="x", pady=(10, 0))
    
    def _create_api_key_field(self, parent, display_name: str, key_name: str):
        """Create an API key input field."""
        field_frame = ctk.CTkFrame(parent, fg_color="transparent")
        field_frame.pack(fill="x", padx=20, pady=5)
        
        label = ctk.CTkLabel(
            field_frame,
            text=display_name,
            font=("Segoe UI", 13),
            text_color=self.TEXT_COLOR,
            width=150,
            anchor="w"
        )
        label.pack(side="left", padx=(0, 10))
        
        entry = ctk.CTkEntry(
            field_frame,
            show="*",
            height=35,
            font=("Segoe UI", 12),
            fg_color="#1E293B",
            border_color="#475569",
            border_width=1,
            text_color=self.TEXT_COLOR,
            placeholder_text="sk-..."
        )
        entry.pack(side="left", fill="x", expand=True)
        
        self.api_key_entries[key_name] = entry
    
    def _on_initialize(self):
        """Handle initialize button click."""
        # Collect API keys
        api_keys = {}
        for key_name, entry in self.api_key_entries.items():
            value = entry.get().strip()
            if value:
                api_keys[key_name] = value
        
        # Get budget limit
        try:
            budget_limit = float(self.budget_entry.get().strip())
        except ValueError:
            budget_limit = 5.0
        
        # Prepare config
        config = {
            "api_keys": api_keys,
            "budget_limit": budget_limit
        }
        
        # Call callback if provided
        if self.on_complete:
            self.on_complete(config)
        
        # Close this window
        self.destroy()


# Standalone test
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    
    def on_setup_complete(config):
        print("Setup complete!")
        print(f"API Keys: {list(config['api_keys'].keys())}")
        print(f"Budget: ${config['budget_limit']:.2f}")
    
    app = ctk.CTk()
    app.withdraw()  # Hide main window
    
    setup = SetupView(app, on_complete=on_setup_complete)
    
    app.mainloop()
