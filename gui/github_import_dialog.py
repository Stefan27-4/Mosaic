"""
GitHub Import Dialog for Mosaic.

This dialog allows users to import code from GitHub repositories
for context-aware code analysis and Q&A.
"""

import customtkinter as ctk
from typing import Optional, Callable, List, Dict
import threading


class GitHubImportDialog(ctk.CTkToplevel):
    """
    Dialog for importing code from GitHub repositories.
    
    Allows users to specify:
    - Repository URL
    - Branch (optional)
    - File extensions to filter
    - Path filter
    - GitHub token (for private repos)
    """
    
    # Lovable Software Theme Colors (matching main app)
    BG_COLOR = "#0F172A"  # Deep Midnight Blue
    CARD_COLOR = "#1E293B"  # Dark Slate
    ACCENT_COLOR = "#8B5CF6"  # Vivid Purple
    TEXT_COLOR = "#F8FAFC"  # Off-white
    
    def __init__(
        self,
        parent,
        on_import: Optional[Callable[[Dict[str, any]], None]] = None
    ):
        """
        Initialize the GitHub import dialog.
        
        Args:
            parent: Parent window
            on_import: Callback function called with import parameters when user clicks Import
        """
        super().__init__(parent)
        
        self.on_import = on_import
        self.is_loading = False
        
        # Window configuration
        self.title("Import from GitHub")
        self.geometry("600x550")
        self.configure(fg_color=self.BG_COLOR)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create and layout all widgets."""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color=self.BG_COLOR)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkLabel(
            main_frame,
            text="🐙 Import from GitHub",
            font=("Segoe UI", 24, "bold"),
            text_color=self.TEXT_COLOR
        )
        header.pack(pady=(0, 20))
        
        # Description
        description = ctk.CTkLabel(
            main_frame,
            text="Import code from a GitHub repository for analysis and Q&A",
            font=("Segoe UI", 12),
            text_color="#94A3B8"
        )
        description.pack(pady=(0, 20))
        
        # Form card
        form_card = ctk.CTkFrame(main_frame, fg_color=self.CARD_COLOR, corner_radius=10)
        form_card.pack(fill="both", expand=True, pady=(0, 15))
        
        # Repository URL (required)
        url_label = ctk.CTkLabel(
            form_card,
            text="Repository URL *",
            font=("Segoe UI", 13, "bold"),
            text_color=self.TEXT_COLOR,
            anchor="w"
        )
        url_label.pack(fill="x", padx=20, pady=(20, 5))
        
        self.url_entry = ctk.CTkEntry(
            form_card,
            placeholder_text="https://github.com/owner/repo or owner/repo",
            font=("Segoe UI", 12),
            height=35,
            fg_color="#0F172A",
            border_color=self.ACCENT_COLOR,
            text_color=self.TEXT_COLOR
        )
        self.url_entry.pack(fill="x", padx=20, pady=(0, 15))
        
        # Branch (optional)
        branch_label = ctk.CTkLabel(
            form_card,
            text="Branch (optional)",
            font=("Segoe UI", 13, "bold"),
            text_color=self.TEXT_COLOR,
            anchor="w"
        )
        branch_label.pack(fill="x", padx=20, pady=(0, 5))
        
        self.branch_entry = ctk.CTkEntry(
            form_card,
            placeholder_text="Leave empty for default branch",
            font=("Segoe UI", 12),
            height=35,
            fg_color="#0F172A",
            border_color=self.ACCENT_COLOR,
            text_color=self.TEXT_COLOR
        )
        self.branch_entry.pack(fill="x", padx=20, pady=(0, 15))
        
        # File Extensions (optional)
        ext_label = ctk.CTkLabel(
            form_card,
            text="File Extensions (optional)",
            font=("Segoe UI", 13, "bold"),
            text_color=self.TEXT_COLOR,
            anchor="w"
        )
        ext_label.pack(fill="x", padx=20, pady=(0, 5))
        
        self.ext_entry = ctk.CTkEntry(
            form_card,
            placeholder_text="e.g., .py, .js, .ts (leave empty for all text files)",
            font=("Segoe UI", 12),
            height=35,
            fg_color="#0F172A",
            border_color=self.ACCENT_COLOR,
            text_color=self.TEXT_COLOR
        )
        self.ext_entry.pack(fill="x", padx=20, pady=(0, 15))
        
        # Path Filter (optional)
        path_label = ctk.CTkLabel(
            form_card,
            text="Path Filter (optional)",
            font=("Segoe UI", 13, "bold"),
            text_color=self.TEXT_COLOR,
            anchor="w"
        )
        path_label.pack(fill="x", padx=20, pady=(0, 5))
        
        self.path_entry = ctk.CTkEntry(
            form_card,
            placeholder_text="e.g., src/ (only files under this path)",
            font=("Segoe UI", 12),
            height=35,
            fg_color="#0F172A",
            border_color=self.ACCENT_COLOR,
            text_color=self.TEXT_COLOR
        )
        self.path_entry.pack(fill="x", padx=20, pady=(0, 15))
        
        # GitHub Token (optional, password-masked)
        token_label = ctk.CTkLabel(
            form_card,
            text="GitHub Token (optional)",
            font=("Segoe UI", 13, "bold"),
            text_color=self.TEXT_COLOR,
            anchor="w"
        )
        token_label.pack(fill="x", padx=20, pady=(0, 5))
        
        self.token_entry = ctk.CTkEntry(
            form_card,
            placeholder_text="For private repos or higher rate limits",
            font=("Segoe UI", 12),
            height=35,
            fg_color="#0F172A",
            border_color=self.ACCENT_COLOR,
            text_color=self.TEXT_COLOR,
            show="•"  # Mask the input
        )
        self.token_entry.pack(fill="x", padx=20, pady=(0, 20))
        
        # Status label (for loading/error messages)
        self.status_label = ctk.CTkLabel(
            main_frame,
            text="",
            font=("Segoe UI", 12),
            text_color="#94A3B8"
        )
        self.status_label.pack(pady=(0, 10))
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        # Cancel button
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            font=("Segoe UI", 13),
            height=40,
            width=120,
            fg_color="#475569",
            hover_color="#334155",
            text_color=self.TEXT_COLOR,
            corner_radius=8,
            command=self._on_cancel
        )
        cancel_btn.pack(side="right", padx=(5, 0))
        
        # Import button
        self.import_btn = ctk.CTkButton(
            button_frame,
            text="Import",
            font=("Segoe UI", 13),
            height=40,
            width=120,
            fg_color=self.ACCENT_COLOR,
            hover_color="#7C3AED",
            text_color=self.TEXT_COLOR,
            corner_radius=8,
            command=self._on_import_click
        )
        self.import_btn.pack(side="right")
    
    def _on_import_click(self):
        """Handle Import button click."""
        # Validate required field
        repo_url = self.url_entry.get().strip()
        if not repo_url:
            self.status_label.configure(text="❌ Repository URL is required", text_color="#EF4444")
            return
        
        # Disable button and show loading
        self.import_btn.configure(state="disabled", text="Importing...")
        self.status_label.configure(text="🔄 Fetching repository...", text_color="#94A3B8")
        self.is_loading = True
        
        # Get all parameters
        branch = self.branch_entry.get().strip() or None
        
        # Parse file extensions
        ext_input = self.ext_entry.get().strip()
        file_extensions = None
        if ext_input:
            file_extensions = [ext.strip() for ext in ext_input.split(',') if ext.strip()]
        
        path_filter = self.path_entry.get().strip() or None
        github_token = self.token_entry.get().strip() or None
        
        # Prepare parameters
        params = {
            'repo_url': repo_url,
            'branch': branch,
            'file_extensions': file_extensions,
            'path_filter': path_filter,
            'github_token': github_token
        }
        
        # Call the callback
        if self.on_import:
            self.on_import(params)
    
    def _on_cancel(self):
        """Handle Cancel button click."""
        if not self.is_loading:
            self.destroy()
    
    def show_error(self, message: str):
        """
        Show an error message in the dialog.
        
        Args:
            message: Error message to display
        """
        self.status_label.configure(text=f"❌ {message}", text_color="#EF4444")
        self.import_btn.configure(state="normal", text="Import")
        self.is_loading = False
    
    def show_success(self, message: str):
        """
        Show a success message and close the dialog.
        
        Args:
            message: Success message to display
        """
        self.status_label.configure(text=f"✅ {message}", text_color="#10B981")
        # Close dialog after a short delay
        self.after(500, self.destroy)
