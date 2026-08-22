from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "plugins/aquarium/skills/test-setup/scripts/inspect_testing.py"


def run_inspector(repository: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--repository", str(repository)],
        check=False,
        capture_output=True,
        text=True,
    )


def write_conforming_repository(repository: Path) -> None:
    repository.joinpath("Makefile").write_text(
        """\
.PHONY: test test-prepare test-unit test-int test-e2e
test:
\t$(MAKE) test-prepare
\t$(MAKE) test-unit
\t$(MAKE) test-int
\t$(MAKE) test-e2e
test-prepare test-unit test-int test-e2e:
\t@true
""",
        encoding="utf-8",
    )
    repository.joinpath("TESTING.md").write_text(
        "Contract: aquarium-test-contract/v1\nProfile: make\n",
        encoding="utf-8",
    )
    repository.joinpath("pyproject.toml").write_text(
        '[tool.pytest.ini_options]\naddopts = ["--strict-config"]\n',
        encoding="utf-8",
    )
    repository.joinpath("requirements.txt").write_text(
        "pytest==9.1.1\n",
        encoding="utf-8",
    )


def test_cli_reports_a_conforming_python_repository(tmp_path: Path) -> None:
    write_conforming_repository(tmp_path)

    completed = run_inspector(tmp_path)
    payload = json.loads(completed.stdout)

    assert completed.returncode == 0
    assert completed.stderr == ""
    assert payload["schema_version"] == "aquarium-test-setup-inspection.v1"
    assert payload["selected_profile"] == "make"
    assert payload["detected_languages"] == ["python"]
    assert payload["structural_status"] == "conforming"
    assert payload["findings"] == []


def test_cli_reports_missing_contract_entrypoints_without_mutation(
    tmp_path: Path,
) -> None:
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    completed = run_inspector(tmp_path)
    payload = json.loads(completed.stdout)

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    codes = {item["code"] for item in payload["findings"]}
    assert completed.returncode == 0
    assert payload["structural_status"] == "nonconforming"
    assert {"makefile_missing", "testing_document_missing"} <= codes
    assert after == before
