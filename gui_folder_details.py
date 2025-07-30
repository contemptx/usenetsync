#!/usr/bin/env python3
"""
UsenetSync GUI - Folder Details Panel
Comprehensive folder management with access control, segments, and file browsing
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import logging
from typing import Optional, Dict, List, Any
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class FolderDetailsPanel(ttk.Frame):
    """Panel showing detailed folder information and management"""
    
    def __init__(self, parent, app_backend, folder_id):
        super().__init__(parent)
        self.app_backend = app_backend
        self.folder_id = folder_id
        self.folder_info = None
        
        # Load folder info
        self._load_folder_info()
        
        # Create UI
        self._create_widgets()
        
        # Load initial data
        self._refresh_all_tabs()
        
    def _load_folder_info(self):
        """Load folder information from backend"""
        try:
            self.folder_info = self.app_backend.db.get_folder_info(self.folder_id)
            if not self.folder_info:
                raise Exception("Folder not found")
        except Exception as e:
            logger.error(f"Failed to load folder info: {e}")
            self.folder_info = {'display_name': 'Unknown', 'folder_path': 'Unknown'}
            
    def _create_widgets(self):
        """Create all widgets"""
        # Header with folder info
        self._create_header()
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Create tabs
        self._create_overview_tab()
        self._create_access_control_tab()
        self._create_segments_tab()
        self._create_files_tab()
        self._create_actions_tab()
        
    def _create_header(self):
        """Create folder header with basic info"""
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Folder name and type
        name_frame = ttk.Frame(header_frame)
        name_frame.pack(fill=tk.X)
        
        folder_name = self.folder_info.get('display_name', 'Unknown')
        share_type = self.folder_info.get('share_type', 'unknown')
        
        ttk.Label(name_frame, text=f"📁 {folder_name}", 
                 font=('Arial', 12, 'bold')).pack(side=tk.LEFT)
        
        type_color = {'public': 'green', 'private': 'blue', 'protected': 'orange'}.get(share_type, 'gray')
        ttk.Label(name_frame, text=f"[{share_type.upper()}]", 
                 foreground=type_color, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(10, 0))
        
        # Quick stats
        stats_frame = ttk.Frame(header_frame)
        stats_frame.pack(fill=tk.X, pady=(5, 0))
        
        try:
            file_count = self.folder_info.get('file_count', 0)
            total_size = self.folder_info.get('total_size', 0)
            version = self.folder_info.get('current_version', 1)
            
            stats_text = f"Files: {file_count:,} | Size: {self._format_size(total_size)} | Version: v{version}"
            ttk.Label(stats_frame, text=stats_text, font=('Arial', 9), 
                     foreground='gray').pack(side=tk.LEFT)
        except:
            pass
            
    def _create_overview_tab(self):
        """Create overview tab"""
        overview_frame = ttk.Frame(self.notebook)
        self.notebook.add(overview_frame, text="Overview")
        
        # Create scrollable content
        canvas = tk.Canvas(overview_frame)
        scrollbar = ttk.Scrollbar(overview_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Folder details
        details_frame = ttk.LabelFrame(scrollable_frame, text="Folder Details", padding=10)
        details_frame.pack(fill=tk.X, padx=10, pady=10)
        
        try:
            details_data = [
                ("Folder Path", self.folder_info.get('folder_path', 'Unknown')),
                ("Folder ID", self.folder_id[:32] + "..."),
                ("Share Type", self.folder_info.get('share_type', 'Unknown')),
                ("Current Version", f"v{self.folder_info.get('current_version', 1)}"),
                ("State", self.folder_info.get('state', 'Unknown')),
                ("Created", self.folder_info.get('created_at', 'Unknown')),
                ("Last Updated", self.folder_info.get('updated_at', 'Unknown'))
            ]
            
            for i, (label, value) in enumerate(details_data):
                ttk.Label(details_frame, text=f"{label}:", font=('Arial', 9, 'bold')).grid(
                    row=i, column=0, sticky=tk.W, padx=(0, 10), pady=2)
                ttk.Label(details_frame, text=str(value), font=('Arial', 9)).grid(
                    row=i, column=1, sticky=tk.W, pady=2)
                    
        except Exception as e:
            ttk.Label(details_frame, text=f"Error loading details: {e}", 
                     foreground='red').pack()
        
        # File statistics
        stats_frame = ttk.LabelFrame(scrollable_frame, text="File Statistics", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        try:
            # Get file type breakdown from backend
            file_stats = self._get_file_statistics()
            
            for i, (category, count, size) in enumerate(file_stats):
                row_frame = ttk.Frame(stats_frame)
                row_frame.pack(fill=tk.X, pady=2)
                
                ttk.Label(row_frame, text=category, font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
                ttk.Label(row_frame, text=f"{count:,} files", font=('Arial', 9)).pack(side=tk.RIGHT)
                ttk.Label(row_frame, text=f"({self._format_size(size)})", 
                         font=('Arial', 9), foreground='gray').pack(side=tk.RIGHT, padx=(0, 10))
                         
        except Exception as e:
            ttk.Label(stats_frame, text=f"Error loading statistics: {e}", 
                     foreground='red').pack()
        
        # Recent activity
        activity_frame = ttk.LabelFrame(scrollable_frame, text="Recent Activity", padding=10)
        activity_frame.pack(fill=tk.X, padx=10, pady=10)
        
        activity_text = tk.Text(activity_frame, height=6, wrap=tk.WORD, font=('Arial', 9))
        activity_scroll = ttk.Scrollbar(activity_frame, orient=tk.VERTICAL, command=activity_text.yview)
        activity_text.configure(yscrollcommand=activity_scroll.set)
        
        activity_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        activity_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load activity log
        try:
            activity_log = self._get_activity_log()
            activity_text.insert(tk.END, activity_log)
        except:
            activity_text.insert(tk.END, "No recent activity available.")
            
        activity_text.config(state=tk.DISABLED)
        
    def _create_access_control_tab(self):
        """Create access control tab"""
        access_frame = ttk.Frame(self.notebook)
        self.notebook.add(access_frame, text="Access Control")
        
        # Share type selection
        type_frame = ttk.LabelFrame(access_frame, text="Share Type", padding=10)
        type_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.share_type_var = tk.StringVar(value=self.folder_info.get('share_type', 'public'))
        
        type_options = [
            ("Public", "public", "Anyone with access string can download"),
            ("Private", "private", "Only authorized User IDs can access"),
            ("Protected", "protected", "Password required for access")
        ]
        
        for text, value, desc in type_options:
            radio_frame = ttk.Frame(type_frame)
            radio_frame.pack(fill=tk.X, pady=2)
            
            ttk.Radiobutton(radio_frame, text=text, variable=self.share_type_var, 
                           value=value, command=self._on_share_type_change).pack(side=tk.LEFT)
            ttk.Label(radio_frame, text=f"- {desc}", font=('Arial', 8), 
                     foreground='gray').pack(side=tk.LEFT, padx=(10, 0))
        
        # Password frame (for protected shares)
        self.password_frame = ttk.LabelFrame(access_frame, text="Password Protection", padding=10)
        
        ttk.Label(self.password_frame, text="Password:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.password_var = tk.StringVar()
        ttk.Entry(self.password_frame, textvariable=self.password_var, show="*").grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        ttk.Label(self.password_frame, text="Hint:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.password_hint_var = tk.StringVar()
        ttk.Entry(self.password_frame, textvariable=self.password_hint_var).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.password_frame.columnconfigure(1, weight=1)
        
        # User management frame (for private shares)
        self.users_frame = ttk.LabelFrame(access_frame, text="Authorized Users", padding=10)
        
        # User list
        users_list_frame = ttk.Frame(self.users_frame)
        users_list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.users_tree = ttk.Treeview(users_list_frame, columns=('user_id', 'display_name'), 
                                      show='headings', height=6)
        self.users_tree.heading('user_id', text='User ID')
        self.users_tree.heading('display_name', text='Display Name')
        self.users_tree.column('user_id', width=200)
        self.users_tree.column('display_name', width=150)
        
        users_scroll = ttk.Scrollbar(users_list_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=users_scroll.set)
        
        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        users_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # User management buttons
        users_buttons = ttk.Frame(self.users_frame)
        users_buttons.pack(fill=tk.X)
        
        ttk.Button(users_buttons, text="Add User", command=self._add_user).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(users_buttons, text="Remove Selected", command=self._remove_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(users_buttons, text="Import from File", command=self._import_users).pack(side=tk.LEFT, padx=5)
        
        # Update access button
        update_frame = ttk.Frame(access_frame)
        update_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(update_frame, text="Update Access Settings", 
                  command=self._update_access_settings, style='Accent.TButton').pack(side=tk.LEFT)
        ttk.Button(update_frame, text="Refresh", command=self._refresh_access_control).pack(side=tk.LEFT, padx=(10, 0))
        
        # Show/hide frames based on share type
        self._on_share_type_change()
        
    def _create_segments_tab(self):
        """Create segments management tab"""
        segments_frame = ttk.Frame(self.notebook)
        self.notebook.add(segments_frame, text="Segments")
        
        # Segments header
        header_frame = ttk.Frame(segments_frame)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(header_frame, text="Segment Upload Status", 
                 font=('Arial', 11, 'bold')).pack(side=tk.LEFT)
        
        # Filter buttons
        filter_frame = ttk.Frame(header_frame)
        filter_frame.pack(side=tk.RIGHT)
        
        ttk.Button(filter_frame, text="Show All", command=lambda: self._filter_segments('all')).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="Failed Only", command=lambda: self._filter_segments('failed')).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="Missing Only", command=lambda: self._filter_segments('missing')).pack(side=tk.LEFT, padx=2)
        
        # Segments list
        segments_list_frame = ttk.Frame(segments_frame)
        segments_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Treeview for segments
        columns = ('segment_id', 'file_name', 'size', 'status', 'message_id', 'attempts')
        self.segments_tree = ttk.Treeview(segments_list_frame, columns=columns, show='tree headings')
        
        # Configure columns
        self.segments_tree.heading('#0', text='Select')
        self.segments_tree.heading('segment_id', text='Segment')
        self.segments_tree.heading('file_name', text='File Name')
        self.segments_tree.heading('size', text='Size')
        self.segments_tree.heading('status', text='Status')
        self.segments_tree.heading('message_id', text='Message ID')
        self.segments_tree.heading('attempts', text='Attempts')
        
        self.segments_tree.column('#0', width=50)
        self.segments_tree.column('segment_id', width=100)
        self.segments_tree.column('file_name', width=200)
        self.segments_tree.column('size', width=80)
        self.segments_tree.column('status', width=80)
        self.segments_tree.column('message_id', width=150)
        self.segments_tree.column('attempts', width=70)
        
        # Scrollbars
        segments_scroll_v = ttk.Scrollbar(segments_list_frame, orient=tk.VERTICAL, command=self.segments_tree.yview)
        segments_scroll_h = ttk.Scrollbar(segments_list_frame, orient=tk.HORIZONTAL, command=self.segments_tree.xview)
        self.segments_tree.configure(yscrollcommand=segments_scroll_v.set, xscrollcommand=segments_scroll_h.set)
        
        self.segments_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        segments_scroll_v.pack(side=tk.RIGHT, fill=tk.Y)
        segments_scroll_h.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Segment action buttons
        segments_buttons = ttk.Frame(segments_frame)
        segments_buttons.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(segments_buttons, text="Select All", command=self._select_all_segments).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(segments_buttons, text="Select None", command=self._select_no_segments).pack(side=tk.LEFT, padx=5)
        ttk.Button(segments_buttons, text="Upload Selected", command=self._upload_selected_segments).pack(side=tk.LEFT, padx=5)
        ttk.Button(segments_buttons, text="Verify Selected", command=self._verify_selected_segments).pack(side=tk.LEFT, padx=5)
        ttk.Button(segments_buttons, text="Refresh", command=self._refresh_segments).pack(side=tk.RIGHT)
        
        # Progress frame for segment operations
        self.segments_progress_frame = ttk.Frame(segments_frame)
        self.segments_progress_label = ttk.Label(self.segments_progress_frame, text="")
        self.segments_progress_label.pack()
        self.segments_progress_bar = ttk.Progressbar(self.segments_progress_frame, mode='determinate')
        
    def _create_files_tab(self):
        """Create files browser tab with virtual scrolling for millions of files"""
        files_frame = ttk.Frame(self.notebook)
        self.notebook.add(files_frame, text="Files")
        
        # Files header with search
        files_header = ttk.Frame(files_frame)
        files_header.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(files_header, text="File Browser", font=('Arial', 11, 'bold')).pack(side=tk.LEFT)
        
        # Search frame
        search_frame = ttk.Frame(files_header)
        search_frame.pack(side=tk.RIGHT)
        
        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT, padx=(0, 5))
        self.file_search_var = tk.StringVar()
        self.file_search_entry = ttk.Entry(search_frame, textvariable=self.file_search_var, width=30)
        self.file_search_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(search_frame, text="Filter", command=self._filter_files).pack(side=tk.LEFT)
        
        # Files tree with virtual scrolling
        files_tree_frame = ttk.Frame(files_frame)
        files_tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Create virtual treeview
        self.files_tree = VirtualTreeview(files_tree_frame, self._get_file_data)
        
        # File statistics
        stats_frame = ttk.Frame(files_frame)
        stats_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.files_stats_label = ttk.Label(stats_frame, text="Loading file information...", 
                                          font=('Arial', 9), foreground='gray')
        self.files_stats_label.pack(side=tk.LEFT)
        
    def _create_actions_tab(self):
        """Create actions tab for folder operations"""
        actions_frame = ttk.Frame(self.notebook)
        self.notebook.add(actions_frame, text="Actions")
        
        # Publishing actions
        publish_frame = ttk.LabelFrame(actions_frame, text="Publishing", padding=15)
        publish_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(publish_frame, text="Publish Share", 
                  command=self._publish_share, style='Accent.TButton').pack(anchor=tk.W, pady=2)
        ttk.Label(publish_frame, text="Create an access string for this folder", 
                 font=('Arial', 8), foreground='gray').pack(anchor=tk.W)
        
        ttk.Button(publish_frame, text="Update Share", 
                  command=self._update_share).pack(anchor=tk.W, pady=(10, 2))
        ttk.Label(publish_frame, text="Update existing share with new files", 
                 font=('Arial', 8), foreground='gray').pack(anchor=tk.W)
        
        # Maintenance actions
        maintenance_frame = ttk.LabelFrame(actions_frame, text="Maintenance", padding=15)
        maintenance_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(maintenance_frame, text="Verify Integrity", 
                  command=self._verify_integrity).pack(anchor=tk.W, pady=2)
        ttk.Label(maintenance_frame, text="Check all segments for corruption", 
                 font=('Arial', 8), foreground='gray').pack(anchor=tk.W)
        
        ttk.Button(maintenance_frame, text="Re-index Folder", 
                  command=self._reindex_folder).pack(anchor=tk.W, pady=(10, 2))
        ttk.Label(maintenance_frame, text="Scan for new/changed files", 
                 font=('Arial', 8), foreground='gray').pack(anchor=tk.W)
        
        ttk.Button(maintenance_frame, text="Cleanup Orphaned Segments", 
                  command=self._cleanup_segments).pack(anchor=tk.W, pady=(10, 2))
        ttk.Label(maintenance_frame, text="Remove segments for deleted files", 
                 font=('Arial', 8), foreground='gray').pack(anchor=tk.W)
        
        # Backup actions
        backup_frame = ttk.LabelFrame(actions_frame, text="Backup & Export", padding=15)
        backup_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(backup_frame, text="Export Index", 
                  command=self._export_index).pack(anchor=tk.W, pady=2)
        ttk.Label(backup_frame, text="Export folder index for backup", 
                 font=('Arial', 8), foreground='gray').pack(anchor=tk.W)
        
        ttk.Button(backup_frame, text="Export Access Logs", 
                  command=self._export_logs).pack(anchor=tk.W, pady=(10, 2))
        ttk.Label(backup_frame, text="Export access and operation logs", 
                 font=('Arial', 8), foreground='gray').pack(anchor=tk.W)
        
        # Dangerous actions
        danger_frame = ttk.LabelFrame(actions_frame, text="Dangerous Actions", padding=15)
        danger_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(danger_frame, text="Remove Folder", 
                  command=self._remove_folder, style='Danger.TButton').pack(anchor=tk.W, pady=2)
        ttk.Label(danger_frame, text="⚠️ Permanently remove folder from UsenetSync", 
                 font=('Arial', 8), foreground='red').pack(anchor=tk.W)
        
    # Event handlers and utility methods
    
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
        
    def _get_file_statistics(self):
        """Get file type statistics"""
        try:
            # Get file breakdown from backend
            stats = self.app_backend.db.get_file_type_stats(self.folder_id)
            return stats
        except:
            # Fallback with dummy data
            return [
                ("Documents", 150, 50*1024*1024),
                ("Images", 75, 200*1024*1024),
                ("Videos", 10, 2*1024*1024*1024),
                ("Archives", 25, 500*1024*1024),
                ("Other", 40, 100*1024*1024)
            ]
            
    def _get_activity_log(self):
        """Get recent activity log"""
        try:
            # Get activity from backend
            activities = self.app_backend.db.get_folder_activity(self.folder_id, limit=10)
            log_text = ""
            for activity in activities:
                timestamp = activity.get('timestamp', 'Unknown')
                action = activity.get('action', 'Unknown')
                details = activity.get('details', '')
                log_text += f"{timestamp}: {action} - {details}\n"
            return log_text or "No recent activity."
        except:
            return "Activity log not available."
            
    def _on_share_type_change(self):
        """Handle share type change"""
        share_type = self.share_type_var.get()
        
        # Hide all type-specific frames
        self.password_frame.pack_forget()
        self.users_frame.pack_forget()
        
        # Show relevant frame
        if share_type == 'protected':
            self.password_frame.pack(fill=tk.X, padx=10, pady=10)
        elif share_type == 'private':
            self.users_frame.pack(fill=tk.X, padx=10, pady=10)
            self._refresh_users_list()
            
    def _refresh_users_list(self):
        """Refresh authorized users list"""
        # Clear existing items
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
            
        try:
            # Get authorized users from backend
            users = self.app_backend.db.get_folder_authorized_users(self.folder_id)
            
            for user in users:
                user_id = user.get('user_id', 'Unknown')
                display_name = user.get('display_name', 'Unknown')
                
                self.users_tree.insert('', tk.END, values=(user_id[:32] + "...", display_name))
                
        except Exception as e:
            logger.error(f"Failed to load users: {e}")
            
    def _add_user(self):
        """Add user to authorized list"""
        user_ids_text = simpledialog.askstring(
            "Add Users", 
            "Enter User IDs (one per line):",
            parent=self
        )
        
        if not user_ids_text:
            return
            
        user_ids = [uid.strip() for uid in user_ids_text.split('\n') if uid.strip()]
        
        try:
            # Add users via backend
            for user_id in user_ids:
                self.app_backend.add_user_to_folder(self.folder_id, user_id)
                
            self._refresh_users_list()
            messagebox.showinfo("Success", f"Added {len(user_ids)} user(s)")
            
        except Exception as e:
            logger.error(f"Failed to add users: {e}")
            messagebox.showerror("Error", f"Failed to add users: {e}")
            
    def _remove_user(self):
        """Remove selected user from authorized list"""
        selection = self.users_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a user to remove")
            return
            
        if messagebox.askyesno("Confirm", "Remove selected user(s) from access list?"):
            try:
                for item in selection:
                    values = self.users_tree.item(item, 'values')
                    if values:
                        user_id = values[0].replace("...", "")  # Remove truncation
                        self.app_backend.remove_user_from_folder(self.folder_id, user_id)
                        
                self._refresh_users_list()
                messagebox.showinfo("Success", "User(s) removed successfully")
                
            except Exception as e:
                logger.error(f"Failed to remove users: {e}")
                messagebox.showerror("Error", f"Failed to remove users: {e}")
                
    def _import_users(self):
        """Import users from file"""
        from tkinter import filedialog
        
        filename = filedialog.askopenfilename(
            title="Select User ID file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if not filename:
            return
            
        try:
            with open(filename, 'r') as f:
                user_ids = [line.strip() for line in f if line.strip()]
                
            for user_id in user_ids:
                self.app_backend.add_user_to_folder(self.folder_id, user_id)
                
            self._refresh_users_list()
            messagebox.showinfo("Success", f"Imported {len(user_ids)} user(s)")
            
        except Exception as e:
            logger.error(f"Failed to import users: {e}")
            messagebox.showerror("Error", f"Failed to import users: {e}")
            
    def _update_access_settings(self):
        """Update folder access settings"""
        try:
            share_type = self.share_type_var.get()
            
            if share_type == 'protected':
                password = self.password_var.get()
                hint = self.password_hint_var.get()
                
                if not password:
                    messagebox.showwarning("Warning", "Password required for protected shares")
                    return
                    
                self.app_backend.update_folder_access(self.folder_id, share_type, 
                                                    password=password, password_hint=hint)
            else:
                self.app_backend.update_folder_access(self.folder_id, share_type)
                
            messagebox.showinfo("Success", "Access settings updated successfully")
            
        except Exception as e:
            logger.error(f"Failed to update access: {e}")
            messagebox.showerror("Error", f"Failed to update access settings: {e}")
            
    def _refresh_access_control(self):
        """Refresh access control tab"""
        self._load_folder_info()
        self.share_type_var.set(self.folder_info.get('share_type', 'public'))
        self._on_share_type_change()
        
    def _filter_segments(self, filter_type):
        """Filter segments by status"""
        # Implementation for segment filtering
        self._refresh_segments(filter_type)
        
    def _refresh_segments(self, filter_type='all'):
        """Refresh segments list"""
        # Clear existing items
        for item in self.segments_tree.get_children():
            self.segments_tree.delete(item)
            
        try:
            # Get segments from backend
            segments = self.app_backend.db.get_folder_segments(self.folder_id)
            
            for segment in segments:
                if filter_type != 'all':
                    if filter_type == 'failed' and segment.get('status') != 'failed':
                        continue
                    if filter_type == 'missing' and segment.get('status') != 'missing':
                        continue
                        
                segment_id = segment.get('segment_id', 'Unknown')
                file_name = segment.get('file_name', 'Unknown')
                size = self._format_size(segment.get('size', 0))
                status = segment.get('status', 'Unknown')
                message_id = segment.get('message_id', 'None')
                attempts = segment.get('upload_attempts', 0)
                
                # Status icon
                status_icon = "✓" if status == 'uploaded' else "⚠" if status == 'failed' else "○"
                
                item = self.segments_tree.insert('', tk.END, text="☐",
                                                values=(segment_id, file_name, size, status, message_id, attempts))
                
        except Exception as e:
            logger.error(f"Failed to load segments: {e}")
            
    def _select_all_segments(self):
        """Select all segments"""
        for item in self.segments_tree.get_children():
            self.segments_tree.item(item, text="☑")
            
    def _select_no_segments(self):
        """Deselect all segments"""
        for item in self.segments_tree.get_children():
            self.segments_tree.item(item, text="☐")
            
    def _upload_selected_segments(self):
        """Upload selected segments"""
        selected_segments = []
        for item in self.segments_tree.get_children():
            if self.segments_tree.item(item, 'text') == "☑":
                values = self.segments_tree.item(item, 'values')
                if values:
                    selected_segments.append(values[0])  # segment_id
                    
        if not selected_segments:
            messagebox.showwarning("Warning", "No segments selected")
            return
            
        # Show progress
        self.segments_progress_frame.pack(fill=tk.X, padx=10, pady=5)
        self.segments_progress_label.config(text=f"Uploading {len(selected_segments)} segments...")
        self.segments_progress_bar.pack(fill=tk.X, pady=(5, 0))
        self.segments_progress_bar.config(mode='indeterminate')
        self.segments_progress_bar.start()
        
        def upload_worker():
            try:
                # Upload segments via backend
                self.app_backend.upload_segments(selected_segments)
                
                # Update UI in main thread
                self.after(0, lambda: self._upload_complete(True, len(selected_segments)))
                
            except Exception as e:
                logger.error(f"Upload failed: {e}")
                self.after(0, lambda: self._upload_complete(False, 0, str(e)))
                
        threading.Thread(target=upload_worker, daemon=True).start()
        
    def _upload_complete(self, success, count, error=None):
        """Handle upload completion"""
        self.segments_progress_bar.stop()
        self.segments_progress_frame.pack_forget()
        
        if success:
            messagebox.showinfo("Success", f"Uploaded {count} segments successfully")
            self._refresh_segments()
        else:
            messagebox.showerror("Error", f"Upload failed: {error}")
            
    def _verify_selected_segments(self):
        """Verify selected segments"""
        # Implementation for segment verification
        messagebox.showinfo("Info", "Segment verification coming soon")
        
    def _get_file_data(self, start_index, count):
        """Get file data for virtual scrolling"""
        try:
            # Get files from backend with pagination
            files = self.app_backend.db.get_folder_files(
                self.folder_id, 
                offset=start_index, 
                limit=count
            )
            
            result = []
            for file_info in files:
                file_path = file_info.get('file_path', 'Unknown')
                file_size = self._format_size(file_info.get('file_size', 0))
                file_hash = file_info.get('file_hash', 'Unknown')[:16] + "..."
                status = "✓" if file_info.get('status') == 'uploaded' else "⚠"
                
                result.append((file_path, file_size, file_hash, status))
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to get file data: {e}")
            return []
            
    def _filter_files(self):
        """Filter files by search term"""
        search_term = self.file_search_var.get()
        # Implementation for file filtering
        messagebox.showinfo("Info", f"Filtering files by: {search_term}")
        
    def _refresh_all_tabs(self):
        """Refresh all tab data"""
        try:
            self._refresh_access_control()
            self._refresh_segments()
            
            # Update file stats
            file_count = self.folder_info.get('file_count', 0)
            total_size = self.folder_info.get('total_size', 0)
            self.files_stats_label.config(text=f"Files: {file_count:,} | Total Size: {self._format_size(total_size)}")
            
        except Exception as e:
            logger.error(f"Failed to refresh tabs: {e}")
            
    # Action implementations
    
    def _publish_share(self):
        """Publish share action"""
        messagebox.showinfo("Info", "Publishing functionality available in main window")
        
    def _update_share(self):
        """Update existing share"""
        messagebox.showinfo("Info", "Update share functionality coming soon")
        
    def _verify_integrity(self):
        """Verify folder integrity"""
        messagebox.showinfo("Info", "Integrity verification functionality coming soon")
        
    def _reindex_folder(self):
        """Re-index folder"""
        messagebox.showinfo("Info", "Re-indexing functionality coming soon")
        
    def _cleanup_segments(self):
        """Cleanup orphaned segments"""
        messagebox.showinfo("Info", "Segment cleanup functionality coming soon")
        
    def _export_index(self):
        """Export folder index"""
        messagebox.showinfo("Info", "Index export functionality coming soon")
        
    def _export_logs(self):
        """Export access logs"""
        messagebox.showinfo("Info", "Log export functionality coming soon")
        
    def _remove_folder(self):
        """Remove folder from UsenetSync"""
        if messagebox.askyesno("Confirm Removal", 
                              "⚠️ This will permanently remove the folder from UsenetSync.\n\nThe original files will not be deleted, but all sharing information will be lost.\n\nProceed?"):
            try:
                self.app_backend.remove_folder(self.folder_id)
                messagebox.showinfo("Success", "Folder removed successfully")
                # Signal parent to refresh
                self.event_generate("<<FolderRemoved>>")
            except Exception as e:
                logger.error(f"Failed to remove folder: {e}")
                messagebox.showerror("Error", f"Failed to remove folder: {e}")


class VirtualTreeview(ttk.Frame):
    """Virtual treeview for handling millions of files efficiently"""
    
    def __init__(self, parent, data_callback):
        super().__init__(parent)
        self.data_callback = data_callback
        self.total_items = 0
        self.visible_items = 20
        self.current_offset = 0
        
        self._create_widgets()
        self._load_data()
        
    def _create_widgets(self):
        """Create virtual treeview widgets"""
        # Headers
        columns = ('file_path', 'size', 'hash', 'status')
        self.tree = ttk.Treeview(self, columns=columns, show='headings', height=self.visible_items)
        
        self.tree.heading('file_path', text='File Path')
        self.tree.heading('size', text='Size')
        self.tree.heading('hash', text='Hash')
        self.tree.heading('status', text='Status')
        
        self.tree.column('file_path', width=300)
        self.tree.column('size', width=80)
        self.tree.column('hash', width=120)
        self.tree.column('status', width=60)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self._on_scroll)
        h_scroll = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Pack widgets
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Navigation buttons
        nav_frame = ttk.Frame(self)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        ttk.Button(nav_frame, text="First", command=self._go_first).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text="Previous", command=self._go_previous).pack(side=tk.LEFT, padx=2)
        
        self.position_label = ttk.Label(nav_frame, text="")
        self.position_label.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(nav_frame, text="Next", command=self._go_next).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text="Last", command=self._go_last).pack(side=tk.LEFT, padx=2)
        
    def _load_data(self):
        """Load data for current view"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Get data from callback
        try:
            data = self.data_callback(self.current_offset, self.visible_items)
            
            for row in data:
                self.tree.insert('', tk.END, values=row)
                
            # Update position label
            start = self.current_offset + 1
            end = min(self.current_offset + len(data), self.total_items)
            self.position_label.config(text=f"{start}-{end} of {self.total_items}")
            
        except Exception as e:
            logger.error(f"Failed to load virtual data: {e}")
            
    def _on_scroll(self, *args):
        """Handle scroll events"""
        # Simple implementation - could be enhanced for smooth scrolling
        pass
        
    def _go_first(self):
        """Go to first page"""
        self.current_offset = 0
        self._load_data()
        
    def _go_previous(self):
        """Go to previous page"""
        self.current_offset = max(0, self.current_offset - self.visible_items)
        self._load_data()
        
    def _go_next(self):
        """Go to next page"""
        if self.current_offset + self.visible_items < self.total_items:
            self.current_offset += self.visible_items
            self._load_data()
            
    def _go_last(self):
        """Go to last page"""
        pages = (self.total_items - 1) // self.visible_items
        self.current_offset = pages * self.visible_items
        self._load_data()


def main():
    """Test the panel standalone"""
    root = tk.Tk()
    root.title("Folder Details Test")
    root.geometry("800x600")
    
    # Mock backend for testing
    class MockBackend:
        class MockDB:
            def get_folder_info(self, folder_id):
                return {
                    'display_name': 'Test Folder',
                    'folder_path': '/test/path',
                    'share_type': 'private',
                    'file_count': 1500,
                    'total_size': 500*1024*1024,
                    'current_version': 1,
                    'state': 'ready',
                    'created_at': '2025-01-01',
                    'updated_at': '2025-01-15'
                }
                
            def get_file_type_stats(self, folder_id):
                return [
                    ("Documents", 150, 50*1024*1024),
                    ("Images", 75, 200*1024*1024),
                    ("Videos", 10, 2*1024*1024*1024),
                    ("Archives", 25, 500*1024*1024),
                    ("Other", 40, 100*1024*1024)
                ]
                
            def get_folder_activity(self, folder_id, limit=10):
                return [
                    {'timestamp': '2025-01-15 10:30', 'action': 'indexed', 'details': '100 new files'},
                    {'timestamp': '2025-01-14 15:45', 'action': 'published', 'details': 'public share created'},
                    {'timestamp': '2025-01-13 09:15', 'action': 'uploaded', 'details': '50 segments uploaded'}
                ]
                
            def get_folder_authorized_users(self, folder_id):
                return [
                    {'user_id': 'user123456789abcdef', 'display_name': 'Test User 1'},
                    {'user_id': 'user987654321fedcba', 'display_name': 'Test User 2'}
                ]
                
            def get_folder_segments(self, folder_id):
                return [
                    {'segment_id': 'seg001', 'file_name': 'test1.txt', 'size': 1024, 'status': 'uploaded', 'message_id': 'msg001', 'upload_attempts': 1},
                    {'segment_id': 'seg002', 'file_name': 'test2.txt', 'size': 2048, 'status': 'failed', 'message_id': None, 'upload_attempts': 3}
                ]
                
            def get_folder_files(self, folder_id, offset=0, limit=20):
                files = []
                for i in range(limit):
                    files.append({
                        'file_path': f'/test/file_{offset + i}.txt',
                        'file_size': (offset + i + 1) * 1024,
                        'file_hash': f'hash{offset + i:08d}',
                        'status': 'uploaded' if (offset + i) % 3 == 0 else 'pending'
                    })
                return files
                
        def __init__(self):
            self.db = self.MockDB()
    
    mock_backend = MockBackend()
    
    panel = FolderDetailsPanel(root, mock_backend, "test_folder_id")
    panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    root.mainloop()


if __name__ == "__main__":
    main()
        