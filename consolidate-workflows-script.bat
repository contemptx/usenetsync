@echo off
REM Consolidate GitHub Workflows Script
REM This script helps migrate to the consolidated advanced workflow system

echo ================================================
echo GitHub Workflow Consolidation Script
echo ================================================
echo.

REM Step 1: Backup existing files
echo Step 1: Creating backups of existing workflows...
echo ================================================

if not exist "workflow_backup" mkdir workflow_backup

REM Backup existing workflow files
if exist "automated_github_workflow.py" (
    copy "automated_github_workflow.py" "workflow_backup\automated_github_workflow_old.py"
    echo Backed up: automated_github_workflow.py
)

if exist "gitops_manager.py" (
    copy "gitops_manager.py" "workflow_backup\gitops_manager_old.py" 
    echo Backed up: gitops_manager.py
)

if exist "update_github.py" (
    copy "update_github.py" "workflow_backup\update_github_old.py"
    echo Backed up: update_github.py
)

if exist "github_deploy.py" (
    copy "github_deploy.py" "workflow_backup\github_deploy_old.py"
    echo Backed up: github_deploy.py
)

echo.

REM Step 2: Save the new consolidated workflow
echo Step 2: Installing consolidated workflow manager...
echo ==================================================

REM Note: The consolidated_github_workflow.py content was created in the previous artifact
echo Please save the "Consolidated Advanced GitHub Workflow Manager" artifact as: consolidated_github_workflow.py
echo.
pause

REM Step 3: Create migration config
echo Step 3: Creating migration configuration...
echo ==========================================

REM Create .workflow directory
if not exist ".workflow" mkdir .workflow

REM Create temporary Python script for config creation
echo Creating unified configuration...
echo import json > temp_config.py
echo from pathlib import Path >> temp_config.py
echo. >> temp_config.py
echo # Load existing configs if they exist >> temp_config.py
echo config = { >> temp_config.py
echo     'branch': 'main', >> temp_config.py
echo     'remote': 'origin', >> temp_config.py
echo     'auto_deploy': True, >> temp_config.py
echo     'validate_before_deploy': True, >> temp_config.py
echo     'auto_rollback': True, >> temp_config.py
echo     'max_deployments_per_hour': 10, >> temp_config.py
echo     'check_syntax': True, >> temp_config.py
echo     'check_security': True, >> temp_config.py
echo     'check_performance': True, >> temp_config.py
echo     'fix_indentation': True, >> temp_config.py
echo     'create_workflows': True, >> temp_config.py
echo     'monitoring_interval': 5, >> temp_config.py
echo     'health_check_timeout': 30, >> temp_config.py
echo     'rollback_on_health_failure': True >> temp_config.py
echo } >> temp_config.py
echo. >> temp_config.py
echo # Try to load existing deploy_config.json >> temp_config.py
echo if Path('deploy_config.json').exists(): >> temp_config.py
echo     with open('deploy_config.json', 'r') as f: >> temp_config.py
echo         old_config = json.load(f) >> temp_config.py
echo         if 'repository' in old_config: >> temp_config.py
echo             config['branch'] = old_config['repository'].get('branch', 'main') >> temp_config.py
echo. >> temp_config.py
echo # Save new config >> temp_config.py
echo Path('.workflow').mkdir(exist_ok=True) >> temp_config.py
echo with open('.workflow/config.json', 'w') as f: >> temp_config.py
echo     json.dump(config, f, indent=2) >> temp_config.py
echo. >> temp_config.py
echo print('Created .workflow/config.json') >> temp_config.py

REM Run the temporary Python script
python temp_config.py

REM Clean up
del temp_config.py

echo.

REM Step 4: Clean up old GitHub workflows
echo Step 4: Updating GitHub workflows...
echo ====================================

if exist ".github\workflows" (
    echo Backing up existing workflows...
    if not exist "workflow_backup\.github\workflows" mkdir "workflow_backup\.github\workflows"
    xcopy ".github\workflows\*" "workflow_backup\.github\workflows\" /E /Y
    
    echo Removing old workflows...
    del /Q ".github\workflows\*.yml" 2>nul
    del /Q ".github\workflows\*.yaml" 2>nul
)

echo.

REM Step 5: Generate new advanced workflows
echo Step 5: Generating advanced GitHub workflows...
echo ===============================================

python consolidated_github_workflow.py setup

echo.

REM Step 6: Create helper scripts
echo Step 6: Creating helper scripts...
echo ==================================

REM Quick start script
echo @echo off > start_workflow.bat
echo echo Starting Consolidated GitHub Workflow Manager... >> start_workflow.bat
echo python consolidated_github_workflow.py start --daemon >> start_workflow.bat
echo start_workflow.bat

REM Status check script  
echo @echo off > check_status.bat
echo echo Checking workflow status... >> check_status.bat
echo python consolidated_github_workflow.py status >> check_status.bat
echo pause >> check_status.bat
echo check_status.bat

REM Manual deploy script
echo @echo off > deploy_now.bat
echo set /p MESSAGE="Enter commit message: " >> deploy_now.bat
echo python consolidated_github_workflow.py deploy --message "%%MESSAGE%%" >> deploy_now.bat
echo pause >> deploy_now.bat
echo deploy_now.bat

REM Validate file script
echo @echo off > validate_file.bat
echo set /p FILE="Enter file to validate: " >> validate_file.bat
echo python consolidated_github_workflow.py validate --file "%%FILE%%" >> validate_file.bat
echo pause >> validate_file.bat
echo validate_file.bat

echo Created helper scripts:
echo - start_workflow.bat (Start monitoring)
echo - check_status.bat (Check status)
echo - deploy_now.bat (Manual deployment)
echo - validate_file.bat (Validate specific file)

echo.

REM Step 7: Create removal script for old files
echo Step 7: Creating cleanup script...
echo ==================================

echo @echo off > remove_old_workflows.bat
echo echo This will remove old workflow files after confirming backups are good. >> remove_old_workflows.bat
echo echo. >> remove_old_workflows.bat
echo set /p CONFIRM="Are you sure you want to remove old workflow files? (y/N): " >> remove_old_workflows.bat
echo if /i "%%CONFIRM%%"=="y" ( >> remove_old_workflows.bat
echo     echo Removing old files... >> remove_old_workflows.bat
echo     if exist "automated_github_workflow.py" del "automated_github_workflow.py" >> remove_old_workflows.bat
echo     if exist "gitops_manager.py" del "gitops_manager.py" >> remove_old_workflows.bat
echo     if exist "update_github.py" del "update_github.py" >> remove_old_workflows.bat
echo     if exist "github_deploy.py" del "github_deploy.py" >> remove_old_workflows.bat
echo     if exist "deploy_config.json" move "deploy_config.json" "workflow_backup\" >> remove_old_workflows.bat
echo     echo Old files removed. Backups are in workflow_backup\ >> remove_old_workflows.bat
echo ) else ( >> remove_old_workflows.bat
echo     echo Cancelled. >> remove_old_workflows.bat
echo ) >> remove_old_workflows.bat
echo pause >> remove_old_workflows.bat

echo Created: remove_old_workflows.bat

echo.

REM Step 8: Test the new system
echo Step 8: Testing consolidated workflow...
echo ========================================

echo Running validation test...
python consolidated_github_workflow.py validate --file consolidated_github_workflow.py

echo.
echo Checking system status...
python consolidated_github_workflow.py status

echo.

REM Step 9: Show summary
echo ================================================
echo Consolidation Complete!
echo ================================================
echo.
echo The new consolidated workflow includes:
echo.
echo 1. ADVANCED FEATURES:
echo    - Automatic indentation fixing
echo    - Syntax validation with auto-repair
echo    - Security pattern detection
echo    - Performance monitoring
echo    - Automatic rollback on failures
echo    - Health monitoring with metrics
echo.
echo 2. GITHUB WORKFLOWS:
echo    - Advanced CI/CD pipeline
echo    - Security scanning (Trivy, Semgrep, OWASP)
echo    - Performance benchmarking
echo    - CodeQL analysis
echo    - Dependency updates
echo.
echo 3. HELPER SCRIPTS:
echo    - start_workflow.bat - Start monitoring
echo    - check_status.bat - Check current status
echo    - deploy_now.bat - Manual deployment
echo    - validate_file.bat - Validate specific files
echo.
echo 4. NEXT STEPS:
echo    1. Test the new workflow: start_workflow.bat
echo    2. Verify everything works correctly
echo    3. Run remove_old_workflows.bat to clean up old files
echo    4. Commit the changes to GitHub
echo.
echo All old files have been backed up to: workflow_backup\
echo.
pause
