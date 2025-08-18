# PowerShell script to fix Tauri dialog permissions
# Run this from: C:\git\usenetsync

$capabilitiesFile = "C:\git\usenetsync\usenet-sync-app\src-tauri\capabilities\default.json"

$newContent = @'
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
'@

# Backup the original file
if (Test-Path $capabilitiesFile) {
    Copy-Item $capabilitiesFile "$capabilitiesFile.backup"
    Write-Host "Backed up original file to $capabilitiesFile.backup"
}

# Write the new content
$newContent | Out-File -FilePath $capabilitiesFile -Encoding UTF8
Write-Host "Updated $capabilitiesFile with dialog and filesystem permissions"

Write-Host "`nPermissions added:"
Write-Host "  - dialog:default (base dialog functionality)"
Write-Host "  - dialog:allow-open (file/folder selection)"
Write-Host "  - dialog:allow-save (save dialogs)"
Write-Host "  - dialog:allow-message (message boxes)"
Write-Host "  - dialog:allow-ask (question dialogs)"
Write-Host "  - dialog:allow-confirm (confirmation dialogs)"
Write-Host "  - fs:default (filesystem access)"
Write-Host "  - fs:allow-read (read files)"
Write-Host "  - fs:allow-write (write files)"
Write-Host "  - fs:allow-exists (check file existence)"
Write-Host "  - fs:allow-create (create files)"
Write-Host "  - fs:allow-remove (delete files)"
Write-Host "  - path:default (path operations)"

Write-Host "`nNext steps:"
Write-Host "1. Stop the development server (Ctrl+C) if it's running"
Write-Host "2. Restart with: cd usenet-sync-app && npm run tauri dev"
Write-Host "3. The folder selection dialog should now work!"