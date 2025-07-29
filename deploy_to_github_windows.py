#!/usr/bin/env python3
"""
Windows-Compatible GitHub Deployment Script for UsenetSync
Handles Git installation check and provides clear guidance
"""

import os
import json
import subprocess
import sys
import shutil
from pathlib import Path
from datetime import datetime

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_step(step_num, title):
    """Print a step header"""
    print(f"\nStep {step_num}: {title}")
    print("-" * (len(f"Step {step_num}: {title}") + 2))

def print_error(message):
    """Print error message"""
    print(f"\n[ERROR] {message}")

def print_success(message):
    """Print success message"""
    print(f"[OK] {message}")

def print_info(message):
    """Print info message"""
    print(f"[INFO] {message}")

def safe_input(prompt, default=""):
    """Safe input with default value"""
    try:
        result = input(f"{prompt}")
        return result if result.strip() else default
    except (EOFError, KeyboardInterrupt):
        print("\nOperation cancelled by user")
        sys.exit(1)

def check_git_installed():
    """Check if Git is installed and accessible"""
    # Check various possible Git locations on Windows
    git_paths = [
        "git",  # If in PATH
        r"C:\Program Files\Git\bin\git.exe",
        r"C:\Program Files (x86)\Git\bin\git.exe",
        r"C:\Git\bin\git.exe",
        shutil.which("git")  # Find git in PATH
    ]
    
    for git_path in git_paths:
        if git_path and os.path.exists(str(git_path)):
            try:
                result = subprocess.run([git_path, "--version"], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return git_path
            except:
                continue
    
    return None

def run_git_command(git_exe, args, cwd=None):
    """Run a git command with the specified git executable"""
    cmd = [git_exe] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        return result
    except Exception as e:
        print_error(f"Failed to run git command: {e}")
        return None

def update_deploy_config(repo_url):
    """Update deploy_config.json with repository URL"""
    config_path = Path("deploy_config.json")
    
    # Default configuration
    config = {
        'repository': {
            'url': repo_url,
            'branch': 'main',
            'remote': 'origin'
        },
        'deployment': {
            'auto_commit': True,
            'commit_message_template': 'Production deployment - {timestamp}',
            'create_release': False,
            'tag_format': 'v{version}',
            'exclude_patterns': [
                '*.pyc', '__pycache__', '*.log', '.vscode', '.idea',
                'node_modules', 'venv', '.env', 'secure_config.py',
                '*.db', 'data/*', 'logs/*', 'temp/*', '.temp/*',
                'upload/*', 'download/*', '*.backup_*', '.git', '.gitignore'
            ]
        },
        'github': {
            'create_workflows': True,
            'create_issues_templates': True,
            'create_pr_template': True
        },
        'validation': {
            'check_syntax': True,
            'run_tests': False,
            'lint_code': False
        }
    }
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print_success("Updated deploy_config.json")
        return True
    except Exception as e:
        print_error(f"Failed to update deploy_config.json: {e}")
        return False

def check_git_status(git_exe):
    """Check if Git repository is initialized"""
    result = run_git_command(git_exe, ['status'], cwd='.')
    return result and result.returncode == 0

def initialize_git(git_exe):
    """Initialize Git repository"""
    print_info("Initializing Git repository...")
    
    # Initialize repository
    result = run_git_command(git_exe, ['init'])
    if not result or result.returncode != 0:
        print_error("Failed to initialize Git repository")
        return False
    
    # Set user configuration
    commands = [
        ['config', 'user.name', 'UsenetSync Developer'],
        ['config', 'user.email', 'dev@usenetsync.local']
    ]
    
    for cmd in commands:
        result = run_git_command(git_exe, cmd)
        if not result or result.returncode != 0:
            print_error(f"Failed to set git {cmd[1]}")
            return False
    
    print_success("Git repository initialized")
    return True

def update_repository_files(username, email):
    """Update repository files with user information"""
    print_info("Updating repository files...")
    
    files_to_update = {
        '.github/CODEOWNERS': {
            '@yourusername': f'@{username}',
            'yourusername': username
        },
        '.github/FUNDING.yml': {
            'yourusername': username
        },
        'README.md': {
            'yourusername': username,
            'team@usenetsync.dev': email
        }
    }
    
    updated_count = 0
    for file_path, replacements in files_to_update.items():
        try:
            path = Path(file_path)
            if path.exists():
                content = path.read_text(encoding='utf-8')
                
                for old_text, new_text in replacements.items():
                    content = content.replace(old_text, new_text)
                
                path.write_text(content, encoding='utf-8')
                print_success(f"Updated {file_path}")
                updated_count += 1
            else:
                print_info(f"File not found: {file_path}")
        except Exception as e:
            print_error(f"Could not update {file_path}: {e}")
    
    return updated_count > 0

def get_git_status(git_exe):
    """Get Git status information"""
    result = run_git_command(git_exe, ['status', '--porcelain'])
    if result and result.returncode == 0:
        lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
        new_files = [line for line in lines if line.startswith('??')]
        modified_files = [line for line in lines if line.startswith(' M')]
        staged_files = [line for line in lines if line.startswith('A ')]
        
        return {
            'new_files': len(new_files),
            'modified_files': len(modified_files),
            'staged_files': len(staged_files),
            'total_changes': len(lines)
        }
    return {'new_files': 0, 'modified_files': 0, 'staged_files': 0, 'total_changes': 0}

def create_gitignore():
    """Create a comprehensive .gitignore file"""
    gitignore_content = """# UsenetSync specific
data/
logs/
temp/
.temp/
upload/
download/
*.backup*
posted_files.json
posting_history.log
monitoring_alerts.db
monitoring_alerts.log
security-report.*
improvement_report.txt

# Sensitive configuration
secure_config.py
.env
*.key
*.pem

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/

# Databases
*.db
*.sqlite
*.sqlite3

# Logs
*.log

# Documentation
docs/_build/
"""
    
    try:
        with open('.gitignore', 'w') as f:
            f.write(gitignore_content)
        print_success("Created .gitignore file")
        return True
    except Exception as e:
        print_error(f"Failed to create .gitignore: {e}")
        return False

def deploy_to_github(git_exe, repo_url):
    """Deploy repository to GitHub"""
    print_info("Preparing for GitHub deployment...")
    
    # Create .gitignore if it doesn't exist
    if not Path('.gitignore').exists():
        create_gitignore()
    
    # Add all files
    print_info("Adding files to Git...")
    result = run_git_command(git_exe, ['add', '.'])
    if not result or result.returncode != 0:
        print_error("Failed to add files to Git")
        return False
    
    # Create commit
    print_info("Creating initial commit...")
    commit_message = f"""feat: Complete UsenetSync repository setup

- Add comprehensive project structure
- Include all production modules
- Add deployment and configuration files
- Include comprehensive documentation
- Ready for production deployment

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    result = run_git_command(git_exe, ['commit', '-m', commit_message])
    if not result or result.returncode != 0:
        if "nothing to commit" in (result.stdout + result.stderr if result else ""):
            print_info("No changes to commit")
        else:
            print_error("Failed to create commit")
            return False
    else:
        print_success("Initial commit created")
    
    # Add remote
    print_info("Configuring remote repository...")
    result = run_git_command(git_exe, ['remote', 'add', 'origin', repo_url])
    if not result or result.returncode != 0:
        # Remote might already exist, try to update it
        result = run_git_command(git_exe, ['remote', 'set-url', 'origin', repo_url])
        if result and result.returncode == 0:
            print_success("Remote repository URL updated")
        else:
            print_error("Could not set remote URL")
    else:
        print_success("Remote repository configured")
    
    # Get current branch name
    result = run_git_command(git_exe, ['branch', '--show-current'])
    current_branch = result.stdout.strip() if result and result.returncode == 0 else 'master'
    
    # Push to GitHub
    print_info(f"Pushing to GitHub (branch: {current_branch})...")
    print_info("This may take a moment...")
    
    # Try pushing with the current branch name
    result = run_git_command(git_exe, ['push', '-u', 'origin', current_branch])
    
    if not result or result.returncode != 0:
        error_msg = result.stderr if result else "Unknown error"
        
        if "remote: Repository not found" in error_msg:
            print_error("Repository not found on GitHub")
            print_info("Please ensure the repository exists at: " + repo_url)
            print_info("Create it on GitHub first, then try again")
        elif "Authentication failed" in error_msg or "could not read Username" in error_msg:
            print_error("GitHub authentication failed")
            print_info("\nTo fix this, you need to set up GitHub authentication:")
            print_info("1. Generate a Personal Access Token on GitHub:")
            print_info("   - Go to GitHub Settings > Developer settings > Personal access tokens")
            print_info("   - Create a new token with 'repo' scope")
            print_info("2. Use the token as your password when Git prompts you")
            print_info("   - Username: your GitHub username")
            print_info("   - Password: your Personal Access Token (not your GitHub password)")
        else:
            print_error(f"Push failed: {error_msg}")
        
        print_info("\nYou can try pushing manually later with:")
        print_info(f"   {git_exe} push -u origin {current_branch}")
        return False
    
    print_success("Successfully pushed to GitHub!")
    return True

def show_manual_steps(repo_url):
    """Show manual steps for completing the deployment"""
    print_header("Manual Steps Required")
    
    print("\n1. INSTALL GIT (if not already installed):")
    print("   - Download from: https://git-scm.com/download/win")
    print("   - Run the installer with default settings")
    print("   - Restart your terminal after installation")
    
    print("\n2. CREATE GITHUB REPOSITORY:")
    print("   - Go to: https://github.com/new")
    print("   - Repository name: usenetsync")
    print("   - Keep it public or private as needed")
    print("   - DO NOT initialize with README, .gitignore, or license")
    print("   - Click 'Create repository'")
    
    print("\n3. SET UP GITHUB AUTHENTICATION:")
    print("   - Go to: GitHub Settings > Developer settings > Personal access tokens")
    print("   - Click 'Generate new token'")
    print("   - Give it a name (e.g., 'UsenetSync Deployment')")
    print("   - Select scopes: 'repo' (full control)")
    print("   - Click 'Generate token'")
    print("   - SAVE THE TOKEN - you won't see it again!")
    
    print("\n4. PUSH YOUR CODE:")
    print("   After installing Git, run these commands:")
    print(f"   git init")
    print(f"   git add .")
    print(f'   git commit -m "Initial commit"')
    print(f"   git remote add origin {repo_url}")
    print(f"   git push -u origin main")
    print("\n   When prompted:")
    print("   - Username: your GitHub username")
    print("   - Password: your Personal Access Token (NOT your GitHub password)")

def main():
    """Main deployment function"""
    print_header("UsenetSync GitHub Deployment (Windows)")
    
    # Step 1: Check Git installation
    print_step(1, "Check Git Installation")
    git_exe = check_git_installed()
    
    if not git_exe:
        print_error("Git is not installed or not accessible")
        print_info("Git is required for GitHub deployment")
        show_manual_steps("https://github.com/yourusername/usenetsync.git")
        input("\nPress Enter to exit...")
        return 1
    
    print_success(f"Git found: {git_exe}")
    
    # Step 2: Repository Configuration
    print_step(2, "Repository Configuration")
    repo_url = safe_input("Enter your GitHub repository URL (e.g., https://github.com/username/repo.git): ")
    
    if not repo_url:
        print_error("Repository URL is required")
        return 1
    
    if not update_deploy_config(repo_url):
        return 1
    
    # Step 3: Git Setup
    print_step(3, "Git Repository Setup")
    if not check_git_status(git_exe):
        if not initialize_git(git_exe):
            return 1
    else:
        print_success("Git repository already initialized")
    
    # Step 4: Update repository information
    print_step(4, "Personalize Repository")
    
    # Extract username from repo URL if possible
    default_username = "yourusername"
    if "github.com/" in repo_url:
        try:
            parts = repo_url.split("github.com/")[1].split("/")
            if parts:
                default_username = parts[0]
        except:
            pass
    
    username = safe_input(f"Enter your GitHub username [{default_username}]: ", default_username)
    email = safe_input("Enter your email address [dev@example.com]: ", "dev@example.com")
    
    update_repository_files(username, email)
    
    # Step 5: Show Git status
    print_step(5, "Repository Status")
    status = get_git_status(git_exe)
    print(f"Files to be committed: {status['total_changes']}")
    print(f"Repository URL: {repo_url}")
    print(f"GitHub Username: {username}")
    
    # Step 6: Deploy
    print_step(6, "Deploy to GitHub")
    print_info("Before proceeding, ensure:")
    print_info("1. The repository exists on GitHub")
    print_info("2. You have your GitHub credentials ready")
    print_info("3. If using 2FA, you have a Personal Access Token")
    
    deploy = safe_input("\nReady to deploy? (y/N): ", "n")
    
    if deploy.lower() == 'y':
        if deploy_to_github(git_exe, repo_url):
            print_header("Deployment Successful!")
            print(f"\nYour repository is now live at:")
            print(f"   {repo_url}")
            print("\nNext steps:")
            print("1. Visit your repository on GitHub")
            print("2. Add a description and topics")
            print("3. Configure repository settings")
            print("4. Enable GitHub features (Issues, Discussions, etc.)")
            print("5. Set up branch protection rules")
            print("6. Add collaborators if needed")
        else:
            print_header("Deployment Incomplete")
            print("\nDon't worry! Your files are ready.")
            print("Follow the manual steps above to complete the deployment.")
    else:
        print_info("\nDeployment cancelled.")
        print_info("Your files are ready for manual deployment.")
        show_manual_steps(repo_url)
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        input("\nPress Enter to exit...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)
