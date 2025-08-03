"""
Base component framework for UsenetSync GUI
Provides common functionality for all GUI components
"""

import tkinter as tk
from tkinter import ttk
import threading
import logging
from typing import Optional, Dict, Any, Callable
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class BaseComponent(ABC):
    """Base class for all GUI components"""
    
    def __init__(self, parent, backend_interface=None):
        self.parent = parent
        self.backend = backend_interface
        self.logger = logging.getLogger(self.__class__.__name__)
        self.callbacks = {}
        self.state = {}
        
        # Thread safety
        self.main_thread_id = threading.get_ident()
        
    def add_callback(self, event: str, callback: Callable):
        """Add event callback"""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
    
    def trigger_callback(self, event: str, *args, **kwargs):
        """Trigger event callbacks"""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    self.logger.error(f"Callback error for {event}: {e}")
    
    def safe_call(self, func, *args, **kwargs):
        """Thread-safe function call"""
        if threading.get_ident() == self.main_thread_id:
            return func(*args, **kwargs)
        else:
            # Schedule on main thread
            self.parent.after_idle(lambda: func(*args, **kwargs))
    
    def update_state(self, **kwargs):
        """Update component state"""
        self.state.update(kwargs)
        self.trigger_callback('state_changed', self.state)
    
    @abstractmethod
    def create_widgets(self):
        """Create component widgets"""
        pass
    
    @abstractmethod
    def setup_bindings(self):
        """Setup event bindings"""
        pass

class ResponsiveTreeview(ttk.Treeview):
    """Enhanced Treeview with virtual scrolling for millions of items"""
    
    def __init__(self, parent, data_provider=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.data_provider = data_provider
        self.visible_items = {}
        self.total_items = 0
        self.page_size = 1000
        self.current_page = 0
        
        # Setup virtual scrolling
        self.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<Prior>", self._on_page_up)
        self.bind("<Next>", self._on_page_down)
        
    def set_data_provider(self, provider):
        """Set data provider for virtual scrolling"""
        self.data_provider = provider
        self.refresh_data()
    
    def refresh_data(self):
        """Refresh displayed data"""
        if not self.data_provider:
            return
        
        # Clear existing items
        for item in self.get_children():
            self.delete(item)
        
        # Load current page
        start_idx = self.current_page * self.page_size
        items = self.data_provider.get_items(start_idx, self.page_size)
        
        for item_data in items:
            self.insert('', 'end', values=item_data)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        # Custom scrolling logic for virtual data
        if event.delta > 0:
            self._scroll_up()
        else:
            self._scroll_down()
    
    def _scroll_up(self):
        """Scroll up through virtual data"""
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_data()
    
    def _scroll_down(self):
        """Scroll down through virtual data"""
        max_pages = (self.total_items // self.page_size) + 1
        if self.current_page < max_pages - 1:
            self.current_page += 1
            self.refresh_data()

class ProgressDialog:
    """Enhanced progress dialog with cancellation support"""
    
    def __init__(self, parent, title="Operation in Progress"):
        self.parent = parent
        self.title = title
        self.dialog = None
        self.cancelled = False
        self.progress_var = None
        self.status_var = None
        
    def show(self, max_value=100):
        """Show progress dialog"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry("400x150")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50,
            self.parent.winfo_rooty() + 50
        ))
        
        # Progress widgets
        self.status_var = tk.StringVar(value="Starting...")
        status_label = ttk.Label(self.dialog, textvariable=self.status_var)
        status_label.pack(pady=10)
        
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            self.dialog, 
            variable=self.progress_var,
            maximum=max_value,
            mode='determinate'
        )
        progress_bar.pack(fill=tk.X, padx=20, pady=10)
        
        # Cancel button
        cancel_btn = ttk.Button(
            self.dialog, 
            text="Cancel", 
            command=self._cancel
        )
        cancel_btn.pack(pady=10)
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self._cancel)
    
    def update(self, value, status=""):
        """Update progress"""
        if self.progress_var:
            self.progress_var.set(value)
        if status and self.status_var:
            self.status_var.set(status)
        if self.dialog:
            self.dialog.update_idletasks()
    
    def _cancel(self):
        """Cancel operation"""
        self.cancelled = True
        if self.dialog:
            self.dialog.destroy()
    
    def close(self):
        """Close dialog"""
        if self.dialog:
            self.dialog.destroy()

class StatusBar:
    """Enhanced status bar with multiple sections"""
    
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self.sections = {}
        
        # Default sections
        self.add_section("main", weight=3)
        self.add_section("connection", weight=1)
        self.add_section("operations", weight=1)
        self.add_section("time", weight=1)
        
        self.frame.pack(side=tk.BOTTOM, fill=tk.X)
    
    def add_section(self, name, weight=1):
        """Add status bar section"""
        var = tk.StringVar()
        label = ttk.Label(self.frame, textvariable=var, relief=tk.SUNKEN)
        label.pack(side=tk.LEFT, fill=tk.X, expand=bool(weight))
        
        self.sections[name] = {
            'var': var,
            'label': label,
            'weight': weight
        }
    
    def set_text(self, section, text):
        """Set text for section"""
        if section in self.sections:
            self.sections[section]['var'].set(text)
    
    def clear(self, section=None):
        """Clear section or all sections"""
        if section:
            if section in self.sections:
                self.sections[section]['var'].set("")
        else:
            for sect in self.sections.values():
                sect['var'].set("")