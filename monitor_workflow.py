#!/usr/bin/env python3
"""
Monitor GitHub Actions Workflow Status
"""

import time
import json
import subprocess
from datetime import datetime
import requests
import os

class WorkflowMonitor:
    def __init__(self):
        self.repo = "contemptx/usenetsync"
        self.branch = "cursor/unify-indexing-and-download-systems-e32c"
        self.workflow_file = "gui-tests.yml"
        
    def check_workflow_status(self):
        """Check if workflow is configured and running"""
        print("\n" + "="*80)
        print(f"🔍 GITHUB ACTIONS WORKFLOW MONITOR")
        print("="*80)
        print(f"Repository: {self.repo}")
        print(f"Branch: {self.branch}")
        print(f"Workflow: {self.workflow_file}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
        
        # Check if workflow file exists in the repository
        print("📋 Checking workflow configuration...")
        workflow_url = f"https://github.com/{self.repo}/blob/{self.branch}/.github/workflows/{self.workflow_file}"
        print(f"   Workflow URL: {workflow_url}")
        
        # Get latest commit info
        print("\n📦 Latest commit on branch:")
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-1"],
                capture_output=True,
                text=True,
                cwd="/workspace"
            )
            print(f"   {result.stdout.strip()}")
        except Exception as e:
            print(f"   Error getting commit info: {e}")
        
        # Check workflow runs (using API without auth - limited info)
        print("\n🏃 Checking workflow runs...")
        api_url = f"https://api.github.com/repos/{self.repo}/actions/workflows"
        
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                workflows = data.get('workflows', [])
                
                gui_workflow = None
                for workflow in workflows:
                    if self.workflow_file in workflow.get('path', ''):
                        gui_workflow = workflow
                        break
                
                if gui_workflow:
                    print(f"   ✅ Workflow found: {gui_workflow['name']}")
                    print(f"   State: {gui_workflow['state']}")
                    print(f"   ID: {gui_workflow['id']}")
                    
                    # Check recent runs
                    runs_url = f"https://api.github.com/repos/{self.repo}/actions/workflows/{gui_workflow['id']}/runs"
                    runs_response = requests.get(runs_url)
                    if runs_response.status_code == 200:
                        runs_data = runs_response.json()
                        runs = runs_data.get('workflow_runs', [])
                        
                        if runs:
                            print(f"\n   Recent runs:")
                            for run in runs[:3]:
                                print(f"   - {run['created_at']}: {run['status']} ({run['conclusion'] or 'in progress'})")
                                print(f"     URL: {run['html_url']}")
                else:
                    print(f"   ⚠️ Workflow not found in repository")
                    print(f"   This could mean:")
                    print(f"   1. The workflow file hasn't been merged to main branch yet")
                    print(f"   2. GitHub hasn't indexed it yet (can take a few minutes)")
                    print(f"   3. The workflow has syntax errors")
            else:
                print(f"   ⚠️ Could not fetch workflows (status: {response.status_code})")
                if response.status_code == 404:
                    print("   Repository might be private. Use GitHub web interface to monitor.")
        except Exception as e:
            print(f"   Error checking workflows: {e}")
        
        # Provide direct links
        print("\n🔗 Direct Links:")
        print(f"   Actions Page: https://github.com/{self.repo}/actions")
        print(f"   Workflow File: {workflow_url}")
        print(f"   Branch: https://github.com/{self.repo}/tree/{self.branch}")
        
        # Check if this is first run
        print("\n📝 First Run Notes:")
        print("   If this is the first time the workflow is being added:")
        print("   1. The workflow might not trigger on the branch that adds it")
        print("   2. You may need to merge to main/develop first")
        print("   3. Or manually trigger it from the Actions tab")
        print("   4. Check the workflow file for 'on:' triggers")
        
        # Show workflow triggers
        print("\n⚡ Workflow Triggers:")
        print("   The workflow is configured to run on:")
        print("   - Push to: main, develop, feature/** branches")
        print("   - Pull requests to: main, develop")
        print("   - Manual dispatch (can trigger from Actions tab)")
        
        # Next steps
        print("\n🎯 Next Steps:")
        print("   1. Go to: https://github.com/{}/actions".format(self.repo))
        print("   2. Look for 'GUI Tests' workflow")
        print("   3. If not visible, check the 'All workflows' section")
        print("   4. You can manually trigger it using 'Run workflow' button")
        print("   5. Or create a PR to main/develop to trigger it")
        
        # Alternative trigger
        print("\n🔄 Alternative: Create a PR to trigger the workflow:")
        print("   Run these commands:")
        print("   ```")
        print("   git checkout -b test/gui-workflow")
        print("   git push origin test/gui-workflow")
        print("   # Then create a PR on GitHub to main or develop")
        print("   ```")

def main():
    monitor = WorkflowMonitor()
    
    print("Starting workflow monitoring...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            monitor.check_workflow_status()
            
            print("\n" + "-"*80)
            print("Refreshing in 30 seconds... (Press Ctrl+C to stop)")
            time.sleep(30)
            print("\033[2J\033[H")  # Clear screen
            
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")

if __name__ == "__main__":
    main()