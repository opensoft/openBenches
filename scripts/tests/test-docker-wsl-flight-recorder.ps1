#Requires -Version 7.0
$ErrorActionPreference = 'Stop'
$source = Join-Path (Split-Path $PSScriptRoot -Parent) 'docker-wsl-flight-recorder.ps1'
if (-not (Test-Path -LiteralPath $source)) { throw 'RED: recorder implementation does not exist yet.' }
. $source
$script:Passed = 0
function Assert-Check([bool]$Condition, [string]$Name) {
    if (-not $Condition) { throw "FAILED: $Name" }
    $script:Passed++
    Write-Output "PASS: $Name"
}
$temporaryState = Join-Path ([IO.Path]::GetTempPath()) ('docker-recorder-test-' + [guid]::NewGuid().ToString('N'))
try {
    Initialize-RecorderState $temporaryState
    $lockOne = Enter-RecorderLock $temporaryState
    $lockTwo = Enter-RecorderLock $temporaryState
    Assert-Check ($null -ne $lockOne -and $null -eq $lockTwo) 'exclusive lock prevents overlapping runs'
    $lockOne.Dispose()
    $lockThree = Enter-RecorderLock $temporaryState
    Assert-Check ($null -ne $lockThree) 'lock becomes available after exact owner exits'
    $lockThree.Dispose()

    $self = Get-Process -Id $PID
    $fresh = @{timestamp=[DateTimeOffset]::UtcNow.ToString('o');collector=@{process_id=$PID;process_start_time=$self.StartTime.ToString('o')};issues=@()}
    Assert-Check ((Get-RecorderFreshness $fresh 90) -eq 'current') 'fresh live identity is current'
    $fresh.timestamp = [DateTimeOffset]::UtcNow.AddMinutes(-5).ToString('o')
    Assert-Check ((Get-RecorderFreshness $fresh 90) -eq 'stale') 'old healthy sample is stale'
    $fresh.collector.process_start_time = [DateTimeOffset]::UtcNow.AddDays(-1).ToString('o')
    Assert-Check ((Get-RecorderFreshness $fresh 90) -eq 'stopped') 'PID reuse does not pass identity check'
    Assert-Check ((Get-RecorderFreshness $null 90) -eq 'unavailable') 'missing status is not healthy'
    Assert-Check (Test-RecorderDistroRunning "Ubuntu-24.04`r`ndocker-desktop`r`n" 'Ubuntu-24.04') 'running distro is identified by exact name'
    Assert-Check (-not (Test-RecorderDistroRunning "docker-desktop`nUbuntu-24.04-other" 'Ubuntu-24.04')) 'stopped distro is skipped rather than started'
    Assert-Check (Test-RecorderDistroRunning (([char]0xFEFF)+"Ubuntu-24.04"+([char]0)+"`r`n") 'Ubuntu-24.04') 'Windows WSL enumeration encoding is normalized'

    $memory = ConvertFrom-RecorderLines "anon 512`nfile 4096`nkernel 128`nzombie_leaders 2`nblocked_threads 3`npassword=do-not-retain"
    Assert-Check ($memory.anon -eq 512 -and $memory.file -eq 4096 -and $memory.kernel -eq 128) 'cache remains separate from process memory'
    Assert-Check ($memory.zombie_leaders -eq 2 -and $memory.blocked_threads -eq 3) 'zombies and blocked threads are distinct'
    Assert-Check (-not $memory.Contains('password')) 'guest parser drops non-allowlisted content'
    $cachedBench=@{sample=@{timestamp=[DateTimeOffset]::UtcNow.ToString('o');probe=@{outcome='success'};metrics=@{zombie_leaders=2}}}
    Assert-Check (@(Get-RecorderBenchIssues $cachedBench @('sample') 120) -contains 'zombies-sample') 'zombie finding remains visible between rotated bench probes'
    Assert-Check (@(Get-RecorderBenchIssues @{} @('missing') 120) -contains 'bench-sample-pending-missing') 'unmeasured bench is explicitly pending'
    $cacheHeavy=[ordered]@{MemAvailable_kib=49000000;MemTotal_kib=54000000;memory_psi_full=0}
    Assert-Check (@(Get-RecorderResourceIssues @{available=$true;available_mib=40000;commit_percent=45} $cacheHeavy).Count -eq 0) 'large cache with available RAM is not exhaustion'
    Assert-Check (@(Get-RecorderResourceIssues @{available=$true;available_mib=500;commit_percent=95} $cacheHeavy) -contains 'windows-memory-pressure') 'real Windows pressure is classified separately'
    Assert-Check (@(Get-RecorderResourceIssues @{available=$false} ([ordered]@{MemAvailable_kib=100;MemTotal_kib=10000;memory_psi_full=20})) -contains 'guest-memory-stalls') 'guest stalls remain visible when Windows metrics are unavailable'

    $logFixture = @(
      '{"component":"apiproxy","time":"2026-11-11T18:00:00Z","msg":"<< GET /v1.56/containers/aaaa/stats?stream=false"}',
      '{"component":"apiproxy","time":"2026-11-11T18:00:10Z","msg":"<< GET /v1.56/containers/bbbb/stats?stream=false"}',
      '{"component":"other","time":"2026-11-11T18:00:10Z","msg":"password=private-fixture"}',
      'partial-json')
    $polling = Measure-RecorderPolling $logFixture
    Assert-Check ($polling.stats_request_entries -eq 2 -and $polling.unique_containers -eq 2) 'polling aggregate counts request entries only'
    Assert-Check (($polling | ConvertTo-Json) -notmatch 'private-fixture|aaaa|bbbb') 'polling summary excludes raw content and identities'
    Assert-Check ($polling.window_seconds -eq 10) 'polling summary records observed window'
    $newPhase=Measure-RecorderPolling $logFixture ([DateTimeOffset]'2026-11-11T18:00:11Z')
    Assert-Check (-not $newPhase.available -and $newPhase.stats_request_entries -eq 0) 'previous-phase log entries cannot be attributed to the new phase'
    Assert-Check ((Measure-RecorderPolling @()).available -eq $false) 'missing log window is unavailable rather than zero'

    Write-RecorderJson (Join-Path $temporaryState 'fixture.json') @{value=1}
    Write-RecorderJson (Join-Path $temporaryState 'fixture.json') @{value=2}
    Assert-Check (((Get-Content (Join-Path $temporaryState 'fixture.json') -Raw | ConvertFrom-Json).value) -eq 2) 'atomic JSON replacement keeps latest value'
    1..10 | ForEach-Object { Add-RecorderSample $temporaryState @{value=('x'*100)} -MaxBytes 160 }
    Assert-Check (@(Get-ChildItem $temporaryState -Filter 'samples.jsonl*').Count -le 4) 'sample ring retains at most four files'
    1..16 | ForEach-Object { Add-RecorderIncident $temporaryState @{sequence=$_} }
    Assert-Check (@(Get-ChildItem $temporaryState -Filter 'incident-*.json').Count -eq 12) 'incident retention is bounded'

    $shellExecutable = (Get-Process -Id $PID).Path
    $script:OpenCircuits = @{}
    $result = Invoke-RecorderClient -Program $shellExecutable -Arguments @('-NoProfile','-Command','[Console]::WriteLine("fixture-ok")') -Circuit fixture -TimeoutSeconds 3
    Assert-Check ($result.outcome -eq 'success' -and $result.stdout.Trim() -eq 'fixture-ok') 'bounded client returns fixed probe output'
    $summary = Get-RecorderProbeSummary $result
    Assert-Check (-not $summary.Contains('stdout') -and -not $summary.Contains('stderr')) 'persisted probe metadata excludes raw streams'
    $watch = [Diagnostics.Stopwatch]::StartNew()
    $timeoutResult = Invoke-RecorderClient -Program $shellExecutable -Arguments @('-NoProfile','-Command','Start-Sleep -Seconds 20') -Circuit hung-fixture -TimeoutSeconds 1
    Assert-Check ($timeoutResult.outcome -eq 'timeout' -and $timeoutResult.owned_client_terminated -and $watch.Elapsed.TotalSeconds -lt 4) 'deadline terminates only owned fixture client'
    Assert-Check ($null -eq (Get-Process -Id $timeoutResult.process_id -ErrorAction SilentlyContinue)) 'timed-out owned client is gone'
    $latched = Invoke-RecorderClient -Program $shellExecutable -Arguments @('-NoProfile','-Command','throw "must not execute"') -Circuit hung-fixture -TimeoutSeconds 1
    Assert-Check ($latched.outcome -eq 'circuit-open' -and $null -eq $latched.process_id) 'timeout latches path and prevents a second client'
    Assert-Check ((Get-Process -Id $PID).Id -eq $PID) 'test parent remains alive'

    $script:RuntimeStateDirectory=$temporaryState
    Write-RecorderJson (Join-Path $temporaryState 'probe-inflight.json') @{circuit='wsl';process_id=$PID;stage='running'}
    $script:OpenCircuits=@{}
    Restore-RecorderCircuits $temporaryState
    Assert-Check ($script:OpenCircuits.ContainsKey('wsl')) 'interrupted probe latches its path after restart'
    Assert-Check ((Get-Process -Id $PID).Id -eq $PID) 'recovery never signals a previous run PID'
    Remove-Item -LiteralPath (Join-Path $temporaryState 'probe-inflight.json')
    $script:OpenCircuits=@{}
    Restore-RecorderCircuits $temporaryState
    Assert-Check ($script:OpenCircuits.ContainsKey('wsl')) 'circuit latch survives automatic process replacement'
    $script:RuntimeStateDirectory=$null

    $sourceText = Get-Content -Raw -LiteralPath $source
    Assert-Check ($sourceText -notmatch 'docker\s+(restart|stop|rm|prune)|wsl\s+--shutdown|Get-CimInstance.*CommandLine|Kill\(\$true\)') 'source excludes disruptive commands and process-tree termination'
    Assert-Check ($sourceText -notmatch "'stats'\s*,|--upload|ReadAllText.*credentials") 'routine collection avoids stats endpoint and uploads'
    $installer=Join-Path (Split-Path $PSScriptRoot -Parent) 'install-docker-wsl-flight-recorder.ps1'
    if(-not (Test-Path -LiteralPath $installer)) {throw 'RED: installer is missing'}
    $installPlan=& $shellExecutable -NoProfile -File $installer -Action Plan | ConvertFrom-Json
    Assert-Check ($installPlan.privilege -eq 'Limited' -and -not $installPlan.controls_existing_services) 'installer controls only a non-elevated recorder'
    Assert-Check ($installPlan.executable -notmatch 'WindowsApps|Codex' -and $installPlan.multiple_instances -eq 'IgnoreNew') 'standalone scheduled runtime does not depend on Codex'
    Write-Output "$script:Passed checks passed."
}
finally {
    # Delete only exact fixture files under this freshly created temporary directory.
    if (Test-Path -LiteralPath $temporaryState) {
        Get-ChildItem -LiteralPath $temporaryState -File | Remove-Item -Force
        Remove-Item -LiteralPath $temporaryState -ErrorAction SilentlyContinue
    }
}
