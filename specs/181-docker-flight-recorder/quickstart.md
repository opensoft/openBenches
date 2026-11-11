# Quickstart

From Windows PowerShell 7 in the feature checkout:

```powershell
pwsh -NoProfile -File scripts/tests/test-docker-wsl-flight-recorder.ps1
pwsh -NoProfile -File scripts/docker-wsl-flight-recorder.ps1 -Mode Once
pwsh -NoProfile -File scripts/install-docker-wsl-flight-recorder.ps1 -Action Install
pwsh -NoProfile -File scripts/install-docker-wsl-flight-recorder.ps1 -Action Status
```

Mark controlled dashboard phases using the installed recorder. Stop disables/stops only its own task and preserves evidence. See `docs/docker-wsl-diagnostics.md`. A running task is not proof of long-term Docker stability.
