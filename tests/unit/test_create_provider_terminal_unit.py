from __future__ import annotations

import hashlib
import importlib.util
import json
import shlex
import stat
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
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
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
    command_argv = shlex.split(command)
    assert command_argv[:3] == [str(Path(sys.executable).resolve()), "-I", "-c"]
    assert command_argv[4:] == [
        payload["provider"]["canonical_target"],
        payload["provider"]["sha256"],
        payload["repository"],
        *payload["arguments"],
    ]
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


def test_orca_private_copy_survives_canonical_replacement(tmp_path: Path) -> None:
    payload, _ = request(tmp_path)
    orca = Path(payload["orca"]["canonical_target"])
    expected_digest = payload["orca"]["sha256"]

    with create_provider_terminal.immutable_executable_copy(
        orca, expected_digest
    ) as admitted:
        executable(orca, "#!/bin/sh\nexit 99\n")
        completed = subprocess.run(
            [admitted], check=False, capture_output=True, text=True
        )
        assert admitted.stat().st_flags & stat.UF_IMMUTABLE

    assert completed.returncode == 0
    assert json.loads(completed.stdout) == {"argv": []}


def test_provider_command_uses_verified_canonical_target(tmp_path: Path) -> None:
    payload, _ = request(tmp_path)
    provider_target = Path(payload["provider"]["canonical_target"])
    provider_entrypoint = tmp_path / "installed-provider"
    provider_entrypoint.symlink_to(provider_target)
    payload["provider"]["entrypoint"] = str(provider_entrypoint)

    result = create_provider_terminal.create_terminal(payload)

    orca_argv = result["orca_result"]["argv"]
    command = orca_argv[orca_argv.index("--command") + 1]
    command_argv = shlex.split(command)
    assert command_argv[4:] == [
        str(provider_target),
        payload["provider"]["sha256"],
        payload["repository"],
        *payload["arguments"],
    ]


def test_orca_runs_from_requested_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload, _ = request(tmp_path)
    observed = tmp_path / "orca-cwd"
    orca = Path(payload["orca"]["canonical_target"])
    executable(
        orca,
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        f"open({str(observed)!r}, 'w', encoding='utf-8').write(os.getcwd())\n"
        "print(json.dumps({'argv': sys.argv[1:]}))\n",
    )
    payload["orca"]["sha256"] = digest(orca)
    caller = tmp_path / "caller"
    caller.mkdir()
    monkeypatch.chdir(caller)

    create_provider_terminal.create_terminal(payload)

    assert observed.read_text(encoding="utf-8") == payload["repository"]


def test_repository_must_be_exact_git_root(tmp_path: Path) -> None:
    payload, _ = request(tmp_path)
    nested = Path(payload["repository"]) / "nested"
    nested.mkdir()
    payload["repository"] = str(nested)

    with pytest.raises(create_provider_terminal.RequestError) as error:
        create_provider_terminal.parse_request(payload)

    assert error.value.code == "repository_not_root"


@pytest.mark.parametrize("repository", ["", ".", "relative/repository"])
def test_repository_must_be_nonempty_and_absolute(
    tmp_path: Path, repository: str
) -> None:
    payload, _ = request(tmp_path)
    payload["repository"] = repository

    with pytest.raises(create_provider_terminal.RequestError) as error:
        create_provider_terminal.parse_request(payload)

    assert error.value.code == "repository_invalid"


def test_provider_is_revalidated_in_spawned_command(tmp_path: Path) -> None:
    payload, _ = request(tmp_path)
    provider = Path(payload["provider"]["canonical_target"])
    orca = Path(payload["orca"]["canonical_target"])
    marker = tmp_path / "replacement-executed"
    original = provider.read_text(encoding="utf-8")
    replacement = (
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('executed', encoding='utf-8')\n"
    )
    executable(
        orca,
        "#!/usr/bin/env python3\n"
        "import json, shlex, subprocess, sys\n"
        "from pathlib import Path\n"
        f"provider = Path({str(provider)!r})\n"
        f"provider.write_text({replacement!r}, encoding='utf-8')\n"
        "provider.chmod(provider.stat().st_mode | 0o111)\n"
        "arguments = sys.argv[1:]\n"
        "command = arguments[arguments.index('--command') + 1]\n"
        "child = subprocess.run(shlex.split(command), capture_output=True, text=True)\n"
        f"provider.write_text({original!r}, encoding='utf-8')\n"
        "provider.chmod(provider.stat().st_mode | 0o111)\n"
        "print(json.dumps({'argv': arguments, 'child_exit': child.returncode, 'child_stderr': child.stderr}))\n",
    )
    payload["orca"]["sha256"] = digest(orca)

    result = create_provider_terminal.create_terminal(payload)

    assert result["orca_result"]["child_exit"] == 126
    assert (
        "provider identity changed before execution"
        in result["orca_result"]["child_stderr"]
    )
    assert not marker.exists()
