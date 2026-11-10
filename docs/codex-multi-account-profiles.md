# Codex multi-account profiles

workBenches can launch Codex CLI with separate ChatGPT logins. Each account
receives its own `CODEX_HOME` and file-backed `auth.json`. Profiles in the same
trust family share portable conversation state, while logs, caches, databases,
and credentials remain profile-local. Profile names, aliases, families, and
login emails are inventory metadata only; OAuth credentials are never stored
in a manifest.

## Setup

```bash
cp config/openai-profiles.example.json ~/.config/workbenches/openai-profiles.json
$EDITOR ~/.config/workbenches/openai-profiles.json
./scripts/setup-codex-profiles.sh
codex-profile list
codex-profile login work-chatgpt-1
pcodex work1
```

`codex-profile` and `pcodex` are the same launcher. Supported forms are:

```bash
pcodex list
pcodex login PROFILE
pcodex status PROFILE
pcodex logout PROFILE
pcodex PROFILE [codex arguments]
```

Profile homes are created under:

```text
~/.chatgpt-profiles/
|-- profiles/
|   |-- work-chatgpt-1/
|   |   |-- auth.json       # Created by Codex login; treat like a password
|   |   |-- config.toml
|   |   |-- sessions -> ../../state/work/sessions
|   |   `-- history.jsonl -> ../../state/work/history.jsonl
|   `-- personal-chatgpt-1/
`-- state/
    `-- work/                # Portable history shared by the work family
```

The installer initializes each profile from the user's existing Codex
configuration, then forces ChatGPT login with file credential storage. Shared
skills, prompts, policy, and global instructions link back to `~/.codex`.
`sessions`, `archived_sessions`, `history.jsonl`, and `session_index.jsonl`
link to family state so another login in that family can resume the same work.
Credential files and SQLite runtime state remain isolated per profile.

When existing profiles are adopted, setup merges their portable state into the
family directory without overwriting existing rollouts. The former local paths
are retained as `.pre-shared-state` recovery copies. Re-running setup repairs
the links without importing those recovery copies again.

Codex's built-in `--profile` option is a configuration overlay within one
`CODEX_HOME`; it does not isolate account credentials. Use `pcodex` when the
login identity must change.

Each ChatGPT identity still needs its own applicable product entitlement. A
local profile does not create a ChatGPT Business seat or independent quota.

## Codex Desktop through Multi-CLI

On Windows, the current Desktop store at `%USERPROFILE%\.codex` is the shared
conversation source. Synchronize registry-owned Multi-CLI profiles with:

```powershell
.\scripts\setup-multi-cli-codex-profiles.ps1 `
  -Manifest C:\path\to\openai-profiles.json
```

The script creates `MultiCliProfiles\codex\<profile>` homes for every
non-personal (company) family in the manifest by default, or only the
families passed via `-Family` (e.g. `-Family acme`). Their portable history
paths link to the live Desktop store, while `auth.json`, configuration,
caches, and databases remain inside each Multi-CLI profile. Multiple login
identities in the same company family can therefore open the same Desktop
conversations using different login tokens. Profiles with a `personal` family
are never linked.

The operation is idempotent. It refuses to replace a real profile-local history
path or a link targeting another store; migrate that state explicitly first.

## Shared Opensoft desktop projects

The desktop also keeps an account-scoped project registry and chat membership
map. Sharing session files alone does not preserve the project sidebar when
the login changes. For the `opensoft` family, Windows setup now installs
**Codex - Opensoft shared projects** in the WorkBenches Start menu folder.
Use this launcher after a normal desktop exit to capture the last account's
changes and prepare the enrolled accounts before opening regular Codex.
`-SkipDesktopProjectSharing` skips installing this launcher.

The native launcher can also be run directly:

```powershell
.\scripts\codex-desktop.ps1
# A normal close, preparation, and relaunch when explicitly wanted:
.\scripts\codex-desktop.ps1 -Restart
```

The helper checks the active login against Opensoft `.profile.json` metadata.
A first recovery can select a verified, preserved account by its owner digest
with `-EnrollOwner OWNER -SeedOwner OWNER`. The seed is accepted only before
the catalog exists. `-EnrollIdentities PATH` accepts an explicitly supplied
credential-free identity inventory (`version: 1`, `identities` array containing
`owner`, `userId`, `accountId`, `email`, and `family: opensoft`). These bindings
prepare profiles that have not previously opened this desktop. Never put login
tokens in the inventory.
An installed `opensoft-identities.json` beside the native launcher is used by
default, so the normal Start menu launch also performs initial enrollment.

The catalog preserves local project IDs, names, roots, ordering, appearance,
and local chat grouping. Actual changes since each account's last preparation
are merged into the next shared set, including edits saved before an in-app
account rotation, removals, and projectless chats. Unchanged older snapshots do
not revive deleted projects. The active account wins simultaneous conflicts.
Account-specific
cloud ownership fields, credentials, and other preferences are preserved in
their destination accounts rather than copied from another account.

Catalogs live under the selected Codex home's
`workbenches-projects/<runtime>/opensoft.json`. Windows uses `windows` with the
regular `OpenAI.Codex` package. Beta/WSL uses `beta-wsl` in its own Linux home:

```bash
python3 scripts/codex-project-state.py \
  --runtime beta-wsl --home "$HOME/.codex" \
  --profiles "$HOME/.chatgpt-profiles/profiles" --apply
```

Run that command only with Beta stopped, then open Beta through its existing
launcher. Do not pass a Windows home or catalog to it. The Windows launcher
does not execute WSL, select `OpenAI.CodexBeta`, change terminal settings, or
copy runtime configuration. No SQLite database is rebuilt or linked.

**Launch boundary:** the desktop retains global state in memory. This helper
refuses to change state while the selected package runs. The app's built-in
account switcher cannot invoke an external workBenches hook; use a normal exit
and the shared launcher to propagate edits. Already prepared account snapshots
contain the common set, but changes made since preparation are synchronized at
the next prepared launch. Opening the launcher while Codex already runs simply
activates it; use `-Restart` explicitly to prepare immediately.

Before changes, the helper creates original-file backups alongside the catalog,
checks that inputs have not changed, and uses atomic file replacement. Repeating
an unchanged preparation writes nothing. To roll back, normally exit the selected
desktop and restore its global-state file and catalog from the same backup.
