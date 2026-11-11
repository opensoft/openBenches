#Requires -Version 7.0
[CmdletBinding()]
param(
    [ValidateSet('Once','Watch','Status','Mark','ResetProbes')][string]$Mode = 'Once',
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]*$')][string]$Distribution = 'Ubuntu-24.04',
    [ValidateScript({ $_ | ForEach-Object { if ($_ -notmatch '^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$') { throw 'Invalid container name' } }; $true })]
    [string[]]$Containers = @('py-bench','cloud-bench','m365-bench'),
    [ValidateRange(10,3600)][int]$IntervalSeconds = 30,
    [ValidateRange(1,10)][int]$ProbeTimeoutSeconds = 8,
    [string]$StateDirectory = (Join-Path $env:LOCALAPPDATA 'workBenches/docker-wsl-diagnostics/state'),
    [ValidateSet('baseline','dashboard-open','dashboard-closed','dashboard-reopened')][string]$Phase = 'baseline'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:OpenCircuits = @{}
$script:UnkillableClient = $false
$script:PersistenceFailure = $false
$script:BenchCursor = 0
$script:BenchCache = @{}
$script:RuntimeStateDirectory = $null

# Fixed buffers drain both pipes without retaining unlimited diagnostic output.
if (-not ('RecorderBoundedText' -as [type])) {
    Add-Type -TypeDefinition @'
using System.IO;
using System.Text;
using System.Threading.Tasks;
public sealed class RecorderBoundedText {
    public string Text { get; private set; }
    public bool LimitExceeded { get; private set; }
    public static async Task<RecorderBoundedText> ReadAsync(StreamReader reader, int limit, bool retain) {
        var result = new RecorderBoundedText();
        var buffer = new char[4096];
        var text = retain ? new StringBuilder() : null;
        int total = 0, count;
        while ((count = await reader.ReadAsync(buffer, 0, buffer.Length).ConfigureAwait(false)) > 0) {
            int remaining = limit - total;
            if (retain && remaining > 0) text.Append(buffer, 0, System.Math.Min(count, remaining));
            if (count > remaining) result.LimitExceeded = true;
            total = System.Math.Min(limit, total + count);
        }
        result.Text = retain ? text.ToString() : "";
        return result;
    }
}
'@
}

function Save-RecorderCircuits {
    if ($script:RuntimeStateDirectory) { Write-RecorderJson (Join-Path $script:RuntimeStateDirectory 'circuits.json') $script:OpenCircuits }
}

function Restore-RecorderCircuits([string]$Directory) {
    $path=Join-Path $Directory 'circuits.json'
    if (Test-Path -LiteralPath $path) {
        $saved=Get-Content -LiteralPath $path -Raw | ConvertFrom-Json -AsHashtable
        foreach ($name in @('docker','wsl','bench')) { if ($saved.ContainsKey($name)) {$script:OpenCircuits[$name]=$true} }
    }
    $inflight=Join-Path $Directory 'probe-inflight.json'
    if (Test-Path -LiteralPath $inflight) {
        $pending=Get-Content -LiteralPath $inflight -Raw | ConvertFrom-Json -AsHashtable
        if ($pending.circuit -notin @('docker','wsl','bench')) { throw 'Unrecognized interrupted probe; manual inspection required.' }
        $script:OpenCircuits[$pending.circuit]=$true
        Save-RecorderCircuits
        # Do not signal a PID inherited from another collector run.
    }
}

function Initialize-RecorderState([string]$Directory) {
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    if ((Get-Item -LiteralPath $Directory).Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw 'Recorder state directory must not be a reparse point.'
    }
    $ownerPath = Join-Path $Directory '.recorder-owner'
    if (Test-Path -LiteralPath $ownerPath) {
        if ((Get-Content -LiteralPath $ownerPath -Raw).Trim() -ne 'workbenches-docker-wsl-recorder-v1') { throw 'Unrecognized state owner.' }
    } else {
        if (@(Get-ChildItem -LiteralPath $Directory -Force).Count) { throw 'Refusing to adopt a nonempty unowned directory.' }
        [IO.File]::WriteAllText($ownerPath, 'workbenches-docker-wsl-recorder-v1')
    }
}

function Enter-RecorderLock([string]$Directory) {
    try { return [IO.File]::Open((Join-Path $Directory 'recorder.lock'), 'OpenOrCreate', 'ReadWrite', 'None') }
    catch [IO.IOException] { return $null }
}

function Write-RecorderJson([string]$Path, [object]$Value) {
    $temporaryPath = Join-Path (Split-Path $Path -Parent) ('recording-' + [guid]::NewGuid().ToString('N') + '.tmp')
    try {
        [IO.File]::WriteAllText($temporaryPath, ($Value | ConvertTo-Json -Depth 16), [Text.UTF8Encoding]::new($false))
        # Same-directory File.Move(overwrite) uses a replacing rename, unlike
        # Move-Item -Force / ReplaceFile's observed Windows missing-path gaps.
        # Preserve the previous good record on a sharing/access conflict.
        for ($attempt=0; ; $attempt++) {
            try {
                [IO.File]::Move($temporaryPath,$Path,$true)
                break
            } catch {
                $nativeError=$_.Exception.GetBaseException().HResult -band 0xFFFF
                if ($nativeError -notin @(5,32,33) -or $attempt -ge 19) {throw}
                Start-Sleep -Milliseconds 10
            }
        }
    } finally { if (Test-Path -LiteralPath $temporaryPath) { Remove-Item -LiteralPath $temporaryPath -Force } }
}

function Add-RecorderSample([string]$Directory, [object]$Sample, [int]$MaxBytes = 4MB) {
    $samplePath = Join-Path $Directory 'samples.jsonl'
    $line = ($Sample | ConvertTo-Json -Depth 16 -Compress) + [Environment]::NewLine
    $size = [Text.Encoding]::UTF8.GetByteCount($line)
    if ($size -gt $MaxBytes) { throw 'Sample exceeds ring-file limit.' }
    if ((Test-Path -LiteralPath $samplePath) -and (Get-Item -LiteralPath $samplePath).Length + $size -gt $MaxBytes) {
        for ($index=2; $index -ge 1; $index--) {
            $from = "$samplePath.$index"
            if (Test-Path -LiteralPath $from) { Move-Item -LiteralPath $from -Destination "$samplePath.$($index+1)" -Force }
        }
        Move-Item -LiteralPath $samplePath -Destination "$samplePath.1" -Force
    }
    [IO.File]::AppendAllText($samplePath, $line, [Text.UTF8Encoding]::new($false))
}

function Add-RecorderIncident([string]$Directory, [object]$Sample) {
    $name = 'incident-' + [DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssfffffffZ') + '-' + [guid]::NewGuid().ToString('N') + '.json'
    Write-RecorderJson (Join-Path $Directory $name) $Sample
    Get-ChildItem -LiteralPath $Directory -Filter 'incident-*.json' -File | Sort-Object Name -Descending |
        Select-Object -Skip 12 | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force }
}

function Get-RecorderFreshness($Record, [int]$MaxAgeSeconds) {
    if ($null -eq $Record) { return 'unavailable' }
    try {
        $identity = $Record.collector
        $collectorProcess = Get-Process -Id ([int]$identity.process_id) -ErrorAction Stop
        if ([math]::Abs(([DateTimeOffset]$collectorProcess.StartTime - [DateTimeOffset]$identity.process_start_time).TotalSeconds) -gt 1) { return 'stopped' }
        $age = ([DateTimeOffset]::UtcNow - [DateTimeOffset]$Record.timestamp).TotalSeconds
        if ($age -gt $MaxAgeSeconds -or $age -lt -5) { return 'stale' }
        return 'current'
    } catch { return 'stopped' }
}

function Invoke-RecorderClient {
    param([string]$Program, [string[]]$Arguments, [string]$Circuit, [int]$TimeoutSeconds = 8)
    $result = [ordered]@{outcome='exception';latency_ms=0;exit_code=$null;process_id=$null;owned_client_terminated=$false;stdout=''}
    if ($script:UnkillableClient -or $script:PersistenceFailure) { $result.outcome='collection-stopped'; return $result }
    if ($script:OpenCircuits.ContainsKey($Circuit)) { $result.outcome='circuit-open'; return $result }
    $clock = [Diagnostics.Stopwatch]::StartNew()
    $client = $null
    $inflightPath=if($script:RuntimeStateDirectory){Join-Path $script:RuntimeStateDirectory 'probe-inflight.json'}else{$null}
    try {
        if ($inflightPath) { Write-RecorderJson $inflightPath @{circuit=$Circuit;timestamp=[DateTimeOffset]::UtcNow.ToString('o');stage='starting'} }
        $start = [Diagnostics.ProcessStartInfo]::new()
        $start.FileName=$Program; $start.UseShellExecute=$false; $start.CreateNoWindow=$true
        $start.RedirectStandardOutput=$true; $start.RedirectStandardError=$true
        foreach ($argument in $Arguments) { [void]$start.ArgumentList.Add($argument) }
        $client = [Diagnostics.Process]::new(); $client.StartInfo=$start
        [void]$client.Start(); $result.process_id=$client.Id
        if ($inflightPath) { Write-RecorderJson $inflightPath @{circuit=$Circuit;timestamp=[DateTimeOffset]::UtcNow.ToString('o');stage='running';process_id=$client.Id} }
        $outputRead=[RecorderBoundedText]::ReadAsync($client.StandardOutput,65536,$true)
        $errorRead=[RecorderBoundedText]::ReadAsync($client.StandardError,65536,$false)
        if (-not $client.WaitForExit([int][math]::Max(0,$TimeoutSeconds*1000-$clock.ElapsedMilliseconds))) {
            $result.outcome='timeout'; $script:OpenCircuits[$Circuit]=$true
        } else {
            $result.exit_code=$client.ExitCode
            $result.outcome=if ($client.ExitCode -eq 0) { 'success' } else { 'exit-error' }
            # A descendant holding a pipe open must not create an unbounded wait.
            [void]$outputRead.Wait([int][math]::Max(0,$TimeoutSeconds*1000-$clock.ElapsedMilliseconds))
            [void]$errorRead.Wait([int][math]::Max(0,$TimeoutSeconds*1000-$clock.ElapsedMilliseconds))
            if (-not $outputRead.IsCompletedSuccessfully -or -not $errorRead.IsCompletedSuccessfully) {
                $result.outcome='output-incomplete'; $script:OpenCircuits[$Circuit]=$true
            } elseif ($outputRead.Result.LimitExceeded -or $errorRead.Result.LimitExceeded) {
                $result.outcome='output-limit'; $script:OpenCircuits[$Circuit]=$true
            } else { $result.stdout=$outputRead.Result.Text }
        }
        # stderr is intentionally consumed but never returned or persisted.
        [void]$errorRead
    } catch {
        $result.outcome='exception'
        if ($null -ne $client -and $result.process_id) {
            try {
                if (-not $client.HasExited) {
                    $script:OpenCircuits[$Circuit]=$true
                }
            } catch {$script:UnkillableClient=$true}
        }
    }
    finally {
        # Cleanup is independent of disk writes: full/unavailable storage cannot
        # prevent terminating the exact diagnostic process owned by this call.
        if ($null -ne $client -and $result.process_id) {
            try {
                if (-not $client.HasExited) {
                    $client.Kill(); $result.owned_client_terminated=$client.WaitForExit(1500)
                    if (-not $result.owned_client_terminated) {$script:UnkillableClient=$true}
                }
            } catch {$script:UnkillableClient=$true}
        }
        if ($script:OpenCircuits.ContainsKey($Circuit)) {
            try {Save-RecorderCircuits} catch {$script:PersistenceFailure=$true}
        }
        $result.latency_ms=[int]$clock.ElapsedMilliseconds
        if ($null -ne $client) { $client.Dispose() }
        if ($inflightPath -and -not $script:UnkillableClient -and -not $script:PersistenceFailure -and (Test-Path -LiteralPath $inflightPath)) { Remove-Item -LiteralPath $inflightPath -Force }
    }
    return $result
}

function Get-RecorderProbeSummary($Result) {
    $summary=[ordered]@{}
    foreach ($field in @('outcome','latency_ms','exit_code','process_id','owned_client_terminated')) { $summary[$field]=$Result[$field] }
    return $summary
}

function Test-RecorderDistroRunning([string]$Text, [string]$Name) {
    $names=@(($Text -replace '[\x00\uFEFF]','') -split '\r?\n' | ForEach-Object {$_.Trim()})
    return $names -contains $Name
}

function ConvertFrom-RecorderLines([string]$Text) {
    $values=[ordered]@{}
    $allowed='^(MemTotal|MemFree|MemAvailable|Buffers|Cached|SwapTotal|SwapFree|SReclaimable|Slab|Dirty|Writeback|memory_current|memory_max|anon|file|kernel|slab|inactive_file|active_file|file_dirty|file_writeback|event_(oom|oom_kill|high|max)|zombie_leaders|blocked_threads|load[0-9]+|uptime_seconds|memory_psi_(some|full)|io_psi_(some|full)|wait_[A-Za-z0-9_.-]+)$'
    foreach ($line in ($Text -split '\r?\n')) {
        if ($line -match '^([A-Za-z0-9_.]+):?\s+([0-9]+(?:\.[0-9]+)?)(?:\s+(kB))?\s*$') {
            $key=$Matches[1]; $number=[double]::Parse($Matches[2],[Globalization.CultureInfo]::InvariantCulture)
            if ($key -match $allowed) {
                if ($line -match '\s+kB\s*$') { $key += '_kib' }
                $values[$key]=$number
            }
        }
    }
    return $values
}

function Test-RecorderMetrics($Metrics, [string[]]$Required) {
    foreach ($name in $Required) {if (-not $Metrics.Contains($name)) {return $false}}
    return $true
}

function Measure-RecorderPolling([string[]]$Lines, [Nullable[DateTimeOffset]]$NotBefore = $null) {
    $count=0; $ids=[Collections.Generic.HashSet[string]]::new(); $first=$null; $last=$null
    foreach ($line in $Lines) {
        try {
            $record=ConvertFrom-Json -InputObject $line -AsHashtable
            if ($record.component -ne 'apiproxy' -or $record.msg -notmatch '^<< GET /v[\d.]+/containers/([0-9a-f]+)/stats\?') { continue }
            $containerKey=$Matches[1]; $time=[DateTimeOffset]$record.time
            if ($null -ne $NotBefore -and $time -lt $NotBefore) {continue}
            [void]$ids.Add($containerKey); $count++
            if ($null -eq $first -or $time -lt $first) { $first=$time }
            if ($null -eq $last -or $time -gt $last) { $last=$time }
        } catch {}
    }
    $seconds=if ($null -ne $first) { ($last-$first).TotalSeconds } else { 0 }
    return [ordered]@{available=($count -gt 0);stats_request_entries=$count;unique_containers=$ids.Count;window_seconds=$seconds;
        window_first=if($first){$first.ToString('o')}else{$null};window_last=if($last){$last.ToString('o')}else{$null};
        observed_entries_per_second=if($seconds -gt 0){[math]::Round($count/$seconds,2)}else{$null};scope='bounded-recent-tail-not-complete-interval'}
}

function Get-RecorderPolling([Nullable[DateTimeOffset]]$NotBefore = $null) {
    $logDirectory=Join-Path $env:LOCALAPPDATA 'Docker/log/vm'
    $recent=Get-ChildItem -LiteralPath $logDirectory -Filter 'init.log*' -File -ErrorAction SilentlyContinue |
        Where-Object {$_.Length -gt 0 -and $_.LastWriteTimeUtc -gt [datetime]::UtcNow.AddMinutes(-5)} |
        Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1
    if ($null -eq $recent) { return Measure-RecorderPolling @() }
    # Docker rotates these small files. Never copy raw log lines to evidence.
    $lines=@(Get-Content -LiteralPath $recent.FullName -Tail 1200 -ErrorAction SilentlyContinue)
    $summary=Measure-RecorderPolling $lines $NotBefore
    $summary.window_age_seconds=if($summary.window_last){[math]::Round(([DateTimeOffset]::UtcNow-[DateTimeOffset]$summary.window_last).TotalSeconds,1)}else{$null}
    $summary.fresh=($summary.available -and $summary.window_age_seconds -le 60)
    if(-not $summary.fresh){$summary.available=$false; $summary.observed_entries_per_second=$null}
    return $summary
}

function Get-RecorderWindowsResources {
    $result=[ordered]@{available=$false;disks=@();processes=@()}
    try {
        $memory=Get-CimInstance Win32_PerfFormattedData_PerfOS_Memory -OperationTimeoutSec 5
        $result.available=$true; $result.available_mib=$memory.AvailableMBytes
        $result.committed_bytes=$memory.CommittedBytes; $result.commit_limit_bytes=$memory.CommitLimit
        $result.commit_percent=$memory.PercentCommittedBytesInUse
        $result.pages_in_per_second=$memory.PagesInputPersec; $result.pages_out_per_second=$memory.PagesOutputPersec
    } catch {$result.memory_error_type=$_.Exception.GetType().Name}
    try {
        $result.disks=@(Get-CimInstance Win32_PerfFormattedData_PerfDisk_PhysicalDisk -OperationTimeoutSec 5 |
            Select-Object Name,DiskBytesPersec,CurrentDiskQueueLength,PercentDiskTime)
    } catch {$result.disk_error_type=$_.Exception.GetType().Name}
    $result.processes=@(Get-Process | Where-Object {$_.ProcessName -in @('vmmemWSL','com.docker.backend','Docker Desktop','Wave','waveterm')} |
        Select-Object ProcessName,Id,WorkingSet64,PrivateMemorySize64)
    return $result
}

function Get-RecorderBenchIssues($Cache, [string[]]$Names, [int]$MaximumAge) {
    $issues=@()
    foreach($name in $Names) {
        if(-not $Cache.ContainsKey($name)) {$issues+='bench-sample-pending-'+$name; continue}
        $entry=$Cache[$name]
        if(([DateTimeOffset]::UtcNow-[DateTimeOffset]$entry.timestamp).TotalSeconds -gt $MaximumAge) {$issues+='bench-sample-stale-'+$name}
        if($entry.probe.outcome -ne 'success') {$issues+='bench-'+$entry.probe.outcome+'-'+$name}
        if($entry.metrics.Contains('zombie_leaders') -and $entry.metrics.zombie_leaders -gt 0) {$issues+='zombies-'+$name}
    }
    return $issues
}

function Get-RecorderTaskObservations {
    $records=@()
    foreach ($taskName in @('workBenches WSL Transport Watchdog','Eagle fleet runner','Eagle midNet runner')) {
        try {
            $task=Get-ScheduledTask -TaskName $taskName -ErrorAction Stop
            $info=Get-ScheduledTaskInfo -TaskName $taskName -ErrorAction Stop
            $records+=@{name=$taskName;state=$task.State.ToString();last_run=$info.LastRunTime.ToString('o');last_result=('0x{0:X8}' -f $info.LastTaskResult)}
        } catch { $records+=@{name=$taskName;state='unavailable'} }
    }
    return $records
}

function Get-RecorderResourceIssues($Windows, $Guest) {
    $issues=@()
    if (-not $Windows.available) {$issues+='windows-metrics-unavailable'}
    elseif ($Windows.available_mib -lt 1024 -or $Windows.commit_percent -ge 90) {$issues+='windows-memory-pressure'}
    if ($Guest.Contains('MemAvailable_kib') -and $Guest.Contains('MemTotal_kib')) {
        if ($Guest.MemAvailable_kib -lt $Guest.MemTotal_kib*0.05) {$issues+='guest-low-available-memory'}
    }
    if ($Guest.Contains('memory_psi_full') -and $Guest.memory_psi_full -ge 10) {$issues+='guest-memory-stalls'}
    return $issues
}

function Get-ExternalWatchdogFreshness {
    try {
        $path=Join-Path $env:LOCALAPPDATA 'workBenches/wsl-transport-watchdog/status.json'
        $record=Get-Content -LiteralPath $path -Raw | ConvertFrom-Json -AsHashtable
        $health=Get-RecorderFreshness @{timestamp=$record.timestamp;collector=$record.daemon} 90
        return @{freshness=$health;timestamp=$record.timestamp;reported_health=$record.health}
    } catch { return @{freshness='unavailable'} }
}

function Get-ExternalWatchdogIssues($Observation) {
    if ($Observation.freshness -ne 'current') {return 'external-watchdog-'+$Observation.freshness}
    if ($Observation.reported_health -ne 'healthy') {return 'external-watchdog-unhealthy'}
}

$script:WslPayload=@'
set -e
awk '{print "uptime_seconds "int($1)}' /proc/uptime
awk '{print "load1 "$1; print "load5 "$2; print "load15 "$3}' /proc/loadavg
grep -E '^(MemTotal|MemFree|MemAvailable|Buffers|Cached|SwapTotal|SwapFree|SReclaimable|Slab|Dirty|Writeback):' /proc/meminfo
awk '{split($2,a,"=");print "memory_psi_"$1" "a[2]}' /proc/pressure/memory
awk '{split($2,a,"=");print "io_psi_"$1" "a[2]}' /proc/pressure/io
ps -eo stat= | awk 'BEGIN{z=0} /^Z/{z++} END{print "zombie_leaders "z}'
'@
$script:BenchPayload=@'
set -e
printf 'memory_current '; cat /sys/fs/cgroup/memory.current
grep -E '^(anon|file|kernel|slab|inactive_file|active_file|file_dirty|file_writeback) ' /sys/fs/cgroup/memory.stat
awk '$1=="oom" || $1=="oom_kill" || $1=="high" || $1=="max" {print "event_"$1" "$2}' /sys/fs/cgroup/memory.events
awk '{split($2,a,"=");print "memory_psi_"$1" "a[2]}' /sys/fs/cgroup/memory.pressure
ps -eo stat= | awk 'BEGIN{z=0} /^Z/{z++} END{print "zombie_leaders "z}'
ps -eLo stat=,wchan= | awk 'BEGIN{d=0} $1~/^D/{d++;w[$2]++} END{print "blocked_threads "d;for(k in w) print "wait_"k" "w[k]}'
'@

function New-RecorderSample([string]$DockerExecutable, [string]$WslExecutable) {
    $self=Get-Process -Id $PID
    $sample=[ordered]@{version=1;timestamp=[DateTimeOffset]::UtcNow.ToString('o');interval_seconds=$IntervalSeconds;
        collector=@{process_id=$PID;process_start_time=$self.StartTime.ToString('o')};phase='baseline';issues=@();
        windows=Get-RecorderWindowsResources;tasks=@(Get-RecorderTaskObservations);external_watchdog=Get-ExternalWatchdogFreshness}
    $phasePath=Join-Path $StateDirectory 'phase.json'
    if (Test-Path -LiteralPath $phasePath) {
        try { $phaseRecord=Get-Content -LiteralPath $phasePath -Raw | ConvertFrom-Json
            $label=$phaseRecord.phase
            if ($label -in @('baseline','dashboard-open','dashboard-closed','dashboard-reopened')) {$sample.phase=$label; $sample.phase_started_at=$phaseRecord.timestamp}
        } catch {}
    }
    $infoTemplate='{"server_version":{{json .ServerVersion}},"running":{{.ContainersRunning}},"stopped":{{.ContainersStopped}}}'
    $docker=Invoke-RecorderClient $DockerExecutable @('info','--format',$infoTemplate) docker $ProbeTimeoutSeconds
    $sample.docker_probe=Get-RecorderProbeSummary $docker
    if ($docker.outcome -eq 'success') {
        try {$sample.docker_inventory=$docker.stdout | ConvertFrom-Json -AsHashtable} catch {$sample.issues+='docker-parse-unavailable'}
    } else {$sample.issues+='docker-'+$docker.outcome}
    # Enumeration does not start a stopped distribution. Never defeat an offline maintenance window.
    $runningDistros=Invoke-RecorderClient $WslExecutable @('--list','--running','--quiet') wsl $ProbeTimeoutSeconds
    $sample.wsl_enumeration_probe=Get-RecorderProbeSummary $runningDistros
    if ($runningDistros.outcome -ne 'success') {$guest=$runningDistros}
    elseif (-not (Test-RecorderDistroRunning $runningDistros.stdout $Distribution)) {
        $guest=@{outcome='distro-stopped';latency_ms=0;exit_code=$null;process_id=$null;owned_client_terminated=$false;stdout=''}
    } else {
        $guest=Invoke-RecorderClient $WslExecutable @('-d',$Distribution,'-e','timeout',"$ProbeTimeoutSeconds",'sh','-c',$script:WslPayload) wsl $ProbeTimeoutSeconds
    }
    if ($guest.outcome -eq 'success') {
        $sample.wsl=ConvertFrom-RecorderLines $guest.stdout
        if (-not (Test-RecorderMetrics $sample.wsl @('MemTotal_kib','MemAvailable_kib','SwapTotal_kib','SwapFree_kib','uptime_seconds','zombie_leaders'))) {
            $guest.outcome='metrics-unavailable'
        }
    }
    $sample.wsl_probe=Get-RecorderProbeSummary $guest
    if ($guest.outcome -ne 'success') {$sample.issues+='wsl-'+$guest.outcome}
    if ($docker.outcome -eq 'success' -and -not $script:UnkillableClient) {
        $template='{{.Name}}|{{.State.Status}}|{{.State.OOMKilled}}|{{.RestartCount}}|{{index .HostConfig "Init"}}|{{.Id}}'
        $inventory=Invoke-RecorderClient $DockerExecutable (@('inspect','--format',$template)+$Containers) docker $ProbeTimeoutSeconds
        $sample.bench_states=@()
        foreach ($line in ($inventory.stdout -split '\r?\n')) {
            $parts=$line -split '\|'
            if ($parts.Count -eq 6) {$sample.bench_states+=@{name=$parts[0].TrimStart('/');state=$parts[1];oom=$parts[2];restarts=$parts[3];init=$parts[4];id=$parts[5]}}
        }
        if ($inventory.outcome -ne 'success') {$sample.issues+='bench-inventory-'+$inventory.outcome}
        $chosen=$Containers[$script:BenchCursor % $Containers.Count]; $script:BenchCursor++
        if (@($sample.bench_states | Where-Object {$_.name -eq $chosen -and $_.state -eq 'running'}).Count) {
            if (-not $script:OpenCircuits.ContainsKey('docker')) {
                $bench=Invoke-RecorderClient $DockerExecutable @('exec',$chosen,'timeout',"$ProbeTimeoutSeconds",'sh','-c',$script:BenchPayload) bench $ProbeTimeoutSeconds
                $metrics=ConvertFrom-RecorderLines $bench.stdout
                if ($bench.outcome -eq 'success' -and -not (Test-RecorderMetrics $metrics @('memory_current','anon','file','kernel','event_oom','event_oom_kill','zombie_leaders','blocked_threads'))) {
                    $bench.outcome='metrics-unavailable'
                }
                $script:BenchCache[$chosen]=@{timestamp=[DateTimeOffset]::UtcNow.ToString('o');probe=Get-RecorderProbeSummary $bench;metrics=$metrics}
                if ($bench.outcome -ne 'success') {$sample.issues+='bench-'+$bench.outcome}
                elseif ($script:BenchCache[$chosen].metrics.Contains('zombie_leaders') -and $script:BenchCache[$chosen].metrics.zombie_leaders -gt 0) {$sample.issues+='zombies-'+$chosen}
            }
        } else {$sample.issues+='bench-not-running-'+$chosen}
    }
    $sample.benches=$script:BenchCache.Clone()
    $sample.issues+=@(Get-RecorderBenchIssues $script:BenchCache $Containers ($IntervalSeconds*($Containers.Count+1)))
    foreach ($task in $sample.tasks) {if ($task.state -ne 'Running') {$sample.issues+='task-not-running-'+($task.name -replace ' ','-')}}
    $sample.issues+=@(Get-ExternalWatchdogIssues $sample.external_watchdog)
    $guestMetrics=if($sample.Contains('wsl')){$sample.wsl}else{[ordered]@{}}
    $sample.issues+=@(Get-RecorderResourceIssues $sample.windows $guestMetrics)
    foreach ($circuitName in $script:OpenCircuits.Keys) {$sample.issues+='latched-'+$circuitName}
    if ($script:UnkillableClient) {$sample.issues+='unkillable-owned-client'}
    if ($script:PersistenceFailure) {$sample.issues+='probe-state-persistence-failed'}
    $notBefore=if($sample.Contains('phase_started_at')){[DateTimeOffset]$sample.phase_started_at}else{$null}
    $sample.polling=Get-RecorderPolling $notBefore
    $sample.issues=@($sample.issues | Sort-Object -Unique)
    $sample.health=if ($sample.issues.Count) {'degraded'} else {'healthy'}
    return $sample
}

# Dot-sourcing loads only testable functions and fixed guest payloads.
if ($MyInvocation.InvocationName -eq '.') { return }
if ($Mode -eq 'Status') {
    $path=Join-Path $StateDirectory 'status.json'
    if (-not (Test-Path -LiteralPath $path)) {@{collector_state='unavailable'}|ConvertTo-Json; exit 1}
    $saved=Get-Content -LiteralPath $path -Raw | ConvertFrom-Json -AsHashtable
    $saved.collector_state=Get-RecorderFreshness $saved ([int]$saved.interval_seconds * 3)
    $saved | ConvertTo-Json -Depth 16
    exit $(if($saved.collector_state -eq 'current'){0}else{1})
}
Initialize-RecorderState $StateDirectory
if ($Mode -eq 'Mark') {
    Write-RecorderJson (Join-Path $StateDirectory 'phase.json') @{phase=$Phase;timestamp=[DateTimeOffset]::UtcNow.ToString('o')}
    @{phase=$Phase;recorded=$true}|ConvertTo-Json; exit 0
}
$recorderLock=Enter-RecorderLock $StateDirectory
if ($null -eq $recorderLock) {@{collector_state='already-running'}|ConvertTo-Json; exit 0}
try {
    $script:RuntimeStateDirectory=$StateDirectory
    if ($Mode -eq 'ResetProbes') {
        $script:OpenCircuits=@{}; Save-RecorderCircuits
        $inflight=Join-Path $StateDirectory 'probe-inflight.json'
        if (Test-Path -LiteralPath $inflight) {Remove-Item -LiteralPath $inflight -Force}
        @{probe_circuits_reset=$true}|ConvertTo-Json; exit 0
    }
    Restore-RecorderCircuits $StateDirectory
    $dockerExecutable=(Get-Command docker.exe -ErrorAction Stop).Source
    $wslExecutable=Join-Path $env:SystemRoot 'System32/wsl.exe'
    $previousIssues=''
    do {
        $cycle=[Diagnostics.Stopwatch]::StartNew()
        $snapshot=New-RecorderSample $dockerExecutable $wslExecutable
        Add-RecorderSample $StateDirectory $snapshot
        Write-RecorderJson (Join-Path $StateDirectory 'status.json') $snapshot
        $issueKey=($snapshot.issues | Sort-Object) -join '|'
        if ($issueKey -ne $previousIssues) {Add-RecorderIncident $StateDirectory $snapshot; $previousIssues=$issueKey}
        if ($Mode -eq 'Once') {$snapshot|ConvertTo-Json -Depth 16; break}
        if ($script:UnkillableClient -or $script:PersistenceFailure) {throw 'Probe cleanup or state persistence failed; stopping recorder to prevent overlap.'}
        $remaining=[math]::Max(0,$IntervalSeconds*1000-$cycle.ElapsedMilliseconds)
        if ($remaining -gt 0) {Start-Sleep -Milliseconds $remaining}
    } while ($true)
} finally {$recorderLock.Dispose()}
