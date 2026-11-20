param([Parameter(Mandatory=$true)][string]$Python)
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSHOME 'Modules/Microsoft.PowerShell.Security')
Set-Location $PSScriptRoot
$slot=Join-Path $PSScriptRoot 'slots/ubuntu24-2'
New-Item -ItemType Directory -Path $slot -Force | Out-Null
$watcher=[Threading.Mutex]::new($false,'Local\EagleFleetUbuntu24Parallel')
if(!$watcher.WaitOne(0)){exit 0}
try {
    while($true){
        $secure=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'service-auth.dpapi') -Raw | ConvertTo-SecureString
        try {
            $env:GH_TOKEN=[Net.NetworkCredential]::new('',$secure).Password
            & $Python (Join-Path $PSScriptRoot 'parallel.py') 2>> (Join-Path $slot 'watcher-error.log')
        } finally {
            Remove-Item Env:GH_TOKEN -ErrorAction SilentlyContinue
            $secure.Dispose()
        }
        $settings=(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'config.json') -Raw | ConvertFrom-Json).parallel_capacity
        if((Test-Path -LiteralPath (Join-Path $PSScriptRoot 'STOP')) -or
           (Test-Path -LiteralPath (Join-Path $slot 'STOP')) -or
           !$settings.enabled -or $settings.ubuntu24_workers -ne 2){exit 0}
        Start-Sleep -Seconds 15
    }
} finally {$watcher.ReleaseMutex();$watcher.Dispose()}
