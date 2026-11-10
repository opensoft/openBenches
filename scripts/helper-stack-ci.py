"""Trusted helper entry point for the shared conservative event-proof engine."""

import os
from pathlib import Path
import runpy


POLICY = runpy.run_path(str(Path(__file__).with_name("project-stack-ci.py")),
                       init_globals={"SCOPE": "helper"})
# Export the same proof helpers for offline tests and diagnostics.
globals().update({name: value for name, value in POLICY.items() if not name.startswith("__")})


if __name__ == "__main__":
    classify(os.environ)
