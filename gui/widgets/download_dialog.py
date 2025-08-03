"""
Download Management Dialog
Handles share downloads with progress tracking
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from typing import Optional, Dict, Any
import json

class DownloadDialog:
    """Dialog for downloading shared folders"""
    
    def __init__(self, parent, backend):
        self.parent = parent
        self.backend = backend
        self.result = None
        self.download_session_id = None
        self.progress_thread = None
        self.cancelled = False
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Download Shared Folder")
        self.dialog.geometry("700x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 50,
            parent.winfo_rooty() + 50
        ))
        
        self.create_widgets()
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
    
    def create_widgets(self):
        """Create dialog widgets"""
        # Header
        header_frame = ttk.Frame(self.dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(header_frame, text="Download Shared Folder", 
                 font=('Arial', 14, 'bold')).pack()
        
        # Access string frame
        access_frame = ttk.LabelFrame(self.dialog, text="Share Access", padding=15)
        access_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(access_frame, text="Access String:").pack(anchor=tk.W)
        self.access_string_var = tk.StringVar()
        access_entry = ttk.Entry(access_frame, textvariable=self.access_string_var, width=80)
        access_entry.pack(fill=tk.X, pady=5)
        access_entry.focus()
        
        # Verify button
        ttk.Button(access_frame, text="Verify Share", 
                  command=self.verify_share).pack(anchor=tk.W, pady=5)
        
        # Share info frame
        self.info_frame = ttk.LabelFrame(self.dialog, text="Share Information", padding=15)
        self.info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.info_text = tk.Text(self.info_frame, height=6, wrap=tk.WORD, 
                                font=('Courier', 9), state=tk.DISABLED)
        info_scroll = ttk.Scrollbar(self.info_frame, orient=tk.VERTICAL, 
                                   command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scroll.set)
        
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Password frame (initially hidden)
        self.password_frame = ttk.LabelFrame(self.dialog, text="Password Required", padding=15)
        
        ttk.Label(self.password_frame, text="This share is password protected.").pack(anchor=tk.W)
        ttk.Label(self.password_frame, text="Password:").pack(anchor=tk.W, pady=(10, 0))
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(self.password_frame, textvariable=self.password_var, 
                                  show="*", width=30)
        password_entry.pack(anchor=tk.W, pady=5)
        
        # File selection frame
        self.selection_frame = ttk.LabelFrame(self.dialog, text="File Selection", padding=15)
        
        # Selection controls
        selection_controls = ttk.Frame(self.selection_frame)
        selection_controls.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(selection_controls, text="Select All", 
                  command=self.select_all_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(selection_controls, text="Select None", 
                  command=self.select_no_files).pack(side=tk.LEFT, padx=2)
        ttk.Button(selection_controls, text="Expand All", 
                  command=self.expand_all).pack(side=tk.LEFT, padx=10)
        ttk.Button(selection_controls, text="Collapse All", 
                  command=self.collapse_all).pack(side=tk.LEFT, padx=2)
        
        # File tree
        tree_frame = ttk.Frame(self.selection_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.file_tree = ttk.Treeview(tree_frame, 
                                     columns=('size', 'modified'),
                                     show='tree headings')
        
        self.file_tree.heading('#0', text='File/Folder Name')
        self.file_tree.heading('size', text='Size')
        self.file_tree.heading('modified', text='Modified')
        
        self.file_tree.column('#0', width=400)
        self.file_tree.column('size', width=100)
        self.file_tree.column('modified', width=120)
        
        # Tree scrollbars
        tree_v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        tree_h_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=tree_v_scroll.set, xscrollcommand=tree_h_scroll.set)
        
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        tree_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind tree events
        self.file_tree.bind('<space>', self.toggle_tree_selection)
        
        # Download options frame
        self.options_frame = ttk.LabelFrame(self.dialog, text="Download Options", padding=15)
        
        # Destination
        dest_frame = ttk.Frame(self.options_frame)
        dest_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(dest_frame, text="Destination:").pack(side=tk.LEFT)
        self.destination_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        dest_entry = ttk.Entry(dest_frame, textvariable=self.destination_var, width=50)
        dest_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(dest_frame, text="Browse", command=self.browse_destination).pack(side=tk.RIGHT)
        
        # Options checkboxes
        options_checks = ttk.Frame(self.options_frame)
        options_checks.pack(fill=tk.X, pady=10)
        
        self.skip_existing_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_checks, text="Skip existing files", 
                       variable=self.skip_existing_var).pack(side=tk.LEFT)
        
        self.verify_integrity_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_checks, text="Verify file integrity", 
                       variable=self.verify_integrity_var).pack(side=tk.LEFT, padx=20)
        
        # Progress frame
        self.progress_frame = ttk.LabelFrame(self.dialog, text="Download Progress", padding=15)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.progress_frame, variable=self.progress_var,
                                           mode='determinate', length=400)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.progress_label = ttk.Label(self.progress_frame, text="Ready to download")
        self.progress_label.pack(anchor=tk.W, pady=5)
        
        self.speed_label = ttk.Label(self.progress_frame, text="")
        self.speed_label.pack(anchor=tk.W)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.dialog)
        buttons_frame.pack(fill=tk.X, padx=20, pady=20)
        
        self.download_button = ttk.Button(buttons_frame, text="Start Download", 
                                         command=self.start_download, 
                                         style='Primary.TButton', state=tk.DISABLED)
        self.download_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = ttk.Button(buttons_frame, text="Cancel", 
                                       command=self.on_cancel)
        self.cancel_button.pack(side=tk.RIGHT, padx=5)
        
        self.pause_button = ttk.Button(buttons_frame, text="Pause", 
                                      command=self.pause_download, state=tk.DISABLED)
        self.pause_button.pack(side=tk.RIGHT, padx=5)
        
        # State variables
        self.share_info = None
        self.verified = False
    
    def verify_share(self):
        """Verify share access string"""
        access_string = self.access_string_var.get().strip()
        if not access_string:
            messagebox.showerror("Error", "Please enter an access string")
            return
        
        # Disable verify button during verification
        verify_btn = None
        for widget in self.access_frame.winfo_children():
            if isinstance(widget, ttk.Button) and widget.cget('text') == 'Verify Share':
                verify_btn = widget
                break
        
        if verify_btn:
            verify_btn.config(state=tk.DISABLED, text="Verifying...")
        
        def verify_worker():
            try:
                # TODO: Implement share verification in backend
                # For now, simulate verification
                time.sleep(1)
                
                # Mock share info
                share_info = {
                    'folder_name': 'Example Shared Folder',
                    'total_files': 150,
                    'total_size': 1024 * 1024 * 500,  # 500 MB
                    'share_type': 'public',
                    'created_date': '2024-01-15',
                    'files': self.generate_mock_file_list()
                }
                
                self.dialog.after(0, lambda: self.on_share_verified(share_info))
                
            except Exception as e:
                self.dialog.after(0, lambda: self.on_verify_error(str(e)))
            finally:
                if verify_btn:
                    self.dialog.after(0, lambda: verify_btn.config(state=tk.NORMAL, text="Verify Share"))
        
        threading.Thread(target=verify_worker, daemon=True).start()
    
    def generate_mock_file_list(self):
        """Generate mock file list for demonstration"""
        files = [
            {'path': 'Documents/report.pdf', 'size': 1024*500, 'type': 'file'},
            {'path': 'Documents/presentation.pptx', 'size': 1024*1024*5, 'type': 'file'},
            {'path': 'Images/', 'size': 0, 'type': 'folder'},
            {'path': 'Images/photo1.jpg', 'size': 1024*800, 'type': 'file'},
            {'path': 'Images/photo2.jpg', 'size': 1024*750, 'type': 'file'},
            {'path': 'Videos/', 'size': 0, 'type': 'folder'},
            {'path': 'Videos/movie.mp4', 'size': 1024*1024*100, 'type': 'file'},
        ]
        return files
    
    def on_share_verified(self, share_info):
        """Handle successful share verification"""
        self.share_info = share_info
        self.verified = True
        
        # Update info display
        self.update_info_display(share_info)
        
        # Show password frame if needed
        if share_info.get('share_type') == 'protected':
            self.password_frame.pack(fill=tk.X, padx=20, pady=10)
        else:
            self.password_frame.pack_forget()
        
        # Show file selection
        self.selection_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Populate file tree
        self.populate_file_tree(share_info.get('files', []))
        
        # Show download options
        self.options_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Show progress frame
        self.progress_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Enable download button
        self.download_button.config(state=tk.NORMAL)
        
        # Resize dialog
        self.dialog.geometry("700x900")
    
    def on_verify_error(self, error_message):
        """Handle share verification error"""
        messagebox.showerror("Verification Error", f"Failed to verify share:\n\n{error_message}")
    
    def update_info_display(self, share_info):
        """Update share information display"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete('1.0', tk.END)
        
        # Format share info
        size_mb = round(share_info.get('total_size', 0) / (1024 * 1024), 1)
        
        info_lines = [
            f"Folder Name: {share_info.get('folder_name', 'Unknown')}",
            f"Total Files: {share_info.get('total_files', 0):,}",
            f"Total Size: {size_mb:,.1f} MB",
            f"Share Type: {share_info.get('share_type', 'unknown').title()}",
            f"Created: {share_info.get('created_date', 'Unknown')}",
            "",
            "✓ Share verified successfully"
        ]
        
        self.info_text.insert('1.0', '\n'.join(info_lines))
        self.info_text.config(state=tk.DISABLED)
    
    def populate_file_tree(self, files):
        """Populate file tree with share contents"""
        # Clear existing items
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # Build tree structure
        folders = {}
        
        for file_info in files:
            path = file_info['path']
            parts = path.split('/')
            
            if file_info['type'] == 'folder':
                # Create folder entry
                parent = ''
                for i, part in enumerate(parts[:-1]):
                    folder_path = '/'.join(parts[:i+1])
                    if folder_path not in folders:
                        folders[folder_path] = self.file_tree.insert(parent, 'end',
                                                                    text=part,
                                                                    values=('', ''),
                                                                    tags=('folder',))
                    parent = folders[folder_path]
                
                # Add the folder itself
                if path not in folders:
                    folders[path] = self.file_tree.insert(parent, 'end',
                                                         text=parts[-1],
                                                         values=('Folder', ''),
                                                         tags=('folder',))
            else:
                # Create file entry
                parent = ''
                if len(parts) > 1:
                    folder_path = '/'.join(parts[:-1])
                    if folder_path not in folders:
                        # Create parent folders
                        temp_parent = ''
                        for i, part in enumerate(parts[:-1]):
                            temp_path = '/'.join(parts[:i+1])
                            if temp_path not in folders:
                                folders[temp_path] = self.file_tree.insert(temp_parent, 'end',
                                                                          text=part,
                                                                          values=('Folder', ''),
                                                                          tags=('folder',))
                            temp_parent = folders[temp_path]
                    parent = folders[folder_path]
                
                # Format file size
                size = file_info['size']
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{round(size / 1024, 1)} KB"
                else:
                    size_str = f"{round(size / (1024 * 1024), 1)} MB"
                
                self.file_tree.insert(parent, 'end',
                                     text=parts[-1],
                                     values=(size_str, ''),
                                     tags=('file', 'selected'))
        
        # Expand all folders initially
        self.expand_all()
    
    def toggle_tree_selection(self, event):
        """Toggle selection for tree item"""
        item = self.file_tree.focus()
        if item:
            tags = list(self.file_tree.item(item, 'tags'))
            if 'selected' in tags:
                tags.remove('selected')
                # Also deselect children if folder
                if 'folder' in tags:
                    self.deselect_children(item)
            else:
                tags.append('selected')
                # Also select children if folder
                if 'folder' in tags:
                    self.select_children(item)
            
            self.file_tree.item(item, tags=tags)
            self.update_selection_display()
    
    def select_children(self, parent):
        """Select all children of parent item"""
        for child in self.file_tree.get_children(parent):
            tags = list(self.file_tree.item(child, 'tags'))
            if 'selected' not in tags:
                tags.append('selected')
                self.file_tree.item(child, tags=tags)
            self.select_children(child)  # Recursive
    
    def deselect_children(self, parent):
        """Deselect all children of parent item"""
        for child in self.file_tree.get_children(parent):
            tags = list(self.file_tree.item(child, 'tags'))
            if 'selected' in tags:
                tags.remove('selected')
                self.file_tree.item(child, tags=tags)
            self.deselect_children(child)  # Recursive
    
    def select_all_files(self):
        """Select all files"""
        def select_recursive(parent=''):
            for child in self.file_tree.get_children(parent):
                tags = list(self.file_tree.item(child, 'tags'))
                if 'selected' not in tags:
                    tags.append('selected')
                    self.file_tree.item(child, tags=tags)
                select_recursive(child)
        
        select_recursive()
        self.update_selection_display()
    
    def select_no_files(self):
        """Deselect all files"""
        def deselect_recursive(parent=''):
            for child in self.file_tree.get_children(parent):
                tags = list(self.file_tree.item(child, 'tags'))
                if 'selected' in tags:
                    tags.remove('selected')
                    self.file_tree.item(child, tags=tags)
                deselect_recursive(child)
        
        deselect_recursive()
        self.update_selection_display()
    
    def expand_all(self):
        """Expand all tree items"""
        def expand_recursive(parent=''):
            for child in self.file_tree.get_children(parent):
                self.file_tree.item(child, open=True)
                expand_recursive(child)
        
        expand_recursive()
    
    def collapse_all(self):
        """Collapse all tree items"""
        def collapse_recursive(parent=''):
            for child in self.file_tree.get_children(parent):
                self.file_tree.item(child, open=False)
                collapse_recursive(child)
        
        collapse_recursive()
    
    def update_selection_display(self):
        """Update visual display of selected items"""
        # TODO: Update tree display to show selected items differently
        pass
    
    def browse_destination(self):
        """Browse for destination directory"""
        directory = filedialog.askdirectory(title="Select Download Destination",
                                           initialdir=self.destination_var.get())
        if directory:
            self.destination_var.set(directory)
    
    def start_download(self):
        """Start the download process"""
        if not self.verified:
            messagebox.showerror("Error", "Please verify the share first")
            return
        
        destination = self.destination_var.get().strip()
        if not destination:
            messagebox.showerror("Error", "Please select a destination directory")
            return
        
        # Validate destination
        dest_path = Path(destination)
        try:
            dest_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot create destination directory:\n{e}")
            return
        
        # Get selected files
        selected_files = self.get_selected_files()
        if not selected_files:
            messagebox.showerror("Error", "No files selected for download")
            return
        
        # Update UI state
        self.download_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.cancel_button.config(text="Cancel Download")
        
        # Start download
        self.start_download_async(destination, selected_files)
    
    def get_selected_files(self):
        """Get list of selected files"""
        selected = []
        
        def collect_selected(parent=''):
            for child in self.file_tree.get_children(parent):
                item_tags = self.file_tree.item(child, 'tags')
                if 'selected' in item_tags and 'file' in item_tags:
                    file_path = self.get_item_full_path(child)
                    selected.append(file_path)
                collect_selected(child)
        
        collect_selected()
        return selected
    
    def get_item_full_path(self, item):
        """Get full path for tree item"""
        path_parts = []
        current = item
        
        while current:
            text = self.file_tree.item(current, 'text')
            path_parts.insert(0, text)
            current = self.file_tree.parent(current)
        
        return '/'.join(path_parts)
    
    def start_download_async(self, destination, selected_files):
        """Start download in background thread"""
        def download_worker():
            try:
                # TODO: Implement actual download using backend
                # For now, simulate download progress
                
                total_files = len(selected_files)
                self.dialog.after(0, lambda: self.progress_bar.config(maximum=total_files))
                
                for i, file_path in enumerate(selected_files):
                    if self.cancelled:
                        break
                    
                    # Simulate download time
                    time.sleep(0.1)
                    
                    # Update progress
                    progress = i + 1
                    percentage = (progress / total_files) * 100
                    
                    self.dialog.after(0, lambda p=progress: self.progress_var.set(p))
                    self.dialog.after(0, lambda f=file_path, pct=percentage: 
                                     self.progress_label.config(text=f"Downloading: {f} ({pct:.1f}%)"))
                    
                    # Simulate speed calculation
                    speed = f"{1.5 + (i % 5) * 0.3:.1f} MB/s"
                    self.dialog.after(0, lambda s=speed: self.speed_label.config(text=f"Speed: {s}"))
                
                if not self.cancelled:
                    self.dialog.after(0, self.on_download_complete)
                else:
                    self.dialog.after(0, self.on_download_cancelled)
                    
            except Exception as e:
                self.dialog.after(0, lambda: self.on_download_error(str(e)))
        
        self.progress_thread = threading.Thread(target=download_worker, daemon=True)
        self.progress_thread.start()
    
    def on_download_complete(self):
        """Handle download completion"""
        self.progress_label.config(text="Download completed successfully!")
        self.speed_label.config(text="")
        
        self.download_button.config(state=tk.NORMAL, text="Download Complete")
        self.pause_button.config(state=tk.DISABLED)
        self.cancel_button.config(text="Close")
        
        self.result = {
            'success': True,
            'destination': self.destination_var.get(),
            'files_downloaded': len(self.get_selected_files())
        }
        
        messagebox.showinfo("Download Complete", 
                           f"Download completed successfully!\n\n"
                           f"Files saved to: {self.destination_var.get()}")
    
    def on_download_cancelled(self):
        """Handle download cancellation"""
        self.progress_label.config(text="Download cancelled")
        self.speed_label.config(text="")
        
        self.download_button.config(state=tk.NORMAL, text="Start Download")
        self.pause_button.config(state=tk.DISABLED)
        self.cancel_button.config(text="Close")
    
    def on_download_error(self, error_message):
        """Handle download error"""
        self.progress_label.config(text="Download failed")
        self.speed_label.config(text="")
        
        self.download_button.config(state=tk.NORMAL, text="Retry Download")
        self.pause_button.config(state=tk.DISABLED)
        self.cancel_button.config(text="Close")
        
        messagebox.showerror("Download Error", f"Download failed:\n\n{error_message}")
    
    def pause_download(self):
        """Pause/resume download"""
        # TODO: Implement pause/resume functionality
        current_text = self.pause_button.cget('text')
        if current_text == "Pause":
            self.pause_button.config(text="Resume")
            self.progress_label.config(text="Download paused")
        else:
            self.pause_button.config(text="Pause")
            self.progress_label.config(text="Download resumed")
    
    def on_cancel(self):
        """Handle dialog cancellation"""
        if self.progress_thread and self.progress_thread.is_alive():
            result = messagebox.askyesno("Cancel Download", 
                                        "Download is in progress. Cancel and close?")
            if result:
                self.cancelled = True
                self.dialog.destroy()
        else:
            self.dialog.destroy()