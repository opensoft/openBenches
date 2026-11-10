[CmdletBinding()]
param(
    [switch]$Restart,
    [switch]$PrepareOnly,
    [string]$CodexHome = (Join-Path $env:USERPROFILE '.codex'),
    [string]$ProfileRoot = (Join-Path $env:USERPROFILE 'MultiCliProfiles\codex'),
    [string]$Python,
    [string[]]$EnrollOwner = @(),
    [string]$SeedOwner,
    [string]$EnrollIdentities
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# This entry point belongs exclusively to regular, Windows-native Codex.
# Beta/WSL uses the Python helper inside its own Linux environment/home.
$package = Get-AppxPackage -Name 'OpenAI.Codex' | Select-Object -First 1
if ($null -eq $package) { throw 'Regular Windows Codex package is not installed.' }
$packageRoot = $package.InstallLocation.TrimEnd('\') + '\'
$resolvedHome = [IO.Path]::GetFullPath($CodexHome)
if ($resolvedHome.StartsWith('\\')) { throw 'Regular Codex requires a local Windows home.' }
if (-not $Python) {
    $installedPython = @(Get-ChildItem -Path (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python*\python.exe') -ErrorAction SilentlyContinue)
    if ($installedPython.Count -gt 0) { $Python = $installedPython[0].FullName }
    else { $Python = (Get-Command python -ErrorAction Stop).Source }
}

function Get-SelectedDesktopProcess {
    @(Get-CimInstance Win32_Process | Where-Object {
        $_.ExecutablePath -and $_.ExecutablePath.StartsWith($packageRoot, [StringComparison]::OrdinalIgnoreCase)
    })
}

$processes = @(Get-SelectedDesktopProcess)
if ($processes.Count -gt 0) {
    if (-not $Restart) {
        if ($PrepareOnly) { throw 'Codex is running. Exit it normally before preparing state.' }
        Write-Output 'Codex is already running; project synchronization occurs on its next prepared launch.'
        Start-Process -FilePath (Join-Path $package.InstallLocation 'app\ChatGPT.exe') -WindowStyle Hidden
        return
    }
    $closed = $false
    foreach ($entry in $processes) {
        $process = Get-Process -Id $entry.ProcessId -ErrorAction SilentlyContinue
        if ($process -and $process.MainWindowHandle -ne 0) {
            $closed = $process.CloseMainWindow() -or $closed
        }
    }
    if (-not $closed) { throw 'No desktop window accepted a normal close. Quit Codex from its menu and retry.' }
    $deadline = [DateTime]::UtcNow.AddSeconds(60)
    while (@(Get-SelectedDesktopProcess).Count -gt 0 -and [DateTime]::UtcNow -lt $deadline) {
        Start-Sleep -Milliseconds 250
    }
    if (@(Get-SelectedDesktopProcess).Count -gt 0) { throw 'Codex is still running; no project state was changed.' }
}

$arguments = @((Join-Path $PSScriptRoot 'codex-project-state.py'), '--runtime', 'windows', '--home', $resolvedHome, '--profiles', $ProfileRoot, '--apply')
foreach ($owner in $EnrollOwner) { $arguments += @('--enroll-owner', $owner) }
if ($SeedOwner) { $arguments += @('--seed-owner', $SeedOwner) }
if ($EnrollIdentities) { $arguments += @('--enroll-identities', $EnrollIdentities) }
& $Python @arguments
if ($LASTEXITCODE -ne 0) { throw 'Project preparation failed. The selected desktop was left stopped.' }
if (-not $PrepareOnly) {
    $executable = Join-Path $package.InstallLocation 'app\ChatGPT.exe'
    if (-not (Test-Path -LiteralPath $executable)) { throw 'Selected package desktop executable was not found.' }
    Start-Process -FilePath $executable -WindowStyle Hidden
}
