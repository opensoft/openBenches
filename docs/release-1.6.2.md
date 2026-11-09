# v1.6.2 — workstation setup and source-pin maintenance

This maintenance candidate contains the changes merged after v1.6.1. It keeps
the twelve reviewed source revisions recorded on main while advancing VERSION
and the source-lock version together. Existing published tags are unchanged.

## Included changes

- Tools detects SSH-agent socket changes even when its container is healthy.
  Native bench callbacks retain the workstation's agent path instead of the
  container-only socket path, avoiding an unintended Tools restart during setup.
- Bench-home preparation validates existing host links, preserves settings,
  and creates missing children through the native host boundary when needed.
  Shared helpers support numeric bench names such as 365Bench.
- Wave setup reconciles owned shortcuts with installed benches, migrates the
  previous shortcut format, and uses local connections on native platforms.
  Concurrent settings saves are not silently overwritten; displaced originals
  remain available in a reported private recovery directory. Unrelated widgets,
  connection settings, and fonts are preserved.
- Bootstrap and source records use the canonical openBenches and public
  cloudBench repositories while retaining the documented compatibility paths.
  Historical source recovery remains separate from the portable public bench.
- OpenSpec/Speckit setup handles linked or temporarily unavailable agent-skill
  directories without overwriting user changes, and keeps generated agent
  scaffolding out of normal Git status through local exclusions.
- The base image includes PostgreSQL 16 server and client support for the
  vendored repository tools' real-database tests. Developer and bio layers use
  the base image's Node 24 major so the expected Corepack tooling remains present.
- Setup keeps the installation display visible while logs scroll.

## Frozen standalone bench revisions

These forward-only revisions match the clean standalone checkouts and their
reviewed public main commits. Their changes are limited to CI routing and the
configuration-checker repository name; they do not downgrade bench runtime code.

| Bench | Revision |
| --- | --- |
| gentecBench | c8006dac9486fc47e76349ddd235c53d696e6472 |
| simBench | 2bd8714705220e52760b6940a4ece77923452a6e |
| flutterBench | 6df93c965e7551c0da79a32262cea57651041c56 |
| frappeBench | 4af1cad8bc60ab8b06aef91f4c1cee2d60d6a0b8 |

The other eight source revisions and all repository URLs remain unchanged from
the reviewed assembly. The lockfile is the authoritative list of all twelve.

## Scope and compatibility

The open company-connection wizard is not included in this maintenance candidate;
its future release assignment is separate from earlier notes that anticipated
it in v1.6.2. The v1.7 device-trust work is also outside this release.

Existing profiles, credentials, custom settings, and unrelated work must remain
intact. Refreshing source or Wave shortcuts does not implicitly recreate running
benches or rebuild their images. Frozen Git revisions establish source identity,
not byte-identical external package downloads.

## Qualification and publication

Use the [automated release procedure](release-automation.md). Ordinary CI and
fixture success are not stable-publication authorization. The final main commit
must pass all twelve hosted suites and four required v1.6 native/live suites:
Windows/WSL2, GitHub authentication, company authentication, and the approved
provider/broker/Key Vault flows. Cleanup and source-bound evidence are required.

**Native Arch qualification is waived-not-executed for exact stable version
1.6.2.** The release maintainer approved this exception on 2026-11-08 because
native Arch QA capacity is unavailable and replacement capacity is not qualified.
This release therefore does not claim fresh native Arch acceptance. The reviewed
manifest records the exception and the validation report discloses it separately
from passed tests. Arch remains required for every other applicable version,
including 1.6.2 prereleases and 1.6.3. Remove the waiver when native Arch QA capacity
returns. No other suite, cleanup, freshness or publication control is waived.

The publisher requires a successful full release-validation run for the exact
current main commit, with matching version, source-lock and test-manifest digests,
run identity and attempt, and evidence younger than 24 hours. It creates the
annotated v1.6.2 tag and release only after that gate succeeds. Missing QA workers,
credentials, adapters, or real browser/MFA acceptance remain explicit blockers;
they are not replaced by cached logins, synthetic fixtures, or historical tests.
