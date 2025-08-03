"""
GUI Error Handling and Logging Utilities
Centralized error handling for the GUI application
"""

import tkinter as tk
from tkinter import messagebox
import logging
import traceback
import threading
import sys
from pathlib import Path
from typing import Optional, Callable, Any
import time
from datetime import datetime

class GUIErrorHandler:
    """Centralized error handler for GUI operations"""
    
    def __init__(self, parent_window=None):
        self.parent = parent_window
        self.logger = logging.getLogger(__name__)
        self.error_count = 0
        self.last_error_time = 0
        self.error_suppression_threshold = 5  # Max errors per minute
        
        # Setup exception hook
        self.original_excepthook = sys.excepthook
        sys.excepthook = self.handle_exception
        
        # Thread-local storage for error context
        self.error_contexts = {}
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow keyboard interrupts to work normally
            self.original_excepthook(exc_type, exc_value, exc_traceback)
            return
        
        # Log the error
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        self.logger.error(f"Uncaught exception: {error_msg}")
        
        # Show error dialog if GUI is available
        if self.parent:
            self.show_error_dialog(
                "Unexpected Error", 
                f"An unexpected error occurred:\n\n{exc_type.__name__}: {exc_value}",
                details=error_msg
            )
    
    def show_error_dialog(self, title: str, message: str, details: str = None, 
                         error_type: str = "error"):
        """Show error dialog with optional details"""
        try:
            # Check error suppression
            current_time = time.time()
            if current_time - self.last_error_time < 60:  # Within 1 minute
                self.error_count += 1
                if self.error_count > self.error_suppression_threshold:
                    return  # Suppress excessive errors
            else:
                self.error_count = 1
            
            self.last_error_time = current_time
            
            # Create error dialog
            dialog = ErrorDialog(self.parent, title, message, details, error_type)
            
        except Exception as e:
            # Fallback to basic messagebox if custom dialog fails
            messagebox.showerror("Error", f"{title}\n\n{message}")
    
    def handle_async_error(self, error: Exception, context: str = ""):
        """Handle errors from background threads"""
        error_msg = f"Background operation error"
        if context:
            error_msg += f" in {context}"
        error_msg += f": {error}"
        
        self.logger.error(error_msg, exc_info=True)
        
        # Schedule error dialog on main thread
        if self.parent:
            self.parent.after(0, lambda: self.show_error_dialog(
                "Background Operation Error",
                error_msg,
                traceback.format_exc()
            ))
    
    def safe_call(self, func: Callable, *args, error_context: str = "", **kwargs) -> Any:
        """Safely call a function with error handling"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error in {error_context or func.__name__}: {e}", exc_info=True)
            if self.parent:
                self.show_error_dialog(
                    "Operation Error",
                    f"Error in {error_context or 'operation'}: {e}"
                )
            return None
    
    def async_safe_call(self, func: Callable, callback: Callable = None, 
                       error_context: str = "", *args, **kwargs):
        """Safely call a function in background thread with error handling"""
        def worker():
            try:
                result = func(*args, **kwargs)
                if callback and self.parent:
                    self.parent.after(0, lambda: callback(result))
            except Exception as e:
                self.handle_async_error(e, error_context)
        
        threading.Thread(target=worker, daemon=True).start()

class ErrorDialog:
    """Custom error dialog with expandable details"""
    
    def __init__(self, parent, title: str, message: str, details: str = None, 
                 error_type: str = "error"):
        self.parent = parent
        self.title = title
        self.message = message
        self.details = details
        self.error_type = error_type
        
        self.dialog = tk.Toplevel(parent) if parent else tk.Tk()
        self.dialog.title(title)
        self.dialog.geometry("500x200")
        
        if parent:
            self.dialog.transient(parent)
            self.dialog.grab_set()
            # Center on parent
            self.dialog.geometry("+%d+%d" % (
                parent.winfo_rootx() + 50,
                parent.winfo_rooty() + 50
            ))
        
        self.details_visible = False
        self.create_widgets()
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self.close_dialog)
    
    def create_widgets(self):
        """Create dialog widgets"""
        # Icon and message frame
        top_frame = ttk.Frame(self.dialog)
        top_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Error icon (text-based)
        icon_text = {
            "error": "✗",
            "warning": "⚠",
            "info": "ℹ"
        }.get(self.error_type, "✗")
        
        icon_color = {
            "error": "red",
            "warning": "orange", 
            "info": "blue"
        }.get(self.error_type, "red")
        
        icon_label = tk.Label(top_frame, text=icon_text, font=('Arial', 24), 
                             fg=icon_color)
        icon_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Message
        message_label = tk.Label(top_frame, text=self.message, wraplength=400,
                                justify=tk.LEFT, font=('Arial', 10))
        message_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Details frame (initially hidden)
        self.details_frame = ttk.LabelFrame(self.dialog, text="Details", padding=10)
        
        self.details_text = tk.Text(self.details_frame, height=10, wrap=tk.WORD,
                                   font=('Courier', 9))
        details_scroll = ttk.Scrollbar(self.details_frame, orient=tk.VERTICAL,
                                      command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scroll.set)
        
        if self.details:
            self.details_text.insert('1.0', self.details)
            self.details_text.configure(state=tk.DISABLED)
        
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.dialog)
        buttons_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Details button (only if details available)
        if self.details:
            self.details_button = ttk.Button(buttons_frame, text="Show Details",
                                           command=self.toggle_details)
            self.details_button.pack(side=tk.LEFT)
        
        # Report button
        ttk.Button(buttons_frame, text="Report Bug",
                  command=self.report_bug).pack(side=tk.LEFT, padx=10)
        
        # OK button
        ttk.Button(buttons_frame, text="OK", command=self.close_dialog,
                  style='Primary.TButton').pack(side=tk.RIGHT)
    
    def toggle_details(self):
        """Toggle details visibility"""
        if self.details_visible:
            # Hide details
            self.details_frame.pack_forget()
            self.dialog.geometry("500x200")
            self.details_button.config(text="Show Details")
            self.details_visible = False
        else:
            # Show details
            self.details_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
            self.dialog.geometry("600x500")
            self.details_button.config(text="Hide Details")
            self.details_visible = True
    
    def report_bug(self):
        """Open bug report dialog or webpage"""
        # Create simple bug report info
        report_dialog = tk.Toplevel(self.dialog)
        report_dialog.title("Report Bug")
        report_dialog.geometry("400x300")
        report_dialog.transient(self.dialog)
        
        ttk.Label(report_dialog, text="Bug Report Information", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        info_text = f"""
To report this bug, please include the following information:

Error: {self.title}
Message: {self.message}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Details:
{self.details or 'No additional details'}

Please send this information to:
support@usenetsync.dev
        """
        
        text_widget = tk.Text(report_dialog, wrap=tk.WORD, font=('Courier', 9))
        text_widget.insert('1.0', info_text.strip())
        text_widget.configure(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Button(report_dialog, text="Close", 
                  command=report_dialog.destroy).pack(pady=10)
    
    def close_dialog(self):
        """Close the dialog"""
        self.dialog.destroy()

class GUILogger:
    """GUI-friendly logger that can display messages in the interface"""
    
    def __init__(self, log_widget=None):
        self.log_widget = log_widget
        self.logger = logging.getLogger('GUI')
        self.max_lines = 1000  # Maximum lines to keep in GUI log
        
        # Setup custom handler if widget provided
        if log_widget:
            handler = GUILogHandler(log_widget, self.max_lines)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            ))
            self.logger.addHandler(handler)
    
    def log_to_gui(self, level: str, message: str):
        """Log message to GUI widget"""
        if self.log_widget:
            timestamp = datetime.now().strftime('%H:%M:%S')
            log_line = f"[{timestamp}] {level.upper()}: {message}\n"
            
            # Add to widget
            self.log_widget.config(state=tk.NORMAL)
            self.log_widget.insert(tk.END, log_line)
            
            # Limit lines
            lines = int(self.log_widget.index('end-1c').split('.')[0])
            if lines > self.max_lines:
                self.log_widget.delete('1.0', f'{lines - self.max_lines}.0')
            
            # Auto-scroll to bottom
            self.log_widget.see(tk.END)
            self.log_widget.config(state=tk.DISABLED)
    
    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)
        self.log_to_gui('INFO', message)
    
    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
        self.log_to_gui('WARNING', message)
    
    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)
        self.log_to_gui('ERROR', message)
    
    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
        self.log_to_gui('DEBUG', message)

class GUILogHandler(logging.Handler):
    """Custom logging handler for GUI text widget"""
    
    def __init__(self, text_widget, max_lines=1000):
        super().__init__()
        self.text_widget = text_widget
        self.max_lines = max_lines
    
    def emit(self, record):
        """Emit log record to GUI"""
        try:
            msg = self.format(record)
            
            # Schedule on main thread
            def update_gui():
                if self.text_widget.winfo_exists():
                    self.text_widget.config(state=tk.NORMAL)
                    self.text_widget.insert(tk.END, msg + '\n')
                    
                    # Limit lines
                    lines = int(self.text_widget.index('end-1c').split('.')[0])
                    if lines > self.max_lines:
                        self.text_widget.delete('1.0', f'{lines - self.max_lines}.0')
                    
                    self.text_widget.see(tk.END)
                    self.text_widget.config(state=tk.DISABLED)
            
            self.text_widget.after(0, update_gui)
            
        except Exception:
            self.handleError(record)