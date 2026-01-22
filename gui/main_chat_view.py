"""
Main Chat View - The Primary Interface

Window 2: Chat interface with budget monitoring and controls.
"""

import customtkinter as ctk
from typing import Optional, Callable
import time
import queue
import os
from tkinter import filedialog
from rlm.utils import load_pdf, chunk_text
from .backend_bridge import MosaicBridge


class MainChatView(ctk.CTk):
    """
    Main chat window with budget monitoring and RLM controls.
    
    Features:
    - Budget health dashboard with progress bar
    - Chat interface
    - Document loading
    - Smart router toggle
    - Debug log (collapsible)
    """
    
    # Lovable Software Theme Colors
    BG_COLOR = "#0F172A"  # Deep Midnight Blue
    CARD_COLOR = "#1E293B"  # Dark Slate
    ACCENT_COLOR = "#8B5CF6"  # Vivid Purple
    TEXT_COLOR = "#F8FAFC"  # Off-white
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the main chat view.
        
        Args:
            config: Configuration dict with 'api_keys' and 'budget_limit'
        """
        super().__init__()
        
        self.config = config or {"api_keys": {}, "budget_limit": 5.0}
        self.current_spend = 0.0
        self.budget_limit = self.config.get("budget_limit", 5.0)
        self.smart_router_enabled = True
        self.debug_visible = False
        
        # Message queue for backend communication
        self.message_queue = queue.Queue()
        
        # Backend bridge (lazy initialization)
        self.backend = None
        self.loaded_context = []
        self.loaded_documents = []  # Track loaded document names
        
        # Window configuration
        self.title("Mosaic - Infinite Context Chat")
        self.geometry("1200x800")
        self.configure(fg_color=self.BG_COLOR)
        
        self._create_widgets()
        
        # Initialize backend
        self._initialize_backend()
        
        # Start queue checker
        self._check_queue()
    
    def _create_widgets(self):
        """Create and layout all widgets."""
        # Main container
        main_container = ctk.CTkFrame(self, fg_color=self.BG_COLOR)
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Create sidebar and chat area
        self._create_sidebar(main_container)
        self._create_chat_area(main_container)
        
        # Create debug log at bottom
        self._create_debug_log()
    
    def _create_sidebar(self, parent):
        """Create the left sidebar with budget dashboard and controls."""
        self.sidebar = ctk.CTkFrame(parent, fg_color=self.CARD_COLOR, corner_radius=15, width=300)
        self.sidebar.pack(side="left", fill="y", padx=(0, 15))
        self.sidebar.pack_propagate(False)
        
        # Budget Health Dashboard
        budget_card = ctk.CTkFrame(self.sidebar, fg_color="#1E293B", corner_radius=10)
        budget_card.pack(fill="x", padx=15, pady=15)
        
        budget_header = ctk.CTkLabel(
            budget_card,
            text="💰 Budget Health",
            font=("Segoe UI", 18, "bold"),
            text_color=self.TEXT_COLOR
        )
        budget_header.pack(pady=(15, 10), padx=15, anchor="w")
        
        # Progress bar
        self.budget_progress = ctk.CTkProgressBar(
            budget_card,
            height=20,
            corner_radius=10,
            progress_color="#10B981"  # Start green
        )
        self.budget_progress.pack(fill="x", padx=15, pady=(0, 10))
        self.budget_progress.set(0)
        
        # Spend label
        self.spend_label = ctk.CTkLabel(
            budget_card,
            text=f"Spent: ${self.current_spend:.2f} / ${self.budget_limit:.2f}",
            font=("Segoe UI", 13),
            text_color="#94A3B8"
        )
        self.spend_label.pack(pady=(0, 15), padx=15, anchor="w")
        
        # Separator
        separator1 = ctk.CTkFrame(self.sidebar, fg_color="#334155", height=2)
        separator1.pack(fill="x", padx=15, pady=10)
        
        # Controls Section
        controls_label = ctk.CTkLabel(
            self.sidebar,
            text="Controls",
            font=("Segoe UI", 16, "bold"),
            text_color=self.TEXT_COLOR
        )
        controls_label.pack(pady=(10, 15), padx=15, anchor="w")
        
        # Load Document Button
        load_doc_btn = ctk.CTkButton(
            self.sidebar,
            text="📄 Load Document (PDF)",
            font=("Segoe UI", 13),
            height=40,
            fg_color=self.ACCENT_COLOR,
            hover_color="#7C3AED",
            text_color=self.TEXT_COLOR,
            corner_radius=8,
            command=self._on_load_document
        )
        load_doc_btn.pack(fill="x", padx=15, pady=5)
        
        # Smart Router Toggle
        router_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        router_frame.pack(fill="x", padx=15, pady=15)
        
        router_label = ctk.CTkLabel(
            router_frame,
            text="Smart Router",
            font=("Segoe UI", 13),
            text_color=self.TEXT_COLOR
        )
        router_label.pack(side="left")
        
        self.router_switch = ctk.CTkSwitch(
            router_frame,
            text="",
            width=50,
            fg_color=self.ACCENT_COLOR,
            progress_color=self.ACCENT_COLOR,
            command=self._on_router_toggle
        )
        self.router_switch.pack(side="right")
        self.router_switch.select()  # On by default
        
        # Model Selector
        model_label = ctk.CTkLabel(
            self.sidebar,
            text="Model Selection",
            font=("Segoe UI", 13),
            text_color=self.TEXT_COLOR
        )
        model_label.pack(pady=(5, 5), padx=15, anchor="w")
        
        self.model_selector = ctk.CTkComboBox(
            self.sidebar,
            values=["GPT-4o", "Claude Opus", "Gemini Pro", "GPT-4o-mini"],
            font=("Segoe UI", 12),
            fg_color=self.CARD_COLOR,
            button_color=self.ACCENT_COLOR,
            border_color="#475569",
            text_color=self.TEXT_COLOR,
            state="disabled"  # Disabled when router is on
        )
        self.model_selector.pack(fill="x", padx=15, pady=(0, 15))
        self.model_selector.set("GPT-4o")
    
    def _create_chat_area(self, parent):
        """Create the main chat area."""
        chat_container = ctk.CTkFrame(parent, fg_color="transparent")
        chat_container.pack(side="left", fill="both", expand=True)
        
        # Header
        header = ctk.CTkLabel(
            chat_container,
            text="Mosaic Chat",
            font=("Segoe UI", 24, "bold"),
            text_color=self.TEXT_COLOR
        )
        header.pack(pady=(0, 15), anchor="w")
        
        # Chat history (scrollable)
        self.chat_frame = ctk.CTkScrollableFrame(
            chat_container,
            fg_color=self.CARD_COLOR,
            corner_radius=15
        )
        self.chat_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Welcome message
        self._add_system_message("Welcome to Mosaic! Your infinite context AI assistant.")
        self._add_system_message(f"Budget limit: ${self.budget_limit:.2f}")
        
        # Input area
        input_frame = ctk.CTkFrame(chat_container, fg_color=self.CARD_COLOR, corner_radius=15)
        input_frame.pack(fill="x")
        
        self.input_field = ctk.CTkTextbox(
            input_frame,
            height=80,
            font=("Segoe UI", 13),
            fg_color="#1E293B",
            border_color="#475569",
            border_width=2,
            text_color=self.TEXT_COLOR,
            wrap="word"
        )
        self.input_field.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        
        send_btn = ctk.CTkButton(
            input_frame,
            text="Send",
            font=("Segoe UI", 14, "bold"),
            width=100,
            height=80,
            fg_color=self.ACCENT_COLOR,
            hover_color="#7C3AED",
            text_color=self.TEXT_COLOR,
            corner_radius=10,
            command=self._on_send_message
        )
        send_btn.pack(side="right", padx=(0, 15), pady=15)
    
    def _create_debug_log(self):
        """Create the collapsible debug log section."""
        self.debug_container = ctk.CTkFrame(self, fg_color=self.BG_COLOR)
        self.debug_container.pack(fill="x", padx=20, pady=(0, 20))
        
        # Debug toggle
        debug_toggle_frame = ctk.CTkFrame(self.debug_container, fg_color="transparent")
        debug_toggle_frame.pack(fill="x")
        
        self.debug_checkbox = ctk.CTkCheckBox(
            debug_toggle_frame,
            text="Show Debug Log (Matrix Mode)",
            font=("Segoe UI", 12),
            text_color=self.TEXT_COLOR,
            fg_color=self.ACCENT_COLOR,
            hover_color="#7C3AED",
            command=self._toggle_debug_log
        )
        self.debug_checkbox.pack(side="left")
        
        # Debug log (initially hidden)
        self.debug_log = ctk.CTkTextbox(
            self.debug_container,
            height=150,
            font=("Consolas", 10),
            fg_color="#0A0F1E",
            border_color="#22C55E",
            border_width=2,
            text_color="#22C55E",
            wrap="none"
        )
        # Don't pack initially - will be shown when toggled
    
    def _toggle_debug_log(self):
        """Toggle debug log visibility."""
        self.debug_visible = self.debug_checkbox.get()
        
        if self.debug_visible:
            self.debug_log.pack(fill="x", pady=(10, 0))
            self._add_debug_message("[MATRIX] Debug log activated...")
            self._add_debug_message("[REPL] Python environment initialized")
        else:
            self.debug_log.pack_forget()
    
    def _on_router_toggle(self):
        """Handle smart router toggle."""
        self.smart_router_enabled = self.router_switch.get()
        
        if self.smart_router_enabled:
            self.model_selector.configure(state="disabled")
            self._add_system_message("Smart Router: ENABLED - Automatic model selection active")
        else:
            self.model_selector.configure(state="normal")
            self._add_system_message("Smart Router: DISABLED - Manual model selection")
    
    def _on_load_document(self):
        """Handle document loading."""
        try:
            # Open file dialog for PDF selection
            file_path = filedialog.askopenfilename(
                title="Select PDF Document",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                parent=self
            )
            
            # Check if user cancelled
            if not file_path:
                self._add_debug_message("[LOAD] Document loading cancelled by user")
                return
            
            # Extract filename for display
            filename = os.path.basename(file_path)
            
            # Show loading message
            self._add_system_message(f"📄 Loading: {filename}...")
            self._add_debug_message(f"[LOAD] Starting PDF extraction from: {file_path}")
            
            # Extract text from PDF
            try:
                pdf_text = load_pdf(file_path)
                self._add_debug_message(f"[LOAD] Extracted {len(pdf_text)} characters from PDF")
            except FileNotFoundError as e:
                error_msg = f"File not found: {filename}"
                self._add_system_message(f"❌ {error_msg}")
                self._add_debug_message(f"[ERROR] {str(e)}")
                return
            except ValueError as e:
                error_msg = str(e)
                self._add_system_message(f"❌ {error_msg}")
                self._add_debug_message(f"[ERROR] {error_msg}")
                return
            except Exception as e:
                error_msg = f"Failed to load PDF: {str(e)}"
                self._add_system_message(f"❌ {error_msg}")
                self._add_debug_message(f"[ERROR] {error_msg}")
                return
            
            # Chunk the text
            chunk_size = 4000
            overlap = 200
            try:
                chunks = chunk_text(pdf_text, chunk_size=chunk_size, overlap=overlap)
                self._add_debug_message(f"[LOAD] Split into {len(chunks)} chunks (size={chunk_size}, overlap={overlap})")
            except Exception as e:
                error_msg = f"Failed to chunk text: {str(e)}"
                self._add_system_message(f"❌ {error_msg}")
                self._add_debug_message(f"[ERROR] {error_msg}")
                return
            
            # Add chunks to loaded context
            self.loaded_context.extend(chunks)
            self.loaded_documents.append(filename)
            
            # Show success message
            success_msg = f"✅ Loaded {len(chunks)} chunks from {filename}"
            self._add_system_message(success_msg)
            self._add_debug_message(f"[LOAD] Total context chunks: {len(self.loaded_context)}")
            self._add_debug_message(f"[LOAD] Loaded documents: {', '.join(self.loaded_documents)}")
            
            # Show summary of loaded documents
            if len(self.loaded_documents) > 1:
                self._add_system_message(f"📚 Total documents loaded: {len(self.loaded_documents)}")
            
        except Exception as e:
            # Catch any unexpected errors
            error_msg = f"Unexpected error during document loading: {str(e)}"
            self._add_system_message(f"❌ {error_msg}")
            self._add_debug_message(f"[ERROR] {error_msg}")
            import traceback
            self._add_debug_message(f"[TRACEBACK] {traceback.format_exc()}")
    
    def _on_send_message(self):
        """Handle send button click."""
        message = self.input_field.get("1.0", "end-1c").strip()
        
        if not message:
            return
        
        # Add user message to chat
        self._add_user_message(message)
        
        # Clear input
        self.input_field.delete("1.0", "end")
        
        # Simulate processing and response
        self._simulate_response(message)
    
    def _add_user_message(self, message: str):
        """Add a user message to the chat."""
        msg_frame = ctk.CTkFrame(self.chat_frame, fg_color="#1E293B", corner_radius=10)
        msg_frame.pack(fill="x", pady=5, padx=10, anchor="e")
        
        label = ctk.CTkLabel(
            msg_frame,
            text=f"You: {message}",
            font=("Segoe UI", 12),
            text_color=self.TEXT_COLOR,
            wraplength=600,
            justify="left",
            anchor="w"
        )
        label.pack(pady=10, padx=15, anchor="w")
    
    def _add_assistant_message(self, message: str):
        """Add an assistant message to the chat."""
        msg_frame = ctk.CTkFrame(self.chat_frame, fg_color="#7C3AED", corner_radius=10)
        msg_frame.pack(fill="x", pady=5, padx=10)
        
        label = ctk.CTkLabel(
            msg_frame,
            text=f"Mosaic: {message}",
            font=("Segoe UI", 12),
            text_color=self.TEXT_COLOR,
            wraplength=600,
            justify="left",
            anchor="w"
        )
        label.pack(pady=10, padx=15, anchor="w")
    
    def _add_system_message(self, message: str):
        """Add a system message to the chat."""
        msg_frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        msg_frame.pack(fill="x", pady=3, padx=10)
        
        label = ctk.CTkLabel(
            msg_frame,
            text=f"💡 {message}",
            font=("Segoe UI", 11, "italic"),
            text_color="#94A3B8",
            wraplength=600,
            justify="left"
        )
        label.pack(pady=5, padx=15, anchor="w")
    
    def _add_debug_message(self, message: str):
        """Add a message to the debug log."""
        if self.debug_visible:
            timestamp = time.strftime("%H:%M:%S")
            self.debug_log.insert("end", f"[{timestamp}] {message}\n")
            self.debug_log.see("end")
    
    def _initialize_backend(self):
        """Initialize the backend bridge."""
        try:
            self.backend = MosaicBridge(
                config=self.config,
                message_callback=self._handle_backend_message
            )
            self._add_system_message("✅ Backend initialized successfully")
        except Exception as e:
            self._add_system_message(f"⚠️ Backend initialization failed: {str(e)}")
            self._add_debug_message(f"[ERROR] {str(e)}")
    
    def _handle_backend_message(self, message: tuple):
        """
        Handle message from backend (called from background thread).
        
        Args:
            message: Tuple of (type, data)
        """
        # Add to queue for thread-safe processing
        self.message_queue.put(message)
    
    def _check_queue(self):
        """Check message queue and update GUI (runs in main thread)."""
        try:
            # Process all pending messages
            while True:
                try:
                    message = self.message_queue.get_nowait()
                    self._process_backend_message(message)
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Error checking queue: {e}")
        
        # Schedule next check
        self.after(100, self._check_queue)
    
    def _process_backend_message(self, message: tuple):
        """
        Process a message from the backend.
        
        Args:
            message: Tuple of (type, data)
        """
        msg_type, data = message
        
        if msg_type == "LOG":
            # Debug log message
            self._add_debug_message(data)
        
        elif msg_type == "BUDGET":
            # Update budget
            self.update_budget(self.current_spend + data, self.budget_limit)
        
        elif msg_type == "DONE":
            # Final answer
            self._add_assistant_message(data)
            
            # Check hive state
            if self.backend:
                hive_state = self.backend.get_hive_state()
                if hive_state:
                    self._add_debug_message(f"[HIVE] Memory state: {hive_state}")
        
        elif msg_type == "ERROR":
            # Error message
            self._add_system_message(f"❌ Error: {data}")
            self._add_debug_message(f"[ERROR] {data}")
        
        elif msg_type == "HIVE":
            # Hive memory update
            self._add_debug_message(f"[HIVE] Updated: {data}")
    
    def _simulate_response(self, user_message: str):
        """Run actual RLM query via backend."""
        if not self.backend:
            self._add_system_message("⚠️ Backend not available - using simulated response")
            response = "Backend not initialized. Please check API keys and restart."
            self._add_assistant_message(response)
            return
        
        if self.backend.is_busy():
            self._add_system_message("⚠️ Backend is busy - please wait for current query to complete")
            return
        
        # Run query via backend
        self.backend.run_query(
            user_prompt=user_message,
            context=self.loaded_context,
            use_router=self.smart_router_enabled
        )
    
    def update_budget(self, current: float, maximum: float):
        """
        Update the budget progress bar and label.
        
        Args:
            current: Current spend amount
            maximum: Maximum budget limit
        """
        self.current_spend = current
        self.budget_limit = maximum
        
        # Calculate percentage
        percentage = min(current / maximum, 1.0) if maximum > 0 else 0
        
        # Update progress bar
        self.budget_progress.set(percentage)
        
        # Update color based on percentage
        if percentage < 0.5:
            color = "#10B981"  # Green
        elif percentage < 0.8:
            color = "#F59E0B"  # Yellow
        else:
            color = "#EF4444"  # Red
        
        self.budget_progress.configure(progress_color=color)
        
        # Update label
        self.spend_label.configure(text=f"Spent: ${current:.2f} / ${maximum:.2f}")
        
        # Check if limit exceeded
        if current >= maximum:
            self._add_system_message("⚠️ BUDGET LIMIT REACHED - Processing halted!")
            self._add_debug_message("[CIRCUIT BREAKER] Budget limit exceeded - shutting down")


# Standalone test
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    
    config = {
        "api_keys": {"openai": "test-key"},
        "budget_limit": 5.0
    }
    
    app = MainChatView(config)
    app.mainloop()
