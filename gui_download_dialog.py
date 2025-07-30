#!/usr/bin/env python3
"""
UsenetSync GUI - Download Dialog
Advanced download interface with selective file downloading and progress tracking
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import logging
import os
from typing import Optional, Dict, List, Any
from pathlib import Path
import time

logger = logging.getLogger(__name__)

class DownloadDialog:
    """Dialog for downloading shares with selective file picking"""
    
    def __init__(self, parent, app_backend):
        self.parent = parent
        self.app_backend = app_backend
        self.share_info = None
        self.download_in_progress = False
        self.download_thread = None
        
        # Create modal dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Download Share")
        self.dialog.geometry("900x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(True, True)
        
        # Center dialog
        self._center_dialog()
        
        # Create UI
        self._create_widgets()
        
        # Focus on dialog
        self.dialog.focus_set()
        
        # Bind events
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_closing)
        
    def _center_dialog(self):
        """Center dialog on parent window"""
        self.dialog.update_idletasks()
        x = self.parent.winfo_rootx() + (self.parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = self.parent.winfo_rooty() + (self.parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main container
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text="Download Shared Content", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Access string input section
        self._create_access_input_section(main_frame)
        
        # Share information section (initially hidden)
        self._create_share_info_section(main_frame)
        
        # File selection section (initially hidden)
        self._create_file_selection_section(main_frame)
        
        # Download options section (initially hidden)
        self._create_download_options_section(main_frame)
        
        # Progress section (initially hidden)
        self._create_progress_section(main_frame)
        
        # Button section
        self._create_button_section(main_frame)
        
    def _create_access_input_section(self, parent):
        """Create access string input section"""
        self.access_frame = ttk.LabelFrame(parent, text="Share Access String", padding=15)
        self.access_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Instructions
        instructions = """Paste the share access string you received below. This string contains all the information needed to download the shared content."""
        ttk.Label(self.access_frame, text=instructions, wraplength=850, 
                 justify=tk.LEFT, font=('Arial', 9)).pack(pady=(0, 10))
        
        # Access string input
        self.access_var = tk.StringVar()
        self.access_entry = tk.Text(self.access_frame, height=4, wrap=tk.WORD, font=('Courier', 9))
        self.access_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Verify button
        verify_frame = ttk.Frame(self.access_frame)
        verify_frame.pack(fill=tk.X)
        
        self.verify_button = ttk.Button(verify_frame, text="Verify Share", 
                                       command=self._verify_share, style='Accent.TButton')
        self.verify_button.pack(side=tk.LEFT)
        
        ttk.Button(verify_frame, text="Paste from Clipboard", 
                  command=self._paste_from_clipboard).pack(side=tk.LEFT, padx=(10, 0))
        
        # Status label
        self.verify_status = ttk.Label(verify_frame, text="", font=('Arial', 9))
        self.verify_status.pack(side=tk.RIGHT)
        
    def _create_share_info_section(self, parent):
        """Create share information display section"""
        self.info_frame = ttk.LabelFrame(parent, text="Share Information", padding=15)
        
        # Share details will be populated after verification
        self.info_content_frame = ttk.Frame(self.info_frame)
        self.info_content_frame.pack(fill=tk.BOTH, expand=True)
        
    def _create_file_selection_section(self, parent):
        """Create file selection section with tree view"""
        self.selection_frame = ttk.LabelFrame(parent, text="Select Files to Download", padding=15)
        
        # File tree header
        tree_header_frame = ttk.Frame(self.selection_frame)
        tree_header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(tree_header_frame, text="Select files and folders to download:", 
                 font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        
        # Selection buttons
        selection_buttons = ttk.Frame(tree_header_frame)
        selection_buttons.pack(side=tk.RIGHT)
        
        ttk.Button(selection_buttons, text="Select All", 
                  command=self._select_all_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(selection_buttons, text="Select None", 
                  command=self._select_no_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(selection_buttons, text="Expand All", 
                  command=self._expand_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(selection_buttons, text="Collapse All", 
                  command=self._collapse_all).pack(side=tk.LEFT, padx=2)
        
        # File tree
        tree_frame = ttk.Frame(self.selection_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create treeview with checkboxes
        self.file_tree = CheckboxTreeview(tree_frame)
        
        # Selection statistics
        self.selection_stats_frame = ttk.Frame(self.selection_frame)
        self.selection_stats_frame.pack(fill=tk.X)
        
        self.selection_stats_label = ttk.Label(self.selection_stats_frame, 
                                              text="No files selected", font=('Arial', 9))
        self.selection_stats_label.pack(side=tk.LEFT)
        
    def _create_download_options_section(self, parent):
        """Create download options section"""
        self.options_frame = ttk.LabelFrame(parent, text="Download Options", padding=15)
        
        options_grid = ttk.Frame(self.options_frame)
        options_grid.pack(fill=tk.X)
        
        # Download path
        ttk.Label(options_grid, text="Download Path:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        path_frame = ttk.Frame(options_grid)
        path_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        options_grid.columnconfigure(1, weight=1)
        
        self.download_path_var = tk.StringVar(value=self.app_backend.user.get_download_path() if self.app_backend else "./downloads")
        path_entry = ttk.Entry(path_frame, textvariable=self.download_path_var)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(path_frame, text="Browse", 
                  command=self._browse_download_path).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Options checkboxes
        self.preserve_structure_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_grid, text="Preserve folder structure", 
                       variable=self.preserve_structure_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        self.skip_existing_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_grid, text="Skip existing files (resume downloads)", 
                       variable=self.skip_existing_var).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        self.verify_integrity_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_grid, text="Verify file integrity after download", 
                       variable=self.verify_integrity_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        self.create_log_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_grid, text="Create download log", 
                       variable=self.create_log_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)
        
    def _create_progress_section(self, parent):
        """Create download progress section"""
        self.progress_frame = ttk.LabelFrame(parent, text="Download Progress", padding=15)
        
        # Overall progress
        ttk.Label(self.progress_frame, text="Overall Progress:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        self.overall_progress_var = tk.DoubleVar()
        self.overall_progress = ttk.Progressbar(self.progress_frame, variable=self.overall_progress_var, 
                                               length=400, mode='determinate')
        self.overall_progress.pack(fill=tk.X, pady=(5, 10))
        
        # Progress stats
        stats_frame = ttk.Frame(self.progress_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_label = ttk.Label(stats_frame, text="", font=('Arial', 9))
        self.progress_label.pack(side=tk.LEFT)
        
        self.speed_label = ttk.Label(stats_frame, text="", font=('Arial', 9))
        self.speed_label.pack(side=tk.RIGHT)
        
        # Current file progress
        ttk.Label(self.progress_frame, text="Current File:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        self.current_file_label = ttk.Label(self.progress_frame, text="", font=('Arial', 9))
        self.current_file_label.pack(anchor=tk.W, pady=(5, 5))
        
        self.file_progress_var = tk.DoubleVar()
        self.file_progress = ttk.Progressbar(self.progress_frame, variable=self.file_progress_var, 
                                            length=400, mode='determinate')
        self.file_progress.pack(fill=tk.X, pady=(0, 10))
        
        # Download log
        log_frame = ttk.Frame(self.progress_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(log_frame, text="Download Log:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD, font=('Courier', 8))
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
    def _create_button_section(self, parent):
        """Create dialog buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(side=tk.BOTTOM, pady=(20, 0))
        
        # Download button (initially disabled)
        self.download_button = ttk.Button(button_frame, text="Start Download", 
                                         command=self._start_download, 
                                         style='Accent.TButton', state='disabled')
        self.download_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Cancel/Close button
        self.cancel_button = ttk.Button(button_frame, text="Cancel", command=self._on_closing)
        self.cancel_button.pack(side=tk.LEFT)
        
        # Pause/Resume button (initially hidden)
        self.pause_button = ttk.Button(button_frame, text="Pause", command=self._pause_download)
        
    def _paste_from_clipboard(self):
        """Paste access string from clipboard"""
        try:
            clipboard_content = self.dialog.clipboard_get()
            self.access_entry.delete(1.0, tk.END)
            self.access_entry.insert(1.0, clipboard_content)
        except tk.TclError:
            messagebox.showwarning("Warning", "No text in clipboard")
            
    def _verify_share(self):
        """Verify the share access string using production system"""
        access_string = self.access_entry.get(1.0, tk.END).strip()
        
        if not access_string:
            messagebox.showwarning("Warning", "Please enter an access string")
            return
            
        # Disable verify button and show progress
        self.verify_button.config(state='disabled')
        self.verify_status.config(text="Verifying...", foreground='blue')
        
        def verify_worker():
            try:
                # Parse and verify share using production publishing system
                share_data = self.app_backend.publishing.parse_access_string(access_string)
                
                # Verify access and get share info
                share_info = self.app_backend.publishing.verify_share_access(share_data)
                
                # Update UI in main thread
                self.dialog.after(0, lambda: self._verification_complete(True, share_info))
                
            except Exception as e:
                logger.error(f"Share verification failed: {e}")
                self.dialog.after(0, lambda: self._verification_complete(False, None, str(e)))
                
        threading.Thread(target=verify_worker, daemon=True).start()
        
    def _verification_complete(self, success, share_info=None, error=None):
        """Handle verification completion"""
        self.verify_button.config(state='normal')
        
        if success:
            self.share_info = share_info
            self.verify_status.config(text="✓ Share verified", foreground='green')
            self._show_share_details()
            self._load_file_tree()
            self._enable_download_sections()
        else:
            self.verify_status.config(text=f"✗ Verification failed", foreground='red')
            messagebox.showerror("Verification Failed", f"Failed to verify share:\n\n{error}")
            
    def _show_share_details(self):
        """Show verified share details"""
        # Clear existing content
        for widget in self.info_content_frame.winfo_children():
            widget.destroy()
            
        if not self.share_info:
            return
            
        # Create details grid
        details_grid = ttk.Frame(self.info_content_frame)
        details_grid.pack(fill=tk.X)
        
        details = [
            ("Share Name", self.share_info.get('name', 'Unknown')),
            ("Share Type", self.share_info.get('share_type', 'Unknown')),
            ("Total Files", f"{self.share_info.get('file_count', 0):,}"),
            ("Total Size", self._format_size(self.share_info.get('total_size', 0))),
            ("Created", self.share_info.get('created_at', 'Unknown')),
            ("Version", f"v{self.share_info.get('version', 1)}")
        ]
        
        for i, (label, value) in enumerate(details):
            ttk.Label(details_grid, text=f"{label}:", font=('Arial', 9, 'bold')).grid(
                row=i//2, column=(i%2)*2, sticky=tk.W, padx=(0, 10), pady=2)
            ttk.Label(details_grid, text=str(value), font=('Arial', 9)).grid(
                row=i//2, column=(i%2)*2+1, sticky=tk.W, padx=(0, 20), pady=2)
                
        # Pack and show info frame
        self.info_frame.pack(fill=tk.X, pady=(0, 10))
        
    def _load_file_tree(self):
        """Load file tree from share info using production index system"""
        if not self.share_info:
            return
            
        try:
            # Get file structure from production index system
            share_id = self.share_info['share_id']
            
            # Download and parse the core index
            index_data = self.app_backend.download_system.get_share_index(share_id)
            
            # Parse index to get file structure
            file_structure = self.app_backend.index_system.parse_index_structure(index_data)
            
            # Populate tree
            self.file_tree.load_structure(file_structure)
            
            # Update selection stats
            self._update_selection_stats()
            
        except Exception as e:
            logger.error(f"Failed to load file tree: {e}")
            messagebox.showerror("Error", f"Failed to load file list: {e}")
            
    def _enable_download_sections(self):
        """Enable download-related sections"""
        self.selection_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.options_frame.pack(fill=tk.X, pady=(0, 10))
        self.download_button.config(state='normal')
        
    def _select_all_files(self):
        """Select all files in tree"""
        self.file_tree.select_all()
        self._update_selection_stats()
        
    def _select_no_files(self):
        """Deselect all files in tree"""
        self.file_tree.select_none()
        self._update_selection_stats()
        
    def _expand_all(self):
        """Expand all tree nodes"""
        self.file_tree.expand_all()
        
    def _collapse_all(self):
        """Collapse all tree nodes"""
        self.file_tree.collapse_all()
        
    def _update_selection_stats(self):
        """Update selection statistics"""
        selected_count, selected_size = self.file_tree.get_selection_stats()
        
        if selected_count == 0:
            self.selection_stats_label.config(text="No files selected")
        else:
            self.selection_stats_label.config(
                text=f"Selected: {selected_count:,} files ({self._format_size(selected_size)})")
            
    def _browse_download_path(self):
        """Browse for download directory"""
        path = filedialog.askdirectory(
            title="Select Download Directory",
            initialdir=self.download_path_var.get()
        )
        
        if path:
            self.download_path_var.set(path)
            
    def _start_download(self):
        """Start the download process"""
        # Validate inputs
        if not self.share_info:
            messagebox.showerror("Error", "No share verified")
            return
            
        selected_files = self.file_tree.get_selected_files()
        if not selected_files:
            messagebox.showwarning("Warning", "No files selected for download")
            return
            
        download_path = self.download_path_var.get()
        if not download_path:
            messagebox.showerror("Error", "Please select a download directory")
            return
            
        # Create download directory
        try:
            os.makedirs(download_path, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot create download directory: {e}")
            return
            
        # Prepare download options
        options = {
            'preserve_structure': self.preserve_structure_var.get(),
            'skip_existing': self.skip_existing_var.get(),
            'verify_integrity': self.verify_integrity_var.get(),
            'create_log': self.create_log_var.get()
        }
        
        # Show progress section and start download
        self.progress_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.download_button.config(state='disabled')
        self.pause_button.pack(side=tk.LEFT, padx=(10, 0))
        self.cancel_button.config(text="Cancel Download")
        
        self.download_in_progress = True
        
        def download_worker():
            try:
                # Start download with production download system
                download_session = self.app_backend.download_system.start_download(
                    share_info=self.share_info,
                    selected_files=selected_files,
                    download_path=download_path,
                    options=options
                )
                
                # Monitor download progress
                while download_session.is_active():
                    stats = download_session.get_progress()
                    
                    # Update progress callbacks
                    if self.download_in_progress:
                        self._download_progress_callback(
                            stats['bytes_downloaded'], 
                            stats['total_bytes'], 
                            stats['download_speed']
                        )
                        
                        if stats['current_file']:
                            self._download_file_callback(
                                stats['current_file'], 
                                stats['file_progress']
                            )
                    
                    time.sleep(0.5)  # Update every 500ms
                
                # Check final status
                if download_session.is_complete():
                    self.dialog.after(0, lambda: self._download_complete(True))
                else:
                    error = download_session.get_error()
                    self.dialog.after(0, lambda: self._download_complete(False, error))
                
            except Exception as e:
                logger.error(f"Download failed: {e}")
                self.dialog.after(0, lambda: self._download_complete(False, str(e)))
                
        self.download_thread = threading.Thread(target=download_worker, daemon=True)
        self.download_thread.start()
        
    def _download_progress_callback(self, current, total, speed):
        """Handle download progress updates"""
        def update():
            if total > 0:
                progress = (current / total) * 100
                self.overall_progress_var.set(progress)
                
            self.progress_label.config(text=f"Downloaded: {self._format_size(current)} / {self._format_size(total)}")
            
            if speed > 0:
                self.speed_label.config(text=f"Speed: {self._format_size(speed)}/s")
                
        self.dialog.after(0, update)
        
    def _download_file_callback(self, filename, file_progress):
        """Handle current file progress updates"""
        def update():
            self.current_file_label.config(text=f"Downloading: {filename}")
            self.file_progress_var.set(file_progress)
            
        self.dialog.after(0, update)
        
    def _download_log_callback(self, message):
        """Handle download log messages"""
        def update():
            timestamp = time.strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
            
        self.dialog.after(0, update)
        
    def _download_complete(self, success, error=None):
        """Handle download completion"""
        self.download_in_progress = False
        
        if success:
            messagebox.showinfo("Success", "Download completed successfully!")
            self.cancel_button.config(text="Close")
        else:
            messagebox.showerror("Download Failed", f"Download failed:\n\n{error}")
            self.cancel_button.config(text="Close")
            
        self.pause_button.pack_forget()
        
    def _pause_download(self):
        """Pause/resume download"""
        # Implementation for pause/resume
        if self.pause_button.cget('text') == 'Pause':
            self.pause_button.config(text='Resume')
            # Pause download
        else:
            self.pause_button.config(text='Pause')
            # Resume download
            
    def _format_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
            
        return f"{size_bytes:.1f} {size_names[i]}"
        
    def _on_closing(self):
        """Handle dialog closing"""
        if self.download_in_progress:
            if messagebox.askyesno("Confirm", "Download is in progress. Cancel download and close?"):
                # Cancel download
                self.download_in_progress = False
                self.dialog.destroy()
        else:
            self.dialog.destroy()


class CheckboxTreeview(ttk.Frame):
    """Treeview with checkbox functionality for file selection"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.file_data = {}  # Store file information
        self.selection_callbacks = []
        
        self._create_widgets()
        
    def _create_widgets(self):
        """Create treeview with checkboxes"""
        # Treeview
        columns = ('size', 'type')
        self.tree = ttk.Treeview(self, columns=columns, show='tree headings')
        
        # Configure columns
        self.tree.heading('#0', text='Files and Folders')
        self.tree.heading('size', text='Size')
        self.tree.heading('type', text='Type')
        
        self.tree.column('#0', width=400)
        self.tree.column('size', width=80)
        self.tree.column('type', width=80)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Pack widgets
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind events
        self.tree.bind('<Button-1>', self._on_click)
        self.tree.bind('<space>', self._on_space)
        
    def load_structure(self, file_structure):
        """Load file structure into tree"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        self.file_data.clear()
        
        # Load structure recursively
        self._load_structure_recursive('', file_structure)
        
    def _load_structure_recursive(self, parent, structure):
        """Recursively load file structure"""
        for item in structure:
            name = item['name']
            size = item.get('size', 0)
            is_folder = item.get('is_folder', False)
            
            # Create display text with checkbox
            display_text = f"☐ {name}"
            
            # Create tree item
            item_id = self.tree.insert(parent, tk.END, text=display_text,
                                     values=(self._format_size(size) if not is_folder else '',
                                            'Folder' if is_folder else 'File'))
            
            # Store file data
            self.file_data[item_id] = {
                'name': name,
                'size': size,
                'is_folder': is_folder,
                'selected': False,
                'path': item.get('path', name)
            }
            
            # Load children if folder
            if is_folder and 'children' in item:
                self._load_structure_recursive(item_id, item['children'])
                
    def _on_click(self, event):
        """Handle mouse click on tree item"""
        item = self.tree.identify('item', event.x, event.y)
        if item:
            self._toggle_selection(item)
            
    def _on_space(self, event):
        """Handle space key press"""
        selection = self.tree.selection()
        if selection:
            self._toggle_selection(selection[0])
            
    def _toggle_selection(self, item):
        """Toggle selection state of item"""
        if item not in self.file_data:
            return
            
        # Toggle selection
        self.file_data[item]['selected'] = not self.file_data[item]['selected']
        
        # Update display
        self._update_item_display(item)
        
        # Update children
        self._update_children_selection(item, self.file_data[item]['selected'])
        
        # Update parent
        self._update_parent_selection(item)
        
        # Call callbacks
        for callback in self.selection_callbacks:
            callback()
            
    def _update_item_display(self, item):
        """Update visual display of item"""
        name = self.file_data[item]['name']
        selected = self.file_data[item]['selected']
        
        checkbox = "☑" if selected else "☐"
        display_text = f"{checkbox} {name}"
        
        self.tree.item(item, text=display_text)
        
    def _update_children_selection(self, item, selected):
        """Update selection of all children"""
        for child in self.tree.get_children(item):
            if child in self.file_data:
                self.file_data[child]['selected'] = selected
                self._update_item_display(child)
                self._update_children_selection(child, selected)
                
    def _update_parent_selection(self, item):
        """Update parent selection based on children"""
        parent = self.tree.parent(item)
        if not parent or parent not in self.file_data:
            return
            
        # Check if all children are selected
        children = self.tree.get_children(parent)
        if children:
            all_selected = all(self.file_data[child]['selected'] for child in children if child in self.file_data)
            any_selected = any(self.file_data[child]['selected'] for child in children if child in self.file_data)
            
            # Update parent selection
            if all_selected:
                self.file_data[parent]['selected'] = True
            elif any_selected:
                # Partial selection - could show different indicator
                self.file_data[parent]['selected'] = True
            else:
                self.file_data[parent]['selected'] = False
                
            self._update_item_display(parent)
            
            # Recursively update grandparent
            self._update_parent_selection(parent)
            
    def select_all(self):
        """Select all items in tree"""
        for item in self.file_data:
            self.file_data[item]['selected'] = True
            self._update_item_display(item)
            
    def select_none(self):
        """Deselect all items in tree"""
        for item in self.file_data:
            self.file_data[item]['selected'] = False
            self._update_item_display(item)
            
    def expand_all(self):
        """Expand all tree nodes"""
        def expand_recursive(item):
            self.tree.item(item, open=True)
            for child in self.tree.get_children(item):
                expand_recursive(child)
                
        for item in self.tree.get_children():
            expand_recursive(item)
            
    def collapse_all(self):
        """Collapse all tree nodes"""
        def collapse_recursive(item):
            self.tree.item(item, open=False)
            for child in self.tree.get_children(item):
                collapse_recursive(child)
                
        for item in self.tree.get_children():
            collapse_recursive(item)
            
    def get_selected_files(self):
        """Get list of selected file paths"""
        selected_files = []
        
        for item, data in self.file_data.items():
            if data['selected'] and not data['is_folder']:
                selected_files.append(data['path'])
                
        return selected_files
        
    def get_selection_stats(self):
        """Get selection statistics"""
        selected_count = 0
        selected_size = 0
        
        for item, data in self.file_data.items():
            if data['selected'] and not data['is_folder']:
                selected_count += 1
                selected_size += data['size']
                
        return selected_count, selected_size
        
    def add_selection_callback(self, callback):
        """Add callback for selection changes"""
        self.selection_callbacks.append(callback)
        
    def _format_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
            
        return f"{size_bytes:.1f} {size_names[i]}"


def main():
    """Test the download dialog with real backend (development only)"""
    import sys
    import os
    
    # Add parent directory for imports
    sys.path.insert(0, str(Path(__file__).parent))
    
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    try:
        # Import real backend
        from main import UsenetSync
        
        # Initialize real backend for testing
        backend = UsenetSync()
        
        # Create and show dialog
        dialog = DownloadDialog(root, backend)
        root.wait_window(dialog.dialog)
        
        print("Download dialog closed")
        
    except Exception as e:
        print(f"Error initializing backend: {e}")
        print("Cannot test without proper backend setup")


if __name__ == "__main__":
    main()