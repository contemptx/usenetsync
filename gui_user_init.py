#!/usr/bin/env python3
"""
UsenetSync GUI - User Initialization Dialog
Handles one-time user setup with secure key generation
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class UserInitDialog:
    """Dialog for user initialization and management"""
    
    def __init__(self, parent, app_backend):
        self.parent = parent
        self.app_backend = app_backend
        self.result = None
        
        # Create modal dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("User Initialization")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(False, False)
        
        # Center dialog
        self._center_dialog()
        
        # Check if user is already initialized
        self.user_initialized = self.app_backend.user.is_initialized() if self.app_backend else False
        
        self._create_widgets()
        
        # Focus on dialog
        self.dialog.focus_set()
        
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
        
        if self.user_initialized:
            self._create_existing_user_view(main_frame)
        else:
            self._create_new_user_view(main_frame)
            
    def _create_new_user_view(self, parent):
        """Create view for new user initialization"""
        # Title
        title_label = ttk.Label(parent, text="Initialize User Profile", 
                               font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # Description
        desc_text = """Welcome to UsenetSync!

This is a one-time setup to create your secure user profile.

Your User ID will be generated automatically and cannot be changed later. This ID is used to identify you in private shares and for secure key exchange.

IMPORTANT: Your private keys will be stored securely on this system and cannot be exported or recovered if lost."""
        
        desc_label = ttk.Label(parent, text=desc_text, wraplength=450, justify=tk.LEFT)
        desc_label.pack(pady=(0, 20))
        
        # Display name input
        name_frame = ttk.LabelFrame(parent, text="Display Name (Optional)", padding=10)
        name_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=self.name_var, font=('Arial', 10))
        name_entry.pack(fill=tk.X)
        
        name_help = ttk.Label(name_frame, text="Friendly name for your profile (can be changed later)", 
                             font=('Arial', 8), foreground='gray')
        name_help.pack(anchor=tk.W, pady=(5, 0))
        
        # Security notice
        security_frame = ttk.LabelFrame(parent, text="Security Notice", padding=10)
        security_frame.pack(fill=tk.X, pady=(0, 20))
        
        security_text = """🔒 Your User ID and private keys will be generated using cryptographically secure methods.

⚠️ This process cannot be undone or repeated. Your User ID is permanent.

✅ Your private keys remain on this system and are never transmitted."""
        
        security_label = ttk.Label(security_frame, text=security_text, wraplength=430, 
                                  justify=tk.LEFT, font=('Arial', 9))
        security_label.pack()
        
        # Progress bar (initially hidden)
        self.progress_frame = ttk.Frame(parent)
        self.progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_label = ttk.Label(self.progress_frame, text="", font=('Arial', 9))
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        
        # Buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(side=tk.BOTTOM, pady=(20, 0))
        
        self.init_button = ttk.Button(button_frame, text="Initialize User Profile", 
                                     command=self._initialize_user, style='Accent.TButton')
        self.init_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Cancel", 
                  command=self.dialog.destroy).pack(side=tk.LEFT)
        
        # Focus on name entry
        name_entry.focus_set()
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self._initialize_user())
        
    def _create_existing_user_view(self, parent):
        """Create view for existing user"""
        try:
            user_id = self.app_backend.user.get_user_id()
            display_name = self.app_backend.user.get_display_name()
            
            # Title
            title_label = ttk.Label(parent, text="User Profile", font=('Arial', 14, 'bold'))
            title_label.pack(pady=(0, 20))
            
            # User info frame
            info_frame = ttk.LabelFrame(parent, text="Current User", padding=15)
            info_frame.pack(fill=tk.X, pady=(0, 20))
            
            # User ID
            ttk.Label(info_frame, text="User ID:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
            
            id_frame = ttk.Frame(info_frame)
            id_frame.pack(fill=tk.X, pady=(5, 15))
            
            id_text = tk.Text(id_frame, height=3, wrap=tk.WORD, font=('Courier', 9), 
                             state=tk.DISABLED, bg='#f0f0f0')
            id_text.pack(fill=tk.X)
            
            id_text.config(state=tk.NORMAL)
            id_text.insert(tk.END, user_id)
            id_text.config(state=tk.DISABLED)
            
            # Display name
            ttk.Label(info_frame, text="Display Name:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
            
            self.name_var = tk.StringVar(value=display_name or "")
            name_entry = ttk.Entry(info_frame, textvariable=self.name_var, font=('Arial', 10))
            name_entry.pack(fill=tk.X, pady=(5, 10))
            
            # Update button for name
            ttk.Button(info_frame, text="Update Display Name", 
                      command=self._update_display_name).pack(anchor=tk.W)
            
            # Statistics frame
            stats_frame = ttk.LabelFrame(parent, text="Statistics", padding=15)
            stats_frame.pack(fill=tk.X, pady=(0, 20))
            
            # Get user stats
            try:
                folders = self.app_backend.db.get_indexed_folders()
                folder_count = len(folders)
                
                total_files = sum(f.get('file_count', 0) for f in folders)
                total_size = sum(f.get('total_size', 0) for f in folders)
                
                stats_text = f"""Indexed Folders: {folder_count}
Total Files: {total_files:,}
Total Size: {self._format_size(total_size)}"""
                
                ttk.Label(stats_frame, text=stats_text, font=('Arial', 10)).pack(anchor=tk.W)
                
            except Exception as e:
                ttk.Label(stats_frame, text=f"Error loading statistics: {e}", 
                         foreground='red').pack(anchor=tk.W)
            
            # Warning about User ID
            warning_frame = ttk.LabelFrame(parent, text="Important", padding=15)
            warning_frame.pack(fill=tk.X, pady=(0, 20))
            
            warning_text = """⚠️ Your User ID is permanent and cannot be changed.

🔒 Your private keys are stored securely on this system.

❌ User ID and private keys cannot be exported or recovered."""
            
            ttk.Label(warning_frame, text=warning_text, wraplength=430, 
                     justify=tk.LEFT, font=('Arial', 9), foreground='#d6401e').pack()
            
            # Buttons
            button_frame = ttk.Frame(parent)
            button_frame.pack(side=tk.BOTTOM, pady=(20, 0))
            
            def copy_user_id():
                parent.clipboard_clear()
                parent.clipboard_append(user_id)
                messagebox.showinfo("Copied", "User ID copied to clipboard!")
                
            ttk.Button(button_frame, text="Copy User ID", 
                      command=copy_user_id).pack(side=tk.LEFT, padx=(0, 10))
            
            ttk.Button(button_frame, text="Close", 
                      command=self.dialog.destroy).pack(side=tk.LEFT)
            
        except Exception as e:
            logger.error(f"Error creating existing user view: {e}")
            
            # Fallback error view
            error_label = ttk.Label(parent, text=f"Error loading user profile: {e}", 
                                   foreground='red', wraplength=450)
            error_label.pack(pady=20)
            
            ttk.Button(parent, text="Close", 
                      command=self.dialog.destroy).pack(pady=10)
            
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
        
    def _initialize_user(self):
        """Initialize new user in background thread"""
        if not self.app_backend:
            messagebox.showerror("Error", "Backend not available")
            return
            
        display_name = self.name_var.get().strip()
        
        # Disable button and show progress
        self.init_button.config(state='disabled')
        self.progress_label.config(text="Generating secure User ID and cryptographic keys...")
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        self.progress_bar.start()
        
        def init_worker():
            try:
                # Initialize user with backend
                user_id = self.app_backend.initialize_user(display_name if display_name else None)
                
                # Update UI in main thread
                self.dialog.after(0, lambda: self._init_success(user_id))
                
            except Exception as e:
                logger.error(f"User initialization failed: {e}")
                self.dialog.after(0, lambda: self._init_failed(str(e)))
                
        threading.Thread(target=init_worker, daemon=True).start()
        
    def _init_success(self, user_id):
        """Handle successful initialization"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        
        # Show success message
        success_text = f"""✅ User Profile Created Successfully!

Your User ID: {user_id[:16]}...

This ID is permanent and uniquely identifies you in the UsenetSync network. Your private keys have been generated and stored securely on this system.

You can now index folders and create shares!"""
        
        messagebox.showinfo("Success", success_text)
        
        # Close dialog
        self.result = user_id
        self.dialog.destroy()
        
    def _init_failed(self, error_msg):
        """Handle failed initialization"""
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.init_button.config(state='normal')
        self.progress_label.config(text="")
        
        messagebox.showerror("Initialization Failed", 
                           f"Failed to initialize user profile:\n\n{error_msg}")
        
    def _update_display_name(self):
        """Update display name"""
        if not self.app_backend:
            return
            
        new_name = self.name_var.get().strip()
        
        try:
            self.app_backend.user.set_display_name(new_name)
            messagebox.showinfo("Success", "Display name updated successfully!")
            
        except Exception as e:
            logger.error(f"Failed to update display name: {e}")
            messagebox.showerror("Error", f"Failed to update display name:\n{e}")


def main():
    """Test the dialog standalone"""
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    # Mock backend for testing
    class MockBackend:
        class MockUser:
            def is_initialized(self):
                return False
                
            def get_user_id(self):
                return "test_user_id_1234567890abcdef" * 2
                
            def get_display_name(self):
                return "Test User"
                
            def set_display_name(self, name):
                pass
                
        def __init__(self):
            self.user = self.MockUser()
            
        def initialize_user(self, name):
            import time
            time.sleep(2)  # Simulate work
            return "test_user_id_1234567890abcdef" * 2
            
        class MockDB:
            def get_indexed_folders(self):
                return [
                    {'file_count': 100, 'total_size': 1024*1024*100},
                    {'file_count': 50, 'total_size': 1024*1024*50}
                ]
                
        def __init__(self):
            self.user = self.MockUser()
            self.db = self.MockDB()
    
    mock_backend = MockBackend()
    
    dialog = UserInitDialog(root, mock_backend)
    root.wait_window(dialog.dialog)
    
    if dialog.result:
        print(f"User initialized: {dialog.result}")
    else:
        print("Dialog cancelled")


if __name__ == "__main__":
    main()
