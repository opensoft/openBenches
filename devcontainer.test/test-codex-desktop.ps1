[CmdletBinding()]
param([Parameter(Mandatory = $true)][string]$Python)

$ErrorActionPreference = 'Stop'
$temporary = Join-Path ([IO.Path]::GetTempPath()) ('wb-codex-desktop-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $temporary | Out-Null
$global:WbTestPackage = Join-Path $temporary 'OpenAI.Codex_fixture'
$global:WbTestProcesses = @()
$global:WbTestLaunches = @()
$originalLog = $env:WB_CODEX_TEST_LOG
$env:WB_CODEX_TEST_LOG = Join-Path $temporary 'arguments.json'

function global:Get-AppxPackage {
    param([string]$Name)
    if ($Name -ne 'OpenAI.Codex') { throw 'Wrong desktop package selected' }
    [pscustomobject]@{ InstallLocation = $global:WbTestPackage }
}
function global:Get-CimInstance { param([string]$ClassName) $global:WbTestProcesses }
function global:Start-Process {
    param([string]$FilePath, [string]$WindowStyle)
    $global:WbTestLaunches += $FilePath
}
function Assert-True { param([bool]$Value, [string]$Message) if (-not $Value) { throw $Message } }

try {
    $source = Join-Path (Split-Path $PSScriptRoot -Parent) 'scripts\codex-desktop.ps1'
    Copy-Item -LiteralPath $source -Destination (Join-Path $temporary 'codex-desktop.ps1')
    New-Item -ItemType Directory -Path (Join-Path $global:WbTestPackage 'app') -Force | Out-Null
    New-Item -ItemType File -Path (Join-Path $global:WbTestPackage 'app\ChatGPT.exe') | Out-Null
    @'
import json, os, sys
from pathlib import Path
Path(os.environ['WB_CODEX_TEST_LOG']).write_text(json.dumps(sys.argv[1:]))
'@ | Set-Content -LiteralPath (Join-Path $temporary 'codex-project-state.py') -Encoding UTF8
    $launcher = Join-Path $temporary 'codex-desktop.ps1'
    $homePath = Join-Path $temporary 'windows-home'
    $profiles = Join-Path $temporary 'profiles'

    # A running Beta must neither block nor be selected by the Windows wrapper.
    $global:WbTestProcesses = @([pscustomobject]@{ ExecutablePath = (Join-Path $temporary 'OpenAI.CodexBeta_fixture\app\ChatGPT.exe') })
    & $launcher -Python $Python -CodexHome $homePath -ProfileRoot $profiles -EnrollOwner ('a' * 64)
    $arguments = Get-Content -LiteralPath $env:WB_CODEX_TEST_LOG -Raw | ConvertFrom-Json
    Assert-True ($arguments[1] -eq 'windows') 'Wrong runtime passed to helper'
    Assert-True ($arguments -contains $homePath) 'Windows home was not passed'
    Assert-True ($arguments -contains $profiles) 'Profile metadata root was not passed'
    Assert-True ($arguments -contains '--apply') 'Missing apply boundary'
    Assert-True ($global:WbTestLaunches.Count -eq 1) 'Regular desktop was not launched'
    Assert-True ($global:WbTestLaunches[0].StartsWith($global:WbTestPackage)) 'Another package was launched'

    # Preparing while regular Codex is running must leave the helper uncalled.
    Remove-Item -LiteralPath $env:WB_CODEX_TEST_LOG
    $global:WbTestProcesses = @([pscustomobject]@{ ExecutablePath = (Join-Path $global:WbTestPackage 'app\ChatGPT.exe') })
    $refused = $false
    try { & $launcher -Python $Python -CodexHome $homePath -PrepareOnly }
    catch { $refused = $_.Exception.Message -like '*running*' }
    Assert-True $refused 'Live desktop preparation was not refused'
    Assert-True (-not (Test-Path -LiteralPath $env:WB_CODEX_TEST_LOG)) 'Helper ran against live desktop'

    $global:WbTestProcesses = @()
    $refused = $false
    try { & $launcher -Python $Python -CodexHome '\\wsl.localhost\fixture\home\user\.codex' -PrepareOnly }
    catch { $refused = $_.Exception.Message -like '*local Windows*' }
    Assert-True $refused 'WSL-bound Windows home was not refused'
    Write-Output 'Windows desktop fixtures passed: package selection, runtime/home arguments, live-process refusal, and WSL isolation.'
}
finally {
    # Only remove this test's verified, unique temporary directory.
    $resolved = [IO.Path]::GetFullPath($temporary)
    $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\') + '\'
    if ($resolved.StartsWith($tempRoot) -and (Split-Path $resolved -Leaf).StartsWith('wb-codex-desktop-')) {
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
    if ($null -eq $originalLog) { Remove-Item Env:WB_CODEX_TEST_LOG -ErrorAction SilentlyContinue }
    else { $env:WB_CODEX_TEST_LOG = $originalLog }
    Remove-Item Function:Get-AppxPackage, Function:Get-CimInstance, Function:Start-Process -ErrorAction SilentlyContinue
    Remove-Variable WbTestPackage, WbTestProcesses, WbTestLaunches -Scope Global -ErrorAction SilentlyContinue
}
