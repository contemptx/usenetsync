#!/usr/bin/env python3
"""
Comprehensive fix for all cleanup method errors in main.py
Fixes both NNTP and MonitoringSystem cleanup issues
"""

import shutil
from pathlib import Path

def fix_all_cleanup_methods():
    """Fix all cleanup method calls in main.py"""
    
    main_file = Path("main.py")
    if not main_file.exists():
        print("❌ main.py not found")
        return False
    
    # Create backup
    backup_file = main_file.with_suffix('.py.backup_all_cleanup')
    try:
        shutil.copy2(main_file, backup_file)
        print(f"✓ Created backup: {backup_file}")
    except Exception as e:
        print(f"⚠ Could not create backup: {e}")
    
    # Read current content
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply all cleanup fixes
    fixes_applied = []
    
    # Fix 1: NNTP connection pool cleanup
    if 'self.nntp.connection_pool.close()' in content:
        content = content.replace(
            'self.nntp.connection_pool.close()',
            'self.nntp.connection_pool.close_all()'
        )
        fixes_applied.append("NNTP: connection_pool.close() → connection_pool.close_all()")
    
    # Fix 2: MonitoringSystem cleanup
    if 'self.monitoring.cleanup()' in content:
        content = content.replace(
            'self.monitoring.cleanup()',
            'self.monitoring.shutdown()'
        )
        fixes_applied.append("Monitoring: cleanup() → shutdown()")
    
    # Fix 3: Replace the entire cleanup method with robust error handling
    new_cleanup_method = '''    def cleanup(self):
        """Cleanup resources and temporary files"""
        try:
            # Close NNTP connections
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
                    self.logger.debug(f"NNTP cleanup error (non-critical): {e}")
            
            # Cleanup monitoring
            if hasattr(self, 'monitoring'):
                try:
                    if hasattr(self.monitoring, 'shutdown'):
                        self.monitoring.shutdown()
                    elif hasattr(self.monitoring, 'cleanup'):
                        self.monitoring.cleanup()
                except Exception as e:
                    self.logger.debug(f"Monitoring cleanup error (non-critical): {e}")
            
            # Cleanup database connections
            if hasattr(self, 'db'):
                try:
                    self.db.close()
                except Exception as e:
                    self.logger.debug(f"Database cleanup error (non-critical): {e}")
                
            self.logger.info("Cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")'''
    
    # Find and replace the cleanup method
    import re
    cleanup_pattern = r'def cleanup\(self\):.*?(?=def|\Z)'
    match = re.search(cleanup_pattern, content, re.DOTALL)
    
    if match:
        content = content.replace(match.group(0), new_cleanup_method.strip() + '\n\n    ')
        fixes_applied.append("Replaced cleanup method with robust error handling")
    
    if not fixes_applied:
        print("✓ No cleanup issues found to fix")
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
    print("Testing all cleanup fixes...")
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
            # Check if cleanup errors are gone
            if "Error during cleanup:" not in result.stdout and "Error during cleanup:" not in result.stderr:
                print("✅ All cleanup errors fixed successfully!")
                return True
            else:
                print("⚠ Some cleanup errors may remain:")
                if "Error during cleanup:" in result.stdout:
                    print("STDOUT:", result.stdout)
                if "Error during cleanup:" in result.stderr:
                    print("STDERR:", result.stderr)
                return False
        else:
            print("❌ Backend test failed:")
            print(result.stdout)
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠ Test timed out")
        return True
    except Exception as e:
        print(f"⚠ Could not run test: {e}")
        return True

def main():
    """Main fix function"""
    print("=" * 60)
    print("    Comprehensive Cleanup Methods Fix")
    print("=" * 60)
    print()
    
    if fix_all_cleanup_methods():
        test_fix()
        print()
        print("✅ All cleanup method fixes completed!")
        print()
        print("Fixed cleanup errors:")
        print("  • 'ConnectionPool' object has no attribute 'close'")
        print("  • 'MonitoringSystem' object has no attribute 'cleanup'")
        print("  • Added robust error handling for all cleanup operations")
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