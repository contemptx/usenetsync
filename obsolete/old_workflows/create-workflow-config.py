#!/usr/bin/env python3
"""
Create workflow configuration for consolidated GitHub workflow
"""

import json
from pathlib import Path

def create_workflow_config():
    """Create the workflow configuration"""
    
    # Default configuration
    config = {
        'branch': 'main',
        'remote': 'origin',
        'auto_deploy': True,
        'validate_before_deploy': True,
        'auto_rollback': True,
        'max_deployments_per_hour': 10,
        'check_syntax': True,
        'check_security': True,
        'check_performance': True,
        'fix_indentation': True,
        'create_workflows': True,
        'monitoring_interval': 5,
        'health_check_timeout': 30,
        'rollback_on_health_failure': True
    }
    
    # Try to load existing deploy_config.json to migrate settings
    if Path('deploy_config.json').exists():
        try:
            with open('deploy_config.json', 'r') as f:
                old_config = json.load(f)
                
            # Migrate settings from old config
            if 'repository' in old_config:
                config['branch'] = old_config['repository'].get('branch', 'main')
                config['remote'] = old_config['repository'].get('remote', 'origin')
                
            if 'validation' in old_config:
                config['check_syntax'] = old_config['validation'].get('check_syntax', True)
                
            if 'github' in old_config:
                config['create_workflows'] = old_config['github'].get('create_workflows', True)
                
            print("Migrated settings from deploy_config.json")
            
        except Exception as e:
            print(f"Warning: Could not load old config: {e}")
    
    # Create .workflow directory
    workflow_dir = Path('.workflow')
    workflow_dir.mkdir(exist_ok=True)
    
    # Save new config
    config_file = workflow_dir / 'config.json'
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Created {config_file}")
    
    # Also create a backup of the config
    backup_file = workflow_dir / 'config.backup.json'
    with open(backup_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"Created backup at {backup_file}")
    
    return config

if __name__ == '__main__':
    config = create_workflow_config()
    print("\nConfiguration created:")
    print(json.dumps(config, indent=2))
