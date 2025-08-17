#!/bin/bash

# Create obsolete subdirectories
mkdir -p obsolete/old_gui
mkdir -p obsolete/old_workflows
mkdir -p obsolete/old_scripts
mkdir -p obsolete/old_tests

# Move old GUI implementations (keeping only the gui/ directory version)
mv usenetsync_gui_*.py obsolete/old_gui/ 2>/dev/null
mv gui_*.py obsolete/old_gui/ 2>/dev/null
mv minimal_gui_publishing_fix.py obsolete/old_gui/ 2>/dev/null
mv redesigned_gui.py obsolete/old_gui/ 2>/dev/null
mv complete_gui_rebuild.py obsolete/old_gui/ 2>/dev/null
mv deploy_fixed_gui.py obsolete/old_gui/ 2>/dev/null
mv deploy_redesigned_gui.py obsolete/old_gui/ 2>/dev/null
mv launch_fixed_gui.py obsolete/old_gui/ 2>/dev/null
mv launch_gui.py obsolete/old_gui/ 2>/dev/null
mv run_gui.py obsolete/old_gui/ 2>/dev/null
mv setup_gui_development.py obsolete/old_gui/ 2>/dev/null

# Move old GitHub workflows
mv automated_github_workflow.py obsolete/old_workflows/ 2>/dev/null
mv automated_workflow.py obsolete/old_workflows/ 2>/dev/null
mv consolidated-github-workflow.py obsolete/old_workflows/ 2>/dev/null
mv consolidated_github_workflow.py obsolete/old_workflows/ 2>/dev/null
mv create-workflow-config.py obsolete/old_workflows/ 2>/dev/null
mv deploy_to_github*.py obsolete/old_workflows/ 2>/dev/null
mv github_advanced_features.py obsolete/old_workflows/ 2>/dev/null
mv github_deploy.py obsolete/old_workflows/ 2>/dev/null
mv github_setup_automation.py obsolete/old_workflows/ 2>/dev/null
mv setup_github_repository*.py obsolete/old_workflows/ 2>/dev/null
mv update_github.py obsolete/old_workflows/ 2>/dev/null
mv gitops_manager.py obsolete/old_workflows/ 2>/dev/null

# Move old batch files
mv launch_fixed_gui.bat obsolete/old_scripts/ 2>/dev/null
mv launch_gui.bat obsolete/old_scripts/ 2>/dev/null
mv launch_gui.sh obsolete/old_scripts/ 2>/dev/null
mv next_steps_guide.bat obsolete/old_scripts/ 2>/dev/null
mv push_to_github_master.bat obsolete/old_scripts/ 2>/dev/null
mv quick-setup-script.bat obsolete/old_scripts/ 2>/dev/null
mv rollback.bat obsolete/old_scripts/ 2>/dev/null
mv git-status.bat obsolete/old_scripts/ 2>/dev/null
mv git-sync.bat obsolete/old_scripts/ 2>/dev/null
mv setup_github.bat obsolete/old_scripts/ 2>/dev/null

# Move test/diagnostic files
mv publishing_diagnostic.py obsolete/old_tests/ 2>/dev/null
mv verify_system_working.py obsolete/old_tests/ 2>/dev/null

# Move duplicate/old implementations
mv nntp_client_additions.py obsolete/old_scripts/ 2>/dev/null
mv nntp_connection_additions.py obsolete/old_scripts/ 2>/dev/null
mv publishing_system_additions.py obsolete/old_scripts/ 2>/dev/null

# Move the old workflow directory
mv .workflow obsolete/ 2>/dev/null

echo "Files moved to obsolete directory"
