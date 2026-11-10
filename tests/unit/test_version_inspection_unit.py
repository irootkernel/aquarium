"""Version inventory behavior, with isolated executables and HTTP responses."""

import importlib.util
import json
import shutil
import subprocess
import sys
import urllib.error
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "plugins/aquarium/skills/version/scripts/inspect_versions.py"
spec = importlib.util.spec_from_file_location("version_inspection", SCRIPT)
versions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(versions)


def stable(tag="v9.0.0"):
    return {"tag_name": tag, "draft": False, "prerelease": False}


def test_plugin_uses_exact_package_not_cwd(tmp_path, monkeypatch):
    path = tmp_path / ".codex-plugin/plugin.json"
    path.parent.mkdir()
    path.write_text(json.dumps({"name": "aquarium", "version": "1.2.3"}))
    monkeypatch.chdir("/")
    assert versions.local_plugin(tmp_path)["version"] == "1.2.3"
    path.write_text("{}")
    assert versions.local_plugin(tmp_path)["status"] == "invalid_metadata"
    path.unlink()
    assert versions.local_plugin(tmp_path)["status"] == "unavailable"


@pytest.mark.parametrize(
    "name",
    [
        "sanho",
        "dolgorae",
        "mulgae",
        "gaori",
        "sorage",
        "podway",
        "haepari",
        "herdr",
        "ouroboros",
    ],
)
def test_only_native_version_commands(name, monkeypatch):
    selected = []

    def which(name):
        selected.append(name)
        return "/bin/tool"

    monkeypatch.setattr(versions.shutil, "which", which)
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        assert kwargs["cwd"] == "/"
        assert kwargs["timeout"] == 10
        payload = {"name": name, "version": "v1.2.3"}
        if name == "haepari":
            payload = {
                "schema": "haepari.envelope/v1",
                "ok": True,
                "operation": "version",
                "data": {"version": "v1.2.3"},
            }
        output = (
            f"{name} version 1.2.3\n"
            if name in {"herdr", "ouroboros"}
            else json.dumps(payload)
        )
        return subprocess.CompletedProcess(args, 0, output, "")

    monkeypatch.setattr(versions.subprocess, "run", run)
    assert versions.local_cli(name)["version"].removeprefix("v") == "1.2.3"
    expected = (
        ["--version"] if name in {"herdr", "ouroboros"} else ["version", "--json"]
    )
    if name == "podway":
        expected = ["--contract-generation", "2", *expected]
    assert calls == [["/bin/tool", *expected]]
    assert selected == ["ooo" if name == "ouroboros" else name]


@pytest.mark.parametrize(
    "failure,status",
    [
        ("exit", "command_failed"),
        ("timeout", "timeout"),
        ("json", "invalid_response"),
        ("shape", "invalid_response"),
        ("os", "command_failed"),
    ],
)
def test_cli_failure_is_reported(monkeypatch, failure, status):
    monkeypatch.setattr(versions.shutil, "which", lambda _: "/bin/tool")

    def run(args, **kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired(args, 10)
        if failure == "os":
            raise OSError("unavailable")
        return subprocess.CompletedProcess(
            args, int(failure == "exit"), "[]" if failure == "shape" else "bad", ""
        )

    monkeypatch.setattr(versions.subprocess, "run", run)
    assert versions.local_cli("gaori")["status"] == status


def test_missing_cli_does_not_execute(monkeypatch):
    monkeypatch.setattr(versions.shutil, "which", lambda _: None)
    monkeypatch.setattr(
        versions.subprocess, "run", lambda *a, **k: pytest.fail("unexpected process")
    )
    assert versions.local_cli("gaori")["status"] == "not_installed"


def test_skill_versions_and_ambiguous_copies(tmp_path, monkeypatch):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "active"))
    monkeypatch.setattr(versions.Path, "home", lambda: tmp_path)
    path = tmp_path / "active/skills/humanizer/SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text('---\nname: humanizer\nmetadata:\n  version: "3.1.0"\n---\n')
    assert versions.local_skills("humanizer")["version"] == "3.1.0"
    other = tmp_path / ".agents/skills/humanizer/SKILL.md"
    other.parent.mkdir(parents=True)
    other.write_text(path.read_text())
    assert versions.local_skills("humanizer")["status"] == "version_unverifiable"
    other.unlink()
    path.write_text("---\nname: humanizer\n---\nLatest version 9.9.9")
    assert versions.local_skills("humanizer")["version"] is None
    path.unlink()
    assert versions.local_skills("humanizer")["status"] == "not_installed"


@pytest.mark.parametrize(
    "left,right,result",
    [
        ("1.2.3", "v1.2.3", "current"),
        ("0.1.9", "0.2.0", "update_available"),
        ("2.0.0", "1.0.0", "local_newer"),
        ("1.0.0-rc.1", "1.0.0", "unverifiable"),
        ("1.0.0+dev", "1.0.0", "unverifiable"),
        (None, "1.0.0", "unverifiable"),
    ],
)
def test_version_comparison(left, right, result):
    assert (
        versions.comparison({"status": "observed", "version": left}, {"version": right})
        == result
    )


def test_latest_is_not_limited_to_supported_line(monkeypatch):
    monkeypatch.setattr(versions, "github_json", lambda *a: stable("v99.0.0"))
    assert versions.latest("gaori")["version"] == "v99.0.0"


@pytest.mark.parametrize(
    "payload", [stable("nightly"), {**stable(), "prerelease": True}, [], {}]
)
def test_invalid_release_is_not_latest(monkeypatch, payload):
    monkeypatch.setattr(versions, "github_json", lambda *a: payload)
    assert versions.latest("aquarium")["status"] == "lookup_failed"


@pytest.mark.parametrize(
    "code,empty,status",
    [
        (404, True, "no_release"),
        (404, False, "lookup_failed"),
        (403, False, "lookup_failed"),
        (429, False, "lookup_failed"),
    ],
)
def test_release_absence_and_access_failures(monkeypatch, code, empty, status):
    def fetch(repository, suffix):
        if suffix == "releases?per_page=100&page=1" and empty:
            return []
        raise urllib.error.HTTPError("https://api.github.com", code, "error", {}, None)

    monkeypatch.setattr(versions, "github_json", fetch)
    assert versions.latest("aquarium")["status"] == status


def test_tag_pagination_and_commit_fallback(monkeypatch):
    def fetch(repository, suffix):
        if suffix.endswith("page=1"):
            return [{"name": "v0.1.0"}] * 100
        return [{"name": "v2.0.0"}, {"name": "v3.0.0-rc.1"}]

    monkeypatch.setattr(versions, "github_json", fetch)
    assert versions.latest("lora")["version"] == "v2.0.0"
    monkeypatch.setattr(
        versions,
        "github_json",
        lambda repository, suffix: (
            [] if suffix.startswith("tags?") else {"sha": "a" * 40}
        ),
    )
    for name in ("lora", "deslop"):
        remote = versions.latest(name)
        assert remote["kind"] == "commit"
        assert remote["version"] is None


def test_offline_and_partial_report(monkeypatch):
    monkeypatch.setattr(
        versions, "local_cli", lambda _: {"status": "timeout", "version": None}
    )
    monkeypatch.setattr(
        versions,
        "local_skills",
        lambda _: {"status": "version_unverifiable", "version": None},
    )
    monkeypatch.setattr(
        versions, "latest", lambda _: pytest.fail("offline contacted network")
    )
    report = versions.report(offline=True)
    assert len(report["components"]) == 14
    assert all(
        row["latest"]["status"] == "not_requested" for row in report["components"]
    )
    monkeypatch.setattr(
        versions, "latest", lambda _: {"status": "lookup_failed", "version": None}
    )
    assert len(versions.report()["components"]) == 14


def test_cli_offline_with_empty_path_does_not_write(tmp_path):
    import os

    environment = {
        **os.environ,
        "PATH": str(tmp_path),
        "HOME": str(tmp_path),
        "CODEX_HOME": str(tmp_path / "codex"),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    package = tmp_path / "package"
    script_copy = package / "skills/version/scripts/inspect_versions.py"
    inspector_copy = package / "skills/dev-setup/scripts/inspect_tools.py"
    for target, source in (
        (script_copy, SCRIPT),
        (
            inspector_copy,
            ROOT / "plugins/aquarium/skills/dev-setup/scripts/inspect_tools.py",
        ),
    ):
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    environment.pop("PYTHONDONTWRITEBYTECODE", None)
    before = list(tmp_path.rglob("*"))
    run = subprocess.run(
        [sys.executable, str(script_copy), "--offline"],
        env=environment,
        cwd=tmp_path,
        capture_output=True,
        check=False,
        text=True,
        timeout=20,
    )
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout)["schema"] == "aquarium-version-report/v1"
    assert list(tmp_path.rglob("*")) == before


def test_http_request_is_public_metadata_only(monkeypatch):
    import io

    calls = []

    def open_request(request, **kwargs):
        calls.append((request, kwargs))
        return io.BytesIO(json.dumps(stable()).encode())

    monkeypatch.setattr(versions.urllib.request, "urlopen", open_request)
    assert versions.latest("aquarium")["version"] == "v9.0.0"
    request, kwargs = calls[0]
    assert (
        request.full_url
        == "https://api.github.com/repos/irootkernel/aquarium/releases/latest"
    )
    assert request.get_method() == "GET"
    assert request.data is None
    assert "Authorization" not in request.headers
    assert kwargs == {"timeout": 10}


@pytest.mark.parametrize("error", [TimeoutError(), ValueError("invalid JSON")])
def test_network_failure_preserves_local_result(monkeypatch, error):
    def fetch(*args):
        raise error

    monkeypatch.setattr(versions, "github_json", fetch)
    assert versions.latest("aquarium")["status"] == "lookup_failed"


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_ouroboros_uses_existing_multiline_parser(monkeypatch, stream):
    monkeypatch.setattr(
        versions.shutil, "which", lambda name: "/bin/ooo" if name == "ooo" else None
    )
    output = "runtime 9.9.9\nOuroboros version 1.0.0\n"

    def run(args, **kwargs):
        return subprocess.CompletedProcess(
            args,
            0,
            output if stream == "stdout" else "",
            output if stream == "stderr" else "",
        )

    monkeypatch.setattr(versions.subprocess, "run", run)
    assert versions.local_cli("ouroboros")["version"] == "1.0.0"


def test_relative_path_executable_stays_selected(tmp_path, monkeypatch):
    binary = tmp_path / "bin/gaori"
    binary.parent.mkdir()
    binary.write_text(
        "#!" + sys.executable + '\nprint(\'{"name":"gaori","version":"v1.2.3"}\')\n'
    )
    binary.chmod(0o755)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATH", "bin")
    result = versions.local_cli("gaori")
    assert result["version"] == "v1.2.3"
    assert result["path"] == str(binary)


@pytest.mark.parametrize("home", ["", "relative", "shared"])
def test_existing_root_rules(tmp_path, monkeypatch, home):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(versions.Path, "home", lambda: tmp_path)
    chosen = {
        "": tmp_path / ".codex",
        "relative": tmp_path / "relative",
        "shared": tmp_path / ".agents",
    }[home]
    monkeypatch.setenv("CODEX_HOME", str(chosen) if home == "shared" else home)
    path = chosen / "skills/humanizer/SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text('---\nname: humanizer\nversion: "3.1.0"\n---\n')
    result = versions.local_skills("humanizer")
    assert result["version"] == "3.1.0"
    assert result["installations"] == [
        {"skill": "humanizer", "path": str(path), "version": "3.1.0"}
    ]


@pytest.mark.parametrize(
    "error",
    [
        PermissionError("private-path"),
        RuntimeError("home unavailable"),
        RecursionError("nested JSON"),
    ],
)
def test_local_inspection_failure_keeps_other_rows(monkeypatch, error):
    def inspect(name):
        if name == "humanizer":
            raise error
        return {"status": "not_installed", "version": None}

    monkeypatch.setattr(versions, "local_skills", inspect)
    monkeypatch.setattr(
        versions, "local_cli", lambda name: {"status": "not_installed", "version": None}
    )
    report = versions.report(offline=True)
    rows = {row["name"]: row for row in report["components"]}
    assert len(rows) == 14
    assert rows["humanizer"]["local"]["status"] == "inspection_failed"
    assert rows["im-not-ai"]["local"]["status"] == "not_installed"
    assert "private-path" not in json.dumps(report)


@pytest.mark.parametrize("kind", ["empty", "prerelease", "later_stable", "invalid"])
def test_latest_404_checks_complete_release_list(monkeypatch, kind):
    calls = []

    def fetch(repository, suffix):
        calls.append(suffix)
        if suffix == "releases/latest":
            raise urllib.error.HTTPError("url", 404, "missing", {}, None)
        if kind == "invalid":
            return [{}]
        if kind == "empty":
            return []
        if suffix.endswith("page=1"):
            return [{"draft": False, "prerelease": True}] * 100
        return [stable()] if kind == "later_stable" else []

    monkeypatch.setattr(versions, "github_json", fetch)
    result = versions.latest("aquarium")
    assert result["status"] == (
        "no_release" if kind in {"empty", "prerelease"} else "lookup_failed"
    )
    if kind == "prerelease":
        assert calls[-1].endswith("page=2")
        assert result["reason"] == "no_stable_release"
    if kind == "later_stable":
        assert result["reason"] == "latest_release_unavailable"


def test_lora_rejects_noncanonical_tags(monkeypatch):
    monkeypatch.setattr(
        versions,
        "github_json",
        lambda *a: [
            {"name": "v1.02.0"},
            {"name": "v01.2.0"},
            {"name": "v2.0.0-rc.1"},
            {"name": "v1.2.0"},
        ],
    )
    assert versions.latest("lora")["version"] == "v1.2.0"


@pytest.mark.parametrize(
    "error,reason",
    [
        (TimeoutError("secret"), "timeout"),
        (versions.socket.gaierror("secret"), "dns_error"),
        (versions.ssl.SSLError("secret"), "tls_error"),
        (RecursionError("secret"), "invalid_json"),
        (urllib.error.URLError(TimeoutError("secret")), "timeout"),
        (json.JSONDecodeError("secret", "", 0), "invalid_json"),
        (ValueError("response_too_large"), "response_too_large"),
        (ValueError("invalid_stable_release"), "invalid_stable_release"),
        (ValueError("secret"), "invalid_metadata"),
        (urllib.error.HTTPError("secret", 429, "secret", {}, None), "rate_limited"),
        (
            urllib.error.HTTPError(
                "secret", 403, "secret", {"X-RateLimit-Remaining": "0"}, None
            ),
            "rate_limited",
        ),
        (urllib.error.HTTPError("secret", 403, "secret", {}, None), "http_error"),
    ],
)
def test_safe_lookup_reason(error, reason):
    result = versions.lookup_failure(error)
    assert result["reason"] == reason
    assert "secret" not in json.dumps(result)


def test_failed_command_retains_exit_code(monkeypatch):
    monkeypatch.setattr(versions.shutil, "which", lambda _: "/bin/tool")
    monkeypatch.setattr(
        versions.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 7, "private", "private"),
    )
    assert versions.local_cli("gaori") == {
        "path": "/bin/tool",
        "version": None,
        "status": "command_failed",
        "reason": "nonzero_exit",
        "exit_code": 7,
    }


@pytest.mark.parametrize("value", ["1.2.3-rc.1", "1.2.3+build.7", "1.2.3-rc.1+build.7"])
def test_ouroboros_preserves_full_version_identity(value):
    assert (
        versions.ouroboros_version(f"runtime 9.9.9\nOuroboros version {value}\n")
        == value
    )
    assert (
        versions.comparison(
            {"status": "observed", "version": value}, {"version": "1.2.3"}
        )
        == "unverifiable"
    )
