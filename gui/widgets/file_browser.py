"""
Advanced File Browser Widget
Supports millions of files with virtual scrolling and search
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Optional, List, Dict, Any, Callable
import os
from pathlib import Path

class VirtualFileModel:
    """Data model for virtual file browsing"""
    
    def __init__(self, backend, folder_id):
        self.backend = backend
        self.folder_id = folder_id
        self.files = []
        self.filtered_files = []
        self.search_term = ""
        self.sort_column = "name"
        self.sort_reverse = False
        self.total_count = 0
        
    def load_files(self):
        """Load files from backend"""
        if not self.backend or not self.folder_id:
            return
        
        try:
            self.files = self.backend.database.get_folder_files(self.folder_id)
            self.total_count = len(self.files)
            self.apply_filter()
        except Exception as e:
            raise Exception(f"Failed to load files: {e}")
    
    def apply_filter(self):
        """Apply search filter"""
        if not self.search_term:
            self.filtered_files = self.files[:]
        else:
            term = self.search_term.lower()
            self.filtered_files = [
                f for f in self.files 
                if term in f['file_path'].lower()
            ]
        
        self.sort_files()
    
    def sort_files(self):
        """Sort filtered files"""
        if self.sort_column == "name":
            key_func = lambda f: f['file_path'].lower()
        elif self.sort_column == "size":
            key_func = lambda f: f['file_size']
        elif self.sort_column == "modified":
            key_func = lambda f: f.get('modified_at', '')
        else:
            key_func = lambda f: f['file_path'].lower()
        
        self.filtered_files.sort(key=key_func, reverse=self.sort_reverse)
    
    def get_page(self, start_index, page_size):
        """Get page of files"""
        end_index = start_index + page_size
        return self.filtered_files[start_index:end_index]
    
    def get_file_count(self):
        """Get total filtered file count"""
        return len(self.filtered_files)
    
    def set_search(self, search_term):
        """Set search term"""
        self.search_term = search_term
        self.apply_filter()
    
    def set_sort(self, column, reverse=False):
        """Set sort column and direction"""
        self.sort_column = column
        self.sort_reverse = reverse
        self.sort_files()

class FileBrowserWidget(ttk.Frame):
    """Advanced file browser with virtual scrolling"""
    
    def __init__(self, parent, backend=None):
        super().__init__(parent)
        self.backend = backend
        self.model = None
        self.current_folder_id = None
        self.page_size = 1000
        self.current_page = 0
        self.selected_files = set()
        
        self.create_widgets()
        self.setup_bindings()
    
    def create_widgets(self):
        """Create file browser widgets"""
        # Search and controls frame
        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Search
        ttk.Label(controls_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(controls_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind('<KeyRelease>', self.on_search_changed)
        
        # File count label
        self.file_count_label = ttk.Label(controls_frame, text="0 files")
        self.file_count_label.pack(side=tk.LEFT, padx=20)
        
        # Selection controls
        ttk.Button(controls_frame, text="Select All", 
                  command=self.select_all, width=10).pack(side=tk.RIGHT, padx=2)
        ttk.Button(controls_frame, text="Select None", 
                  command=self.select_none, width=10).pack(side=tk.RIGHT, padx=2)
        
        # File tree
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview with columns
        self.file_tree = ttk.Treeview(tree_frame, 
                                     columns=('size', 'modified', 'status', 'segments'),
                                     show='tree headings')
        
        # Configure columns
        self.file_tree.heading('#0', text='File Name', command=lambda: self.sort_by('name'))
        self.file_tree.heading('size', text='Size', command=lambda: self.sort_by('size'))
        self.file_tree.heading('modified', text='Modified', command=lambda: self.sort_by('modified'))
        self.file_tree.heading('status', text='Status', command=lambda: self.sort_by('status'))
        self.file_tree.heading('segments', text='Segments', command=lambda: self.sort_by('segments'))
        
        self.file_tree.column('#0', width=300, minwidth=200)
        self.file_tree.column('size', width=100, minwidth=80)
        self.file_tree.column('modified', width=120, minwidth=100)
        self.file_tree.column('status', width=80, minwidth=60)
        self.file_tree.column('segments', width=80, minwidth=60)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Pack tree and scrollbars
        self.file_tree.grid(row=0, column=0, sticky='nsew')
        v_scroll.grid(row=0, column=1, sticky='ns')
        h_scroll.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Pagination frame
        pagination_frame = ttk.Frame(self)
        pagination_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.prev_button = ttk.Button(pagination_frame, text="< Previous", 
                                     command=self.prev_page, state=tk.DISABLED)
        self.prev_button.pack(side=tk.LEFT)
        
        self.page_label = ttk.Label(pagination_frame, text="Page 1 of 1")
        self.page_label.pack(side=tk.LEFT, padx=20)
        
        self.next_button = ttk.Button(pagination_frame, text="Next >", 
                                     command=self.next_page, state=tk.DISABLED)
        self.next_button.pack(side=tk.LEFT)
        
        # Page size selector
        ttk.Label(pagination_frame, text="Per page:").pack(side=tk.RIGHT, padx=5)
        self.page_size_var = tk.StringVar(value="1000")
        page_size_combo = ttk.Combobox(pagination_frame, textvariable=self.page_size_var,
                                      values=["100", "500", "1000", "2000", "5000"],
                                      width=6, state="readonly")
        page_size_combo.pack(side=tk.RIGHT)
        page_size_combo.bind('<<ComboboxSelected>>', self.on_page_size_changed)
    
    def setup_bindings(self):
        """Setup event bindings"""
        # Tree selection
        self.file_tree.bind('<<TreeviewSelect>>', self.on_file_select)
        self.file_tree.bind('<Button-3>', self.show_context_menu)
        self.file_tree.bind('<Double-1>', self.on_file_double_click)
        
        # Keyboard shortcuts
        self.file_tree.bind('<Control-a>', lambda e: self.select_all())
        self.file_tree.bind('<Control-n>', lambda e: self.select_none())
        self.file_tree.bind('<space>', self.toggle_selection)
        
        # Context menu
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Download Selected", command=self.download_selected)
        self.context_menu.add_command(label="View Details", command=self.view_file_details)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Copy Path", command=self.copy_file_path)
        self.context_menu.add_command(label="Show in Explorer", command=self.show_in_explorer)
    
    def load_folder(self, folder_id):
        """Load files for folder"""
        self.current_folder_id = folder_id
        self.current_page = 0
        self.selected_files.clear()
        
        if not self.backend:
            return
        
        try:
            # Create model
            self.model = VirtualFileModel(self.backend, folder_id)
            
            # Load files in background
            self.load_files_async()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load folder: {e}")
    
    def load_files_async(self):
        """Load files asynchronously"""
        def load_worker():
            try:
                self.model.load_files()
                self.after(0, self.update_display)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Failed to load files: {e}"))
        
        threading.Thread(target=load_worker, daemon=True).start()
    
    def update_display(self):
        """Update file display"""
        if not self.model:
            return
        
        # Clear existing items
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        # Get current page
        start_index = self.current_page * self.page_size
        files_page = self.model.get_page(start_index, self.page_size)
        
        # Populate tree
        for file_info in files_page:
            # Format file size
            size_mb = round(file_info['file_size'] / (1024 * 1024), 2)
            if size_mb < 1:
                size_str = f"{round(file_info['file_size'] / 1024, 1)} KB"
            else:
                size_str = f"{size_mb} MB"
            
            # Format modified date
            modified = file_info.get('modified_at', '')
            if modified:
                modified = modified.split(' ')[0]  # Date only
            
            # Status indicator
            uploaded_segments = file_info.get('uploaded_segments', 0)
            total_segments = file_info.get('total_segments', 0)
            
            if total_segments == 0:
                status = "○ Pending"
            elif uploaded_segments == total_segments:
                status = "✓ Complete"
            elif uploaded_segments > 0:
                status = f"◐ {uploaded_segments}/{total_segments}"
            else:
                status = "⚠ Failed"
            
            # Segments info
            segments_info = f"{uploaded_segments}/{total_segments}" if total_segments > 0 else "0/0"
            
            # Insert item
            item_id = self.file_tree.insert('', 'end',
                                           text=file_info['file_path'],
                                           values=(size_str, modified, status, segments_info),
                                           tags=(str(file_info['id']),))
            
            # Mark selected files
            if file_info['id'] in self.selected_files:
                self.file_tree.selection_add(item_id)
        
        # Update pagination
        self.update_pagination()
        
        # Update file count
        total_files = self.model.get_file_count()
        self.file_count_label.config(text=f"{total_files:,} files")
    
    def update_pagination(self):
        """Update pagination controls"""
        if not self.model:
            return
        
        total_files = self.model.get_file_count()
        total_pages = max(1, (total_files + self.page_size - 1) // self.page_size)
        current_page_display = self.current_page + 1
        
        # Update page label
        self.page_label.config(text=f"Page {current_page_display} of {total_pages}")
        
        # Update button states
        self.prev_button.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if self.current_page < total_pages - 1 else tk.DISABLED)
    
    def on_search_changed(self, event):
        """Handle search term change"""
        if self.model:
            self.model.set_search(self.search_var.get())
            self.current_page = 0
            self.update_display()
    
    def on_page_size_changed(self, event):
        """Handle page size change"""
        try:
            self.page_size = int(self.page_size_var.get())
            self.current_page = 0
            self.update_display()
        except ValueError:
            pass
    
    def sort_by(self, column):
        """Sort files by column"""
        if self.model:
            # Toggle reverse if same column
            if self.model.sort_column == column:
                self.model.sort_reverse = not self.model.sort_reverse
            else:
                self.model.sort_reverse = False
            
            self.model.set_sort(column, self.model.sort_reverse)
            self.update_display()
    
    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_display()
    
    def next_page(self):
        """Go to next page"""
        if self.model:
            total_files = self.model.get_file_count()
            total_pages = (total_files + self.page_size - 1) // self.page_size
            if self.current_page < total_pages - 1:
                self.current_page += 1
                self.update_display()
    
    def on_file_select(self, event):
        """Handle file selection"""
        selection = self.file_tree.selection()
        self.selected_files.clear()
        
        for item_id in selection:
            item = self.file_tree.item(item_id)
            if item['tags']:
                file_id = int(item['tags'][0])
                self.selected_files.add(file_id)
    
    def toggle_selection(self, event):
        """Toggle selection for current item"""
        item = self.file_tree.focus()
        if item:
            if item in self.file_tree.selection():
                self.file_tree.selection_remove(item)
            else:
                self.file_tree.selection_add(item)
    
    def select_all(self):
        """Select all visible files"""
        for item in self.file_tree.get_children():
            self.file_tree.selection_add(item)
        self.on_file_select(None)
    
    def select_none(self):
        """Clear selection"""
        self.file_tree.selection_remove(*self.file_tree.selection())
        self.selected_files.clear()
    
    def show_context_menu(self, event):
        """Show context menu"""
        item = self.file_tree.identify_row(event.y)
        if item:
            if item not in self.file_tree.selection():
                self.file_tree.selection_set(item)
                self.on_file_select(None)
            self.context_menu.post(event.x_root, event.y_root)
    
    def on_file_double_click(self, event):
        """Handle file double-click"""
        self.view_file_details()
    
    def download_selected(self):
        """Download selected files"""
        if not self.selected_files:
            messagebox.showwarning("Warning", "No files selected")
            return
        
        messagebox.showinfo("Download", f"Download {len(self.selected_files)} files")
        # TODO: Implement selective file download
    
    def view_file_details(self):
        """View file details"""
        if not self.selected_files:
            messagebox.showwarning("Warning", "No file selected")
            return
        
        # Show details for first selected file
        file_id = next(iter(self.selected_files))
        self.show_file_details_dialog(file_id)
    
    def show_file_details_dialog(self, file_id):
        """Show file details dialog"""
        try:
            # Get file info
            if not self.backend:
                return
            
            file_info = None
            for f in self.model.files:
                if f['id'] == file_id:
                    file_info = f
                    break
            
            if not file_info:
                return
            
            # Create details dialog
            dialog = tk.Toplevel(self)
            dialog.title("File Details")
            dialog.geometry("500x400")
            dialog.transient(self.winfo_toplevel())
            dialog.grab_set()
            
            # File info
            info_frame = ttk.LabelFrame(dialog, text="File Information", padding=10)
            info_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Label(info_frame, text=f"Path: {file_info['file_path']}").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Size: {file_info['file_size']:,} bytes").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Hash: {file_info['file_hash']}").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Modified: {file_info.get('modified_at', 'Unknown')}").pack(anchor=tk.W)
            
            # Segments info
            segments_frame = ttk.LabelFrame(dialog, text="Segments", padding=10)
            segments_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            segments = self.backend.database.get_file_segments(file_id)
            
            segments_tree = ttk.Treeview(segments_frame, 
                                        columns=('index', 'size', 'status', 'message_id'),
                                        show='headings')
            
            segments_tree.heading('index', text='Index')
            segments_tree.heading('size', text='Size')
            segments_tree.heading('status', text='Status')
            segments_tree.heading('message_id', text='Message ID')
            
            for segment in segments:
                size_kb = round(segment['segment_size'] / 1024, 1)
                segments_tree.insert('', 'end', values=(
                    segment['segment_index'],
                    f"{size_kb} KB",
                    segment['state'],
                    segment.get('message_id', 'Not uploaded')
                ))
            
            segments_tree.pack(fill=tk.BOTH, expand=True)
            
            ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show file details: {e}")
    
    def copy_file_path(self):
        """Copy file path to clipboard"""
        if not self.selected_files:
            return
        
        # Get first selected file path
        selection = self.file_tree.selection()
        if selection:
            item = self.file_tree.item(selection[0])
            file_path = item['text']
            
            self.clipboard_clear()
            self.clipboard_append(file_path)
            
            messagebox.showinfo("Copied", f"File path copied to clipboard:\n{file_path}")
    
    def show_in_explorer(self):
        """Show file in system file explorer"""
        if not self.selected_files or not self.current_folder_id:
            return
        
        try:
            # Get folder path
            folder = self.backend.database.get_folder(self.current_folder_id)
            if not folder:
                return
            
            folder_path = folder['folder_path']
            
            # Get first selected file
            selection = self.file_tree.selection()
            if selection:
                item = self.file_tree.item(selection[0])
                file_path = item['text']
                
                full_path = os.path.join(folder_path, file_path)
                
                # Open in file explorer
                import platform
                if platform.system() == "Windows":
                    os.system(f'explorer /select,"{full_path}"')
                elif platform.system() == "Darwin":  # macOS
                    os.system(f'open -R "{full_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{os.path.dirname(full_path)}"')
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show in explorer: {e}")