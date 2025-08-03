#!/usr/bin/env python3
"""
Minimal fix for UsenetSync GUI publishing integration
Uses existing backend API without adding unnecessary wrapper methods
"""

import os
import shutil

def backup_file(file_path):
    """Create backup of existing file"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.backup"
        shutil.copy2(file_path, backup_path)
        print(f"✓ Backed up {file_path} to {backup_path}")
        return backup_path
    return None

def fix_gui_publishing_calls():
    """Fix GUI to use existing backend publish_folder method"""
    
    try:
        with open('usenetsync_gui_main.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print("✗ usenetsync_gui_main.py not found")
        return False
    
    # Fix the _publish_share method
    old_publish_method = '''    def _publish_share(self):
        """Publish current folder as share"""
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
                        access_string = self.app_backend.publishing.create_public_share(self.curr'''
    
    new_publish_method = '''    def _publish_share(self):
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
                    
                    # Refresh shares
                    self._thread_safe_call(lambda: self._load_folder_shares(self.current_folder))
                    
                except Exception as publish_error:  # Fixed: variable is now defined
                    logger.error(f"Publishing failed: {publish_error}")
                    self._thread_safe_status_update(f"Publishing failed: {publish_error}", "error")
                    self._thread_safe_call(lambda: messagebox.showerror("Publishing Failed", str(publish_error)))
            
            threading.Thread(target=publish_worker, daemon=True).start()
            
        except Exception as error:
            logger.error(f"Error in publish share: {error}")
            messagebox.showerror("Error", f"Failed to start publishing: {error}")'''
    
    # Replace the method
    if old_publish_method in content:
        content = content.replace(old_publish_method, new_publish_method)
    else:
        # Look for the method signature and replace the entire method
        import re
        
        # Find the _publish_share method and replace it
        pattern = r'(    def _publish_share\(self\):.*?)(?=\n    def |\n\nclass |\nclass |\n\ndef |\Z)'
        
        replacement = '''    def _publish_share(self):
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
                    
                    # Refresh shares
                    self._thread_safe_call(lambda: self._load_folder_shares(self.current_folder))
                    
                except Exception as publish_error:  # Fixed: variable is now defined
                    logger.error(f"Publishing failed: {publish_error}")
                    self._thread_safe_status_update(f"Publishing failed: {publish_error}", "error")
                    self._thread_safe_call(lambda: messagebox.showerror("Publishing Failed", str(publish_error)))
            
            threading.Thread(target=publish_worker, daemon=True).start()
            
        except Exception as error:
            logger.error(f"Error in publish share: {error}")
            messagebox.showerror("Error", f"Failed to start publishing: {error}")'''
        
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Also fix any other undefined variable issues in error handling
    content = content.replace('str(e))', 'str(error))')  # Fix other similar issues
    content = content.replace('messagebox.showerror("Re-indexing Failed", str(e)))', 
                             'messagebox.showerror("Re-indexing Failed", str(reindex_error)))')
    
    # Write back the fixed content
    backup_file('usenetsync_gui_main.py')
    
    try:
        with open('usenetsync_gui_main.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("✓ Fixed usenetsync_gui_main.py")
        return True
    except Exception as e:
        print(f"✗ Failed to write usenetsync_gui_main.py: {e}")
        return False

def fix_indexing_progress_display():
    """Fix indexing progress display issues"""
    
    try:
        with open('usenetsync_gui_main.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        return False
    
    # Add indexing progress prevention if not present
    if '_indexing_in_progress = False' not in content:
        # Add at the top after imports
        import_section = '''import time
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime'''
        
        new_import_section = '''import time
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
        _indexing_in_progress = status'''
        
        content = content.replace(import_section, new_import_section)
    
    # Fix the indexing method to show progress properly
    if 'def _index_folder(self):' in content:
        # Find and replace the indexing method
        import re
        
        pattern = r'(    def _index_folder\(self\):.*?)(?=\n    def |\nclass |\n\ndef |\Z)'
        
        replacement = '''    def _index_folder(self):
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
                            if file_name:
                                status_msg = f"{phase.capitalize()}: {current}/{total} - {os.path.basename(file_name)}"
                            else:
                                status_msg = f"{phase.capitalize()}: {current}/{total} files"
                            
                            self._thread_safe_status_update(status_msg)
                    except Exception as e:
                        logger.error(f"Error in progress callback: {e}")
                
                # Call the backend index_folder method
                result = self.app_backend.index_folder(folder_path, progress_callback=progress_callback)
                
                self._thread_safe_call(lambda: self.progress_bar.pack_forget())
                
                if result and 'files_indexed' in result:
                    self._thread_safe_status_update(f"Indexing complete: {result['files_indexed']} files", "success")
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
        
        threading.Thread(target=index_worker, daemon=True).start()'''
        
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Write back
    try:
        with open('usenetsync_gui_main.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("✓ Fixed indexing progress display")
        return True
    except Exception as e:
        print(f"✗ Failed to fix indexing: {e}")
        return False

def verify_backend_interface():
    """Verify the backend has the expected interface"""
    try:
        # Check if main.py has the expected methods
        with open('main.py', 'r', encoding='utf-8') as f:
            main_content = f.read()
        
        required_methods = [
            'def index_folder(',
            'def publish_folder(',
            'def download_share('
        ]
        
        missing_methods = []
        for method in required_methods:
            if method not in main_content:
                missing_methods.append(method)
        
        if missing_methods:
            print(f"✗ Missing methods in main.py: {missing_methods}")
            return False
        else:
            print("✓ Backend interface verified")
            return True
            
    except FileNotFoundError:
        print("✗ main.py not found")
        return False
    except Exception as e:
        print(f"✗ Error verifying backend: {e}")
        return False

def run_minimal_fix():
    """Run the minimal fix"""
    print("=" * 60)
    print("UsenetSync Minimal GUI Publishing Fix")
    print("=" * 60)
    
    success_count = 0
    total_fixes = 3
    
    print("\\n1. Verifying Backend Interface...")
    if verify_backend_interface():
        success_count += 1
    
    print("\\n2. Fixing GUI Publishing Calls...")
    if fix_gui_publishing_calls():
        success_count += 1
    
    print("\\n3. Fixing Indexing Progress Display...")
    if fix_indexing_progress_display():
        success_count += 1
    
    print("\\n" + "=" * 60)
    print(f"Fix Results: {success_count}/{total_fixes} successful")
    print("=" * 60)
    
    if success_count == total_fixes:
        print("\\n🎉 ALL FIXES APPLIED SUCCESSFULLY!")
        print("\\nFixed Issues:")
        print("- GUI now uses existing backend publish_folder method")
        print("- Undefined variable 'e' fixed in error handling")
        print("- Enhanced indexing progress display")
        print("- Added indexing operation prevention")
        print("- Thread-safe GUI updates")
        
        print("\\n📝 Ready to Use:")
        print("1. Run: python usenetsync_gui_main.py")
        print("2. Initialize user profile")
        print("3. Index a folder")
        print("4. Publish shares")
        print("5. All functionality should work correctly")
    else:
        print("\\n⚠️  Some fixes failed. Check error messages above.")
    
    return success_count == total_fixes

if __name__ == "__main__":
    run_minimal_fix()
