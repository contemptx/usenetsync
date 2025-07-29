#!/usr/bin/env python3
"""
Test script to verify the consolidated workflow installation
"""

import sys
import json
from pathlib import Path

def test_installation():
    """Test if the consolidated workflow is properly installed"""
    
    print("Testing Consolidated GitHub Workflow Installation...")
    print("=" * 50)
    
    # Check Python version
    print(f"Python version: {sys.version}")
    print()
    
    # Check required modules
    required_modules = ['watchdog', 'psutil']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module} is installed")
        except ImportError:
            print(f"✗ {module} is NOT installed")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\nPlease install missing modules: pip install {' '.join(missing_modules)}")
    
    print()
    
    # Check configuration
    config_file = Path('.workflow/config.json')
    if config_file.exists():
        print("✓ Configuration file exists")
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            print("✓ Configuration is valid JSON")
            print(f"  Branch: {config.get('branch', 'not set')}")
            print(f"  Auto-deploy: {config.get('auto_deploy', 'not set')}")
            print(f"  Fix indentation: {config.get('fix_indentation', 'not set')}")
        except Exception as e:
            print(f"✗ Error reading configuration: {e}")
    else:
        print("✗ Configuration file not found at .workflow/config.json")
    
    print()
    
    # Check for backup directory
    backup_dir = Path('workflow_backup')
    if backup_dir.exists():
        print("✓ Backup directory exists")
        backups = list(backup_dir.glob('*.py'))
        if backups:
            print(f"  Found {len(backups)} backup files:")
            for backup in backups[:5]:  # Show first 5
                print(f"    - {backup.name}")
    else:
        print("ℹ No backup directory found (this is fine for fresh installs)")
    
    print()
    
    # Check for helper scripts
    helper_scripts = [
        'start_workflow.bat',
        'check_status.bat',
        'deploy_now.bat',
        'validate_file.bat',
        'rollback.bat',
        'stop_workflow.bat'
    ]
    
    print("Helper scripts:")
    for script in helper_scripts:
        if Path(script).exists():
            print(f"  ✓ {script}")
        else:
            print(f"  ✗ {script} not found")
    
    print()
    print("=" * 50)
    
    # Check if consolidated_github_workflow.py exists
    if Path('consolidated_github_workflow.py').exists():
        print("✓ consolidated_github_workflow.py exists")
        
        # Try to import it
        try:
            import consolidated_github_workflow
            print("✓ Module imports successfully")
            
            # Try to create instance
            workflow = consolidated_github_workflow.ConsolidatedGitHubWorkflow()
            print("✓ Workflow instance created successfully")
            
            # Show status
            status = workflow.status()
            print("\nCurrent Status:")
            print(f"  Monitoring: {status['monitoring']}")
            print(f"  Branch: {status['config']['branch']}")
            print(f"  Auto-deploy: {status['config']['auto_deploy']}")
            
        except Exception as e:
            print(f"✗ Error importing module: {e}")
            print("\nThis might be due to syntax errors in the file.")
            print("Please check that the file contains valid Python code.")
    else:
        print("✗ consolidated_github_workflow.py NOT FOUND")
        print("\nPlease save the 'Consolidated Advanced GitHub Workflow Manager' artifact")
        print("as 'consolidated_github_workflow.py' in the current directory.")
    
    print("\n" + "=" * 50)
    print("Installation test complete!")

if __name__ == '__main__':
    test_installation()
