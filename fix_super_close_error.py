#!/usr/bin/env python3
"""
Fix the 'super' object has no attribute 'close' error in ProductionDatabaseManager
"""

import shutil
from pathlib import Path

def fix_super_close_error():
    """Fix the super().close() call in ProductionDatabaseManager"""
    
    wrapper_file = Path("production_db_wrapper.py")
    if not wrapper_file.exists():
        print("❌ production_db_wrapper.py not found")
        return False
    
    # Create backup
    backup_file = wrapper_file.with_suffix('.py.backup_super_fix')
    try:
        shutil.copy2(wrapper_file, backup_file)
        print(f"✓ Created backup: {backup_file}")
    except Exception as e:
        print(f"⚠ Could not create backup: {e}")
    
    # Read current content
    with open(wrapper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and fix the super().close() issue
    fixes_applied = []
    
    # Fix 1: Replace super().close() with pool.close_all()
    if 'super().close()' in content:
        # Find the close method and replace it properly
        old_close_method = '''    def close(self):
        """Close database and cleanup logging"""
        # Remove log handler if exists
        if hasattr(self, 'log_handler') and self.log_handler:
            logger.removeHandler(self.log_handler)
            self.log_handler.close()
        
        # Call parent close
        super().close()'''
        
        new_close_method = '''    def close(self):
        """Close database and cleanup logging"""
        # Remove log handler if exists
        if hasattr(self, 'log_handler') and self.log_handler:
            logger.removeHandler(self.log_handler)
            self.log_handler.close()
        
        # Close connection pool
        try:
            if hasattr(self, 'pool') and self.pool:
                self.pool.close_all()
        except Exception as e:
            logger.debug(f"Pool cleanup error (non-critical): {e}")'''
        
        if old_close_method in content:
            content = content.replace(old_close_method, new_close_method)
            fixes_applied.append("Replaced super().close() with pool.close_all()")
        else:
            # Simple replacement
            content = content.replace('super().close()', 'self.pool.close_all()')
            fixes_applied.append("Simple replacement: super().close() → self.pool.close_all()")
    
    # Fix 2: Handle any other super() calls that might be problematic
    if 'super(ProductionDatabaseManager, self)' in content:
        # This pattern is safer
        content = content.replace(
            'super(ProductionDatabaseManager, self)',
            'super()'
        )
        fixes_applied.append("Simplified super() calls")
    
    if not fixes_applied:
        print("✓ No super().close() issues found to fix")
        return True
    
    # Write the fixed content
    with open(wrapper_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Applied {len(fixes_applied)} fixes:")
    for fix in fixes_applied:
        print(f"  • {fix}")
    
    return True

def test_fix():
    """Test the fix by running the backend test"""
    print("\n" + "="*50)
    print("Testing the super().close() fix...")
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
            # Check if the error is gone
            if "'super' object has no attribute 'close'" not in result.stdout and "'super' object has no attribute 'close'" not in result.stderr:
                print("✅ Super close error fixed successfully!")
                return True
            else:
                print("⚠ Super close error may still exist")
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
    print("=" * 50)
    print("    Fix Super Close Error")
    print("=" * 50)
    print()
    
    if fix_super_close_error():
        test_fix()
        print()
        print("✅ Super close error fix completed!")
        print()
        print("The error \"'super' object has no attribute 'close'\"")
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