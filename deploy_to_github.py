#!/usr/bin/env python3
"""
Windows-Compatible GitHub Deployment Script
Interactive deployment guide for UsenetSync repository
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*50)
    print(f"  {title}")
    print("="*50)

def print_step(step_num, title):
    """Print a step header"""
    print(f"\nStep {step_num}: {title}")
    print("=" + "="*len(f"Step {step_num}: {title}"))

def safe_input(prompt, default=""):
    """Safe input with default value"""
    try:
        result = input(f"{prompt}")
        return result if result.strip() else default
    except (EOFError, KeyboardInterrupt):
        print("\nOperation cancelled by user")
        sys.exit(1)

def run_command(command, capture_output=True, check=False):
    """Run a command safely"""
    try:
        if isinstance(command, str):
            result = subprocess.run(command, shell=True, capture_output=capture_output, 
                                  text=True, check=check)
        else:
            result = subprocess.run(command, capture_output=capture_output, 
                                  text=True, check=check)
        return result
    except subprocess.CalledProcessError as e:
        if not capture_output:
            print(f"Command failed: {e}")
        return e
    except Exception as e:
        print(f"Error running command: {e}")
        return None

def update_deploy_config(repo_url):
    """Update deploy_config.json with repository URL"""
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
        with open('deploy_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        print("✓ Updated deploy_config.json")
        return True
    except Exception as e:
        print(f"❌ Failed to update deploy_config.json: {e}")
        return False

def check_git_status():
    """Check if Git is initialized"""
    result = run_command(['git', 'status'])
    return result.returncode == 0 if result else False

def initialize_git():
    """Initialize Git repository"""
    print("Initializing Git repository...")
    
    commands = [
        ['git', 'init'],
        ['git', 'config', 'user.name', 'UsenetSync Developer'],
        ['git', 'config', 'user.email', 'dev@usenetsync.local']
    ]
    
    for cmd in commands:
        result = run_command(cmd)
        if result and result.returncode != 0:
            print(f"❌ Failed to run: {' '.join(cmd)}")
            return False
    
    print("✓ Git repository initialized")
    return True

def update_repository_files(username, email):
    """Update repository files with user information"""
    print("Updating repository files with your information...")
    
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
            if Path(file_path).exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for old_text, new_text in replacements.items():
                    content = content.replace(old_text, new_text)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"✓ Updated {file_path}")
                updated_count += 1
            else:
                print(f"⚠ File not found: {file_path}")
        except Exception as e:
            print(f"⚠ Could not update {file_path}: {e}")
    
    return updated_count > 0

def validate_repository_setup():
    """Validate that the repository setup is complete"""
    required_files = [
        'README.md', 'LICENSE', 'SECURITY.md', 'CONTRIBUTING.md',
        'CODE_OF_CONDUCT.md', 'CHANGELOG.md', '.gitignore',
        '.github/ISSUE_TEMPLATE/bug_report.yml',
        '.github/PULL_REQUEST_TEMPLATE.md',
        '.github/workflows/security-scan.yml'
    ]
    
    required_dirs = [
        '.github/ISSUE_TEMPLATE',
        '.github/workflows',
        'docs',
        'scripts',
        'tests'
    ]
    
    missing_files = []
    missing_dirs = []
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
    
    if missing_files:
        print("❌ Missing files:")
        for file in missing_files:
            print(f"   - {file}")
    
    if missing_dirs:
        print("❌ Missing directories:")
        for dir in missing_dirs:
            print(f"   - {dir}")
    
    if not missing_files and not missing_dirs:
        print("✓ All required files and directories present")
        return True
    
    return False

def get_git_status():
    """Get Git status information"""
    result = run_command(['git', 'status', '--porcelain'])
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

def deploy_to_github(repo_url):
    """Deploy repository to GitHub"""
    print("Creating initial commit...")
    
    # Add all files
    result = run_command(['git', 'add', '.'])
    if result and result.returncode != 0:
        print("❌ Failed to add files to Git")
        return False
    
    # Create commit
    commit_message = """feat: Complete professional repository setup with AI-assisted development workflow

- Add comprehensive GitHub repository structure
- Include professional issue and PR templates  
- Add advanced CI/CD pipeline with security scanning
- Include community health files and governance
- Add Docker containerization support
- Include comprehensive documentation structure
- Add AI-powered development tools and automation
- Include security audit and monitoring systems
- Add contributor recognition and community features
- Ready for enterprise-grade open source development"""
    
    result = run_command(['git', 'commit', '-m', commit_message])
    if result and result.returncode != 0:
        print("❌ Failed to create commit")
        return False
    
    print("✓ Initial commit created")
    
    # Add remote
    print("Adding remote repository...")
    result = run_command(['git', 'remote', 'add', 'origin', repo_url])
    if result and result.returncode != 0:
        # Remote might already exist, try to update it
        result = run_command(['git', 'remote', 'set-url', 'origin', repo_url])
        if result and result.returncode == 0:
            print("✓ Remote repository URL updated")
        else:
            print("⚠ Could not set remote URL")
    else:
        print("✓ Remote repository configured")
    
    # Push to GitHub
    print("Pushing to GitHub...")
    result = run_command(['git', 'push', '-u', 'origin', 'main'], capture_output=False)
    if result and result.returncode != 0:
        print("\n⚠ Push failed. Trying 'master' branch...")
        result = run_command(['git', 'push', '-u', 'origin', 'master'], capture_output=False)
        if result and result.returncode != 0:
            print("\n❌ Push failed. This might be because:")
            print("   1. The repository doesn't exist on GitHub yet")
            print("   2. You need to authenticate with GitHub")
            print("   3. Network connectivity issues")
            print("\nPlease:")
            print("   1. Create the repository on GitHub if it doesn't exist")
            print("   2. Set up authentication (SSH keys or Personal Access Token)")
            print("   3. Try running: git push -u origin main")
            return False
    
    print("\n✅ SUCCESS! Repository deployed to GitHub!")
    return True

def main():
    """Main deployment function"""
    print_header("UsenetSync Repository Deployment Guide")
    
    # Step 1: Repository Configuration
    print_step(1, "Update Repository Configuration")
    repo_url = safe_input("Enter your GitHub repository URL (e.g., https://github.com/username/usenetsync.git): ")
    
    if not repo_url:
        print("❌ Repository URL is required")
        return 1
    
    if not update_deploy_config(repo_url):
        return 1
    
    # Step 2: Git Setup
    print_step(2, "Initialize Git Repository")
    if not check_git_status():
        if not initialize_git():
            return 1
    else:
        print("✓ Git repository already initialized")
    
    # Step 3: Update repository information
    print_step(3, "Update Repository Information")
    username = safe_input("Enter your GitHub username: ", "yourusername")
    email = safe_input("Enter your email address: ", "dev@example.com")
    
    if username == "yourusername":
        print("Using default username: yourusername")
    if email == "dev@example.com":
        print("Using default email: dev@example.com")
    
    update_repository_files(username, email)
    
    # Step 4: Validate setup
    print_step(4, "Validate Repository Setup")
    print("Running validation checks...")
    if not validate_repository_setup():
        print("\n⚠ Some files are missing, but deployment can continue")
    
    # Step 5: Show Git status
    print_step(5, "Prepare for GitHub Deployment")
    status = get_git_status()
    print(f"Repository status:")
    print(f"   New files: {status['new_files']}")
    print(f"   Total changes: {status['total_changes']}")
    print(f"   Repository URL: {repo_url}")
    print(f"   GitHub Username: {username}")
    
    # Step 6: Deploy
    print_step(6, "Deploy to GitHub")
    deploy = safe_input("Ready to deploy to GitHub? This will create your first commit. (y/N): ", "n")
    
    if deploy.lower() == 'y':
        if deploy_to_github(repo_url):
            # Success message
            print_header("Repository Setup Complete!")
            print("\n🎉 Your repository is now live at:")
            print(f"   {repo_url}")
            print("\n✅ What's been created:")
            print("   • Professional GitHub repository structure")
            print("   • AI-assisted development workflow")
            print("   • Comprehensive security scanning")
            print("   • Advanced CI/CD pipeline")
            print("   • Community management tools")
            print("   • Docker containerization")
            print("   • Complete documentation framework")
            
            print("\n🔧 Next steps to complete setup:")
            print("\n1. Visit your repository and enable GitHub features:")
            print("   ✓ Issues (with templates)")
            print("   ✓ Discussions (for community support)")
            print("   ✓ Security (Dependabot, CodeQL scanning)")
            print("   ✓ Pages (for documentation)")
            print("   ✓ Projects (for roadmap management)")
            
            print("\n2. Configure repository secrets (Settings → Secrets):")
            print("   • PYPI_API_TOKEN (for automated PyPI releases)")
            print("   • SLACK_WEBHOOK_URL (for deployment notifications)")
            
            print("\n3. Set up branch protection rules (Settings → Branches):")
            print("   • Require pull request reviews")
            print("   • Require status checks")
            print("   • Require up-to-date branches")
            
            print("\n4. Start using AI-assisted development:")
            print("   python automated_github_workflow.py start --daemon")
            
            print("\n🚀 Your repository is now enterprise-ready!")
            print("   Professional • Secure • AI-Powered • Community-Friendly")
            
        else:
            print("\n❌ Deployment failed. Please check the errors above and try again.")
            return 1
    else:
        print("\nDeployment skipped. You can deploy later with:")
        print("   git add .")
        print("   git commit -m 'Initial repository setup'")
        print("   git push -u origin main")
    
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
        print(f"\n❌ Unexpected error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)
