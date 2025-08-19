import subprocess, json, sys, tempfile, shutil
from pathlib import Path

def run_cmd(cmd):
    result = subprocess.run([sys.executable, "/workspace/src/cli.py"] + cmd.split(), 
                          capture_output=True, text=True, timeout=30)
    return result

# Create test dir
test_dir = tempfile.mkdtemp(prefix="test_")
print(f"Test dir: {test_dir}")

# Add files
for i in range(3):
    Path(test_dir, f"file_{i}.txt").write_text(f"Content {i}\n" * 100)

# Add folder
result = run_cmd(f"add-folder --path {test_dir} --name TestFolder")
print(f"Add folder: {result.returncode == 0}")
if result.stdout:
    data = json.loads(result.stdout)
    folder_id = data.get('folder_id')
    print(f"Folder ID: {folder_id}")

# List folders
result = run_cmd("list-folders")
if result.stdout:
    folders = json.loads(result.stdout)
    print(f"Folders found: {len(folders)}")

# Clean up
shutil.rmtree(test_dir)
print("Done")
