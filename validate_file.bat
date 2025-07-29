@echo off 
set /p FILE="Enter file to validate: " 
python consolidated_github_workflow.py validate --file "%FILE%" 
pause 
