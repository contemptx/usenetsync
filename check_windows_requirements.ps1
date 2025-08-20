# PowerShell script to check and install all required modules on Windows

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "CHECKING USENETSYNC REQUIREMENTS" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Critical modules to check
$criticalModules = @{
    "psycopg2-binary" = "PostgreSQL database (for production)"
    "pynntp" = "NNTP/Usenet client (CRITICAL!)"
    "cryptography" = "Encryption support"
    "PyNaCl" = "Ed25519 keys"
    "fastapi" = "API backend"
    "uvicorn" = "ASGI server"
    "redis" = "Caching"
}

Write-Host "`nChecking critical modules..." -ForegroundColor Yellow

$missing = @()

foreach ($module in $criticalModules.Keys) {
    $importName = $module
    if ($module -eq "pynntp") { $importName = "nntp" }
    if ($module -eq "psycopg2-binary") { $importName = "psycopg2" }
    if ($module -eq "PyNaCl") { $importName = "nacl" }
    
    $result = python -c "import $importName; print('OK')" 2>$null
    if ($result -eq "OK") {
        Write-Host "✅ $module - $($criticalModules[$module])" -ForegroundColor Green
    } else {
        Write-Host "❌ $module - $($criticalModules[$module]) - NOT INSTALLED" -ForegroundColor Red
        $missing += $module
    }
}

if ($missing.Count -gt 0) {
    Write-Host "`n⚠️ Missing modules: $($missing -join ', ')" -ForegroundColor Yellow
    Write-Host "`nInstalling missing modules..." -ForegroundColor Cyan
    
    foreach ($module in $missing) {
        Write-Host "Installing $module..." -ForegroundColor Yellow
        pip install $module
    }
} else {
    Write-Host "`n✅ All critical modules are installed!" -ForegroundColor Green
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "INSTALLATION COMPLETE" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan