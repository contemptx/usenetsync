@echo off
REM Next Steps Deployment Script for UsenetSync
REM Guides you through the complete repository setup process

echo.
echo =============================================
echo   UsenetSync Repository Deployment Guide
echo =============================================
echo.

REM Step 1: Update repository configuration
echo Step 1: Update Repository Configuration
echo =======================================
echo.
set /p REPO_URL="Enter your GitHub repository URL (e.g., https://github.com/username/usenetsync.git): "

if "%REPO_URL%"=="" (
    echo ERROR: Repository URL is required
    pause
    exit /b 1
)

echo Updating deploy_config.json with your repository URL...
python -c "
import json
try:
    with open('deploy_config.json', 'r') as f:
        config = json.load(f)
    config['repository']['url'] = '%REPO_URL%'
    with open('deploy_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    print('✓ Updated deploy_config.json')
except FileNotFoundError:
    config = {
        'repository': {
            'url': '%REPO_URL%',
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
    with open('deploy_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    print('✓ Created deploy_config.json')
"

echo.

REM Step 2: Initialize Git repository if needed
echo Step 2: Initialize Git Repository
echo =================================
echo.

git status >nul 2>&1
if errorlevel 1 (
    echo Initializing Git repository...
    git init
    git config user.name "UsenetSync Developer"
    git config user.email "dev@usenetsync.local"
    echo ✓ Git repository initialized
) else (
    echo ✓ Git repository already initialized
)

REM Step 3: Update key files with user information
echo.
echo Step 3: Update Repository Information
echo ====================================
echo.

set /p USERNAME="Enter your GitHub username: "
set /p EMAIL="Enter your email address: "

if "%USERNAME%"=="" (
    set USERNAME=yourusername
    echo Using default username: yourusername
)

if "%EMAIL%"=="" (
    set EMAIL=dev@example.com
    echo Using default email: dev@example.com
)

echo Updating repository files with your information...

REM Update CODEOWNERS
python -c "
try:
    with open('.github/CODEOWNERS', 'r') as f:
        content = f.read()
    content = content.replace('@yourusername', '@%USERNAME%')
    content = content.replace('yourusername', '%USERNAME%')
    with open('.github/CODEOWNERS', 'w') as f:
        f.write(content)
    print('✓ Updated CODEOWNERS')
except Exception as e:
    print('⚠ Could not update CODEOWNERS:', e)
"

REM Update FUNDING.yml
python -c "
try:
    with open('.github/FUNDING.yml', 'r') as f:
        content = f.read()
    content = content.replace('yourusername', '%USERNAME%')
    with open('.github/FUNDING.yml', 'w') as f:
        f.write(content)
    print('✓ Updated FUNDING.yml')
except Exception as e:
    print('⚠ Could not update FUNDING.yml:', e)
"

REM Update README.md
python -c "
try:
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()
    content = content.replace('yourusername', '%USERNAME%')
    content = content.replace('team@usenetsync.dev', '%EMAIL%')
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✓ Updated README.md')
except Exception as e:
    print('⚠ Could not update README.md:', e)
"

echo.

REM Step 4: Validate the setup
echo Step 4: Validate Repository Setup
echo =================================
echo.

echo Running validation checks...

REM Check if all required files exist
python -c "
import os
from pathlib import Path

required_files = [
    'README.md', 'LICENSE', 'SECURITY.md', 'CONTRIBUTING.md',
    'CODE_OF_CONDUCT.md', 'CHANGELOG.md', '.gitignore',
    '.github/ISSUE_TEMPLATE/bug_report.yml',
    '.github/PULL_REQUEST_TEMPLATE.md',
    '.github/workflows/security-scan.yml'
]

missing_files = []
for file_path in required_files:
    if not Path(file_path).exists():
        missing_files.append(file_path)

if missing_files:
    print('❌ Missing files:')
    for file in missing_files:
        print(f'   - {file}')
else:
    print('✓ All required files present')

# Check directory structure
required_dirs = [
    '.github/ISSUE_TEMPLATE',
    '.github/workflows',
    'docs',
    'scripts',
    'tests'
]

missing_dirs = []
for dir_path in required_dirs:
    if not Path(dir_path).exists():
        missing_dirs.append(dir_path)

if missing_dirs:
    print('❌ Missing directories:')
    for dir in missing_dirs:
        print(f'   - {dir}')
else:
    print('✓ All required directories present')
"

echo.

REM Step 5: Stage files for Git
echo Step 5: Prepare for GitHub Deployment
echo ======================================
echo.

echo Adding files to Git...
git add .

echo.
echo Files ready for deployment:
git status --porcelain | findstr /C:"A " | wc -l >temp_count.txt
set /p FILE_COUNT=<temp_count.txt
del temp_count.txt

echo   New files: %FILE_COUNT%
echo   Repository URL: %REPO_URL%
echo   GitHub Username: %USERNAME%

echo.

REM Step 6: Ask for deployment confirmation
echo Step 6: Deploy to GitHub
echo =======================
echo.

set /p DEPLOY="Ready to deploy to GitHub? This will create your first commit. (y/N): "

if /i "%DEPLOY%"=="y" (
    echo.
    echo Creating initial commit...
    git commit -m "feat: Complete professional repository setup with AI-assisted development workflow

    - Add comprehensive GitHub repository structure
    - Include professional issue and PR templates  
    - Add advanced CI/CD pipeline with security scanning
    - Include community health files and governance
    - Add Docker containerization support
    - Include comprehensive documentation structure
    - Add AI-powered development tools and automation
    - Include security audit and monitoring systems
    - Add contributor recognition and community features
    - Ready for enterprise-grade open source development"
    
    if errorlevel 1 (
        echo ❌ Commit failed
        pause
        exit /b 1
    )
    
    echo ✓ Initial commit created
    echo.
    
    echo Adding remote repository...
    git remote add origin %REPO_URL% 2>nul
    if errorlevel 1 (
        echo Remote already exists, updating URL...
        git remote set-url origin %REPO_URL%
    )
    echo ✓ Remote repository configured
    echo.
    
    echo Pushing to GitHub...
    git push -u origin main
    
    if errorlevel 1 (
        echo.
        echo ⚠ Push failed. This might be because:
        echo   1. The repository doesn't exist on GitHub yet
        echo   2. You need to authenticate with GitHub
        echo   3. The branch name might be 'master' instead of 'main'
        echo.
        echo Please:
        echo   1. Create the repository on GitHub if it doesn't exist
        echo   2. Try: git push -u origin master (if main branch fails)
        echo   3. Or run: gh auth login (if you have GitHub CLI)
        echo.
        pause
    ) else (
        echo.
        echo ✅ SUCCESS! Repository deployed to GitHub!
        echo.
        echo 🎉 Your repository is now live at:
        echo    %REPO_URL%
        echo.
    )
) else (
    echo.
    echo Deployment skipped. You can deploy later with:
    echo   git commit -m "Initial repository setup"
    echo   git remote add origin %REPO_URL%
    echo   git push -u origin main
    echo.
)

REM Step 7: Next steps summary
echo.
echo ============================================
echo   Repository Setup Complete!
echo ============================================
echo.
echo ✅ What's been created:
echo   • Professional GitHub repository structure
echo   • AI-assisted development workflow
echo   • Comprehensive security scanning
echo   • Advanced CI/CD pipeline
echo   • Community management tools
echo   • Docker containerization
echo   • Complete documentation framework
echo.
echo 🔧 Next steps to complete setup:
echo.
echo 1. Visit your repository: %REPO_URL%
echo.
echo 2. Enable GitHub features in repository settings:
echo    ✓ Issues (with templates)
echo    ✓ Discussions (for community support)
echo    ✓ Security (Dependabot, CodeQL scanning)
echo    ✓ Pages (for documentation)
echo    ✓ Projects (for roadmap management)
echo.
echo 3. Configure repository secrets (Settings → Secrets):
echo    • PYPI_API_TOKEN (for automated PyPI releases)
echo    • SLACK_WEBHOOK_URL (for deployment notifications)
echo.
echo 4. Set up branch protection rules (Settings → Branches):
echo    • Require pull request reviews
echo    • Require status checks
echo    • Require up-to-date branches
echo.
echo 5. Start using AI-assisted development:
echo    python automated_github_workflow.py start --daemon
echo.
echo 🚀 Your repository is now enterprise-ready!
echo    Professional • Secure • AI-Powered • Community-Friendly
echo.

pause
