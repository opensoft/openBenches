#Requires -Version 7.0
[CmdletBinding()]
param([ValidateSet('Install','Start','Stop','Status','Plan')][string]$Action='Status')
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$taskName='workBenches Docker WSL Flight Recorder'
$installDirectory=Join-Path $env:LOCALAPPDATA 'workBenches/docker-wsl-diagnostics'
$stateDirectory=Join-Path $installDirectory 'state'
$installedScript=Join-Path $installDirectory 'docker-wsl-flight-recorder.ps1'
$sourceScript=Join-Path $PSScriptRoot 'docker-wsl-flight-recorder.ps1'
# Deliberately do not use a PowerShell executable bundled inside an agent package.
$powerShellPath=Join-Path $env:ProgramFiles 'PowerShell/7/pwsh.exe'
$arguments='-NoProfile -NonInteractive -WindowStyle Hidden -File "{0}" -Mode Watch -StateDirectory "{1}"' -f $installedScript,$stateDirectory
if ($Action -eq 'Plan') {
    @{task_name=$taskName;install_directory=$installDirectory;state_directory=$stateDirectory;executable=$powerShellPath;
        arguments=$arguments;privilege='Limited';multiple_instances='IgnoreNew';periodic_supervision_minutes=1;
        controls_existing_services=$false;uploads_data=$false}|ConvertTo-Json
    exit 0
}
if (-not (Test-Path -LiteralPath $powerShellPath)) {throw 'Standalone Windows PowerShell 7 is required; no package installation was attempted.'}
$existingTask=Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($Action -eq 'Status') {
    if ($null -eq $existingTask -or -not (Test-Path -LiteralPath $installedScript)) {@{installed=$false}|ConvertTo-Json; exit 1}
    $output=& $powerShellPath -NoProfile -File $installedScript -Mode Status -StateDirectory $stateDirectory
    $statusExit=$LASTEXITCODE
    $status=$output | ConvertFrom-Json -AsHashtable
    @{installed=$true;task_state=$existingTask.State.ToString();source_sha256=(Get-FileHash -LiteralPath $installedScript -Algorithm SHA256).Hash;
        state_directory=$stateDirectory;status=$status}|ConvertTo-Json -Depth 18
    exit $statusExit
}
if ($Action -eq 'Stop') {
    if ($null -ne $existingTask) {
        Disable-ScheduledTask -TaskName $taskName | Out-Null
        Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    }
    @{stopped=$true;task_name=$taskName;evidence_preserved=$true}|ConvertTo-Json; exit 0
}
if ($Action -eq 'Start') {
    if ($null -eq $existingTask) {throw 'Recorder is not installed.'}
    Enable-ScheduledTask -TaskName $taskName | Out-Null
    Start-ScheduledTask -TaskName $taskName
    @{start_requested=$true;task_name=$taskName;probe_latches_preserved=$true}|ConvertTo-Json; exit 0
}
if ($null -ne $existingTask -and $existingTask.State -eq 'Running') {throw 'Stop this recorder before updating its installed source. Existing services are unaffected.'}
New-Item -ItemType Directory -Path $installDirectory -Force | Out-Null
Copy-Item -LiteralPath $sourceScript -Destination $installedScript -Force
$identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name
$taskAction=New-ScheduledTaskAction -Execute $powerShellPath -Argument $arguments -WorkingDirectory $installDirectory
$logon=New-ScheduledTaskTrigger -AtLogOn -User $identity
$supervision=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1)
$settings=New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
$principal=New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $taskName -Action $taskAction -Trigger @($logon,$supervision) -Settings $settings -Principal $principal -Description 'Local metrics-only Docker/WSL diagnostics. No service recovery, user-process termination or uploads.' -Force | Out-Null
Start-ScheduledTask -TaskName $taskName
@{installed=$true;task_name=$taskName;installed_script=$installedScript;state_directory=$stateDirectory;
    source_sha256=(Get-FileHash -LiteralPath $installedScript -Algorithm SHA256).Hash;start_requested=$true}|ConvertTo-Json
