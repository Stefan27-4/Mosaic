#!/usr/bin/env python3
"""
Example: Integrating the Settings Tab into a Mosaic Application

This example shows how to add the Data Donation settings tab
to an existing Mosaic GUI application.
"""

import customtkinter as ctk
from mosaic.gui.settings_tab import SettingsTab


class ExampleApp(ctk.CTk):
    """
    Example application showing Settings Tab integration.
    
    Demonstrates:
    1. Creating a tabbed interface
    2. Adding the Settings tab
    3. Basic tab navigation
    """
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("Mosaic - Example with Settings")
        self.geometry("900x700")
        
        # Configure appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create the main interface with tabs."""
        # Create tabview
        tabview = ctk.CTkTabview(self)
        tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Add tabs
        tabview.add("Main")
        tabview.add("Settings")
        
        # Main tab content (example)
        main_frame = ctk.CTkFrame(tabview.tab("Main"))
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        main_label = ctk.CTkLabel(
            main_frame,
            text="Main Application Content",
            font=("Segoe UI", 24, "bold")
        )
        main_label.pack(pady=50)
        
        info_label = ctk.CTkLabel(
            main_frame,
            text="Click the 'Settings' tab to see the Data Donation feature",
            font=("Segoe UI", 14)
        )
        info_label.pack(pady=20)
        
        # Settings tab with Data Donation feature
        settings = SettingsTab(tabview.tab("Settings"))
        settings.pack(fill="both", expand=True)


def main():
    """Run the example application."""
    app = ExampleApp()
    app.mainloop()


if __name__ == "__main__":
    main()
