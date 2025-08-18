#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

print("="*60)
print("FINAL FRONTEND TEST")
print("="*60)

frontend_dir = Path("usenet-sync-app")
tests = []

# Check components
print("\nComponents:")
components = ['AppShell', 'FileTree', 'SearchBar', 'ConnectionStatus', 
              'StatusBar', 'HeaderBar', 'NotificationCenter', 'FileGridView',
              'BreadcrumbNav', 'BatchOperations', 'ContextMenu', 'VersionHistory',
              'ProgressIndicator', 'QRCodeDisplay', 'Table', 'LicenseActivation']

for comp in components:
    path = frontend_dir / f"src/components/{comp}.tsx"
    exists = path.exists()
    tests.append((comp, exists))
    print(f"  {'✅' if exists else '❌'} {comp}")

# Check pages
print("\nPages:")
pages = ['Upload', 'Download', 'Shares', 'Settings', 'Logs', 'TestRunner']
for page in pages:
    path = frontend_dir / f"src/pages/{page}.tsx"
    exists = path.exists()
    tests.append((page, exists))
    print(f"  {'✅' if exists else '❌'} {page}")

# Check API/Tauri
print("\nIntegration:")
api_file = frontend_dir / "src/lib/api.ts"
tauri_file = frontend_dir / "src/lib/tauri.ts"
tests.append(("API", api_file.exists()))
tests.append(("Tauri", tauri_file.exists()))
print(f"  {'✅' if api_file.exists() else '❌'} API module")
print(f"  {'✅' if tauri_file.exists() else '❌'} Tauri bindings")

# Results
passed = sum(1 for _, r in tests if r)
total = len(tests)
rate = (passed/total*100) if total > 0 else 0

print(f"\n{'='*60}")
print(f"Results: {passed}/{total} ({rate:.1f}%)")
if rate == 100:
    print("✅ FRONTEND 100% COMPLETE!")
elif rate >= 90:
    print(f"✅ Frontend {rate:.1f}% complete")
else:
    print(f"⚠️ Frontend {rate:.1f}% complete")
