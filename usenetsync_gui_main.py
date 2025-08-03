#!/usr/bin/env python3
"""
UsenetSync GUI - Main Application Window - CLEAN VERSION
Production-ready GUI for UsenetSync with full integration to backend systems
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
from usenetsync_gui_folder import FolderDetailsPanel
from usenetsync_gui_download import DownloadDialog

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MainApplication:
    """Main GUI application for UsenetSync"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("UsenetSync v1.0 - Secure Usenet File Synchronization")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Application state
        self.app_backend = None
        self.current_folder = None
        self.status_timer = None
        self.background_operations = {}
        
        # Threading
        self.main_thread_id = threading.get_ident()
        
        # Initialize backend in thread
        self.init_thread = threading.Thread(target=self._init_backend, daemon=True)
        self.init_thread.start()
        
        # Setup GUI
        self._setup_styles()
        self._create_menu()
        self._create_toolbar()
        self._create_main_layout()
        self._create_status_bar()
        
        # Bind events
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.bind("<Control-i>", lambda e: self._show_user_init())
        self.root.bind("<Control-f>", lambda e: self._index_folder())
        self.root.bind("<Control-p>", lambda e: self._publish_share())
        self.root.bind("<Control-d>", lambda e: self._download_share())
        self.root.bind("<F5>", lambda e: self._refresh_all())
        
        # Start status updates
        self._start_status_updates()
        
    def _setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Status.TLabel', font=('Arial', 9))
        style.configure('Success.TLabel', foreground='green')
        style.configure('Error.TLabel', foreground='red')
        style.configure('Warning.TLabel', foreground='orange')
    
    def _create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Initialize User...", command=self._show_user_init, accelerator="Ctrl+I")
        file_menu.add_separator()
        file_menu.add_command(label="Index Folder...", command=self._index_folder, accelerator="Ctrl+F")
        file_menu.add_command(label="Publish Share...", command=self._publish_share, accelerator="Ctrl+P")
        file_menu.add_command(label="Download Share...", command=self._download_share, accelerator="Ctrl+D")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Refresh All", command=self._refresh_all, accelerator="F5")
        edit_menu.add_command(label="Settings...", command=self._show_settings)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="System Status", command=self._show_system_status)
        tools_menu.add_command(label="Connection Test", command=self._test_connection)
        tools_menu.add_command(label="Cleanup", command=self._cleanup)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Quick Reference", command=self._show_help)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _create_toolbar(self):
        """Create main toolbar"""
        self.toolbar = ttk.Frame(self.root)
        self.toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        
        # User initialization
        ttk.Button(self.toolbar, text="Initialize User", 
                  command=self._show_user_init).pack(side=tk.LEFT, padx=2)
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Folder operations
        ttk.Button(self.toolbar, text="Index Folder", 
                  command=self._index_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.toolbar, text="Publish Share", 
                  command=self._publish_share).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.toolbar, text="Download", 
                  command=self._download_share).pack(side=tk.LEFT, padx=2)
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Refresh
        ttk.Button(self.toolbar, text="Refresh", 
                  command=self._refresh_all).pack(side=tk.LEFT, padx=2)
        
        # Status indicator
        self.connection_status = ttk.Label(self.toolbar, text="Initializing...", 
                                         style='Status.TLabel')
        self.connection_status.pack(side=tk.RIGHT, padx=5)
    
    def _create_main_layout(self):
        """Create main application layout"""
        # Main paned window
        self.main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Navigation tree
        self.left_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.left_frame, weight=1)
        
        # Right panel - Details
        self.right_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.right_frame, weight=3)
        
        self._create_navigation_tree()
        self._create_details_panel()
    
    def _create_navigation_tree(self):
        """Create navigation tree in left panel"""
        # Tree header
        tree_header = ttk.Label(self.left_frame, text="Folders", style='Title.TLabel')
        tree_header.pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        # Tree with scrollbar
        tree_frame = ttk.Frame(self.left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview
        self.folder_tree = ttk.Treeview(tree_frame, selectmode='browse')
        self.folder_tree.heading('#0', text='Indexed Folders', anchor=tk.W)
        
        # Scrollbars
        tree_scroll_v = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.folder_tree.yview)
        tree_scroll_h = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.folder_tree.xview)
        self.folder_tree.configure(yscrollcommand=tree_scroll_v.set, xscrollcommand=tree_scroll_h.set)
        
        # Pack tree and scrollbars
        self.folder_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll_v.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_h.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind selection event
        self.folder_tree.bind('<<TreeviewSelect>>', self._on_folder_select)
        
        # Context menu
        self.tree_context_menu = tk.Menu(self.root, tearoff=0)
        self.tree_context_menu.add_command(label="Refresh", command=self._refresh_selected_folder)
        self.tree_context_menu.add_command(label="Re-index", command=self._reindex_selected_folder)
        self.tree_context_menu.add_separator()
        self.tree_context_menu.add_command(label="Publish Share", command=self._publish_share)
        self.tree_context_menu.add_command(label="Remove", command=self._remove_selected_folder)
        self.folder_tree.bind("<Button-3>", self._show_tree_context_menu)
    
    def _create_details_panel(self):
        """Create details panel in right side"""
        # Details header
        self.details_header = ttk.Label(self.right_frame, text="Select a folder to view details", 
                                       style='Title.TLabel')
        self.details_header.pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        # Details content frame
        self.details_content = ttk.Frame(self.right_frame)
        self.details_content.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initially show welcome message
        self.welcome_label = ttk.Label(self.details_content, 
                                     text="Welcome to UsenetSync!\\n\\nTo get started:\\n1. Initialize your user profile\\n2. Index a folder\\n3. Publish or download shares",
                                     justify=tk.CENTER, font=('Arial', 11))
        self.welcome_label.pack(expand=True)
    
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
        
        # Operation status
        self.operation_status = ttk.Label(self.status_frame, text="", style='Status.TLabel')
        self.operation_status.pack(side=tk.RIGHT, padx=5)
    
    def _init_backend(self):
        """Initialize UsenetSync backend in background thread"""
        try:
            self.app_backend = UsenetSync()
            self._thread_safe_status_update("Backend initialized successfully", "success")
            
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
            # Check if user is initialized
            if self.app_backend.user.is_initialized():
                user_id = self.app_backend.user.get_user_id()
                self._thread_safe_status_update(f"User: {user_id[:16]}...", "success")
            else:
                self._thread_safe_status_update("User not initialized", "warning")
            
            # Load folders
            self._refresh_folder_tree()
            
        except Exception as error:
            logger.error(f"Failed to load initial data: {error}")
            self._thread_safe_status_update(f"Data load failed: {error}", "error")
    
    def _refresh_folder_tree(self):
        """Refresh the folder tree using production database"""
        if not self.app_backend:
            return
        
        try:
            # Clear existing items
            for item in self.folder_tree.get_children():
                self.folder_tree.delete(item)
            
            # Get indexed folders from production database
            with self.app_backend.db.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT folder_unique_id, display_name, folder_path, share_type, 
                           current_version, state, file_count, total_size
                    FROM folders
                    ORDER BY display_name, folder_path
                """)
                
                folders = []
                for row in cursor.fetchall():
                    folder_id, display_name, folder_path, share_type, version, state, file_count, total_size = row
                    folders.append({
                        'folder_unique_id': folder_id,
                        'display_name': display_name or os.path.basename(folder_path),
                        'folder_path': folder_path,
                        'share_type': share_type or 'public',
                        'current_version': version or 1,
                        'state': state or 'unknown',
                        'file_count': file_count or 0,
                        'total_size': total_size or 0
                    })
            
            for folder in folders:
                folder_id = folder['folder_unique_id']
                display_name = folder['display_name']
                
                # Create tree item
                item_text = f"{display_name} [{folder['share_type'].upper()}]"
                status_icon = "✓" if folder['state'] == 'ready' else "⚠"
                tree_item = self.folder_tree.insert('', tk.END, 
                                                   text=f"{status_icon} {item_text}",
                                                   values=(folder_id,))
            
            logger.info(f"Loaded {len(folders)} folders into tree")
            
        except Exception as error:
            logger.error(f"Failed to refresh folder tree: {error}")
            # Insert error indicator
            self.folder_tree.insert('', tk.END, text="✗ Error loading folders", values=("",))
    
    def _on_folder_select(self, event):
        """Handle folder selection in tree"""
        selection = self.folder_tree.selection()
        if not selection:
            return
        
        try:
            item = selection[0]
            values = self.folder_tree.item(item, 'values')
            if values:
                folder_id = values[0]
                self._show_folder_details(folder_id)
        except Exception as error:
            logger.error(f"Error selecting folder: {error}")
    
    def _show_folder_details(self, folder_id):
        """Show detailed folder view"""
        if not self.app_backend or not folder_id:
            return
        
        try:
            # Clear existing details
            for widget in self.details_content.winfo_children():
                widget.destroy()
            
            # Create folder details panel
            self.folder_details = FolderDetailsPanel(self.details_content, self.app_backend, folder_id)
            self.folder_details.pack(fill=tk.BOTH, expand=True)
            
            # Update header
            with self.app_backend.db.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT display_name, folder_path FROM folders WHERE folder_unique_id = ?
                """, (folder_id,))
                row = cursor.fetchone()
                
                if row:
                    display_name, folder_path = row
                    self.details_header.config(text=f"Folder: {display_name or os.path.basename(folder_path)}")
                else:
                    self.details_header.config(text="Folder: Unknown")
            
            self.current_folder = folder_id
            
        except Exception as error:
            logger.error(f"Error showing folder details: {error}")
            messagebox.showerror("Error", f"Failed to load folder details: {error}")
    
    def _show_user_init(self):
        """Show user initialization dialog"""
        try:
            dialog = UserInitDialog(self.root, self.app_backend)
            self.root.wait_window(dialog.dialog)
            
            # Refresh status after dialog
            self._load_initial_data()
            
        except Exception as error:
            logger.error(f"Error showing user init dialog: {error}")
            messagebox.showerror("Error", f"Failed to show user dialog: {error}")
    
    def _index_folder(self):
        """Index a new folder"""
        if not self.app_backend:
            messagebox.showerror("Error", "Backend not initialized")
            return
        
        if not self.app_backend.user.is_initialized():
            messagebox.showwarning("Warning", "Please initialize user first")
            self._show_user_init()
            return
        
        # Check if indexing is already in progress
        if _is_indexing_in_progress():
            messagebox.showwarning("Warning", "Indexing operation already in progress")
            return
        
        # Select folder
        folder_path = filedialog.askdirectory(title="Select folder to index")
        if not folder_path:
            return
        
        # Show progress
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
        self.progress_var.set(0)
        
        def index_worker():
            try:
                _set_indexing_progress(True)
                
                def progress_callback(progress_data):
                    """Enhanced progress callback that handles dict or simple current/total"""
                    try:
                        if isinstance(progress_data, dict):
                            current = progress_data.get('current', 0)
                            total = progress_data.get('total', 1)
                            file_name = progress_data.get('file', '')
                            phase = progress_data.get('phase', 'indexing')
                        else:
                            # Handle legacy tuple format (current, total)
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
                            
                            # Update status with file info if available
                            if file_name and file_name != 'Starting indexing...':
                                display_name = os.path.basename(file_name)
                                status_msg = f"{phase.capitalize()}: {current}/{total} - {display_name}"
                            else:
                                status_msg = f"{phase.capitalize()}: {current}/{total} files"
                            
                            self._thread_safe_status_update(status_msg)
                            
                            # Also log for debugging
                            logger.info(f"PROGRESS: {status_msg}")
                            
                    except Exception as e:
                        logger.error(f"Error in progress callback: {e}")
                
                # Call the backend index_folder method
                result = self.app_backend.index_folder(folder_path, progress_callback=progress_callback)
                
                self._thread_safe_call(lambda: self.progress_bar.pack_forget())
                
                # Enhanced result reporting
                if result:
                    files_processed = result.get('files_processed', result.get('files_indexed', 0))
                    segments_created = result.get('segments_created', 0)
                    elapsed_time = result.get('elapsed_time', 0)
                    
                    if files_processed > 0:
                        status_msg = f"Indexing complete: {files_processed} files"
                        if segments_created > 0:
                            status_msg += f", {segments_created} segments"
                        if elapsed_time > 0:
                            status_msg += f" ({elapsed_time:.1f}s)"
                        self._thread_safe_status_update(status_msg, "success")
                    else:
                        self._thread_safe_status_update("Indexing completed (no files processed)", "warning")
                else:
                    self._thread_safe_status_update("Indexing completed", "success")
                
                self._thread_safe_call(self._refresh_folder_tree)
                
            except Exception as error:
                logger.error(f"Indexing failed: {error}")
                self._thread_safe_call(lambda: self.progress_bar.pack_forget())
                self._thread_safe_status_update(f"Indexing failed: {error}", "error")
                self._thread_safe_call(lambda: messagebox.showerror("Indexing Failed", str(error)))
            finally:
                _set_indexing_progress(False)
        
        threading.Thread(target=index_worker, daemon=True).start()
    
    def _publish_share(self):
        """Publish current folder as share - FIXED VERSION"""
        if not self.current_folder:
            messagebox.showwarning("Warning", "Please select a folder first")
            return
        
        try:
            # Simple publish dialog
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
                        access_string = self.app_backend.publish_folder(
                            self.current_folder, 
                            share_type='public'
                        )
                        self._thread_safe_status_update("Public share created successfully", "success")
                    else:
                        # Private share - get authorized users
                        users_input = simpledialog.askstring("Authorized Users", 
                                                            "Enter authorized user emails (comma-separated):")
                        if not users_input:
                            self._thread_safe_status_update("Private share cancelled", "error")
                            return
                        
                        authorized_users = [u.strip() for u in users_input.split(',')]
                        self._thread_safe_status_update("Creating private share...")
                        access_string = self.app_backend.publish_folder(
                            self.current_folder,
                            share_type='private',
                            authorized_users=authorized_users
                        )
                        self._thread_safe_status_update("Private share created successfully", "success")
                    
                    # Show access string
                    self._thread_safe_call(lambda: messagebox.showinfo("Share Created", 
                                                                      f"Access string:\\n{access_string}"))
                    
                    # Refresh the folder tree to show updated status
                    self._thread_safe_call(self._refresh_folder_tree)
                    
                except Exception as publish_error:
                    logger.error(f"Publishing failed: {publish_error}")
                    self._thread_safe_status_update(f"Publishing failed: {publish_error}", "error")
                    self._thread_safe_call(lambda: messagebox.showerror("Publishing Failed", str(publish_error)))
            
            threading.Thread(target=publish_worker, daemon=True).start()
            
        except Exception as error:
            logger.error(f"Error in publish share: {error}")
            messagebox.showerror("Error", f"Failed to start publishing: {error}")
    
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
        self._thread_safe_status_update("Refreshing...")
        
        def refresh_worker():
            try:
                self._thread_safe_call(self._refresh_folder_tree)
                if self.current_folder:
                    self._thread_safe_call(lambda: self._show_folder_details(self.current_folder))
                self._thread_safe_status_update("Refresh complete", "success")
            except Exception as error:
                logger.error(f"Refresh failed: {error}")
                self._thread_safe_status_update(f"Refresh failed: {error}", "error")
        
        threading.Thread(target=refresh_worker, daemon=True).start()
    
    def _start_status_updates(self):
        """Start periodic status updates"""
        def update_status():
            try:
                if self.app_backend and hasattr(self.app_backend, 'nntp'):
                    # Update connection status
                    self.connection_status.config(text="Connected", style='Success.TLabel')
                else:
                    self.connection_status.config(text="Disconnected", style='Error.TLabel')
            except Exception as error:
                self.connection_status.config(text="Error", style='Error.TLabel')
            
            # Schedule next update
            self.status_timer = self.root.after(5000, update_status)
        
        update_status()
    
    def _show_tree_context_menu(self, event):
        """Show context menu for tree"""
        try:
            self.tree_context_menu.post(event.x_root, event.y_root)
        except Exception as error:
            pass
    
    def _refresh_selected_folder(self):
        """Refresh selected folder"""
        if self.current_folder:
            self._show_folder_details(self.current_folder)
    
    def _reindex_selected_folder(self):
        """Re-index selected folder using production indexing system"""
        if not self.current_folder:
            messagebox.showwarning("Warning", "No folder selected")
            return
        
        try:
            # Get folder path from database
            with self.app_backend.db.pool.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT folder_path FROM folders WHERE folder_unique_id = ?
                """, (self.current_folder,))
                row = cursor.fetchone()
                
                if not row:
                    messagebox.showerror("Error", "Folder not found in database")
                    return
                    
                folder_path = row[0]
            
            if messagebox.askyesno("Confirm Re-index", f"Re-index folder:\\n{folder_path}\\n\\nThis will scan for new and changed files."):
                # Show progress
                self.progress_bar.pack(side=tk.RIGHT, padx=5)
                self.progress_var.set(0)
                
                def reindex_worker():
                    try:
                        def progress_callback(progress_data):
                            try:
                                if isinstance(progress_data, dict):
                                    current = progress_data.get('current', 0)
                                    total = progress_data.get('total', 1)
                                else:
                                    current, total = progress_data[0], progress_data[1]
                                
                                if total > 0:
                                    progress = (current / total) * 100
                                    self._thread_safe_call(lambda: self.progress_var.set(progress))
                                    self._thread_safe_status_update(f"Re-indexing: {current}/{total} files")
                            except Exception as e:
                                logger.error(f"Error in reindex progress callback: {e}")
                        
                        # Re-index using production system
                        result = self.app_backend.index_folder(
                            folder_path, 
                            folder_id=self.current_folder,
                            reindex=True,
                            progress_callback=progress_callback
                        )
                        
                        self._thread_safe_call(lambda: self.progress_bar.pack_forget())
                        files_updated = result.get('files_updated', 0) if result else 0
                        self._thread_safe_status_update(f"Re-indexing complete: {files_updated} files updated", "success")
                        self._thread_safe_call(self._refresh_folder_tree)
                        
                    except Exception as reindex_error:
                        logger.error(f"Re-indexing failed: {reindex_error}")
                        self._thread_safe_call(lambda: self.progress_bar.pack_forget())
                        self._thread_safe_status_update(f"Re-indexing failed: {reindex_error}", "error")
                        self._thread_safe_call(lambda: messagebox.showerror("Re-indexing Failed", str(reindex_error)))
                        
                threading.Thread(target=reindex_worker, daemon=True).start()
                
        except Exception as error:
            logger.error(f"Error in re-index: {error}")
            messagebox.showerror("Error", f"Failed to re-index: {error}")
    
    def _remove_selected_folder(self):
        """Remove selected folder using production database"""
        if not self.current_folder:
            messagebox.showwarning("Warning", "No folder selected")
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
                # Remove from database
                with self.app_backend.db.pool.get_connection() as conn:
                    # Get folder ID first
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
                
                self.current_folder = None
                self.details_header.config(text="Select a folder")
                self._refresh_folder_tree()
                self._thread_safe_status_update(f"Removed folder '{name}'", "success")
                
        except Exception as error:
            logger.error(f"Error removing folder: {error}")
            messagebox.showerror("Error", f"Failed to remove folder: {error}")
    
    def _show_settings(self):
        """Show settings dialog"""
        messagebox.showinfo("Settings", "Settings dialog not implemented yet")
    
    def _show_system_status(self):
        """Show system status dialog"""
        messagebox.showinfo("System Status", "System status dialog not implemented yet")
    
    def _test_connection(self):
        """Test NNTP connection"""
        messagebox.showinfo("Connection Test", "Connection test not implemented yet")
    
    def _cleanup(self):
        """Cleanup temporary files"""
        messagebox.showinfo("Cleanup", "Cleanup operation not implemented yet")
    
    def _show_help(self):
        """Show help dialog"""
        help_text = """UsenetSync Quick Reference:

Keyboard Shortcuts:
- Ctrl+I: Initialize User
- Ctrl+F: Index Folder  
- Ctrl+P: Publish Share
- Ctrl+D: Download Share
- F5: Refresh All

Basic Workflow:
1. Initialize your user profile (one-time setup)
2. Index folders you want to share
3. Publish shares (public/private)
4. Download shared content from access strings

Security:
- Each folder has unique encryption keys
- Private shares require user authorization
- All data is encrypted before upload"""

        messagebox.showinfo("Quick Reference", help_text)
    
    def _show_about(self):
        """Show about dialog"""
        about_text = """UsenetSync v1.0
Secure Usenet File Synchronization

A production-grade system for sharing files
securely via Usenet with end-to-end encryption.

Features:
- End-to-end encryption
- Million-file scalability  
- Intelligent segmentation
- Access control
- Resume support

Copyright 2025 - UsenetSync Team"""

        messagebox.showinfo("About UsenetSync", about_text)
    
    def _on_closing(self):
        """Handle application closing"""
        try:
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
