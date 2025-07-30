#!/usr/bin/env python3
"""
Fix the SyntaxError: keyword argument repeated: enabled
"""

def fix_duplicate_enabled():
    """Fix the duplicate enabled parameter in configuration_manager.py"""
    
    print("Fixing duplicate 'enabled' parameter...")
    
    # Read the file
    with open('configuration_manager.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the problematic ServerConfig section
    lines = content.split('\n')
    
    # Look for the _create_default_config method and ServerConfig call
    in_serverconfig = False
    serverconfig_start = -1
    serverconfig_end = -1
    
    for i, line in enumerate(lines):
        if 'ServerConfig(' in line:
            in_serverconfig = True
            serverconfig_start = i
            print(f"Found ServerConfig call at line {i+1}")
        
        if in_serverconfig and (')' in line and 'enabled' in line):
            serverconfig_end = i
            break
    
    if serverconfig_start != -1 and serverconfig_end != -1:
        print(f"ServerConfig call spans lines {serverconfig_start+1} to {serverconfig_end+1}")
        
        # Extract the ServerConfig section
        serverconfig_lines = lines[serverconfig_start:serverconfig_end+1]
        
        print("Current ServerConfig call:")
        for i, line in enumerate(serverconfig_lines):
            print(f"  {serverconfig_start+i+1}: {line}")
        
        # Fix the ServerConfig call
        fixed_serverconfig = [
            "            ServerConfig(",
            "                name=\"Primary\",",
            "                hostname=\"news.example.com\",",
            "                port=563,",
            "                username=\"\",",
            "                password=\"\",",
            "                use_ssl=True,",
            "                max_connections=10,",
            "                priority=1,",
            "                enabled=True",
            "            )"
        ]
        
        # Replace the problematic section
        new_lines = (
            lines[:serverconfig_start] + 
            fixed_serverconfig + 
            lines[serverconfig_end+1:]
        )
        
        # Write back the fixed content
        with open('configuration_manager.py', 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        
        print("\n✓ Fixed the ServerConfig call")
        print("New ServerConfig call:")
        for line in fixed_serverconfig:
            print(f"  {line}")
        
        return True
    else:
        print("✗ Could not locate the problematic ServerConfig call")
        return False

def verify_syntax():
    """Verify the syntax is now correct"""
    
    print("\nVerifying syntax...")
    
    try:
        # Try to compile the file
        with open('configuration_manager.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        compile(content, 'configuration_manager.py', 'exec')
        print("✓ Syntax is now correct")
        return True
        
    except SyntaxError as e:
        print(f"✗ Syntax error still exists: {e}")
        print(f"   Line {e.lineno}: {e.text}")
        return False

def main():
    """Main function"""
    print("Fixing SyntaxError in configuration_manager.py")
    print("=" * 50)
    
    if fix_duplicate_enabled():
        if verify_syntax():
            print("\n" + "=" * 50)
            print("SUCCESS! Syntax error fixed.")
            print("=" * 50)
            print("\nNow try your CLI command:")
            print("  python cli.py init --name scott")
        else:
            print("\n" + "=" * 50)
            print("MANUAL FIX NEEDED")
            print("=" * 50)
            print("The automatic fix didn't resolve all syntax issues.")
            print("Please check configuration_manager.py around the ServerConfig call")
    else:
        print("\n" + "=" * 50)
        print("MANUAL FIX REQUIRED")
        print("=" * 50)
        print("1. Open configuration_manager.py")
        print("2. Go to line 774 (around the ServerConfig call)")
        print("3. Remove the duplicate 'enabled=True' parameter")
        print("4. Ensure proper syntax with commas")

if __name__ == '__main__':
    main()
