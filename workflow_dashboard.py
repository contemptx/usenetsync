#!/usr/bin/env python3
"""
GitHub Actions Workflow Dashboard
"""

import requests
import json
from datetime import datetime
import time

def display_dashboard():
    """Display comprehensive workflow status"""
    
    print("\033[2J\033[H")  # Clear screen
    print("="*80)
    print("📊 GITHUB ACTIONS DASHBOARD - UsenetSync")
    print("="*80)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    repo = "contemptx/usenetsync"
    
    # Get workflows
    workflows_url = f"https://api.github.com/repos/{repo}/actions/workflows"
    response = requests.get(workflows_url)
    
    if response.status_code == 200:
        data = response.json()
        workflows = data.get('workflows', [])
        
        print("\n📋 AVAILABLE WORKFLOWS:")
        print("-"*40)
        for w in workflows:
            status_icon = "✅" if w['state'] == 'active' else "⚠️"
            print(f"{status_icon} {w['name']}")
            print(f"   Path: {w['path']}")
            print(f"   ID: {w['id']}")
        
        # Check for GUI Tests workflow
        gui_workflow = None
        for w in workflows:
            if 'gui-tests' in w['path'].lower():
                gui_workflow = w
                break
        
        if not gui_workflow:
            print("\n⚠️  GUI Tests workflow not found in default branch")
            print("   The workflow file exists in branch: cursor/unify-indexing-and-download-systems-e32c")
            print("   But GitHub requires it to be in the default branch (master) first")
    
    # Get recent runs
    runs_url = f"https://api.github.com/repos/{repo}/actions/runs?per_page=10"
    runs_response = requests.get(runs_url)
    
    if runs_response.status_code == 200:
        runs_data = runs_response.json()
        runs = runs_data.get('workflow_runs', [])
        
        print("\n🏃 RECENT WORKFLOW RUNS:")
        print("-"*40)
        
        for run in runs[:5]:
            created = datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))
            
            # Status icon
            if run['status'] == 'completed':
                if run['conclusion'] == 'success':
                    icon = "✅"
                elif run['conclusion'] == 'failure':
                    icon = "❌"
                elif run['conclusion'] == 'cancelled':
                    icon = "🚫"
                else:
                    icon = "⚠️"
            else:
                icon = "🔄"
            
            print(f"\n{icon} {run['name']}")
            print(f"   Status: {run['status']} ({run['conclusion'] or 'running'})")
            print(f"   Branch: {run['head_branch']}")
            print(f"   Started: {created.strftime('%H:%M:%S')}")
            print(f"   URL: {run['html_url']}")
    
    print("\n" + "="*80)
    print("🎯 NEXT STEPS TO RUN GUI TESTS:")
    print("="*80)
    
    print("\nOption 1: MERGE TO MASTER (Recommended)")
    print("-"*40)
    print("1. Create a Pull Request:")
    print(f"   https://github.com/{repo}/pull/new/test/gui-workflow-trigger")
    print("2. Merge the PR to master")
    print("3. The GUI Tests workflow will then be available")
    print("4. Trigger it manually from Actions tab")
    
    print("\nOption 2: RUN EXISTING WORKFLOW")
    print("-"*40)
    print("The 'live-fullstack' workflow is already running on your branch")
    print("Latest run: https://github.com/contemptx/usenetsync/actions/runs/17122172425")
    
    print("\nOption 3: LOCAL TESTING")
    print("-"*40)
    print("Run the GUI tests locally:")
    print("  cd frontend")
    print("  npm run test:e2e")
    
    print("\n" + "="*80)
    print("📈 WORKFLOW STATISTICS:")
    print("="*80)
    
    # Count run statistics
    if runs_response.status_code == 200:
        success_count = sum(1 for r in runs if r.get('conclusion') == 'success')
        failure_count = sum(1 for r in runs if r.get('conclusion') == 'failure')
        running_count = sum(1 for r in runs if r['status'] != 'completed')
        
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {failure_count}")
        print(f"🔄 Running: {running_count}")
        print(f"📊 Total: {len(runs)}")
    
    print("\n" + "="*80)
    print("🔗 QUICK LINKS:")
    print("="*80)
    print(f"Actions: https://github.com/{repo}/actions")
    print(f"PR: https://github.com/{repo}/pull/new/test/gui-workflow-trigger")
    print(f"Branch: https://github.com/{repo}/tree/cursor/unify-indexing-and-download-systems-e32c")
    print("="*80)

def monitor_mode():
    """Continuous monitoring mode"""
    print("Starting continuous monitoring (Ctrl+C to stop)...")
    
    try:
        while True:
            display_dashboard()
            print("\nRefreshing in 30 seconds...")
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        monitor_mode()
    else:
        display_dashboard()
        print("\nTip: Run with --monitor for continuous updates")
        print("     python3 workflow_dashboard.py --monitor")