#!/usr/bin/env python3
"""
Automated GitHub Workflow for UsenetSync
Integrates AI assistance with GitHub operations
"""

import os
import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

class GitHubWorkflow:
    """Manages GitHub operations and AI integration"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.git_exe = self._find_git()
        self.config_file = self.repo_path / ".github_workflow.json"
        self.load_config()
        
    def _find_git(self) -> str:
        """Find Git executable"""
        git_paths = [
            "git",
            r"C:\Program Files\Git\bin\git.exe",
            r"C:\Program Files (x86)\Git\bin\git.exe",
        ]
        
        for git_path in git_paths:
            try:
                result = subprocess.run([git_path, "--version"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return git_path
            except:
                continue
        
        raise RuntimeError("Git not found. Please install Git.")
    
    def load_config(self):
        """Load workflow configuration"""
        default_config = {
            "repository": {
                "url": "https://github.com/contemptx/usenetsync.git",
                "branch": "master",
                "remote": "origin"
            },
            "workflow": {
                "auto_commit": False,
                "check_before_commit": True,
                "run_tests": True,
                "update_changelog": True,
                "semantic_commits": True
            },
            "ai_integration": {
                "review_changes": True,
                "suggest_commit_message": True,
                "check_security": True,
                "update_documentation": True
            }
        }
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save workflow configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def git_command(self, args: List[str]) -> Tuple[int, str, str]:
        """Execute a git command"""
        cmd = [self.git_exe] + args
        result = subprocess.run(cmd, capture_output=True, text=True, 
                              cwd=self.repo_path)
        return result.returncode, result.stdout, result.stderr
    
    def get_status(self) -> Dict:
        """Get current repository status"""
        code, stdout, stderr = self.git_command(['status', '--porcelain'])
        
        files = {
            'modified': [],
            'added': [],
            'deleted': [],
            'untracked': []
        }
        
        if code == 0 and stdout:
            for line in stdout.splitlines():
                status = line[:2]
                filepath = line[3:]
                
                if status == '??':
                    files['untracked'].append(filepath)
                elif status.strip() == 'M':
                    files['modified'].append(filepath)
                elif status.strip() == 'A':
                    files['added'].append(filepath)
                elif status.strip() == 'D':
                    files['deleted'].append(filepath)
        
        # Get current branch
        code, branch, _ = self.git_command(['branch', '--show-current'])
        current_branch = branch.strip() if code == 0 else 'unknown'
        
        # Get last commit
        code, last_commit, _ = self.git_command(['log', '-1', '--oneline'])
        
        return {
            'branch': current_branch,
            'files': files,
            'last_commit': last_commit.strip() if code == 0 else None,
            'total_changes': sum(len(f) for f in files.values())
        }
    
    def check_code_quality(self, files: List[str]) -> Dict:
        """Run code quality checks"""
        issues = {
            'syntax_errors': [],
            'security_issues': [],
            'style_issues': [],
            'missing_docstrings': []
        }
        
        for filepath in files:
            if filepath.endswith('.py'):
                full_path = self.repo_path / filepath
                if full_path.exists():
                    # Check syntax
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            compile(f.read(), filepath, 'exec')
                    except SyntaxError as e:
                        issues['syntax_errors'].append(f"{filepath}: {e}")
                    
                    # Basic security checks
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Check for hardcoded secrets
                        suspicious_patterns = [
                            ('password =', 'Hardcoded password'),
                            ('api_key =', 'Hardcoded API key'),
                            ('secret =', 'Hardcoded secret'),
                            ('eval(', 'Use of eval()'),
                            ('exec(', 'Use of exec()'),
                            ('pickle.loads', 'Unsafe pickle usage')
                        ]
                        
                        for pattern, desc in suspicious_patterns:
                            if pattern in content and not filepath.endswith('_test.py'):
                                issues['security_issues'].append(f"{filepath}: {desc}")
        
        return issues
    
    def suggest_commit_message(self, files: Dict) -> str:
        """Generate semantic commit message based on changes"""
        total_changes = sum(len(f) for f in files.values())
        
        if not total_changes:
            return "chore: minor updates"
        
        # Determine commit type
        if any('test' in f for f in files['modified'] + files['added']):
            commit_type = "test"
            desc = "testing"
        elif any('doc' in f.lower() or f.endswith('.md') for f in files['modified'] + files['added']):
            commit_type = "docs"
            desc = "documentation"
        elif any('fix' in f or 'bug' in f for f in files['modified']):
            commit_type = "fix"
            desc = "bug fixes"
        elif files['added'] and len(files['added']) > len(files['modified']):
            commit_type = "feat"
            desc = "new features"
        elif any('security' in f or 'auth' in f for f in files['modified']):
            commit_type = "security"
            desc = "security improvements"
        elif any('perf' in f or 'optim' in f for f in files['modified']):
            commit_type = "perf"
            desc = "performance improvements"
        else:
            commit_type = "refactor"
            desc = "code improvements"
        
        # Build message
        message_parts = []
        if files['added']:
            message_parts.append(f"add {len(files['added'])} files")
        if files['modified']:
            message_parts.append(f"update {len(files['modified'])} files")
        if files['deleted']:
            message_parts.append(f"remove {len(files['deleted'])} files")
        
        details = " and ".join(message_parts)
        
        return f"{commit_type}: {desc} - {details}"
    
    def create_safety_checklist(self) -> List[str]:
        """Create a pre-commit safety checklist"""
        return [
            "No sensitive data (passwords, API keys, tokens) in code",
            "All new features have error handling",
            "Database changes are backward compatible",
            "Security implications have been considered",
            "Code follows project style guidelines",
            "Documentation has been updated if needed",
            "No debug print statements left in code",
            "All imports are used and necessary",
            "No TODO comments that should be addressed",
            "Version numbers updated if needed"
        ]
    
    def interactive_commit(self):
        """Interactive commit process with AI assistance"""
        print("\n" + "="*60)
        print("GitHub Workflow Assistant")
        print("="*60)
        
        # Get status
        status = self.get_status()
        print(f"\nCurrent branch: {status['branch']}")
        print(f"Last commit: {status['last_commit']}")
        
        if status['total_changes'] == 0:
            print("\nNo changes to commit.")
            return
        
        # Show changes
        print(f"\nChanges detected: {status['total_changes']} files")
        for change_type, files in status['files'].items():
            if files:
                print(f"\n{change_type.upper()} ({len(files)} files):")
                for f in files[:5]:  # Show first 5
                    print(f"  - {f}")
                if len(files) > 5:
                    print(f"  ... and {len(files) - 5} more")
        
        # Run code quality checks
        print("\nRunning code quality checks...")
        all_files = []
        for file_list in status['files'].values():
            all_files.extend(file_list)
        
        issues = self.check_code_quality(all_files)
        
        has_issues = False
        for issue_type, issue_list in issues.items():
            if issue_list:
                has_issues = True
                print(f"\n⚠️  {issue_type.replace('_', ' ').title()}:")
                for issue in issue_list:
                    print(f"   - {issue}")
        
        if not has_issues:
            print("✅ All quality checks passed!")
        
        # Safety checklist
        print("\n📋 Pre-commit Checklist:")
        checklist = self.create_safety_checklist()
        for item in checklist:
            response = input(f"✓ {item}? (y/n) [y]: ").lower() or 'y'
            if response != 'y':
                print("\n⚠️  Please address the issue before committing.")
                return
        
        # Suggest commit message
        suggested_msg = self.suggest_commit_message(status['files'])
        print(f"\n💡 Suggested commit message: {suggested_msg}")
        
        commit_msg = input("\nEnter commit message (or press Enter for suggested): ").strip()
        if not commit_msg:
            commit_msg = suggested_msg
        
        # Stage and commit
        print("\nStaging changes...")
        self.git_command(['add', '.'])
        
        print("Creating commit...")
        code, stdout, stderr = self.git_command(['commit', '-m', commit_msg])
        
        if code == 0:
            print("✅ Commit created successfully!")
            
            # Ask about pushing
            push = input("\nPush to GitHub? (y/n) [y]: ").lower() or 'y'
            if push == 'y':
                print("\nPushing to GitHub...")
                code, stdout, stderr = self.git_command(['push'])
                if code == 0:
                    print("✅ Successfully pushed to GitHub!")
                else:
                    print(f"❌ Push failed: {stderr}")
        else:
            print(f"❌ Commit failed: {stderr}")
    
    def sync_from_github(self):
        """Pull latest changes from GitHub"""
        print("\nSyncing with GitHub...")
        
        # Fetch latest
        print("Fetching latest changes...")
        code, stdout, stderr = self.git_command(['fetch'])
        
        if code != 0:
            print(f"❌ Fetch failed: {stderr}")
            return
        
        # Check if we're behind
        code, stdout, stderr = self.git_command(['status', '-sb'])
        if 'behind' in stdout:
            print("📥 New changes available from GitHub")
            pull = input("Pull changes? (y/n) [y]: ").lower() or 'y'
            
            if pull == 'y':
                code, stdout, stderr = self.git_command(['pull'])
                if code == 0:
                    print("✅ Successfully pulled latest changes!")
                else:
                    print(f"❌ Pull failed: {stderr}")
        else:
            print("✅ Already up to date with GitHub")
    
    def create_branch(self, branch_name: str = None):
        """Create a new feature branch"""
        if not branch_name:
            branch_name = input("Enter branch name (e.g., feature/new-function): ")
        
        if not branch_name:
            print("❌ Branch name required")
            return
        
        print(f"\nCreating branch '{branch_name}'...")
        code, stdout, stderr = self.git_command(['checkout', '-b', branch_name])
        
        if code == 0:
            print(f"✅ Switched to new branch '{branch_name}'")
            print("\n💡 Remember to create a Pull Request when ready to merge!")
        else:
            print(f"❌ Failed to create branch: {stderr}")

def main():
    """Main workflow interface"""
    workflow = GitHubWorkflow()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'commit':
            workflow.interactive_commit()
        elif command == 'sync':
            workflow.sync_from_github()
        elif command == 'branch':
            branch_name = sys.argv[2] if len(sys.argv) > 2 else None
            workflow.create_branch(branch_name)
        elif command == 'status':
            status = workflow.get_status()
            print(json.dumps(status, indent=2))
        else:
            print(f"Unknown command: {command}")
    else:
        # Interactive menu
        print("\n=== GitHub Workflow Assistant ===")
        print("1. 📝 Commit changes (with AI assistance)")
        print("2. 🔄 Sync from GitHub")
        print("3. 🌿 Create feature branch")
        print("4. 📊 Show status")
        print("5. ❌ Exit")
        
        choice = input("\nSelect option (1-5): ")
        
        if choice == '1':
            workflow.interactive_commit()
        elif choice == '2':
            workflow.sync_from_github()
        elif choice == '3':
            workflow.create_branch()
        elif choice == '4':
            status = workflow.get_status()
            print(json.dumps(status, indent=2))

if __name__ == "__main__":
    main()
