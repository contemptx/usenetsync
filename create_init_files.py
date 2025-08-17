#!/usr/bin/env python3
"""Create __init__.py files for proper package structure"""

import os
from pathlib import Path

# Define package directories
packages = [
    'src',
    'src/core',
    'src/networking',
    'src/database',
    'src/security',
    'src/upload',
    'src/download',
    'src/indexing',
    'src/monitoring',
    'src/config',
    'src/utils',
    'tests',
    'tests/integration',
    'tests/e2e',
    'tests/fixtures',
]

# Create __init__.py files
for package in packages:
    init_file = Path(package) / '__init__.py'
    if not init_file.exists():
        init_file.parent.mkdir(parents=True, exist_ok=True)
        with open(init_file, 'w') as f:
            f.write(f'"""Package: {package}"""\n')
        print(f"Created {init_file}")

print("Package structure initialized")
