@echo off
REM Quick Setup Script for Consolidated Workflow
REM Run this after saving consolidated_github_workflow.py

echo ================================================
echo Quick Setup for Consolidated GitHub Workflow
echo ================================================
echo.

REM Step 1: Create .workflow directory
echo Creating .workflow directory...
if not exist ".workflow" mkdir .workflow
echo Done.
echo.

REM Step 2: Create configuration manually
echo Creating workflow configuration...
(
echo {
echo   "branch": "main",
echo   "remote": "origin",
echo   "auto_deploy": true,
echo   "validate_before_deploy": true,
echo   "auto_rollback": true,
echo   "max_deployments_per_hour": 10,
echo   "check_syntax": true,
echo   "check_security": true,
echo   "check_performance": true,
echo   "fix_indentation": true,
echo   "create_workflows": true,
echo   "monitoring_interval": 5,
echo   "health_check_timeout": 30,
echo   "rollback_on_health_failure": true
echo }
) > .workflow\config.json

echo Configuration created at .workflow\config.json
echo.

REM Step 3: Install required dependencies
echo Installing required Python packages...
pip install watchdog psutil
echo.

REM Step 4: Generate GitHub workflows
echo Generating advanced GitHub workflows...
python consolidated_github_workflow.py setup
echo.

REM Step 5: Create helper scripts
echo Creating helper scripts...

echo @echo off > start_workflow.bat
echo echo Starting Consolidated GitHub Workflow Manager... >> start_workflow.bat
echo python consolidated_github_workflow.py start --daemon >> start_workflow.bat

echo @echo off > check_status.bat
echo echo Checking workflow status... >> check_status.bat
echo echo. >> check_status.bat
echo python consolidated_github_workflow.py status >> check_status.bat
echo pause >> check_status.bat

echo @echo off > deploy_now.bat
echo set /p MESSAGE="Enter commit message: " >> deploy_now.bat
echo python consolidated_github_workflow.py deploy --message "%%MESSAGE%%" >> deploy_now.bat
echo pause >> deploy_now.bat

echo @echo off > validate_file.bat
echo set /p FILE="Enter file to validate: " >> validate_file.bat
echo python consolidated_github_workflow.py validate --file "%%FILE%%" >> validate_file.bat
echo pause >> validate_file.bat

echo @echo off > rollback.bat
echo echo Rolling back last deployment... >> rollback.bat
echo python consolidated_github_workflow.py rollback >> rollback.bat
echo pause >> rollback.bat

echo @echo off > stop_workflow.bat
echo echo Stopping workflow monitoring... >> stop_workflow.bat
echo python consolidated_github_workflow.py stop >> stop_workflow.bat
echo pause >> stop_workflow.bat

echo.
echo Helper scripts created:
echo - start_workflow.bat   (Start monitoring)
echo - check_status.bat     (Check status)
echo - deploy_now.bat       (Manual deployment)
echo - validate_file.bat    (Validate specific file)
echo - rollback.bat         (Rollback deployment)
echo - stop_workflow.bat    (Stop monitoring)
echo.

REM Step 6: Test the setup
echo Testing the consolidated workflow system...
echo.
python consolidated_github_workflow.py status

echo.
echo ================================================
echo Setup Complete!
echo ================================================
echo.
echo Next steps:
echo 1. Run 'start_workflow.bat' to begin monitoring
echo 2. Make some code changes to test auto-deployment
echo 3. Use 'check_status.bat' to monitor the system
echo.
echo Your old workflow files have been backed up to: workflow_backup\
echo.
pause
