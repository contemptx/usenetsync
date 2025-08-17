@echo off 
echo Rolling back last deployment... 
python consolidated_github_workflow.py rollback 
pause 
