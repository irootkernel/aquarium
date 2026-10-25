"""Test-only launcher for the offline guest simulation.

It replaces recipe_lib.read_platform_identity in-process with the simulated
platform identity and then calls guest_main.main(); production code reads
only native platform observations. When the cloned candidate checkout
exists, the same simulated identity also replaces the committed driver's
guest_guard for in-process driver calls (baseline, setup), so the
simulation's guest premise is consistent across the recipe and the driver.
Subprocess driver invocations (make test-vm) stay unpatched and stop at
their precise live-only boundary.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
RECIPES_ROOT = REPOSITORY / "tests/vm/recipes"


def main() -> int:
    arguments = [Path(value) for value in sys.argv[1:3]]
    if not all(value.is_absolute() and str(value).strip() for value in arguments):
        raise SystemExit("launcher paths must be non-empty absolute paths")
    identity_path = arguments[0]
    harness = arguments[1].resolve()
    suite_arguments = sys.argv[3:]
    sys.argv = ["guest_main.py", *suite_arguments]
    if str(RECIPES_ROOT) not in sys.path:
        sys.path.insert(0, str(RECIPES_ROOT))
    import recipe_lib

    simulated = json.loads(identity_path.read_text(encoding="utf-8"))
    recipe_lib.read_platform_identity = lambda: simulated
    os_chdir = __import__("os").chdir
    os_chdir(harness)
    driver_root = harness.parent / "checkout/tests/vm"
    if (driver_root / "run_acceptance.py").is_file():
        if str(driver_root) not in sys.path:
            sys.path.insert(0, str(driver_root))
        import run_acceptance

        run_acceptance.guest_guard = lambda expected_uuid: simulated
    import guest_main

    return guest_main.main()


if __name__ == "__main__":
    raise SystemExit(main())
