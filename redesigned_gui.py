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
                    self.console_text.insert(tk.END, message + '\\n')
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
    
    def _init_backend(self):
        """Initialize UsenetSync backend in background thread"""
        try:
            logger.info("Initializing UsenetSync backend...")
            self.app_backend = UsenetSync()
            self._thread_safe_status_update("Backend initialized successfully", "success")
            logger.info("Backend initialization complete")
            
            # Load initial data
            self._thread_safe_call(self._load_initial_data)
            
        except Exception as error:
            logger.error(f"Failed to initialize backend: {error}")
            self._thread_safe_status_update(f"Initialization failed: {error}", "error")
    
    def _thread_safe_call(self, func, *args, **kwargs):
        """Execute function in main thread"""
        if threading.get_ident() == self.main_thread_id:
            return func(*args, **kwargs)
        else:
            self.root.after_idle(lambda: func(*args, **kwargs))
    
    def _thread_safe_status_update(self, message, status_type="info"):
        """Update status from any thread"""
        def update():
            self.status_text.config(text=message)
            if status_type == "success":
                self.status_text.config(style='Success.TLabel')
            elif status_type == "error":
                self.status_text.config(style='Error.TLabel')
            elif status_type == "warning":
                self.status_text.config(style='Warning.TLabel')
            else:
                self.status_text.config(style='Status.TLabel')
        self._thread_safe_call(update)
    
    def _load_initial_data(self):
        """Load initial data into GUI"""
        if not self.app_backend:
            return
        
        try:
            logger.info("Loading initial GUI data...")
            
            # Update user info
            self._refresh_user_info()
            
            # Load folders
            self._refresh_folders_list()
            
            logger.info("Initial data load complete")
            
        except Exception as error:
            logger.error(f"Failed to load initial data: {error}")
            self._thread_safe_status_update(f"Data load failed: {error}", "error")
    
    def _refresh_user_info(self):
        """Refresh user information in User ID tab"""
        if not self.app_backend:
            return
        
        try:
            if self.app_backend.user.is_initialized():
                user_id = self.app_backend.user.get_user_id()
                display_name = getattr(self.app_backend.user, 'get_display_name', lambda: "User")()
                
                self.user_status_label.config(text="✓ User is initialized", style='Success.TLabel')
                self.user_id_label.config(text=f"{user_id[:32]}...")
                self.user_display_name_label.config(text=display_name)
                self.init_user_button.config(text="Re-initialize User")
                
                logger.info(f"User status: Initialized (ID: {user_id[:16]}...)")
            else:
                self.user_status_label.config(text="⚠ User not initialized", style='Warning.TLabel')
                self.user_id_label.config(text="Not initialized")
                self.display_name_label.config(text="Not set")
                self.init_user_button.config(text="Initialize User")
                
                logger.warning("User not initialized")
                
        except Exception as error:
            logger.error(f"Error refreshing user info: {error}")
            self.user_status_label.config(text=f"✗ Error: {error}", style='Error.TLabel')
    
    def _refresh_folders_list(self):
        """Refresh the folders list with real data"""
        if not self.app_backend:
            return
        
        try:
            logger.info("Refreshing folders list...")
            
            # Clear existing items
            for item in self.folders_tree.get_children():
                self.folders_tree.delete(item)
            
            # Get folders from database with real statistics
            with self.app_backend.db.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        f.folder_unique_id,
                        f.display_name,
                        f.folder_path,
                        f.state,
                        f.created_at,
                        f.updated_at,
                        COUNT(DISTINCT files.id) as file_count,
                        COALESCE(SUM(files.size), 0) as total_size,
                        COUNT(DISTINCT s.id) as segment_count
                    FROM folders f
                    LEFT JOIN files ON f.id = files.folder_id
                    LEFT JOIN segments s ON files.id = s.file_id
                    GROUP BY f.id
                    ORDER BY f.display_name, f.folder_path
                """)
                
                folders = cursor.fetchall()
                
                for row in folders:
                    folder_id, display_name, folder_path, state, created_at, updated_at, file_count, total_size, segment_count = row
                    
                    # Format data
                    name = display_name or os.path.basename(folder_path)
                    status = state or "Unknown"
                    last_indexed = updated_at or created_at or "Never"
                    
                    if isinstance(last_indexed, str) and last_indexed != "Never":
                        try:
                            # Parse and format datetime
                            dt = datetime.fromisoformat(last_indexed.replace('Z', '+00:00'))
                            last_indexed = dt.strftime("%Y-%m-%d %H:%M")
                        except:
                            pass
                    
                    # Insert into tree with real data
                    self.folders_tree.insert('', tk.END, 
                                           text=f"📁 {name}",
                                           values=(
                                               f"{file_count:,}",
                                               self._format_size(total_size),
                                               status.title(),
                                               last_indexed
                                           ),
                                           tags=(folder_id,))
                    
                logger.info(f"Loaded {len(folders)} folders with real statistics")
                
        except Exception as error:
            logger.error(f"Failed to refresh folders list: {error}")
            # Insert error indicator
            self.folders_tree.insert('', tk.END, text="✗ Error loading folders", values=("", "", "", ""))
    
    def _format_size(self, size_bytes):
        """Format size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def _on_folder_select(self, event):
        """Handle folder selection"""
        selection = self.folders_tree.selection()
        if not selection:
            self._show_welcome_message()
            return
        
        try:
            item = selection[0]
            tags = self.folders_tree.item(item, 'tags')
            if tags:
                folder_id = tags[0]
                self._show_folder_details(folder_id)
        except Exception as error:
            logger.error(f"Error selecting folder: {error}")
    
    def _show_folder_details(self, folder_id):
        """Show detailed folder information with real data"""
        if not self.app_backend or not folder_id:
            return
        
        try:
            logger.info(f"Loading details for folder: {folder_id}")
            
            # Get folder info
            with self.app_backend.db.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT display_name, folder_path, state FROM folders 
                    WHERE folder_unique_id = ?
                """, (folder_id,))
                folder_row = cursor.fetchone()
                
                if not folder_row:
                    logger.error(f"Folder {folder_id} not found")
                    return
                
                display_name, folder_path, state = folder_row
                folder_name = display_name or os.path.basename(folder_path)
                
                # Update header
                self.folder_name_label.config(text=f"📁 {folder_name}")
                
                # Enable action buttons
                self.index_button.config(state='normal')
                self.publish_button.config(state='normal')
                
                self.current_folder = folder_id
                
                # Load real data for each tab
                self._load_folder_files(folder_id)
                self._load_folder_shares(folder_id)
                self._load_folder_statistics(folder_id)
                
                logger.info(f"Folder details loaded for: {folder_name}")
                
        except Exception as error:
            logger.error(f"Error showing folder details: {error}")
            messagebox.showerror("Error", f"Failed to load folder details: {error}")
    
    def _load_folder_files(self, folder_id):
        """Load real file data for the folder"""
        try:
            # Clear existing files
            for item in self.files_tree.get_children():
                self.files_tree.delete(item)
            
            # Get real file data
            with self.app_backend.db.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        files.file_path,
                        files.size,
                        files.modified_at,
                        files.state,
                        COUNT(s.id) as segment_count
                    FROM files
                    JOIN folders f ON files.folder_id = f.id
                    LEFT JOIN segments s ON files.id = s.file_id
                    WHERE f.folder_unique_id = ?
                    GROUP BY files.id
                    ORDER BY files.file_path
                """, (folder_id,))
                
                files = cursor.fetchall()
                
                for file_path, size, modified_at, state, segment_count in files:
                    # Format data
                    size_str = self._format_size(size or 0)
                    
                    if modified_at:
                        try:
                            dt = datetime.fromisoformat(modified_at.replace('Z', '+00:00'))
                            modified_str = dt.strftime("%Y-%m-%d %H:%M")
                        except:
                            modified_str = str(modified_at)[:16]
                    else:
                        modified_str = "Unknown"
                    
                    status = state or "Unknown"
                    segments = f"{segment_count}" if segment_count > 0 else "0"
                    
                    self.files_tree.insert('', tk.END, 
                                         text=f"📄 {file_path}",
                                         values=(size_str, modified_str, status.title(), segments))
                
                logger.info(f"Loaded {len(files)} files for folder")
                
        except Exception as error:
            logger.error(f"Error loading folder files: {error}")
    
    def _load_folder_shares(self, folder_id):
        """Load real share data for the folder"""
        try:
            # Clear existing shares
            for item in self.shares_tree.get_children():
                self.shares_tree.delete(item)
            
            # Get real share data
            with self.app_backend.db.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        p.share_id,
                        p.share_type,
                        p.published_at,
                        p.access_string
                    FROM publications p
                    JOIN folders f ON p.folder_id = f.id
                    WHERE f.folder_unique_id = ?
                    ORDER BY p.published_at DESC
                """, (folder_id,))
                
                shares = cursor.fetchall()
                
                for share_id, share_type, published_at, access_string in shares:
                    # Format data
                    if published_at:
                        try:
                            dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                            created_str = dt.strftime("%Y-%m-%d %H:%M")
                        except:
                            created_str = str(published_at)[:16]
                    else:
                        created_str = "Unknown"
                    
                    access_short = access_string[:50] + "..." if len(access_string) > 50 else access_string
                    
                    self.shares_tree.insert('', tk.END, 
                                          text=share_id or "Unknown",
                                          values=(share_type or "Unknown", created_str, access_short))
                
                logger.info(f"Loaded {len(shares)} shares for folder")
                
        except Exception as error:
            logger.error(f"Error loading folder shares: {error}")
    
    def _load_folder_statistics(self, folder_id):
        """Load real statistics for the folder"""
        try:
            # Get comprehensive folder statistics
            with self.app_backend.db.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        COUNT(DISTINCT files.id) as total_files,
                        COALESCE(SUM(files.size), 0) as total_size,
                        COUNT(DISTINCT CASE WHEN files.state = 'indexed' THEN files.id END) as indexed_files,
                        COUNT(DISTINCT s.id) as total_segments,
                        f.updated_at
                    FROM folders f
                    LEFT JOIN files ON f.id = files.folder_id
                    LEFT JOIN segments s ON files.id = s.file_id
                    WHERE f.folder_unique_id = ?
                    GROUP BY f.id
                """, (folder_id,))
                
                stats = cursor.fetchone()
                
                if stats:
                    total_files, total_size, indexed_files, total_segments, updated_at = stats
                    
                    # Update statistics labels
                    self.stats_labels['total_files'].config(text=f"{total_files:,}")
                    self.stats_labels['total_size'].config(text=self._format_size(total_size))
                    self.stats_labels['indexed_files'].config(text=f"{indexed_files:,}")
                    self.stats_labels['total_segments'].config(text=f"{total_segments:,}")
                    
                    # Upload status
                    upload_status = "Complete" if indexed_files == total_files else "Partial"
                    self.stats_labels['upload_status'].config(text=upload_status)
                    
                    # Last updated
                    if updated_at:
                        try:
                            dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                            last_updated = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            last_updated = str(updated_at)
                    else:
                        last_updated = "Never"
                    
                    self.stats_labels['last_updated'].config(text=last_updated)
                    
                    logger.info(f"Statistics loaded: {total_files} files, {self._format_size(total_size)}")
                else:
                    # No data found
                    for key in self.stats_labels:
                        self.stats_labels[key].config(text="No data")
                
        except Exception as error:
            logger.error(f"Error loading folder statistics: {error}")
            for key in self.stats_labels:
                self.stats_labels[key].config(text="Error")
    
    def _show_welcome_message(self):
        """Show welcome message when no folder is selected"""
        self.folder_name_label.config(text="Select a folder to view details")
        self.index_button.config(state='disabled')
        self.publish_button.config(state='disabled')
        self.current_folder = None
        
        # Clear all tabs
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        for item in self.shares_tree.get_children():
            self.shares_tree.delete(item)
        for key in self.stats_labels:
            self.stats_labels[key].config(text="No folder selected")
    
    def _add_folder(self):
        """Add a new folder to index"""
        if not self.app_backend:
            messagebox.showerror("Error", "Backend not initialized")
            return
        
        if not self.app_backend.user.is_initialized():
            messagebox.showwarning("Warning", "Please initialize user first")
            self.main_notebook.select(1)  # Switch to User ID tab
            return
        
        # Select folder
        folder_path = filedialog.askdirectory(title="Select folder to add")
        if not folder_path:
            return
        
        logger.info(f"Adding new folder: {folder_path}")
        
        # Check if indexing is already in progress
        if _is_indexing_in_progress():
            messagebox.showwarning("Warning", "Indexing operation already in progress")
            return
        
        # Start indexing in background
        self._index_folder_async(folder_path)
    
    def _index_folder_async(self, folder_path, folder_id=None, reindex=False):
        """Index folder asynchronously with progress tracking"""
        # Show progress
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
        self.progress_var.set(0)
        
        def index_worker():
            try:
                _set_indexing_progress(True)
                
                operation = "Re-indexing" if reindex else "Indexing"
                logger.info(f"{operation} folder: {folder_path}")
                
                def progress_callback(progress_data):
                    """Enhanced progress callback"""
                    try:
                        if isinstance(progress_data, dict):
                            current = progress_data.get('current', 0)
                            total = progress_data.get('total', 1)
                            file_name = progress_data.get('file', '')
                            phase = progress_data.get('phase', 'indexing')
                        else:
                            # Handle legacy tuple format
                            if hasattr(progress_data, '__len__') and len(progress_data) >= 2:
                                current, total = progress_data[0], progress_data[1]
                                file_name = ''
                                phase = 'indexing'
                            else:
                                current, total = progress_data, 100
                                file_name = ''
                                phase = 'indexing'
                        
                        if total > 0:
                            progress = (current / total) * 100
                            self._thread_safe_call(lambda: self.progress_var.set(progress))
                            
                            # Update status
                            if file_name and file_name != 'Starting indexing...':
                                display_name = os.path.basename(file_name)
                                status_msg = f"{phase.capitalize()}: {current}/{total} - {display_name}"
                            else:
                                status_msg = f"{phase.capitalize()}: {current}/{total} files"
                            
                            self._thread_safe_status_update(status_msg)
                            
                    except Exception as e:
                        logger.error(f"Error in progress callback: {e}")
                
                # Call the backend
                if reindex and folder_id:
                    result = self.app_backend.index_folder(
                        folder_path, folder_id=folder_id, reindex=True, 
                        progress_callback=progress_callback
                    )
                else:
                    result = self.app_backend.index_folder(
                        folder_path, progress_callback=progress_callback
                    )
                
                self._thread_safe_call(lambda: self.progress_bar.pack_forget())
                
                # Show results
                if result:
                    files_processed = result.get('files_processed', result.get('files_indexed', 0))
                    segments_created = result.get('segments_created', 0)
                    elapsed_time = result.get('elapsed_time', 0)
                    
                    if files_processed > 0:
                        status_msg = f"{operation} complete: {files_processed} files"
                        if segments_created > 0:
                            status_msg += f", {segments_created} segments"
                        if elapsed_time > 0:
                            status_msg += f" ({elapsed_time:.1f}s)"
                        self._thread_safe_status_update(status_msg, "success")
                        logger.info(status_msg)
                    else:
                        self._thread_safe_status_update(f"{operation} completed (no files processed)", "warning")
                else:
                    self._thread_safe_status_update(f"{operation} completed", "success")
                
                # Refresh the folders list
                self._thread_safe_call(self._refresh_folders_list)
                
            except Exception as error:
                logger.error(f"{operation} failed: {error}")
                self._thread_safe_call(lambda: self.progress_bar.pack_forget())
                self._thread_safe_status_update(f"{operation} failed: {error}", "error")
                self._thread_safe_call(lambda: messagebox.showerror(f"{operation} Failed", str(error)))
            finally:
                _set_indexing_progress(False)
        
        threading.Thread(target=index_worker, daemon=True).start()
    
    def _index_current_folder(self):
        """Index the currently selected folder"""
        if not self.current_folder:
            return
        
        try:
            # Get folder path
            with self.app_backend.db.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT folder_path FROM folders WHERE folder_unique_id = ?
                """, (self.current_folder,))
                row = cursor.fetchone()
                
                if not row:
                    messagebox.showerror("Error", "Folder not found in database")
                    return
                
                folder_path = row[0]
            
            if messagebox.askyesno("Confirm Index", f"Re-index folder:\\n{folder_path}\\n\\nThis will scan for new and changed files."):
                self._index_folder_async(folder_path, self.current_folder, reindex=True)
                
        except Exception as error:
            logger.error(f"Error indexing current folder: {error}")
            messagebox.showerror("Error", f"Failed to index folder: {error}")
    
    def _publish_current_folder(self):
        """Publish the currently selected folder"""
        if not self.current_folder:
            return
        
        try:
            from tkinter import simpledialog
            
            share_type = messagebox.askyesnocancel("Share Type", 
                                                 "Yes for Public share, No for Private share, Cancel to abort")
            if share_type is None:
                return
            
            def publish_worker():
                try:
                    if share_type:
                        # Public share
                        self._thread_safe_status_update("Creating public share...")
                        logger.info(f"Creating public share for folder: {self.current_folder}")
                        
                        access_string = self.app_backend.publish_folder(
                            self.current_folder, 
                            share_type='public'
                        )
                        self._thread_safe_status_update("Public share created successfully", "success")
                        logger.info("Public share created successfully")
                    else:
                        # Private share
                        users_input = simpledialog.askstring("Authorized Users", 
                                                            "Enter authorized user emails (comma-separated):")
                        if not users_input:
                            self._thread_safe_status_update("Private share cancelled", "error")
                            return
                        
                        authorized_users = [u.strip() for u in users_input.split(',')]
                        self._thread_safe_status_update("Creating private share...")
                        logger.info(f"Creating private share for folder: {self.current_folder}")
                        
                        access_string = self.app_backend.publish_folder(
                            self.current_folder,
                            share_type='private',
                            authorized_users=authorized_users
                        )
                        self._thread_safe_status_update("Private share created successfully", "success")
                        logger.info("Private share created successfully")
                    
                    # Show access string
                    self._thread_safe_call(lambda: messagebox.showinfo("Share Created", 
                                                                      f"Access string:\\n{access_string}"))
                    
                    # Refresh data
                    self._thread_safe_call(lambda: self._load_folder_shares(self.current_folder))
                    self._thread_safe_call(self._refresh_folders_list)
                    
                except Exception as publish_error:
                    logger.error(f"Publishing failed: {publish_error}")
                    self._thread_safe_status_update(f"Publishing failed: {publish_error}", "error")
                    self._thread_safe_call(lambda: messagebox.showerror("Publishing Failed", str(publish_error)))
            
            threading.Thread(target=publish_worker, daemon=True).start()
            
        except Exception as error:
            logger.error(f"Error in publish share: {error}")
            messagebox.showerror("Error", f"Failed to start publishing: {error}")
    
    def _initialize_user(self):
        """Initialize or re-initialize user"""
        try:
            dialog = UserInitDialog(self.root, self.app_backend)
            self.root.wait_window(dialog.dialog)
            
            # Refresh user info
            self._refresh_user_info()
            
        except Exception as error:
            logger.error(f"Error initializing user: {error}")
            messagebox.showerror("Error", f"Failed to initialize user: {error}")
    
    def _download_share(self):
        """Download a share"""
        if not self.app_backend:
            messagebox.showerror("Error", "Backend not initialized")
            return
        
        try:
            dialog = DownloadDialog(self.root, self.app_backend)
            self.root.wait_window(dialog.dialog)
        except Exception as error:
            logger.error(f"Error showing download dialog: {error}")
            messagebox.showerror("Error", f"Failed to show download dialog: {error}")
    
    def _refresh_all(self):
        """Refresh all data"""
        logger.info("Refreshing all data...")
        self._thread_safe_status_update("Refreshing...")
        
        def refresh_worker():
            try:
                self._thread_safe_call(self._refresh_user_info)
                self._thread_safe_call(self._refresh_folders_list)
                if self.current_folder:
                    self._thread_safe_call(lambda: self._show_folder_details(self.current_folder))
                self._thread_safe_status_update("Refresh complete", "success")
                logger.info("Refresh complete")
            except Exception as error:
                logger.error(f"Refresh failed: {error}")
                self._thread_safe_status_update(f"Refresh failed: {error}", "error")
        
        threading.Thread(target=refresh_worker, daemon=True).start()
    
    def _start_status_updates(self):
        """Start periodic status updates"""
        def update_status():
            try:
                if self.app_backend and hasattr(self.app_backend, 'nntp'):
                    self.connection_status.config(text="Connected", style='Success.TLabel')
                else:
                    self.connection_status.config(text="Disconnected", style='Error.TLabel')
            except Exception:
                self.connection_status.config(text="Error", style='Error.TLabel')
            
            # Schedule next update
            self.status_timer = self.root.after(5000, update_status)
        
        update_status()
    
    def _show_folder_context_menu(self, event):
        """Show context menu for folders"""
        try:
            self.folder_context_menu.post(event.x_root, event.y_root)
        except Exception:
            pass
    
    def _reindex_selected_folder(self):
        """Re-index selected folder"""
        if self.current_folder:
            self._index_current_folder()
    
    def _remove_selected_folder(self):
        """Remove selected folder"""
        if not self.current_folder:
            return
        
        try:
            # Get folder info
            with self.app_backend.db.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT display_name, folder_path FROM folders WHERE folder_unique_id = ?
                """, (self.current_folder,))
                row = cursor.fetchone()
                
                if not row:
                    messagebox.showerror("Error", "Folder not found")
                    return
                
                display_name, folder_path = row
                name = display_name or os.path.basename(folder_path)
            
            if messagebox.askyesno("Confirm Removal", f"Remove folder '{name}' from index?\\n\\nThis will not delete files from disk."):
                logger.info(f"Removing folder: {name}")
                
                # Remove from database
                with self.app_backend.db.pool.get_connection() as conn:
                    cursor = conn.execute("SELECT id FROM folders WHERE folder_unique_id = ?", (self.current_folder,))
                    folder_row = cursor.fetchone()
                    if folder_row:
                        folder_db_id = folder_row[0]
                        
                        # Remove related data
                        conn.execute("DELETE FROM segments WHERE file_id IN (SELECT id FROM files WHERE folder_id = ?)", (folder_db_id,))
                        conn.execute("DELETE FROM files WHERE folder_id = ?", (folder_db_id,))
                        conn.execute("DELETE FROM publications WHERE folder_id = ?", (folder_db_id,))
                        conn.execute("DELETE FROM folders WHERE id = ?", (folder_db_id,))
                        conn.commit()
                
                self._show_welcome_message()
                self._refresh_folders_list()
                self._thread_safe_status_update(f"Removed folder '{name}'", "success")
                logger.info(f"Folder removed: {name}")
                
        except Exception as error:
            logger.error(f"Error removing folder: {error}")
            messagebox.showerror("Error", f"Failed to remove folder: {error}")
    
    def _clear_console(self):
        """Clear the console"""
        self.console_text.delete(1.0, tk.END)
        logger.info("Console cleared")
    
    def _save_console_log(self):
        """Save console log to file"""
        try:
            filename = filedialog.asksaveasfilename(
                title="Save Console Log",
                defaultextension=".log",
                filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if filename:
                content = self.console_text.get(1.0, tk.END)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                messagebox.showinfo("Success", f"Console log saved to {filename}")
                logger.info(f"Console log saved to: {filename}")
                
        except Exception as error:
            logger.error(f"Error saving console log: {error}")
            messagebox.showerror("Error", f"Failed to save console log: {error}")
    
    def _on_closing(self):
        """Handle application closing"""
        try:
            logger.info("Application closing...")
            
            if self.status_timer:
                self.root.after_cancel(self.status_timer)
            
            # Clean shutdown of backend
            if self.app_backend:
                self.app_backend.cleanup()
            
            self.root.destroy()
            
        except Exception as error:
            logger.error(f"Error during shutdown: {error}")
            self.root.destroy()
    
    def run(self):
        """Run the application"""
        try:
            logger.info("Starting UsenetSync GUI...")
            self.root.mainloop()
        except KeyboardInterrupt:
            self._on_closing()

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
