#!/usr/bin/env python3
"""Fix output_json and output_error functions in cli.py"""

import re

# Read the cli.py file
with open('src/cli.py', 'r') as f:
    content = f.read()

# Replace output_json with click.echo(json.dumps
content = re.sub(r'return output_json\(', r'click.echo(json.dumps(', content)

# Replace output_error with click.echo(json.dumps({"error": 
content = re.sub(r'return output_error\(f?"([^"]+)"\)', r'click.echo(json.dumps({"error": "\1"}), err=True)', content)

# Handle output_error with f-strings
content = re.sub(r'return output_error\(f"([^}]+)\{([^}]+)\}([^"]+)"\)', 
                 r'click.echo(json.dumps({"error": f"\1{\2}\3"}), err=True)', content)

# Add return statements after click.echo where needed
lines = content.split('\n')
fixed_lines = []
for i, line in enumerate(lines):
    fixed_lines.append(line)
    # If we just added a click.echo for error or json output, add a return
    if 'click.echo(json.dumps(' in line and i + 1 < len(lines):
        next_line = lines[i + 1]
        # Check if the next line is not already a return and not part of a continuation
        if not next_line.strip().startswith('return') and not next_line.strip().startswith('}'):
            # Check indentation of current line
            indent = len(line) - len(line.lstrip())
            # If this looks like it was a return statement replacement, add return
            if 'err=True)' in line or ('}))' in line and 'err=' not in line):
                fixed_lines.append(' ' * indent + 'return')

content = '\n'.join(fixed_lines)

# Write the fixed file
with open('src/cli.py', 'w') as f:
    f.write(content)

print("Fixed cli.py - replaced output_json and output_error with click.echo")