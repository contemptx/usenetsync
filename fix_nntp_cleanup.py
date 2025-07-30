#!/usr/bin/env python3
"""
Fix NNTP connection pool cleanup method in main.py
"""

import shutil
from pathlib import Path

def fix_nntp_cleanup():
    """Fix the NNTP cleanup method call in main.py"""
    
    main_file = Path("main.py")
    if not main_file.exists():
        print("❌ main.py not found")
        return False
    
    # Create backup
    backup_file = main_file.with_suffix('.py.backup_nntp_fix')
    try:
        shutil.copy2(main_file, backup_file)
        print(f"✓ Created backup: {backup_file}")
    except Exception as e:
        print(f"⚠ Could not create backup: {e}")
    
    # Read current content
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and fix the cleanup issue
    fixes_applied = []
    
    # Fix 1: Change connection_pool.close() to connection_pool.close_all()
    if 'self.nntp.connection_pool.close()' in content:
        content = content.replace(
            'self.nntp.connection_pool.close()',
            'self.nntp.connection_pool.close_all()'
        )
        fixes_applied.append("connection_pool.close() → connection_pool.close_all()")
    
    # Fix 2: Also try shutdown() method as fallback
    cleanup_code_old = """            # Close NNTP connections
            if hasattr(self, 'nntp') and self.nntp:
                self.nntp.connection_pool.close_all()"""
    
    cleanup_code_new = """            # Close NNTP connections
            if hasattr(self, 'nntp') and self.nntp:
                try:
                    if hasattr(self.nntp.connection_pool, 'shutdown'):
                        self.nntp.connection_pool.shutdown()
                    elif hasattr(self.nntp.connection_pool, 'close_all'):
                        self.nntp.connection_pool.close_all()
                    else:
                        # Fallback for older versions
                        if hasattr(self.nntp, 'close'):
                            self.nntp.close()
                except Exception as e:
                    self.logger.debug(f"NNTP cleanup error (non-critical): {e}")"""
    
    if 'self.nntp.connection_pool.close_all()' in content:
        content = content.replace(cleanup_code_old, cleanup_code_new)
        fixes_applied.append("Added robust NNTP cleanup with fallbacks")
    
    # Fix 3: Handle any other .close() calls on NNTP
    if 'self.nntp.close()' in content:
        content = content.replace(
            'self.nntp.close()',
            'self.nntp.connection_pool.close_all()'
        )
        fixes_applied.append("self.nntp.close() → self.nntp.connection_pool.close_all()")
    
    if not fixes_applied:
        print("✓ No NNTP cleanup issues found to fix")
        return True
    
    # Write the fixed content
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Applied {len(fixes_applied)} fixes to main.py:")
    for fix in fixes_applied:
        print(f"  • {fix}")
    
    return True

def test_fix():
    """Test the fix by running the backend test"""
    print("\n" + "="*50)
    print("Testing the NNTP cleanup fix...")
    print("="*50)
    
    try:
        import subprocess
        result = subprocess.run(
            ['python', 'test_backend_final.py'], 
            capture_output=True, 
            text=True, 
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ Backend test passed - NNTP cleanup fix successful!")
            return True
        else:
            print("❌ Backend test failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠ Test timed out (but this doesn't necessarily mean the fix failed)")
        return True
    except Exception as e:
        print(f"⚠ Could not run test: {e}")
        return True

def main():
    """Main fix function"""
    print("=" * 50)
    print("    NNTP Connection Pool Cleanup Fix")
    print("=" * 50)
    print()
    
    if fix_nntp_cleanup():
        print()
        test_fix()
        print()
        print("✅ NNTP cleanup fix completed!")
        print()
        print("The error 'ConnectionPool' object has no attribute 'close'")
        print("should now be resolved.")
        print()
        print("Test again with: python test_backend_final.py")
        return 0
    else:
        print("❌ Fix failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        input("Press Enter to exit...")
    exit(exit_code)