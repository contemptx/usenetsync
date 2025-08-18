import subprocess, json, sys
cmd = [sys.executable, "src/cli.py", "list-folders"]
result = subprocess.run(cmd, capture_output=True, text=True)
print(f"Exit: {result.returncode}")
print(f"Stdout: {repr(result.stdout[:100]) if result.stdout else 'Empty'}")
print(f"Stderr: {repr(result.stderr[:100]) if result.stderr else 'None'}")
if result.stdout:
    try:
        json.loads(result.stdout)
        print("JSON: Valid")
    except: 
        print("JSON: Invalid")
else:
    print("ERROR: Empty output causes 'EOF while parsing'")
