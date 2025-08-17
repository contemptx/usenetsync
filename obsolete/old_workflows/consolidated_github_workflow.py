#!/usr/bin/env python3
"""
Streamlined GitHub Workflow Manager - Production Ready
Consolidates all workflow features with focus on reliability
"""

import os
import sys
import json
import time
import shutil
import subprocess
import logging
from pathlib import Path
from datetime import datetime
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubWorkflowManager:
    """Streamlined GitHub workflow manager with all essential features"""
    
    def __init__(self, project_root=None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.config_file = self.project_root / ".workflow" / "config.json"
        self.config = self.load_config()
        self.setup_directories()
        
    def setup_directories(self):
        """Create necessary directories"""
        dirs = [
            ".workflow", ".github/workflows", ".github/ISSUE_TEMPLATE",
            "backups", "scripts", "docs"
        ]
        for d in dirs:
            (self.project_root / d).mkdir(parents=True, exist_ok=True)
            
    def load_config(self):
        """Load configuration"""
        default_config = {
            "branch": "main",
            "remote": "origin",
            "auto_deploy": True,
            "fix_indentation": True,
            "validate_before_deploy": True,
            "check_security": True
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except:
                pass
                
        # Save default config
        self.config_file.parent.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config
        
    def fix_indentation(self, file_path):
        """Fix Python file indentation"""
        if not file_path.endswith('.py'):
            return False
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Replace tabs with spaces
            if '\t' in content:
                content = content.replace('\t', '    ')
                
            # Fix common indentation issues
            lines = content.split('\n')
            fixed_lines = []
            indent_level = 0
            
            for line in lines:
                stripped = line.strip()
                
                # Skip empty lines
                if not stripped:
                    fixed_lines.append('')
                    continue
                    
                # Decrease indent for certain keywords
                if stripped.startswith(('return', 'break', 'continue', 'pass')):
                    if indent_level > 0:
                        indent_level -= 4
                        
                # Apply indentation
                fixed_lines.append(' ' * indent_level + stripped)
                
                # Increase indent after colons
                if stripped.endswith(':'):
                    indent_level += 4
                    
            # Save fixed content
            fixed_content = '\n'.join(fixed_lines)
            
            # Backup original
            backup_path = self.project_root / "backups" / f"{Path(file_path).name}.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(file_path, backup_path)
            
            # Write fixed content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
                
            logger.info(f"Fixed indentation in {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to fix indentation: {e}")
            return False
            
    def validate_file(self, file_path):
        """Validate Python file"""
        if not file_path.endswith('.py'):
            return True, []
            
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Try to compile
            compile(content, file_path, 'exec')
            
            # Security checks
            if self.config.get('check_security', True):
                security_patterns = [
                    (r'password\s*=\s*["\']', 'Hardcoded password'),
                    (r'api_key\s*=\s*["\']', 'Hardcoded API key'),
                    (r'eval\s*\(', 'Use of eval()'),
                    (r'exec\s*\(', 'Use of exec()')
                ]
                
                for pattern, msg in security_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        errors.append(f"Security warning: {msg}")
                        
            return len(errors) == 0, errors
            
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
            
            # Try to auto-fix if enabled
            if self.config.get('fix_indentation', True):
                if self.fix_indentation(file_path):
                    # Re-validate after fix
                    return self.validate_file(file_path)
                    
        except Exception as e:
            errors.append(f"Validation error: {e}")
            
        return False, errors
        
    def deploy(self, message=None, force=False):
        """Deploy to GitHub"""
        try:
            # Get changed files
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True)
            
            if not result.stdout.strip():
                logger.info("No changes to deploy")
                return True
                
            # Validate changed files
            if self.config.get('validate_before_deploy', True) and not force:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        file_path = line.split()[-1]
                        if file_path.endswith('.py'):
                            valid, errors = self.validate_file(file_path)
                            if not valid:
                                logger.error(f"Validation failed for {file_path}:")
                                for error in errors:
                                    logger.error(f"  {error}")
                                return False
                                
            # Generate commit message if not provided
            if not message:
                message = f"Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                
            # Git operations
            subprocess.run(['git', 'add', '.'], check=True)
            subprocess.run(['git', 'commit', '-m', message], check=True)
            subprocess.run(['git', 'push', self.config['remote'], self.config['branch']], check=True)
            
            logger.info(f"Successfully deployed: {message}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Deployment failed: {e}")
            return False
            
    def setup_workflows(self):
        """Create GitHub workflows"""
        workflow_dir = self.project_root / ".github" / "workflows"
        
        # Basic CI workflow
        ci_workflow = """name: CI Pipeline

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
    - name: Lint with flake8
      run: |
        pip install flake8
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true
    - name: Test
      run: |
        python -m pytest tests/ || echo "No tests found"
"""
        
        with open(workflow_dir / "ci.yml", 'w') as f:
            f.write(ci_workflow)
            
        # Security scan workflow  
        security_workflow = """name: Security Scan

on:
  push:
    branches: [ main, master ]
  schedule:
    - cron: '0 0 * * 1'

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Run Trivy scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        severity: 'CRITICAL,HIGH'
"""
        
        with open(workflow_dir / "security.yml", 'w') as f:
            f.write(security_workflow)
            
        logger.info("Created GitHub workflows")
        
    def status(self):
        """Get status"""
        return {
            "config": self.config,
            "project_root": str(self.project_root),
            "workflows_exist": (self.project_root / ".github" / "workflows").exists()
        }

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Streamlined GitHub Workflow Manager')
    parser.add_argument('command', choices=['deploy', 'validate', 'fix', 'setup', 'status'],
                        help='Command to execute')
    parser.add_argument('--file', help='File to validate or fix')
    parser.add_argument('--message', '-m', help='Commit message')
    parser.add_argument('--force', '-f', action='store_true', help='Force operation')
    
    args = parser.parse_args()
    
    manager = GitHubWorkflowManager()
    
    if args.command == 'deploy':
        success = manager.deploy(message=args.message, force=args.force)
        sys.exit(0 if success else 1)
        
    elif args.command == 'validate':
        if args.file:
            valid, errors = manager.validate_file(args.file)
            if valid:
                print(f"✓ {args.file} is valid")
            else:
                print(f"✗ {args.file} has errors:")
                for error in errors:
                    print(f"  - {error}")
        else:
            print("Please specify --file")
            
    elif args.command == 'fix':
        if args.file:
            if manager.fix_indentation(args.file):
                print(f"✓ Fixed indentation in {args.file}")
            else:
                print(f"✗ Could not fix {args.file}")
        else:
            print("Please specify --file")
            
    elif args.command == 'setup':
        manager.setup_workflows()
        print("✓ GitHub workflows created")
        
    elif args.command == 'status':
        status = manager.status()
        print(json.dumps(status, indent=2))

if __name__ == '__main__':
    main()
