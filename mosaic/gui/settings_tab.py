"""
Settings Tab for Data Donation feature.

Provides a UI for users to donate their anonymized training data.
"""

import customtkinter as ctk
import threading

# Try to import S3Uploader with graceful handling
try:
    from mosaic.training.uploader import S3Uploader
    UPLOADER_AVAILABLE = True
except ImportError:
    UPLOADER_AVAILABLE = False


class SettingsTab(ctk.CTkFrame):
    """
    Settings tab widget for the Mosaic application.
    
    Features:
    - Data donation section
    - Background thread for uploads
    - Status feedback with success/error indicators
    """
    
    # Theme colors (matching Mosaic's Lovable Software theme)
    BG_COLOR = "#0F172A"  # Deep Midnight Blue
    CARD_COLOR = "#1E293B"  # Dark Slate
    ACCENT_COLOR = "#8B5CF6"  # Vivid Purple
    TEXT_COLOR = "#F8FAFC"  # Off-white
    SUCCESS_COLOR = "#10B981"  # Green
    ERROR_COLOR = "#EF4444"  # Red
    
    def __init__(self, parent, **kwargs):
        """
        Initialize the settings tab.
        
        Args:
            parent: Parent widget
            **kwargs: Additional arguments for CTkFrame
        """
        super().__init__(parent, fg_color=self.BG_COLOR, **kwargs)
        
        self.uploader = S3Uploader() if UPLOADER_AVAILABLE else None
        self.upload_in_progress = False
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create and layout all widgets."""
        # Main container with padding
        main_container = ctk.CTkFrame(self, fg_color=self.BG_COLOR)
        main_container.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Header
        header = ctk.CTkLabel(
            main_container,
            text="Settings",
            font=("Segoe UI", 32, "bold"),
            text_color=self.TEXT_COLOR
        )
        header.pack(pady=(0, 30), anchor="w")
        
        # Data Donation Section
        self._create_donation_section(main_container)
    
    def _create_donation_section(self, parent):
        """Create the data donation section."""
        # Contribute to Science card
        donation_card = ctk.CTkFrame(parent, fg_color=self.CARD_COLOR, corner_radius=15)
        donation_card.pack(fill="x", pady=(0, 20))
        
        # Section header
        section_header = ctk.CTkLabel(
            donation_card,
            text="🔬 Contribute to Science",
            font=("Segoe UI", 24, "bold"),
            text_color=self.TEXT_COLOR
        )
        section_header.pack(pady=(20, 15), padx=20, anchor="w")
        
        # Description
        description_text = (
            "Help improve AI research by donating your anonymized training logs. "
            "Your data will be securely uploaded to our research database and used "
            "to advance language model technology. All personal information is removed "
            "before upload."
        )
        
        description = ctk.CTkLabel(
            donation_card,
            text=description_text,
            font=("Segoe UI", 14),
            text_color="#94A3B8",  # Muted text color
            wraplength=600,
            justify="left"
        )
        description.pack(pady=(0, 20), padx=20, anchor="w")
        
        # Button container
        button_container = ctk.CTkFrame(donation_card, fg_color="transparent")
        button_container.pack(fill="x", padx=20, pady=(0, 15))
        
        # Donate Data button
        self.donate_button = ctk.CTkButton(
            button_container,
            text="Donate Data",
            font=("Segoe UI", 16, "bold"),
            fg_color=self.ACCENT_COLOR,
            hover_color="#7C3AED",
            corner_radius=10,
            height=45,
            command=self._on_donate_clicked
        )
        self.donate_button.pack(side="left", padx=(0, 15))
        
        # Status label
        self.status_label = ctk.CTkLabel(
            button_container,
            text="",
            font=("Segoe UI", 14),
            text_color=self.TEXT_COLOR
        )
        self.status_label.pack(side="left", fill="x", expand=True)
        
        # Technical details (collapsible info)
        trajectories_path = Path.home() / ".mosaic" / "data" / "trajectories"
        details_text = (
            f"📁 Files Location: {trajectories_path}\n"
            "📦 File Format: .jsonl.gz (compressed JSON)\n"
            "🔒 Privacy: All personal data is anonymized before upload"
        )
        
        details = ctk.CTkLabel(
            donation_card,
            text=details_text,
            font=("Segoe UI", 12),
            text_color="#64748B",
            justify="left"
        )
        details.pack(pady=(10, 20), padx=20, anchor="w")
    
    def _on_donate_clicked(self):
        """Handle donate button click."""
        if not UPLOADER_AVAILABLE:
            self._show_status("❌ Error", "Uploader module not available", is_error=True)
            return
        
        if self.upload_in_progress:
            return
        
        # Start upload in background thread
        self.upload_in_progress = True
        self.donate_button.configure(state="disabled", text="Uploading...")
        self.status_label.configure(text="⏳ Preparing upload...", text_color="#F59E0B")
        
        # Run upload in background thread
        thread = threading.Thread(target=self._upload_worker, daemon=True)
        thread.start()
    
    def _upload_worker(self):
        """Worker function that runs in background thread."""
        try:
            success, message = self.uploader.upload_donation_bundle()
            
            # Schedule UI update on main thread
            self.after(0, lambda: self._on_upload_complete(success, message))
            
        except Exception as e:
            # Schedule error UI update on main thread
            self.after(0, lambda: self._on_upload_complete(False, f"Unexpected error: {e}"))
    
    def _on_upload_complete(self, success, message):
        """
        Handle upload completion (called on main thread).
        
        Args:
            success: Whether upload succeeded
            message: Status message to display
        """
        self.upload_in_progress = False
        self.donate_button.configure(state="normal", text="Donate Data")
        
        if success:
            self._show_status("✅ Success", message, is_error=False)
        else:
            self._show_status("❌ Error", message, is_error=True)
    
    def _show_status(self, prefix, message, is_error=False):
        """
        Show status message.
        
        Args:
            prefix: Status prefix (e.g., "✅ Success" or "❌ Error")
            message: Full status message
            is_error: Whether this is an error message
        """
        color = self.ERROR_COLOR if is_error else self.SUCCESS_COLOR
        self.status_label.configure(
            text=f"{prefix}: {message}",
            text_color=color
        )


# Standalone demo/test function
def demo():
    """Run a standalone demo of the settings tab."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    root = ctk.CTk()
    root.title("Settings Tab Demo")
    root.geometry("800x600")
    
    settings = SettingsTab(root)
    settings.pack(fill="both", expand=True)
    
    root.mainloop()


if __name__ == "__main__":
    demo()
