#!/usr/bin/env python3
"""
Git Status Diagnostic Script
Helps diagnose and fix Git repository issues
"""

import subprocess
import os
from pathlib import Path

def run_command(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def main():
    print("Git Repository Diagnostic")
    print("=" * 50)
    
    # Check current directory
    print(f"\nCurrent directory: {os.getcwd()}")
    
    # Check Git status
    print("\n1. Git Status:")
    print("-" * 30)
    code, stdout, stderr = run_command("git status")
    if code == 0:
        print(stdout)
    else:
        print(f"Error: {stderr}")
    
    # Check for .git directory
    if Path(".git").exists():
        print("\n✓ Git repository exists")
    else:
        print("\n✗ No Git repository found")
    
    # Check tracked files
    print("\n2. Tracked Files:")
    print("-" * 30)
    code, stdout, stderr = run_command("git ls-files")
    if stdout:
        print(f"Files already tracked: {len(stdout.splitlines())}")
        print("First 10 files:")
        for line in stdout.splitlines()[:10]:
            print(f"  - {line}")
    else:
        print("No files tracked yet")
    
    # Check untracked files
    print("\n3. Untracked Files:")
    print("-" * 30)
    code, stdout, stderr = run_command("git status --porcelain")
    if stdout:
        untracked = [line for line in stdout.splitlines() if line.startswith("??")]
        if untracked:
            print(f"Untracked files: {len(untracked)}")
            print("First 10 untracked files:")
            for line in untracked[:10]:
                print(f"  - {line[3:]}")
        else:
            print("No untracked files")
    else:
        print("Working directory clean")
    
    # List all Python files
    print("\n4. Python Files in Directory:")
    print("-" * 30)
    py_files = list(Path(".").glob("*.py"))
    print(f"Found {len(py_files)} Python files")
    for f in py_files[:10]:
        print(f"  - {f}")
    
    # Check for .gitignore
    print("\n5. .gitignore Status:")
    print("-" * 30)
    if Path(".gitignore").exists():
        print("✓ .gitignore exists")
        with open(".gitignore", "r") as f:
            lines = f.readlines()
        print(f"  Contains {len(lines)} lines")
    else:
        print("✗ No .gitignore found")
    
    # Check remote
    print("\n6. Git Remote:")
    print("-" * 30)
    code, stdout, stderr = run_command("git remote -v")
    if stdout:
        print(stdout)
    else:
        print("No remote configured")
    
    # Suggest fixes
    print("\n7. Suggested Actions:")
    print("-" * 30)
    
    # Check if we need to add files
    code, stdout, stderr = run_command("git status --porcelain")
    if stdout:
        print("• You have uncommitted changes. Run:")
        print("  git add .")
        print("  git commit -m 'Initial commit'")
        print("  git push -u origin main")
    else:
        # Check if we have any commits
        code, stdout, stderr = run_command("git log --oneline -1")
        if code != 0:
            print("• No commits yet. Add files first:")
            print("  git add .")
            print("  git commit -m 'Initial commit'")
        else:
            print("• Repository has commits. Try pushing:")
            print("  git push -u origin main")
            print("  (or 'master' if that's your branch name)")
    
    # Alternative manual commands
    print("\n8. Manual Git Commands to Try:")
    print("-" * 30)
    print("# Force add all files (ignoring .gitignore):")
    print("git add -f .")
    print("\n# Or add specific file types:")
    print("git add *.py")
    print("git add requirements.txt")
    print("git add setup.py")
    print("git add README.md")
    print("\n# Check what would be added:")
    print("git add --dry-run .")
    print("\n# If files are already committed, just push:")
    print("git push -u origin main")

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")
