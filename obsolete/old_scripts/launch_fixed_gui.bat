@echo off
echo UsenetSync GUI Launcher
echo ========================

if exist "usenetsync_gui_main_complete.py" (
    echo Starting UsenetSync GUI...
    python usenetsync_gui_main_complete.py
) else (
    echo Complete GUI file not found!
    echo Please run deploy_fixed_gui.py first
    pause
)
