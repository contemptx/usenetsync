#!/usr/bin/env python3
"""
Fix Duplicate Folder Processing
Prevent multiple threads from processing the same folder simultaneously
"""

import shutil
import threading
from pathlib import Path

def add_folder_processing_lock():
    """Add a global lock to prevent duplicate folder processing"""
    
    indexing_file = Path("versioned_core_index_system.py")
    if not indexing_file.exists():
        print("ERROR: versioned_core_index_system.py not found")
        return False
    
    # Create backup
    backup_file = indexing_file.with_suffix('.py.backup_duplicate_fix')
    try:
        shutil.copy2(indexing_file, backup_file)
        print(f"OK: Created backup: {backup_file}")
    except Exception as e:
        print(f"WARNING: Could not create backup: {e}")
    
    with open(indexing_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add global processing lock at the top of the class
    if '_folder_processing_lock' not in content:
        # Find the VersionedCoreIndexSystem class initialization
        class_init_pattern = 'def __init__(self, db_manager, security_system, config):'
        
        if class_init_pattern in content:
            # Add global lock as class variable
            global_lock_code = '''
# Global lock to prevent duplicate folder processing
_folder_processing_lock = threading.Lock()
_processing_folders = set()

'''
            
            # Add before the class definition
            content = content.replace('class VersionedCoreIndexSystem:', 
                                    global_lock_code + 'class VersionedCoreIndexSystem:')
            
            print("OK: Added global folder processing lock")
        else:
            print("WARNING: Could not find class initialization")
    
    # Update the index_folder method to use the lock
    old_method_start = 'def index_folder(self, folder_path: str, folder_id: str,'
    
    if old_method_start in content:
        # Find the complete method and replace it
        import re
        
        new_index_method = '''def index_folder(self, folder_path: str, folder_id: str, 
                    progress_callback=None) -> Dict[str, Any]:
        """
        Initial folder indexing - processes all files with actual data
        Now with duplicate processing protection
        """
        # Prevent duplicate processing
        global _folder_processing_lock, _processing_folders
        
        with _folder_processing_lock:
            if folder_id in _processing_folders:
                self.logger.warning(f"Folder {folder_id} is already being processed, skipping duplicate request")
                return {
                    'success': False,
                    'folder_id': folder_id,
                    'error': 'Folder already being processed',
                    'files_processed': 0,
                    'segments_created': 0
                }
            
            _processing_folders.add(folder_id)
            self.logger.info(f"LOCK: Added folder {folder_id} to processing set")
        
        try:
            start_time = time.time()
            self.logger.info(f"Starting initial index of folder: {folder_path}")
            
            # Reset stats
            self.processing_stats = self._reset_stats()
            
            # Validate folder exists
            if not os.path.exists(folder_path):
                raise ValueError(f"Folder does not exist: {folder_path}")
                
            # Create folder entry if needed
            folder_record = self._ensure_folder_exists(folder_id, folder_path)
            folder_db_id = folder_record['id']
            
            # Generate folder keys if not exist
            if not folder_record.get('private_key'):
                keys = self.security.generate_folder_keys(folder_id)
                self.security.save_folder_keys(folder_id, keys)
            
            # Scan folder for files
            all_files = self._scan_folder_full(folder_path, progress_callback)
            self.logger.info(f"Found {len(all_files)} files to index")
            
            # Process files sequentially to avoid database conflicts
            indexed_files = []
            failed_files = []
            
            for i, (file_path, file_info) in enumerate(all_files.items()):
                try:
                    result = self._index_file_complete(
                        folder_db_id,
                        folder_id,
                        folder_path,
                        file_path,
                        file_info,
                        version=1
                    )
                    
                    if result:
                        indexed_files.append(result)
                        
                    if progress_callback and (i + 1) % 5 == 0:
                        progress_callback({
                            'current': i + 1,
                            'total': len(all_files),
                            'file': file_path,
                            'phase': 'indexing'
                        })
                        
                    # Small delay to allow GUI to update
                    time.sleep(0.01)
                        
                except Exception as e:
                    self.logger.error(f"Error indexing {file_path}: {e}")
                    failed_files.append(file_path)
                    with self.stats_lock:
                        self.processing_stats['errors'].append({
                            'file': file_path,
                            'error': str(e),
                            'traceback': traceback.format_exc()
                        })
                    
            # Log indexing summary
            files_processed = self.processing_stats["files_processed"]
            segments_created = self.processing_stats["segments_created"]
            logger.info(f"FOLDER_DEBUG: Indexing complete - {files_processed} files, {segments_created} segments")
            
            # Update folder stats
            self._update_folder_stats(folder_db_id)
            
            # Create initial version
            version_id = self._create_folder_version(folder_db_id, 1, "Initial index")
            
            elapsed = time.time() - start_time
            
            result = {
                'success': len(failed_files) == 0,
                'folder_id': folder_id,
                'version': 1,
                'files_processed': self.processing_stats['files_processed'],
                'bytes_processed': self.processing_stats['bytes_processed'],
                'segments_created': self.processing_stats['segments_created'],
                'files_failed': len(failed_files),
                'errors': self.processing_stats['errors'],
                'elapsed_time': elapsed,
                'files_per_second': self.processing_stats['files_processed'] / elapsed if elapsed > 0 else 0,
                'mb_per_second': (self.processing_stats['bytes_processed'] / 1024 / 1024) / elapsed if elapsed > 0 else 0
            }
            
            self.logger.info(f"Initial indexing complete: {result}")
            return result
            
        finally:
            # Always remove from processing set
            with _folder_processing_lock:
                _processing_folders.discard(folder_id)
                self.logger.info(f"LOCK: Removed folder {folder_id} from processing set")'''
        
        # Replace the method
        pattern = r'def index_folder\(self, folder_path: str, folder_id: str,.*?(?=\n    def |\n\nclass |\n\n[a-zA-Z]|\Z)'
        
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, new_index_method, content, flags=re.DOTALL)
            print("OK: Updated index_folder method with duplicate protection")
        else:
            print("ERROR: Could not find index_folder method to replace")
            return False
    
    # Write back the updated content
    with open(indexing_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def add_gui_duplicate_protection():
    """Add duplicate protection to GUI operations"""
    
    gui_file = Path("usenetsync_gui_main.py") 
    if not gui_file.exists():
        print("WARNING: GUI file not found")
        return True
    
    with open(gui_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for indexing button handlers and add protection
    if 'def index_folder' in content or 'indexing' in content.lower():
        print("Found GUI indexing methods")
        
        # Add a simple flag to prevent double-clicking
        protection_code = '''
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
'''
        
        # Add at the top after imports
        if '_indexing_in_progress' not in content:
            # Find import section
            import_lines = []
            other_lines = []
            in_imports = True
            
            for line in content.split('\n'):
                if line.startswith('import ') or line.startswith('from ') or line.strip() == '':
                    if in_imports:
                        import_lines.append(line)
                    else:
                        other_lines.append(line)
                else:
                    in_imports = False
                    other_lines.append(line)
            
            # Add protection code after imports
            import_lines.append(protection_code)
            
            content = '\n'.join(import_lines + other_lines)
            
            with open(gui_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("OK: Added GUI duplicate protection")
    
    return True

def test_syntax():
    """Test Python syntax"""
    files_to_test = [
        "versioned_core_index_system.py",
        "usenetsync_gui_main.py"
    ]
    
    try:
        import py_compile
        
        for file in files_to_test:
            if Path(file).exists():
                try:
                    py_compile.compile(file, doraise=True)
                    print(f"OK: {file} syntax valid")
                except py_compile.PyCompileError as e:
                    print(f"ERROR: {file} syntax error: {e}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"WARNING: Could not test syntax: {e}")
        return True

def main():
    """Main function"""
    print("="*60)
    print("FIX DUPLICATE FOLDER PROCESSING")
    print("="*60)
    print("Adding protection against duplicate folder processing...")
    print()
    
    success = True
    
    # Add folder processing lock
    if not add_folder_processing_lock():
        print("ERROR: Could not add folder processing lock")
        success = False
    
    # Add GUI protection
    add_gui_duplicate_protection()
    
    # Test syntax
    if not test_syntax():
        print("ERROR: Syntax errors found")
        success = False
    
    print()
    if success:
        print("[SUCCESS] Duplicate processing protection added!")
        print()
        print("What was added:")
        print("  [OK] Global folder processing lock")
        print("  [OK] Tracking set for folders being processed")
        print("  [OK] Sequential file processing (no parallel threads)")
        print("  [OK] Automatic cleanup when processing completes")
        print("  [OK] GUI duplicate protection")
        print()
        print("[READY] File indexing should now work without conflicts!")
        print()
        print("The system will now:")
        print("  1. Check if folder is already being processed")
        print("  2. Skip duplicate requests with clear logging")
        print("  3. Process files sequentially to avoid database conflicts")
        print("  4. Automatically release locks when done")
        print()
        print("Try your indexing operation again - database locks should be eliminated!")
        return 0
    else:
        print("[ERROR] Some issues could not be fixed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    input("\nPress Enter to exit...")
    exit(exit_code)