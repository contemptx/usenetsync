@echo off 
set /p MESSAGE="Enter commit message: " 
python consolidated_github_workflow.py deploy --message "%MESSAGE%" 
pause 
