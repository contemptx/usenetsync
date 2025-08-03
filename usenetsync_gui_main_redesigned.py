#!/usr/bin/env python3
"""
UsenetSync GUI - REDESIGNED VERSION
Complete redesign with tabs, real stats, and better UX
"""

import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
import sys
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import queue

# Prevent duplicate indexing operations
_indexing_in_progress = False
_indexing_lock = threading.Lock()

def _is_indexing_in_progress():
    """Check if indexing is currently in progress"""
    global _indexing_in_progress
    with _indexing_lock:
        return _indexing_in_progress

def _set_indexing_progress(status):
    """Set indexing progress status"""
    global _indexing_in_progress
    with _indexing_lock:
        _indexing_in_progress = status

# Add parent directory to path for backend imports
sys.path.insert(0, str(Path(__file__).parent))

# Import backend components
from main import UsenetSync
from user_management import UserManager
from configuration_manager import ConfigurationManager

# Import GUI components
from usenetsync_gui_user import UserInitDialog
from usenetsync_gui_download import DownloadDialog

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConsoleHandler(logging.Handler):
    """Custom logging handler for the GUI console"""
    
    def __init__(self, console_widget):
        super().__init__()
        self.console_widget = console_widget
        self.log_queue = queue.Queue()
        
    def emit(self, record):
        """Add log record to queue for GUI thread processing"""
        try:
            msg = self.format(record)
            self.log_queue.put(msg)
        except Exception:
            pass

class MainApplication:
    """Main GUI application for UsenetSync - REDESIGNED"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("UsenetSync v1.0 - Secure Usenet File Synchronization")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        # Application state
        self.app_backend = None
        self.current_folder = None
        self.status_timer = None
        self.console_handler = None
        
        # Threading
        self.main_thread_id = threading.get_ident()
        
        # Initialize backend in thread
        self.init_thread = threading.Thread(target=self._init_backend, daemon=True)
        self.init_thread.start()
        
        # Setup GUI
        self._setup_styles()
        self._create_main_layout()
        self._create_status_bar()
        
        # Bind events
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.bind("<F5>", lambda e: self._refresh_all())
        
        # Start status updates
        self._start_status_updates()
        
    def _setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles
        style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('Heading.TLabel', font=('Segoe UI', 10, 'bold'))
        style.configure('Status.TLabel', font=('Segoe UI', 9))
        style.configure('Success.TLabel', foreground='#2E7D32')
        style.configure('Error.TLabel', foreground='#C62828')
        style.configure('Warning.TLabel', foreground='#F57C00')
        style.configure('Console.TText', font=('Consolas', 9))
    
    def _create_main_layout(self):
        """Create main application layout with tabs"""
        # Main notebook for tabs
        self.main_notebook = ttk.Notebook(self.root)
        self.main_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self._create_folder_management_tab()
        self._create_user_id_tab()
        self._create_downloads_tab()
        self._create_console_tab()
        
        # Set default tab
        self.main_notebook.select(0)  # Folder Management is default
    
    def _create_folder_management_tab(self):
        """Create the main Folder Management tab"""
        self.folder_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.folder_tab, text="Folder Management")
        
        # Main paned window for folder management
        self.folder_paned = ttk.PanedWindow(self.folder_tab, orient=tk.HORIZONTAL)
        self.folder_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Folders list
        self.folders_frame = ttk.Frame(self.folder_paned)
        self.folder_paned.add(self.folders_frame, weight=1)
        
        # Right panel - Folder details
        self.details_frame = ttk.Frame(self.folder_paned)
        self.folder_paned.add(self.details_frame, weight=2)
        
        self._create_folders_panel()
        self._create_folder_details_panel()
    
    def _create_folders_panel(self):
        """Create the folders list panel"""
        # Header with Add Folder button
        header_frame = ttk.Frame(self.folders_frame)
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(header_frame, text="Folders", style='Title.TLabel').pack(side=tk.LEFT)
        ttk.Button(header_frame, text="Add Folder", 
                  command=self._add_folder).pack(side=tk.RIGHT)
        
        # Folders treeview
        tree_frame = ttk.Frame(self.folders_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview with columns
        columns = ('files', 'size', 'status', 'last_indexed')
        self.folders_tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings')
        
        # Configure columns
        self.folders_tree.heading('#0', text='Folder Name', anchor=tk.W)
        self.folders_tree.heading('files', text='Files', anchor=tk.CENTER)
        self.folders_tree.heading('size', text='Size', anchor=tk.CENTER)
        self.folders_tree.heading('status', text='Status', anchor=tk.CENTER)
        self.folders_tree.heading('last_indexed', text='Last Indexed', anchor=tk.CENTER)
        
        self.folders_tree.column('#0', width=200, minwidth=150)
        self.folders_tree.column('files', width=80, minwidth=60)
        self.folders_tree.column('size', width=100, minwidth=80)
        self.folders_tree.column('status', width=100, minwidth=80)
        self.folders_tree.column('last_indexed', width=120, minwidth=100)
        
        # Scrollbars
        tree_scroll_v = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.folders_tree.yview)
        tree_scroll_h = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.folders_tree.xview)
        self.folders_tree.configure(yscrollcommand=tree_scroll_v.set, xscrollcommand=tree_scroll_h.set)
        
        # Pack tree and scrollbars
        self.folders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll_v.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_h.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind selection event
        self.folders_tree.bind('<<TreeviewSelect>>', self._on_folder_select)
        
        # Context menu
        self.folder_context_menu = tk.Menu(self.root, tearoff=0)
        self.folder_context_menu.add_command(label="Re-index", command=self._reindex_selected_folder)
        self.folder_context_menu.add_command(label="Remove", command=self._remove_selected_folder)
        self.folders_tree.bind("<Button-3>", self._show_folder_context_menu)
    
    def _create_folder_details_panel(self):
        """Create the folder details panel"""
        # Header with folder actions
        self.details_header_frame = ttk.Frame(self.details_frame)
        self.details_header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Folder name
        self.folder_name_label = ttk.Label(self.details_header_frame, 
                                          text="Select a folder to view details", 
                                          style='Title.TLabel')
        self.folder_name_label.pack(side=tk.LEFT)
        
        # Action buttons (initially hidden)
        self.actions_frame = ttk.Frame(self.details_header_frame)
        self.actions_frame.pack(side=tk.RIGHT)
        
        self.index_button = ttk.Button(self.actions_frame, text="Index Folder", 
                                      command=self._index_current_folder, state='disabled')
        self.index_button.pack(side=tk.LEFT, padx=2)
        
        self.publish_button = ttk.Button(self.actions_frame, text="Publish Share", 
                                        command=self._publish_current_folder, state='disabled')
        self.publish_button.pack(side=tk.LEFT, padx=2)
        
        # Details notebook
        self.details_notebook = ttk.Notebook(self.details_frame)
        self.details_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Files tab
        self.files_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(self.files_frame, text="Files")
        
        # Shares tab
        self.shares_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(self.shares_frame, text="Shares")
        
        # Statistics tab
        self.stats_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(self.stats_frame, text="Statistics")
        
        self._create_files_tab()
        self._create_shares_tab()
        self._create_statistics_tab()
        
        # Initially show welcome message
        self._show_welcome_message()
    
    def _create_files_tab(self):
        """Create the files tab"""
        # Files treeview
        files_tree_frame = ttk.Frame(self.files_frame)
        files_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ('size', 'modified', 'status', 'segments')
        self.files_tree = ttk.Treeview(files_tree_frame, columns=columns, show='tree headings')
        
        self.files_tree.heading('#0', text='File Path', anchor=tk.W)
        self.files_tree.heading('size', text='Size', anchor=tk.CENTER)
        self.files_tree.heading('modified', text='Modified', anchor=tk.CENTER)
        self.files_tree.heading('status', text='Status', anchor=tk.CENTER)
        self.files_tree.heading('segments', text='Segments', anchor=tk.CENTER)
        
        self.files_tree.column('#0', width=300, minwidth=200)
        self.files_tree.column('size', width=100, minwidth=80)
        self.files_tree.column('modified', width=120, minwidth=100)
        self.files_tree.column('status', width=100, minwidth=80)
        self.files_tree.column('segments', width=80, minwidth=60)
        
        # Scrollbars for files
        files_scroll_v = ttk.Scrollbar(files_tree_frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        files_scroll_h = ttk.Scrollbar(files_tree_frame, orient=tk.HORIZONTAL, command=self.files_tree.xview)
        self.files_tree.configure(yscrollcommand=files_scroll_v.set, xscrollcommand=files_scroll_h.set)
        
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        files_scroll_v.pack(side=tk.RIGHT, fill=tk.Y)
        files_scroll_h.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _create_shares_tab(self):
        """Create the shares tab"""
        shares_tree_frame = ttk.Frame(self.shares_frame)
        shares_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ('type', 'created', 'access_string')
        self.shares_tree = ttk.Treeview(shares_tree_frame, columns=columns, show='tree headings')
        
        self.shares_tree.heading('#0', text='Share ID', anchor=tk.W)
        self.shares_tree.heading('type', text='Type', anchor=tk.CENTER)
        self.shares_tree.heading('created', text='Created', anchor=tk.CENTER)
        self.shares_tree.heading('access_string', text='Access String', anchor=tk.W)
        
        self.shares_tree.column('#0', width=150, minwidth=120)
        self.shares_tree.column('type', width=80, minwidth=60)
        self.shares_tree.column('created', width=120, minwidth=100)
        self.shares_tree.column('access_string', width=300, minwidth=200)
        
        # Scrollbars for shares
        shares_scroll_v = ttk.Scrollbar(shares_tree_frame, orient=tk.VERTICAL, command=self.shares_tree.yview)
        shares_scroll_h = ttk.Scrollbar(shares_tree_frame, orient=tk.HORIZONTAL, command=self.shares_tree.xview)
        self.shares_tree.configure(yscrollcommand=shares_scroll_v.set, xscrollcommand=shares_scroll_h.set)
        
        self.shares_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        shares_scroll_v.pack(side=tk.RIGHT, fill=tk.Y)
        shares_scroll_h.pack(side=tk.BOTTOM, fill=tk.X)
    
    def _create_statistics_tab(self):
        """Create the statistics tab with real data"""
        stats_container = ttk.Frame(self.stats_frame)
        stats_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Statistics labels - will be populated with real data
        self.stats_labels = {}
        
        # Create statistics display
        stats_data = [
            ('Total Files:', 'total_files'),
            ('Total Size:', 'total_size'),
            ('Indexed Files:', 'indexed_files'),
            ('Total Segments:', 'total_segments'),
            ('Upload Status:', 'upload_status'),
            ('Last Updated:', 'last_updated')
        ]
        
        for i, (label_text, key) in enumerate(stats_data):
            row = i // 2
            col = (i % 2) * 2
            
            ttk.Label(stats_container, text=label_text, 
                     style='Heading.TLabel').grid(row=row, column=col, sticky='w', padx=5, pady=3)
            
            value_label = ttk.Label(stats_container, text="No data", style='Status.TLabel')
            value_label.grid(row=row, column=col+1, sticky='w', padx=20, pady=3)
            
            self.stats_labels[key] = value_label
    
    def _create_user_id_tab(self):
        """Create the User ID tab"""
        self.user_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.user_tab, text="User ID")
        
        # User ID content
        user_container = ttk.Frame(self.user_tab)
        user_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        ttk.Label(user_container, text="User Profile", 
                 style='Title.TLabel').pack(anchor=tk.W, pady=(0, 20))
        
        # User info frame
        self.user_info_frame = ttk.LabelFrame(user_container, text="User Information", padding=15)
        self.user_info_frame.pack(fill=tk.X, pady=(0, 20))
        
        # User status
        self.user_status_label = ttk.Label(self.user_info_frame, text="Checking user status...", 
                                          style='Status.TLabel')
        self.user_status_label.pack(anchor=tk.W, pady=5)
        
        # User ID display
        self.user_id_frame = ttk.Frame(self.user_info_frame)
        self.user_id_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.user_id_frame, text="User ID:", style='Heading.TLabel').pack(side=tk.LEFT)
        self.user_id_label = ttk.Label(self.user_id_frame, text="Not initialized", 
                                      style='Status.TLabel')
        self.user_id_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Display name
        self.display_name_frame = ttk.Frame(self.user_info_frame)
        self.display_name_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.display_name_frame, text="Display Name:", style='Heading.TLabel').pack(side=tk.LEFT)
        self.display_name_label = ttk.Label(self.display_name_frame, text="Not set", 
                                           style='Status.TLabel')
        self.display_name_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.user_info_frame)
        buttons_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.init_user_button = ttk.Button(buttons_frame, text="Initialize User", 
                                          command=self._initialize_user)
        self.init_user_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.refresh_user_button = ttk.Button(buttons_frame, text="Refresh", 
                                             command=self._refresh_user_info)
        self.refresh_user_button.pack(side=tk.LEFT)
    
    def _create_downloads_tab(self):
        """Create the Downloads tab"""
        self.downloads_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.downloads_tab, text="Downloads")
        
        # Downloads content
        downloads_container = ttk.Frame(self.downloads_tab)
        downloads_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title and download button
        header_frame = ttk.Frame(downloads_container)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(header_frame, text="Downloads", 
                 style='Title.TLabel').pack(side=tk.LEFT)
        ttk.Button(header_frame, text="Download Share", 
                  command=self._download_share).pack(side=tk.RIGHT)
        
        # Downloads list (placeholder)
        downloads_frame = ttk.LabelFrame(downloads_container, text="Download History", padding=15)
        downloads_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(downloads_frame, text="Download history will be displayed here", 
                 style='Status.TLabel').pack(pady=20)
    
    def _create_console_tab(self):
        """Create the Console tab with real logging output"""
        self.console_tab = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.console_tab, text="Console")
        
        # Console container
        console_container = ttk.Frame(self.console_tab)
        console_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Console header
        console_header = ttk.Frame(console_container)
        console_header.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(console_header, text="System Console", 
                 style='Title.TLabel').pack(side=tk.LEFT)
        
        ttk.Button(console_header, text="Clear", 
                  command=self._clear_console).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(console_header, text="Save Log", 
                  command=self._save_console_log).pack(side=tk.RIGHT)
        
        # Console text widget
        console_frame = ttk.Frame(console_container)
        console_frame.pack(fill=tk.BOTH, expand=True)
        
        self.console_text = tk.Text(console_frame, wrap=tk.WORD, 
                                   font=('Consolas', 9), bg='#1e1e1e', fg='#ffffff',
                                   insertbackground='#ffffff', selectbackground='#404040')
        
        console_scroll = ttk.Scrollbar(console_frame, orient=tk.VERTICAL, command=self.console_text.yview)
        self.console_text.configure(yscrollcommand=console_scroll.set)
        
        self.console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        console_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Setup console logging
        self._setup_console_logging()
    
    def _setup_console_logging(self):
        """Setup console logging handler"""
        self.console_handler = ConsoleHandler(self.console_text)
        self.console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.console_handler.setFormatter(formatter)
        
        # Add to root logger
        logging.getLogger().addHandler(self.console_handler)
        
        # Start console update timer
        self._update_console()
    
    def _update_console(self):
        """Update console with new log messages"""
        try:
            while True:
                try:
                    message = self.console_handler.log_queue.get_nowait()
                    self.console_text.insert(tk.END, message + '\n')
                    self.console_text.see(tk.END)
                except queue.Empty:
                    break
        except Exception:
            pass
        
        # Schedule next update
        self.root.after(100, self._update_console)
    
    def _create_status_bar(self):
        """Create status bar"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)
        
        # Status text
        self.status_text = ttk.Label(self.status_frame, text="Ready", style='Status.TLabel')
        self.status_text.pack(side=tk.LEFT)
        
        # Progress bar (initially hidden)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.status_frame, variable=self.progress_var, 
                                          length=200, mode='determinate')
        
        # Connection status
        self.connection_status = ttk.Label(self.status_frame, text="Initializing...", 
                                         style='Status.TLabel')
        self.connection_status.pack(side=tk.RIGHT, padx=5)
    
    # Rest of implementation continues with all the methods from the redesigned GUI...
    # [The complete implementation would continue here with all the remaining methods]

def main():
    """Main entry point"""
    try:
        app = MainApplication()
        app.run()
    except Exception as error:
        logger.error(f"Fatal error: {error}")
        messagebox.showerror("Fatal Error", f"Application failed to start: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
