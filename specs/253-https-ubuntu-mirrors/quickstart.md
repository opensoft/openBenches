# Verification Quickstart

Run `python3 scripts/tests/test_ubuntu_mirror_transport.py` from this feature checkout in the declared Python bench image. Tests are offline and do not modify real package sources.

Rebuild with the existing shared/family/bench wrappers. Set `TMPDIR` to private ext4 storage for image-export checks when the host root filesystem is nearly full. No manifest write is required.

After images pass, run `scripts/wave-container-shell.sh --user brett --check` once per selected bench and repeat to prove container reuse. Keep CI/watchdog paused and retain Desktop storage. An actual Windows reboot is a separate acceptance step, not performed by this fix.
