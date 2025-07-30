#!/usr/bin/env python3
"""
Run All Database Fixes in Correct Order
This script will fix all the database issues preventing file indexing
"""

import subprocess
import sys
from pathlib import Path

def run_script(script_name, description):
    """Run a Python script and return success status"""
    
    script_path = Path(script_name)
    if not script_path.exists():
        print(f"ERROR: {script_name} not found")
        return False
    
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, timeout=120)
        
        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"SUCCESS: {description} completed")
            return True
        else:
            print(f"ERROR: {description} failed (exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"ERROR: {description} timed out")
        return False
    except Exception as e:
        print(f"ERROR: Could not run {description}: {e}")
        return False

def check_prerequisites():
    """Check that required files exist"""
    
    required_files = [
        "production_db_wrapper.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("ERROR: Missing required files:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    print("OK: All required files found")
    return True

def create_fix_scripts():
    """Create the fix scripts if they don't exist"""
    
    scripts_to_create = [
        ("fix_database_transaction_errors.py", "Fix Database Transaction Errors"),
        ("ensure_database_schema.py", "Ensure Database Schema")
    ]
    
    created_scripts = []
    
    for script_name, description in scripts_to_create:
        if not Path(script_name).exists():
            print(f"WARNING: {script_name} not found")
            print(f"You need to save the '{description}' script as {script_name}")
            created_scripts.append(script_name)
    
    if created_scripts:
        print(f"\nPlease save these scripts first:")
        for script in created_scripts:
            print(f"  - {script}")
        return False
    
    return True

def main():
    """Main function to run all fixes"""
    
    print("=" * 70)
    print("DATABASE FIX AUTOMATION SCRIPT")
    print("=" * 70)
    print("This script will fix all database issues preventing file indexing:")
    print("  1. Transaction conflicts (cannot start transaction within transaction)")
    print("  2. SQL syntax errors (near WHERE)")
    print("  3. Database lock issues")
    print("  4. Missing database schema")
    print("  5. Connection pool improvements")
    print()
    
    # Check prerequisites
    if not check_prerequisites():
        print("\nERROR: Prerequisites not met")
        return 1
    
    # Check fix scripts exist
    if not create_fix_scripts():
        print("\nERROR: Fix scripts not available")
        return 1
    
    print("Starting database fixes...\n")
    
    # Track overall success
    overall_success = True
    
    # Step 1: Fix transaction and SQL errors
    if not run_script("fix_database_transaction_errors.py", 
                     "Fix Transaction and SQL Syntax Errors"):
        overall_success = False
        print("WARNING: Transaction fixes failed, continuing anyway...")
    
    # Step 2: Ensure database schema is complete
    if not run_script("ensure_database_schema.py", 
                     "Ensure Complete Database Schema"):
        overall_success = False
        print("WARNING: Schema creation failed, continuing anyway...")
    
    # Final status
    print(f"\n{'='*70}")
    print("DATABASE FIX SUMMARY")
    print(f"{'='*70}")
    
    if overall_success:
        print("[SUCCESS] All database fixes completed successfully!")
        print()
        print("Fixed issues:")
        print("  [OK] Nested transaction errors")
        print("  [OK] Database lock conflicts")
        print("  [OK] SQL syntax errors")
        print("  [OK] Complete database schema")
        print("  [OK] WAL mode for better concurrency")
        print("  [OK] Optimized database settings")
        print()
        print("[READY] Your file indexing should now work without errors!")
        print()
        print("Next steps:")
        print("  1. Try running your indexing operation again")
        print("  2. Check that files are being indexed successfully")
        print("  3. Monitor the logs for any remaining issues")
        print()
        return 0
    else:
        print("[WARNING] Some fixes encountered issues")
        print()
        print("What to do:")
        print("  1. Review the error messages above")
        print("  2. Try running individual fix scripts manually")
        print("  3. Check that your Python environment is working")
        print("  4. Ensure you have write permissions to the files")
        print()
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        
        if exit_code == 0:
            print("Press Enter to continue...")
        else:
            print("Press Enter to exit...")
        
        input()
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)