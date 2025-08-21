#!/usr/bin/env python3
"""
Check GitHub Actions Workflow Status
"""

import requests
import json
from datetime import datetime

def check_workflow():
    print("\n" + "="*80)
    print("🔍 CHECKING GITHUB ACTIONS STATUS")
    print("="*80)
    
    repo = "contemptx/usenetsync"
    
    # Check workflows
    print("\n📋 Fetching workflow information...")
    workflows_url = f"https://api.github.com/repos/{repo}/actions/workflows"
    
    try:
        response = requests.get(workflows_url)
        print(f"API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            workflows = data.get('workflows', [])
            
            print(f"\nFound {len(workflows)} workflow(s) in the repository:")
            for workflow in workflows:
                print(f"\n  📄 {workflow['name']}")
                print(f"     Path: {workflow['path']}")
                print(f"     State: {workflow['state']}")
                print(f"     ID: {workflow['id']}")
                
                # Check recent runs for this workflow
                runs_url = workflow['runs_url']
                runs_response = requests.get(runs_url + "?per_page=3")
                
                if runs_response.status_code == 200:
                    runs_data = runs_response.json()
                    runs = runs_data.get('workflow_runs', [])
                    
                    if runs:
                        print(f"     Recent runs:")
                        for run in runs:
                            created = datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))
                            status_icon = "✅" if run['conclusion'] == 'success' else "❌" if run['conclusion'] == 'failure' else "🔄"
                            print(f"       {status_icon} {created.strftime('%Y-%m-%d %H:%M')} - {run['status']} ({run['conclusion'] or 'running'})")
                            print(f"          Branch: {run['head_branch']}")
                            print(f"          URL: {run['html_url']}")
                    else:
                        print(f"     No recent runs")
        
        elif response.status_code == 404:
            print("\n⚠️ Repository not found or is private")
            print("This could mean:")
            print("1. The repository is private (API requires authentication)")
            print("2. There's a typo in the repository name")
            
        else:
            print(f"\n⚠️ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "="*80)
    print("📌 NEXT STEPS:")
    print("="*80)
    print("\n1. Check the Actions tab directly:")
    print(f"   https://github.com/{repo}/actions")
    print("\n2. If billing issue is resolved, you should see:")
    print("   - 'GUI Tests' workflow listed")
    print("   - Recent run from 'ci: trigger workflow run' commit")
    print("\n3. If no workflow appears:")
    print("   - Billing might still be an issue")
    print("   - Try manual trigger from Actions tab")
    print("   - Create a PR to trigger the workflow")
    print("\n4. Manual trigger instructions:")
    print("   a. Go to Actions tab")
    print("   b. Select 'GUI Tests' workflow")
    print("   c. Click 'Run workflow' button")
    print("   d. Select branch: cursor/unify-indexing-and-download-systems-e32c")
    print("   e. Click green 'Run workflow' button")
    
    print("\n" + "="*80)
    print("💡 BILLING ISSUE RESOLUTION:")
    print("="*80)
    print("\nIf workflows are disabled due to billing:")
    print("1. Go to: https://github.com/settings/billing")
    print("2. Check your GitHub Actions usage")
    print("3. Update payment method if needed")
    print("4. Or switch to GitHub Free (2000 minutes/month)")
    print("\nOnce resolved, workflows should automatically re-enable.")
    print("="*80)

if __name__ == "__main__":
    check_workflow()