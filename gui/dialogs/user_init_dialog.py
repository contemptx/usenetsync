"""
User Initialization Dialog
Handles user profile creation and key management
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Optional

class UserInitDialog:
    """Dialog for user initialization and key generation"""
    
    def __init__(self, parent, backend):
        self.parent = parent
        self.backend = backend
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Initialize User Profile")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + 100,
            parent.winfo_rooty() + 100
        ))
        
        self.create_widgets()
        self.check_existing_user()
        
        # Handle window close
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
    
    def create_widgets(self):
        """Create dialog widgets"""
        # Header
        header_frame = ttk.Frame(self.dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(header_frame, text="User Profile Initialization", 
                 font=('Arial', 14, 'bold')).pack()
        
        # Instructions
        instruction_text = """
Your User Profile contains cryptographic keys for secure file sharing.
Once created, your User ID cannot be changed.
Private keys remain on this system and cannot be exported.
        """
        
        ttk.Label(header_frame, text=instruction_text, 
                 justify=tk.CENTER, wraplength=400).pack(pady=10)
        
        # User info frame
        info_frame = ttk.LabelFrame(self.dialog, text="User Information", padding=15)
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Display name
        ttk.Label(info_frame, text="Display Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.display_name_var = tk.StringVar()
        display_name_entry = ttk.Entry(info_frame, textvariable=self.display_name_var, width=30)
        display_name_entry.grid(row=0, column=1, sticky=tk.W, padx=10)
        display_name_entry.focus()
        
        # Email (optional)
        ttk.Label(info_frame, text="Email (optional):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.email_var = tk.StringVar()
        email_entry = ttk.Entry(info_frame, textvariable=self.email_var, width=30)
        email_entry.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        # Status frame
        self.status_frame = ttk.LabelFrame(self.dialog, text="Status", padding=15)
        self.status_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.status_text = tk.Text(self.status_frame, height=8, wrap=tk.WORD, 
                                  font=('Courier', 9), state=tk.DISABLED)
        status_scroll = ttk.Scrollbar(self.status_frame, orient=tk.VERTICAL, 
                                     command=self.status_text.yview)
        self.status_text.configure(yscrollcommand=status_scroll.set)
        
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        status_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        self.init_button = ttk.Button(button_frame, text="Initialize User Profile", 
                                     command=self.initialize_user, style='Primary.TButton')
        self.init_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Cancel", 
                  command=self.on_cancel).pack(side=tk.RIGHT, padx=5)
    
    def check_existing_user(self):
        """Check if user is already initialized"""
        try:
            if hasattr(self.backend, 'security') and self.backend.security.is_user_initialized():
                user_info = self.backend.security.get_user_info()
                
                self.add_status("User already initialized!")
                self.add_status(f"User ID: {user_info.get('user_id', 'Unknown')}")
                self.add_status(f"Display Name: {user_info.get('display_name', 'Unknown')}")
                self.add_status(f"Created: {user_info.get('created_at', 'Unknown')}")
                self.add_status("")
                self.add_status("You can close this dialog and start using UsenetSync.")
                
                self.init_button.config(text="Re-initialize (Warning: Will lose access to private shares!)")
                
        except Exception as e:
            self.add_status(f"Error checking user status: {e}")
    
    def add_status(self, message):
        """Add message to status display"""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.dialog.update_idletasks()
    
    def initialize_user(self):
        """Initialize user profile"""
        display_name = self.display_name_var.get().strip()
        email = self.email_var.get().strip()
        
        if not display_name:
            messagebox.showerror("Error", "Display name is required")
            return
        
        # Confirm re-initialization
        if hasattr(self.backend, 'security') and self.backend.security.is_user_initialized():
            result = messagebox.askyesnocancel(
                "Re-initialize User", 
                "This will create a new user profile and you will lose access to "
                "all existing private shares. Are you sure you want to continue?"
            )
            if not result:
                return
        
        # Disable button during initialization
        self.init_button.config(state=tk.DISABLED)
        
        # Initialize in background thread
        def init_worker():
            try:
                self.add_status("Starting user initialization...")
                self.add_status("Generating cryptographic keys...")
                
                # Create user
                user_id = self.backend.create_user(display_name, email)
                
                self.add_status("✓ Cryptographic keys generated")
                self.add_status(f"✓ User profile created")
                self.add_status("")
                self.add_status(f"User ID: {user_id}")
                self.add_status(f"Display Name: {display_name}")
                if email:
                    self.add_status(f"Email: {email}")
                self.add_status("")
                self.add_status("IMPORTANT: Save your User ID in a safe place!")
                self.add_status("Your private keys remain on this system only.")
                self.add_status("")
                self.add_status("✓ User initialization complete!")
                
                # Update result
                self.result = {
                    'user_id': user_id,
                    'display_name': display_name,
                    'email': email
                }
                
                # Re-enable button
                self.dialog.after(0, lambda: self.init_button.config(state=tk.NORMAL, text="Close"))
                
            except Exception as e:
                self.add_status(f"✗ Initialization failed: {e}")
                self.dialog.after(0, lambda: self.init_button.config(state=tk.NORMAL))
        
        threading.Thread(target=init_worker, daemon=True).start()
    
    def on_cancel(self):
        """Handle dialog cancellation"""
        self.dialog.destroy()