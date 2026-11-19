[CmdletBinding()]
param(
    [ValidateSet('Install', 'Status', 'Disable')]
    [string]$Action = 'Install',

    [Parameter(Mandatory)]
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]*$')]
    [string]$Distribution,

    [ValidatePattern('^[A-Za-z_][A-Za-z0-9._-]*$')]
    [string]$LinuxUser,

    [ValidatePattern('^/[^''"\r\n]+/setup_profiles\.py$')]
    [string]$Launcher
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$profiles = @('claude', 'openai')
$taskNames = @{}
foreach ($profile in $profiles) {
    $taskNames[$profile] = "workBenches OpenCode $profile ($Distribution, $($identity.User.Value))"
}

function Get-Desktop {
    $paths = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\ai.opencode.desktop\OpenCode.exe'),
        (Join-Path $env:ProgramFiles 'ai.opencode.desktop\OpenCode.exe')
    )
    foreach ($path in $paths) {
        if (Test-Path -LiteralPath $path -PathType Leaf) {
            $version = (Get-Item -LiteralPath $path).VersionInfo.ProductVersion
            if ($version -match '^(\d+\.\d+\.\d+)' -and [version]$Matches[1] -ge [version]'2.3.1') {
                return $path
            }
        }
    }
}

if ($Action -eq 'Status') {
    $registered = @($profiles | Where-Object {
        $task = Get-ScheduledTask -TaskName $taskNames[$_] -ErrorAction SilentlyContinue
        $null -ne $task -and $task.State -ne 'Disabled'
    })
    if ($registered.Count -eq $profiles.Count -and (Get-Desktop)) { 'installed' }
    elseif ($registered.Count -eq 0) { 'not installed' }
    else { 'needs check' }
    exit 0
}

if ($Action -eq 'Disable') {
    foreach ($profile in $profiles) {
        $name = $taskNames[$profile]
        if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) {
            Disable-ScheduledTask -TaskName $name | Out-Null
        }
    }
    Write-Output 'OpenCode profile autostart is disabled. Current servers, Desktop, and sign-ins are retained.'
    exit 0
}

if (!$LinuxUser -or !$Launcher) { throw 'Install requires the Linux user and staged launcher path.' }

if (Get-Desktop) {
    Write-Output 'Reusing the installed OpenCode Desktop application.'
} else {
    Write-Output 'Downloading OpenCode Desktop for Windows.'
    $arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64' -or $env:PROCESSOR_ARCHITEW6432 -eq 'ARM64') { 'arm64' } else { 'x64' }
    $digests = @{
        x64 = '1e73b4f49f591971f4ad61c5a39b284bf74d41f50ca1b84e68ccf2ab2be91e8d'
        arm64 = '2e0f690e6cce23ff352b973503d78c08d24a12d57029797df91b6220f6f29138'
    }
    $installer = Join-Path ([IO.Path]::GetTempPath()) ("workbenches-opencode-{0}.exe" -f [guid]::NewGuid())
    try {
        $url = "https://github.com/anomalyco/opencode/releases/download/v2.3.2/opencode-desktop-win-$arch.exe"
        Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $installer
        if ((Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash -ne $digests[$arch]) {
            throw 'OpenCode Desktop installer SHA-256 does not match the published release.'
        }
        Write-Output 'Running the verified OpenCode Desktop installer.'
        $setup = Start-Process -FilePath $installer -ArgumentList '/S' -WindowStyle Hidden -Wait -PassThru
        if ($setup.ExitCode -ne 0 -or !(Get-Desktop)) { throw "OpenCode Desktop installation did not verify (exit $($setup.ExitCode))." }
    }
    finally {
        if (Test-Path -LiteralPath $installer) { Remove-Item -LiteralPath $installer -Force }
    }
}

$powerShell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$wsl = Join-Path $env:SystemRoot 'System32\wsl.exe'
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $identity.Name
$principal = New-ScheduledTaskPrincipal -UserId $identity.Name -LogonType Interactive -RunLevel Limited
$options = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -MultipleInstances IgnoreNew -RestartCount 10 -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero)

foreach ($profile in $profiles) {
    $name = $taskNames[$profile]
    $existing = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if ($null -ne $existing -and $existing.State -eq 'Running') {
        Write-Output "Retaining the running $profile task. Installed launcher changes take effect on its next start."
        continue
    }
    $command = '& ''{0}'' --distribution ''{1}'' --user ''{2}'' --exec /usr/bin/python3 ''{3}'' supervise --profile {4}; exit $LASTEXITCODE' -f $wsl, $Distribution, $LinuxUser, $Launcher, $profile
    # Encode the command so paths containing spaces survive Task Scheduler and PowerShell argument parsing.
    $encodedCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($command))
    $arguments = "-NoProfile -NonInteractive -WindowStyle Hidden -EncodedCommand $encodedCommand"
    $taskAction = New-ScheduledTaskAction -Execute $powerShell -Argument $arguments
    Register-ScheduledTask -TaskName $name -Action $taskAction -Trigger $trigger -Settings $options `
        -Principal $principal -Description "Runs the private OpenCode $profile server in $Distribution while signed in." -Force | Out-Null
    Start-ScheduledTask -TaskName $name
    Write-Output "OpenCode $profile autostart registered and started."
}
