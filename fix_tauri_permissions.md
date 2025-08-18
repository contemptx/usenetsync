# Fix Tauri Dialog Permissions

The "dialog.open not allowed" error occurs because the Tauri app needs proper permissions to open file dialogs.

## Solution

Edit the file `C:\git\usenetsync\usenet-sync-app\src-tauri\capabilities\default.json` and update it to:

```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "Capability for the main window",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "shell:default",
    "dialog:default",
    "dialog:allow-open",
    "dialog:allow-save",
    "dialog:allow-message",
    "dialog:allow-ask",
    "dialog:allow-confirm",
    "fs:default",
    "fs:allow-read",
    "fs:allow-write",
    "fs:allow-exists",
    "fs:allow-create",
    "fs:allow-remove",
    "path:default"
  ]
}
```

## After Making Changes

1. Stop the development server if it's running (Ctrl+C)
2. Rebuild the Tauri app:
   ```bash
   cd C:\git\usenetsync\usenet-sync-app
   npm run tauri dev
   ```

This will give the app permission to:
- Open file/folder selection dialogs
- Save files
- Show message dialogs
- Access the file system

## Alternative: Add to Cargo.toml

If the above doesn't work, you can also add the permissions to `src-tauri/Cargo.toml`:

```toml
[dependencies.tauri]
version = "2.0"
features = ["dialog-all", "fs-all", "path-all"]
```