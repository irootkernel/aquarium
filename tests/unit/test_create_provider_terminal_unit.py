from __future__ import annotations

import hashlib
import importlib.util
import json
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).parents[2]
    / "plugins/aquarium/skills/orca-review/scripts/create_provider_terminal.py"
)
SPEC = importlib.util.spec_from_file_location("create_provider_terminal", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
create_provider_terminal = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(create_provider_terminal)


def executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | 0o111)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def request(tmp_path: Path) -> tuple[dict[str, object], list[Path]]:
    repository = tmp_path / "repository"
    repository.mkdir()
    sentinel = tmp_path / "unexpected-command"
    semicolon_sentinel = tmp_path / "unexpected-semicolon-command"
    provider = tmp_path / "provider with quote' and space"
    executable(
        provider,
        "#!/usr/bin/env python3\nimport json, sys\nprint(json.dumps(sys.argv[1:]))\n",
    )
    orca = tmp_path / "fake orca"
    executable(
        orca,
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "print(json.dumps({'argv': sys.argv[1:]}))\n",
    )
    payload: dict[str, object] = {
        "schema_version": "aquarium-orca-provider-terminal-request/v1",
        "repository": str(repository),
        "orca": {
            "entrypoint": str(orca),
            "canonical_target": str(orca),
            "sha256": digest(orca),
        },
        "provider": {
            "entrypoint": str(provider),
            "canonical_target": str(provider),
            "sha256": digest(provider),
        },
        "arguments": [
            "argument with spaces",
            "single'quote",
            f"$(touch {sentinel})",
            f"; touch {semicolon_sentinel}",
        ],
        "title": "Aquarium provider review",
        "worktree": "current",
    }
    return payload, [sentinel, semicolon_sentinel]


def test_provider_argv_is_shell_safe_and_exact(tmp_path: Path) -> None:
    payload, sentinels = request(tmp_path)

    completed = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        check=True,
        capture_output=True,
        text=True,
    )
    result = json.loads(completed.stdout)

    orca_argv = result["orca_result"]["argv"]
    command = orca_argv[orca_argv.index("--command") + 1]
    expected = [payload["provider"]["entrypoint"], *payload["arguments"]]
    assert shlex.split(command) == expected
    executed = subprocess.run(
        ["/bin/sh", "-c", command],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(executed.stdout) == payload["arguments"]
    assert all(not sentinel.exists() for sentinel in sentinels)


def test_provider_digest_drift_stops_before_orca(tmp_path: Path) -> None:
    payload, _ = request(tmp_path)
    provider = Path(payload["provider"]["entrypoint"])
    provider.write_text("changed\n", encoding="utf-8")

    with pytest.raises(create_provider_terminal.RequestError) as error:
        create_provider_terminal.create_terminal(payload)

    assert error.value.code == "provider_identity_changed"


def test_provider_command_uses_verified_canonical_target(tmp_path: Path) -> None:
    payload, _ = request(tmp_path)
    provider_target = Path(payload["provider"]["canonical_target"])
    provider_entrypoint = tmp_path / "installed-provider"
    provider_entrypoint.symlink_to(provider_target)
    payload["provider"]["entrypoint"] = str(provider_entrypoint)

    result = create_provider_terminal.create_terminal(payload)

    orca_argv = result["orca_result"]["argv"]
    command = orca_argv[orca_argv.index("--command") + 1]
    assert shlex.split(command) == [str(provider_target), *payload["arguments"]]
