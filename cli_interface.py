# UsenetSync PowerShell Module
# Provides native PowerShell cmdlets for UsenetSync operations

# Module initialization
$script:UsenetSyncPath = Join-Path $PSScriptRoot "cli_interface.py"
$script:PythonPath = "python"

# Helper function to run Python CLI
function Invoke-UsenetSync {
    param(
        [Parameter(Mandatory=$true)]
        [string[]]$Arguments,
        
        [string]$ConfigPath,
        [switch]$Verbose
    )
    
    $args = @()
    
    if ($ConfigPath) {
        $args += "-c", $ConfigPath
    }
    
    if ($Verbose) {
        $args += "-v"
    }
    
    $args += $Arguments
    
    & $script:PythonPath $script:UsenetSyncPath $args
}

# Initialize user profile
function Initialize-UsenetSync {
    [CmdletBinding()]
    param(
        [string]$DisplayName,
        [string]$ConfigPath
    )
    
    $args = @("init")
    
    if ($DisplayName) {
        $args += "--name", $DisplayName
    }
    
    Invoke-UsenetSync -Arguments $args -ConfigPath $ConfigPath -Verbose:$VerbosePreference
}

# Index a folder
function New-UsenetIndex {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true, ValueFromPipeline=$true)]
        [string]$Path,
        
        [string]$FolderId,
        [switch]$ReIndex,
        [string]$ConfigPath