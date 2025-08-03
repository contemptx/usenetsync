"""
Main Application Window for UsenetSync GUI
Production-ready interface with full backend integration
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
import json
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import backend
from src.main import UsenetSync
from src.config.config_manager import ConfigManager

# Import GUI components
from components.base_component import StatusBar, ProgressDialog
from dialogs.user_init_dialog import UserInitDialog
from dialogs.download_dialog import DownloadDialog
from dialogs.settings_dialog import SettingsDialog
from widgets.folder_manager import FolderManagerWidget
from widgets.file_browser import FileBrowserWidget

class MainApplication:
    """Main GUI application for UsenetSync"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        
        # Application state
        self.backend = None
        self.config = None
        self.current_folder = None
        self.background_operations = {}
        self.shutdown_requested = False
        
        # Threading
        self.main_thread_id = threading.get_ident()
        self.init_lock = threading.Lock()
        
        # Setup logging
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize GUI
        self.setup_styles()
        self.create_menu()
        self.create_toolbar()
        self.create_main_layout()
        self.create_status_bar()
        
        # Setup event bindings
        self.setup_bindings()
        
        # Initialize backend
        self.init_backend_async()
        
    def setup_window(self):
        """Setup main window properties"""
        self.root.title("UsenetSync v2.0 - Secure Usenet File Synchronization")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        # Window icon (if available)
        try:
            icon_path = Path(__file__).parent / "resources" / "icons" / "usenetsync.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except:
            pass  # Icon not critical
    
    def setup_logging(self):
        """Setup GUI logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        file_handler = logging.FileHandler(log_dir / "gui.log")
        file_handler.setFormatter(formatter)
        
        # Setup logger
        logger = logging.getLogger()
        logger.addHandler(file_handler)
        logger.setLevel(logging.INFO)
    
    def setup_styles(self):
        """Setup GUI styles and themes"""
        style = ttk.Style()
        
        # Try to use modern theme
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'vista' in available_themes:
            style.theme_use('vista')
        
        # Custom styles
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Subtitle.TLabel', font=('Arial', 10))
        style.configure('Status.TLabel', font=('Arial', 9))
        
        # Button styles
        style.configure('Primary.TButton', font=('Arial', 9, 'bold'))
        style.configure('Success.TButton', foreground='#0F7B0F')
        style.configure('Warning.TButton', foreground='#FF8C00')
        style.configure('Error.TButton', foreground='#D13438')
    
    def create_menu(self):
        """Create application menu"""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        # File menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Initialize User...", command=self.show_user_init, accelerator="Ctrl+I")
        file_menu.add_separator()
        file_menu.add_command(label="Index Folder...", command=self.index_folder, accelerator="Ctrl+O")
        file_menu.add_command(label="Download Share...", command=self.download_share, accelerator="Ctrl+D")
        file_menu.add_separator()
        file_menu.add_command(label="Settings...", command=self.show_settings, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing, accelerator="Alt+F4")
        
        # Edit menu
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Refresh All", command=self.refresh_all, accelerator="F5")
        edit_menu.add_command(label="Clear Logs", command=self.clear_logs)
        
        # Tools menu
        tools_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="System Status", command=self.show_system_status)
        tools_menu.add_command(label="Connection Test", command=self.test_connection)
        tools_menu.add_command(label="Database Maintenance", command=self.database_maintenance)
        
        # Help menu
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self.show_user_guide)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_command(label="About", command=self.show_about)
    
    def create_toolbar(self):
        """Create main toolbar"""
        self.toolbar_frame = ttk.Frame(self.root)
        self.toolbar_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        
        # User operations
        user_frame = ttk.LabelFrame(self.toolbar_frame, text="User", padding=5)
        user_frame.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(user_frame, text="Initialize User", 
                  command=self.show_user_init, width=12).pack(side=tk.LEFT, padx=1)
        
        # Folder operations
        folder_frame = ttk.LabelFrame(self.toolbar_frame, text="Folders", padding=5)
        folder_frame.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(folder_frame, text="Index Folder", 
                  command=self.index_folder, width=12).pack(side=tk.LEFT, padx=1)
        ttk.Button(folder_frame, text="Publish Share", 
                  command=self.publish_share, width=12).pack(side=tk.LEFT, padx=1)
        
        # Download operations
        download_frame = ttk.LabelFrame(self.toolbar_frame, text="Downloads", padding=5)
        download_frame.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(download_frame, text="Download Share", 
                  command=self.download_share, width=12).pack(side=tk.LEFT, padx=1)
        
        # System operations
        system_frame = ttk.LabelFrame(self.toolbar_frame, text="System", padding=5)
        system_frame.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(system_frame, text="Refresh", 
                  command=self.refresh_all, width=8).pack(side=tk.LEFT, padx=1)
        ttk.Button(system_frame, text="Status", 
                  command=self.show_system_status, width=8).pack(side=tk.LEFT, padx=1)
        
        # Connection status
        self.connection_status = ttk.Label(
            self.toolbar_frame, 
            text="Initializing...", 
            style='Status.TLabel'
        )
        self.connection_status.pack(side=tk.RIGHT, padx=10)
    
    def create_main_layout(self):
        """Create main application layout"""
        # Main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Horizontal paned window
        self.main_paned = ttk.PanedWindow(self.main_container, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Navigation
        self.left_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(self.left_panel, weight=1)
        
        # Right panel - Details
        self.right_panel = ttk.Frame(self.main_paned)
        self.main_paned.add(self.right_panel, weight=3)
        
        self.create_navigation_panel()
        self.create_details_panel()
    
    def create_navigation_panel(self):
        """Create left navigation panel"""
        # Navigation header
        nav_header = ttk.Label(self.left_panel, text="Folders", style='Title.TLabel')
        nav_header.pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        # Folder tree with scrollbars
        tree_frame = ttk.Frame(self.left_panel)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.folder_tree = ttk.Treeview(tree_frame, columns=('status', 'files', 'size'), show='tree headings')
        
        # Tree columns
        self.folder_tree.heading('#0', text='Folder Name')
        self.folder_tree.heading('status', text='Status')
        self.folder_tree.heading('files', text='Files')
        self.folder_tree.heading('size', text='Size')
        
        self.folder_tree.column('#0', width=200)
        self.folder_tree.column('status', width=80)
        self.folder_tree.column('files', width=60)
        self.folder_tree.column('size', width=80)
        
        # Scrollbars
        tree_scrolly = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.folder_tree.yview)
        tree_scrollx = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.folder_tree.xview)
        self.folder_tree.configure(yscrollcommand=tree_scrolly.set, xscrollcommand=tree_scrollx.set)
        
        # Pack tree and scrollbars
        self.folder_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrolly.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scrollx.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Tree bindings
        self.folder_tree.bind('<<TreeviewSelect>>', self.on_folder_select)
        self.folder_tree.bind('<Button-3>', self.show_folder_context_menu)
        
        # Context menu
        self.folder_context_menu = tk.Menu(self.root, tearoff=0)
        self.folder_context_menu.add_command(label="Refresh", command=self.refresh_selected_folder)
        self.folder_context_menu.add_command(label="Publish", command=self.publish_selected_folder)
        self.folder_context_menu.add_command(label="Properties", command=self.show_folder_properties)
        self.folder_context_menu.add_separator()
        self.folder_context_menu.add_command(label="Remove", command=self.remove_selected_folder)
    
    def create_details_panel(self):
        """Create right details panel"""
        # Details notebook
        self.details_notebook = ttk.Notebook(self.right_panel)
        self.details_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Overview tab
        self.overview_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(self.overview_frame, text="Overview")
        self.create_overview_tab()
        
        # Files tab
        self.files_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(self.files_frame, text="Files")
        self.create_files_tab()
        
        # Access Control tab
        self.access_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(self.access_frame, text="Access Control")
        self.create_access_tab()
        
        # Segments tab
        self.segments_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(self.segments_frame, text="Segments")
        self.create_segments_tab()
        
        # Upload tab
        self.upload_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(self.upload_frame, text="Upload")
        self.create_upload_tab()
        
        # Logs tab
        self.logs_frame = ttk.Frame(self.details_notebook)
        self.details_notebook.add(self.logs_frame, text="Logs")
        self.create_logs_tab()
    
    def create_overview_tab(self):
        """Create overview tab content"""
        # Folder info section
        info_frame = ttk.LabelFrame(self.overview_frame, text="Folder Information", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.folder_info_vars = {
            'name': tk.StringVar(value="No folder selected"),
            'path': tk.StringVar(value=""),
            'total_files': tk.StringVar(value="0"),
            'total_size': tk.StringVar(value="0 MB"),
            'indexed_date': tk.StringVar(value="Never"),
            'last_published': tk.StringVar(value="Never")
        }
        
        # Info labels
        ttk.Label(info_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, textvariable=self.folder_info_vars['name']).grid(row=0, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(info_frame, text="Path:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, textvariable=self.folder_info_vars['path']).grid(row=1, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(info_frame, text="Files:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, textvariable=self.folder_info_vars['total_files']).grid(row=2, column=1, sticky=tk.W, padx=10)
        
        ttk.Label(info_frame, text="Size:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Label(info_frame, textvariable=self.folder_info_vars['total_size']).grid(row=3, column=1, sticky=tk.W, padx=10)
        
        # Activity section
        activity_frame = ttk.LabelFrame(self.overview_frame, text="Recent Activity", padding=10)
        activity_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.activity_text = tk.Text(activity_frame, height=10, wrap=tk.WORD, font=('Courier', 9))
        activity_scroll = ttk.Scrollbar(activity_frame, orient=tk.VERTICAL, command=self.activity_text.yview)
        self.activity_text.configure(yscrollcommand=activity_scroll.set)
        
        self.activity_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        activity_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_files_tab(self):
        """Create files browser tab"""
        # This will be handled by FileBrowserWidget
        self.file_browser = FileBrowserWidget(self.files_frame, self.backend)
        self.file_browser.pack(fill=tk.BOTH, expand=True)
    
    def create_access_tab(self):
        """Create access control tab"""
        # Share settings
        share_frame = ttk.LabelFrame(self.access_frame, text="Share Settings", padding=10)
        share_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Share type
        ttk.Label(share_frame, text="Share Type:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.share_type_var = tk.StringVar(value="private")
        share_type_combo = ttk.Combobox(share_frame, textvariable=self.share_type_var,
                                       values=["public", "private", "protected"], state="readonly")
        share_type_combo.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        # Password (for protected shares)
        ttk.Label(share_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.share_password_var = tk.StringVar()
        password_entry = ttk.Entry(share_frame, textvariable=self.share_password_var, show="*")
        password_entry.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        # Authorized users (for private shares)
        users_frame = ttk.LabelFrame(self.access_frame, text="Authorized Users", padding=10)
        users_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Users list
        self.users_listbox = tk.Listbox(users_frame, height=8)
        users_scroll = ttk.Scrollbar(users_frame, orient=tk.VERTICAL, command=self.users_listbox.yview)
        self.users_listbox.configure(yscrollcommand=users_scroll.set)
        
        self.users_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        users_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # User management buttons
        user_buttons_frame = ttk.Frame(self.access_frame)
        user_buttons_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(user_buttons_frame, text="Add User", command=self.add_authorized_user).pack(side=tk.LEFT, padx=2)
        ttk.Button(user_buttons_frame, text="Remove User", command=self.remove_authorized_user).pack(side=tk.LEFT, padx=2)
        
        # Action buttons
        action_buttons_frame = ttk.Frame(self.access_frame)
        action_buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(action_buttons_frame, text="Update Settings", 
                  command=self.update_access_settings, style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(action_buttons_frame, text="Publish Share", 
                  command=self.publish_share, style='Success.TButton').pack(side=tk.LEFT, padx=5)
    
    def create_segments_tab(self):
        """Create segments management tab"""
        # Segments tree
        segments_tree_frame = ttk.Frame(self.segments_frame)
        segments_tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.segments_tree = ttk.Treeview(segments_tree_frame, 
                                         columns=('file', 'index', 'size', 'status', 'message_id'),
                                         show='headings')
        
        # Segments columns
        self.segments_tree.heading('file', text='File')
        self.segments_tree.heading('index', text='Index')
        self.segments_tree.heading('size', text='Size')
        self.segments_tree.heading('status', text='Status')
        self.segments_tree.heading('message_id', text='Message ID')
        
        self.segments_tree.column('file', width=200)
        self.segments_tree.column('index', width=60)
        self.segments_tree.column('size', width=80)
        self.segments_tree.column('status', width=80)
        self.segments_tree.column('message_id', width=200)
        
        # Segments scrollbars
        segments_scrolly = ttk.Scrollbar(segments_tree_frame, orient=tk.VERTICAL, command=self.segments_tree.yview)
        segments_scrollx = ttk.Scrollbar(segments_tree_frame, orient=tk.HORIZONTAL, command=self.segments_tree.xview)
        self.segments_tree.configure(yscrollcommand=segments_scrolly.set, xscrollcommand=segments_scrollx.set)
        
        self.segments_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        segments_scrolly.pack(side=tk.RIGHT, fill=tk.Y)
        segments_scrollx.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Segments control
        segments_control_frame = ttk.Frame(self.segments_frame)
        segments_control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(segments_control_frame, text="Refresh Segments", 
                  command=self.refresh_segments).pack(side=tk.LEFT, padx=2)
        ttk.Button(segments_control_frame, text="Upload Failed", 
                  command=self.upload_failed_segments).pack(side=tk.LEFT, padx=2)
        ttk.Button(segments_control_frame, text="Verify All", 
                  command=self.verify_segments).pack(side=tk.LEFT, padx=2)
    
    def create_upload_tab(self):
        """Create upload management tab"""
        # Upload queue
        queue_frame = ttk.LabelFrame(self.upload_frame, text="Upload Queue", padding=10)
        queue_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.upload_tree = ttk.Treeview(queue_frame,
                                       columns=('file', 'progress', 'speed', 'eta', 'status'),
                                       show='headings')
        
        # Upload columns
        self.upload_tree.heading('file', text='File')
        self.upload_tree.heading('progress', text='Progress')
        self.upload_tree.heading('speed', text='Speed')
        self.upload_tree.heading('eta', text='ETA')
        self.upload_tree.heading('status', text='Status')
        
        upload_scrolly = ttk.Scrollbar(queue_frame, orient=tk.VERTICAL, command=self.upload_tree.yview)
        self.upload_tree.configure(yscrollcommand=upload_scrolly.set)
        
        self.upload_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        upload_scrolly.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Upload controls
        upload_controls_frame = ttk.Frame(self.upload_frame)
        upload_controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(upload_controls_frame, text="Start Upload", 
                  command=self.start_upload).pack(side=tk.LEFT, padx=2)
        ttk.Button(upload_controls_frame, text="Pause Upload", 
                  command=self.pause_upload).pack(side=tk.LEFT, padx=2)
        ttk.Button(upload_controls_frame, text="Cancel Upload", 
                  command=self.cancel_upload).pack(side=tk.LEFT, padx=2)
    
    def create_logs_tab(self):
        """Create logs viewer tab"""
        # Log viewer
        self.log_text = tk.Text(self.logs_frame, wrap=tk.WORD, font=('Courier', 9))
        log_scroll = ttk.Scrollbar(self.logs_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=10, padx=(0, 10))
        
        # Log controls
        log_controls_frame = ttk.Frame(self.logs_frame)
        log_controls_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        ttk.Button(log_controls_frame, text="Refresh Logs", 
                  command=self.refresh_logs).pack(side=tk.LEFT, padx=2)
        ttk.Button(log_controls_frame, text="Clear Logs", 
                  command=self.clear_logs).pack(side=tk.LEFT, padx=2)
        ttk.Button(log_controls_frame, text="Save Logs", 
                  command=self.save_logs).pack(side=tk.LEFT, padx=2)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_bar = StatusBar(self.root)
        self.status_bar.set_text("main", "Ready")
        self.status_bar.set_text("connection", "Not connected")
        self.status_bar.set_text("operations", "Idle")
        self.status_bar.set_text("time", datetime.now().strftime("%H:%M:%S"))
        
        # Start status updates
        self.update_status_time()
    
    def setup_bindings(self):
        """Setup keyboard bindings and events"""
        # Keyboard shortcuts
        self.root.bind("<Control-i>", lambda e: self.show_user_init())
        self.root.bind("<Control-o>", lambda e: self.index_folder())
        self.root.bind("<Control-d>", lambda e: self.download_share())
        self.root.bind("<Control-s>", lambda e: self.show_settings())
        self.root.bind("<F5>", lambda e: self.refresh_all())
        
        # Window events
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Focus events
        self.root.bind("<FocusIn>", self.on_focus_in)
    
    def init_backend_async(self):
        """Initialize backend in separate thread"""
        def init_worker():
            try:
                self.logger.info("Initializing backend...")
                
                # Load configuration
                config_path = Path("usenet_sync_config.json")
                if not config_path.exists():
                    raise FileNotFoundError("Configuration file not found: usenet_sync_config.json")
                
                # Initialize backend
                self.backend = UsenetSync(str(config_path))
                
                # Update GUI on main thread
                self.root.after(0, self.on_backend_initialized)
                
            except Exception as e:
                self.logger.error(f"Backend initialization failed: {e}")
                self.root.after(0, lambda: self.on_backend_error(str(e)))
        
        threading.Thread(target=init_worker, daemon=True).start()
    
    def on_backend_initialized(self):
        """Called when backend initialization completes"""
        self.logger.info("Backend initialized successfully")
        self.connection_status.config(text="Connected")
        self.status_bar.set_text("connection", "Connected")
        self.status_bar.set_text("main", "Backend ready")
        
        # Load initial data
        self.refresh_folders()
    
    def on_backend_error(self, error_message):
        """Called when backend initialization fails"""
        self.logger.error(f"Backend error: {error_message}")
        self.connection_status.config(text="Error")
        self.status_bar.set_text("connection", "Error")
        self.status_bar.set_text("main", f"Error: {error_message}")
        
        # Show error dialog
        messagebox.showerror("Backend Error", 
                           f"Failed to initialize backend:\n\n{error_message}\n\n"
                           "Please check your configuration and try again.")
    
    # Event handlers
    def on_folder_select(self, event):
        """Handle folder selection in tree"""
        selection = self.folder_tree.selection()
        if selection:
            folder_id = self.folder_tree.item(selection[0])['tags'][0] if self.folder_tree.item(selection[0])['tags'] else None
            if folder_id:
                self.current_folder = folder_id
                self.load_folder_details(folder_id)
    
    def show_folder_context_menu(self, event):
        """Show folder context menu"""
        item = self.folder_tree.identify_row(event.y)
        if item:
            self.folder_tree.selection_set(item)
            self.folder_context_menu.post(event.x_root, event.y_root)
    
    def on_focus_in(self, event):
        """Handle window focus"""
        if event.widget == self.root:
            self.refresh_connection_status()
    
    def on_closing(self):
        """Handle application closing"""
        if self.background_operations:
            result = messagebox.askyesno(
                "Background Operations", 
                "There are background operations running. Cancel them and exit?"
            )
            if not result:
                return
        
        self.shutdown_requested = True
        
        # Stop background operations
        for op_id, operation in self.background_operations.items():
            if hasattr(operation, 'cancel'):
                operation.cancel()
        
        # Shutdown backend
        if self.backend:
            try:
                self.backend.shutdown()
            except Exception as e:
                self.logger.error(f"Error shutting down backend: {e}")
        
        self.root.destroy()
    
    # Core operations
    def show_user_init(self):
        """Show user initialization dialog"""
        if not self.backend:
            messagebox.showerror("Error", "Backend not initialized")
            return
        
        dialog = UserInitDialog(self.root, self.backend)
        if dialog.result:
            self.status_bar.set_text("main", "User initialized successfully")
            self.refresh_folders()
    
    def index_folder(self):
        """Index a new folder"""
        if not self.backend:
            messagebox.showerror("Error", "Backend not initialized")
            return
        
        folder_path = filedialog.askdirectory(title="Select Folder to Index")
        if not folder_path:
            return
        
        # Get folder name
        folder_name = simpledialog.askstring("Folder Name", 
                                            f"Enter display name for folder:\n{folder_path}",
                                            initialvalue=Path(folder_path).name)
        if not folder_name:
            return
        
        # Index in background
        self.index_folder_async(folder_path, folder_name)
    
    def index_folder_async(self, folder_path, folder_name):
        """Index folder asynchronously"""
        progress = ProgressDialog(self.root, "Indexing Folder")
        progress.show()
        
        def index_worker():
            try:
                # Create folder
                folder_id = self.backend.create_folder(folder_path, folder_name, "private")
                
                # Update GUI
                self.root.after(0, lambda: self.on_folder_indexed(folder_id, folder_name))
                self.root.after(0, progress.close)
                
            except Exception as e:
                self.logger.error(f"Folder indexing failed: {e}")
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to index folder:\n{e}"))
                self.root.after(0, progress.close)
        
        threading.Thread(target=index_worker, daemon=True).start()
    
    def on_folder_indexed(self, folder_id, folder_name):
        """Called when folder indexing completes"""
        self.status_bar.set_text("main", f"Folder '{folder_name}' indexed successfully")
        self.refresh_folders()
    
    def download_share(self):
        """Download a shared folder"""
        if not self.backend:
            messagebox.showerror("Error", "Backend not initialized")
            return
        
        dialog = DownloadDialog(self.root, self.backend)
        if dialog.result:
            self.status_bar.set_text("main", "Download started")
    
    def publish_share(self):
        """Publish selected folder"""
        if not self.current_folder:
            messagebox.showwarning("Warning", "No folder selected")
            return
        
        try:
            access_string = self.backend.publish_folder(self.current_folder, "public")
            
            # Show access string dialog
            result_dialog = tk.Toplevel(self.root)
            result_dialog.title("Share Published")
            result_dialog.geometry("500x200")
            result_dialog.transient(self.root)
            result_dialog.grab_set()
            
            ttk.Label(result_dialog, text="Share published successfully!", style='Title.TLabel').pack(pady=10)
            ttk.Label(result_dialog, text="Access String:").pack()
            
            access_text = tk.Text(result_dialog, height=3, wrap=tk.WORD)
            access_text.pack(fill=tk.X, padx=20, pady=10)
            access_text.insert('1.0', access_string)
            access_text.config(state=tk.DISABLED)
            
            ttk.Button(result_dialog, text="Copy to Clipboard", 
                      command=lambda: self.copy_to_clipboard(access_string)).pack(side=tk.LEFT, padx=10)
            ttk.Button(result_dialog, text="Close", 
                      command=result_dialog.destroy).pack(side=tk.RIGHT, padx=10)
            
            self.status_bar.set_text("main", "Folder published successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to publish folder:\n{e}")
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.status_bar.set_text("main", "Copied to clipboard")
    
    def refresh_all(self):
        """Refresh all data"""
        self.refresh_folders()
        self.refresh_connection_status()
        if self.current_folder:
            self.load_folder_details(self.current_folder)
        self.status_bar.set_text("main", "Refreshed")
    
    def refresh_folders(self):
        """Refresh folder tree"""
        if not self.backend:
            return
        
        # Clear existing items
        for item in self.folder_tree.get_children():
            self.folder_tree.delete(item)
        
        try:
            folders = self.backend.list_folders()
            for folder in folders:
                status = "✓" if folder.get('total_files', 0) > 0 else "⚠"
                files_count = f"{folder.get('total_files', 0):,}"
                size_mb = round(folder.get('total_size', 0) / (1024 * 1024), 1)
                size_str = f"{size_mb:,.1f} MB"
                
                self.folder_tree.insert('', 'end', 
                                       text=folder['display_name'],
                                       values=(status, files_count, size_str),
                                       tags=(str(folder['id']),))
        except Exception as e:
            self.logger.error(f"Failed to refresh folders: {e}")
    
    def load_folder_details(self, folder_id):
        """Load details for selected folder"""
        if not self.backend:
            return
        
        try:
            # Get folder info
            folder = self.backend.database.get_folder(folder_id)
            if not folder:
                return
            
            # Update overview
            self.folder_info_vars['name'].set(folder['display_name'])
            self.folder_info_vars['path'].set(folder['folder_path'])
            self.folder_info_vars['total_files'].set(f"{folder.get('total_files', 0):,}")
            
            size_mb = round(folder.get('total_size', 0) / (1024 * 1024), 1)
            self.folder_info_vars['total_size'].set(f"{size_mb:,.1f} MB")
            
            self.folder_info_vars['indexed_date'].set(folder.get('last_indexed', 'Never'))
            self.folder_info_vars['last_published'].set(folder.get('last_published', 'Never'))
            
            # Load file browser
            if hasattr(self, 'file_browser'):
                self.file_browser.load_folder(folder_id)
            
            # Load segments
            self.refresh_segments()
            
        except Exception as e:
            self.logger.error(f"Failed to load folder details: {e}")
    
    def refresh_segments(self):
        """Refresh segments display"""
        if not self.current_folder:
            return
        
        # Clear segments tree
        for item in self.segments_tree.get_children():
            self.segments_tree.delete(item)
        
        try:
            # Get folder files
            files = self.backend.database.get_folder_files(self.current_folder)
            
            for file_info in files:
                segments = self.backend.database.get_file_segments(file_info['id'])
                
                for segment in segments:
                    status_icon = "✓" if segment['state'] == 'uploaded' else "⚠" if segment['state'] == 'failed' else "○"
                    size_kb = round(segment['segment_size'] / 1024, 1)
                    
                    self.segments_tree.insert('', 'end', values=(
                        file_info['file_path'],
                        segment['segment_index'],
                        f"{size_kb} KB",
                        f"{status_icon} {segment['state']}",
                        segment.get('message_id', 'Not uploaded')
                    ))
        except Exception as e:
            self.logger.error(f"Failed to refresh segments: {e}")
    
    def refresh_connection_status(self):
        """Refresh connection status"""
        if not self.backend:
            return
        
        try:
            if self.backend.nntp.test_connectivity():
                self.connection_status.config(text="Connected")
                self.status_bar.set_text("connection", "Connected")
            else:
                self.connection_status.config(text="Disconnected")
                self.status_bar.set_text("connection", "Disconnected")
        except Exception as e:
            self.connection_status.config(text="Error")
            self.status_bar.set_text("connection", "Error")
    
    def update_status_time(self):
        """Update status bar time"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.status_bar.set_text("time", current_time)
        
        # Schedule next update
        if not self.shutdown_requested:
            self.root.after(1000, self.update_status_time)
    
    # Settings and dialogs
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.root, self.backend)
        if dialog.result:
            # Reload configuration
            self.refresh_connection_status()
    
    def show_system_status(self):
        """Show system status dialog"""
        if not self.backend:
            messagebox.showerror("Error", "Backend not initialized")
            return
        
        try:
            status = self.backend.get_system_status()
            
            status_dialog = tk.Toplevel(self.root)
            status_dialog.title("System Status")
            status_dialog.geometry("600x500")
            status_dialog.transient(self.root)
            status_dialog.grab_set()
            
            # Status text
            status_text = tk.Text(status_dialog, wrap=tk.WORD, font=('Courier', 9))
            status_scroll = ttk.Scrollbar(status_dialog, orient=tk.VERTICAL, command=status_text.yview)
            status_text.configure(yscrollcommand=status_scroll.set)
            
            # Format status
            import json
            formatted_status = json.dumps(status, indent=2)
            status_text.insert('1.0', formatted_status)
            status_text.config(state=tk.DISABLED)
            
            status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            status_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
            
            ttk.Button(status_dialog, text="Close", command=status_dialog.destroy).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get system status:\n{e}")
    
    def test_connection(self):
        """Test NNTP connection"""
        if not self.backend:
            messagebox.showerror("Error", "Backend not initialized")
            return
        
        progress = ProgressDialog(self.root, "Testing Connection")
        progress.show()
        
        def test_worker():
            try:
                result = self.backend.nntp.test_connectivity()
                self.root.after(0, lambda: self.on_connection_tested(result))
                self.root.after(0, progress.close)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Connection test failed:\n{e}"))
                self.root.after(0, progress.close)
        
        threading.Thread(target=test_worker, daemon=True).start()
    
    def on_connection_tested(self, result):
        """Handle connection test result"""
        if result:
            messagebox.showinfo("Connection Test", "Connection successful!")
            self.refresh_connection_status()
        else:
            messagebox.showerror("Connection Test", "Connection failed!")
    
    def show_about(self):
        """Show about dialog"""
        about_dialog = tk.Toplevel(self.root)
        about_dialog.title("About UsenetSync")
        about_dialog.geometry("400x300")
        about_dialog.transient(self.root)
        about_dialog.grab_set()
        
        # Center dialog
        about_dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 100,
            self.root.winfo_rooty() + 100
        ))
        
        about_text = """
UsenetSync v2.0

Secure Usenet File Synchronization System

Features:
- End-to-end encryption
- Million+ file support
- Multi-server redundancy
- Production-grade reliability

© 2024 UsenetSync Project
        """
        
        ttk.Label(about_dialog, text=about_text, justify=tk.CENTER).pack(expand=True)
        ttk.Button(about_dialog, text="Close", command=about_dialog.destroy).pack(pady=10)
    
    def run(self):
        """Start the application"""
        self.logger.info("Starting GUI application")
        self.root.mainloop()

if __name__ == "__main__":
    app = MainApplication()
    app.run()