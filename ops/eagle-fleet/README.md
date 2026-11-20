# Eagle fleet execution

The Windows controller serves selected repositories in organization groups named
`Eagle Linux`. Workflows select `eagle-linux-ubuntu24` explicitly. There is no
GitHub-hosted fallback. A second profile must be qualified before using the
`eagle-linux-ubuntu22` label. Native Windows, macOS and KVM jobs require their own
qualified capacity; changing a label does not change their operating system.

Each assigned job gets a fresh network guard and an unprivileged rootless Docker
backend. The runner itself is a nested container. Its workspace, tool cache,
externals and Docker socket belong exclusively to that backend. No host folder,
host Docker socket, bench credential or GitHub administration token enters it.
The socket mounted in the nested runner is its disposable rootless engine.
Package installation and Bubblewrap capabilities apply inside its user namespace.
The public egress gateway rejects private, loopback, link-local and mixed DNS
answers and connects to validated numeric addresses. Fork approval and protected
environment approval remain GitHub's existing controls. Containers share Eagle's
kernel; this architecture does not provide a VM boundary.

The primary controller runs one worker with an 8 GiB backend limit and four CPUs.
Its legacy admission requires 10 GiB of Linux MemAvailable. With parallel capacity
enabled, primary admission reserves its full 8 GiB allocation plus at least 10 GiB
Linux headroom. An optional second Ubuntu 24 slot uses the same qualified images
and profiles. No bench is stopped or restarted.
The host enforces a 7.5-hour job deadline independently of code running inside
the sandbox; GitHub's original job timeout still applies. A root-owned pre-job
hook waits for the Windows controller to persist that deadline before any service
container or action code starts. The outer engine's root-owned Python supports
supervision even if a job replaces its own toolchain. The exact detached listener
exec must finish before unregistering. GitHub's forced-delete
endpoint is not an assignment-race barrier. Container/volume names are journaled before deletion. An
uncertain create is reconciled by its exact identity, never repeated blindly.

Deploy this directory to a host-local service directory. Keep `config.json`,
`pools.json`, DPAPI authentication, state, locks and logs outside Git. Build the
gateway and worker images from their declared Dockerfiles and pin their image
IDs in configuration, including `backend_image` built with Dockerfile.engine.
Provision selected-repository groups before enabling any
workflow. Start-Infrastructure.ps1 touches only owned fleet infrastructure.
Run Watch-Fleet.ps1 with an explicit Python executable from a current-user
interactive AtLogon task. Authentication uses a same-user DPAPI file and exists
only in the host controller environment; registration tokens go to config.sh over
stdin, never arguments or logs.

Put an empty `STOP` file in the service directory to drain: no new sandbox is
provisioned, and an existing registered once-listener may accept its one final job
and finish naturally. An unassigned listener can keep that pool occupied until
it exits; STOP never uses forced deregistration to prove it is idle. Resume by
removing STOP and starting the scheduled task. Recover a stale create by first
inspecting the exact journaled names and GitHub assignment. Never use global
Docker prune, WSL shutdown or a Docker restart as runner cleanup.

Validation from this directory: `python -m unittest test_controller test_backend
test_proxy test_parallel` covers the Windows runtime. The full suite,
`python -m unittest discover -s . -p 'test_*.py'`, also requires PyYAML.
The Eagle fleet pull-request workflow runs the full suite on Ubuntu 24 and parses
both Windows watcher scripts; native Windows tests remain a separate check.
The local compatibility probe proved nonroot execution, sudo, a user-namespace
UID mapping, private rootless Docker, container-action workspace roundtrip,
localhost service connectivity, public HTTPS/apt and Bubblewrap. Private-address
HTTPS was denied. These probes are preparation; actual GitHub run URLs and job
runner names are required to report successful workflow migration.

Routing changes preserve workflow triggers, job dependencies, test commands,
permissions, environment approvals and matrix rows. Matrix values remain original
so platform conditionals retain their meaning. Pinned reusable workflow providers
must land before consumers advance coherent pins through their declared tooling.
Never edit a shape-copy digest just to silence its drift gate.

The Ubuntu 24 worker also supplies Azure CLI, PowerShell and zstd. SSH uses the
public-address gateway for remote hosts and direct transport for localhost.
No SSH keys are baked into the image. Retain each configured worker image under
a unique immutable tag before rebuilding the convenience tag; Docker Desktop
may discard the old index when its last tag is replaced. Verify the new digest,
qualify its tools and transport, then atomically change the host configuration.
Existing disposable workers finish on their original imported image.

## Optional second Ubuntu 24 slot

`parallel.py` and `Watch-Parallel.ps1` add one worker without restarting the primary.
Set the host-local `parallel_capacity` object to `{"enabled":true,"ubuntu24_workers":2}`.
Its optional `host_disk_roots` list must include the actual disks backing the host
and Docker when they differ from the service drive; keep these machine paths in
host-local configuration outside Git. The default checks the service drive.
Preserve every existing pool, profile and image pin. This does not restore removed
profiles, expand repository access, or change the separate .NET pilot.

Before each sandbox, the second slot reserves both full 8 GiB worker allocations,
including an empty or partly loaded primary: 26 GiB Linux MemAvailable (or the
configured primary reserve plus 16 GiB, whichever is larger), 20 GiB Windows physical
memory available, 80 GiB free on every configured host disk and Docker's filesystem,
at least 16 logical CPUs, and measured CPU utilization plus four CPUs below 80%.
Engine/guard identities, including incomplete creates, reserve capacity; two is
the maximum. Both controllers exclude jobs in active peer journals. A shared
dispatch lock protects the final job reservation before creating a guard, so
simultaneous scans cannot prepare two workers for the same queued job. The
reservation remains until that slot has completed verified cleanup. Pressure pauses new work and never cancels an assigned job. Measurements
fail closed. These are admission reserves, not guarantees against unrelated future
host resource consumption. These conservative checks may defer a second worker
even when a partly loaded primary currently uses less than its allocation.

Run the new watcher using native PowerShell 7, an explicit Python executable, and
a separate current-user interactive AtLogon task with MultipleInstances IgnoreNew.
It reads the existing same-user DPAPI file; do not copy credentials or put them in
arguments. State, logs and an exclusive lock live in `slots/ubuntu24-2`. The primary
journal is untouched. Recovery precedes admission and drain checks. Put `STOP` in
that slot directory to drain only the second slot; service-root `STOP` drains both.
To resume, remove STOP, enable the setting and start the task. Disable the setting
after draining to retain a one-worker configuration. Do not forcibly end the task
or stop its engine to resize capacity. Acceptance requires actual overlapping
GitHub jobs on distinct runner names and successful per-job cleanup.
