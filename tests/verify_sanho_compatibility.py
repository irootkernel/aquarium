"""Exercise Sanho v0.2.10 and Aquarium's adapter using disposable local Git repos."""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins/aquarium/skills/dev-setup/scripts"))
import inspect_tools


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def verify(binary: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="aquarium-sanho-", dir="/tmp") as temporary:
        root = Path(temporary).resolve()
        for name in ("home", "sanho-home", "bin", "seed", "app", "scratch"):
            (root / name).mkdir()
        executable = root / "bin/sanho"
        shutil.copy2(binary, executable)
        binary_digest = hashlib.sha256(executable.read_bytes()).hexdigest()
        git_binary = shutil.which("git")
        require(git_binary is not None, "Git is required")
        git_calls = root / "git-calls"
        git_shim = root / "bin/git"
        # Adapter probes strip inherited GIT_*; enforce fixture isolation in Git itself.
        git_shim.write_text(
            "#!/bin/sh\n"
            "export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_SYSTEM=/dev/null "
            "GIT_CONFIG_GLOBAL=/dev/null GIT_ATTR_NOSYSTEM=1 GIT_ALLOW_PROTOCOL=file\n"
            f"printf '%s\\n' \"$PPID\" >> {shlex.quote(str(git_calls))}\n"
            f'exec {shlex.quote(git_binary)} "$@"\n'
        )
        git_shim.chmod(0o755)
        (root / "home/.gitconfig").write_text(
            f"[core]\n\thooksPath = {root / 'unexpected-hooks'}\n"
        )
        env = {
            "PATH": str(root / "bin") + os.pathsep + os.defpath,
            "HOME": str(root / "home"),
            "SANHO_HOME": str(root / "sanho-home"),
            "TMPDIR": str(root / "scratch"),
            "LC_ALL": "en_US.UTF-8",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_AUTHOR_NAME": "Compatibility Fixture",
            "GIT_AUTHOR_EMAIL": "fixture@example.test",
            "GIT_COMMITTER_NAME": "Compatibility Fixture",
            "GIT_COMMITTER_EMAIL": "fixture@example.test",
            "GIT_EDITOR": "true",
        }
        app, seed = root / "app", root / "seed"
        canonical, remote = root / "canonical.git", root / "application.git"
        passed = []

        def run(cwd: Path, *args: str, code: int = 0) -> subprocess.CompletedProcess:
            result = subprocess.run(
                args,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            require(
                result.returncode == code,
                f"{args[:2]}: expected exit {code}, got {result.returncode}: "
                f"{result.stdout} {result.stderr}",
            )
            return result

        def git(cwd: Path, *args: str, code: int = 0) -> str:
            return run(cwd, "git", *args, code=code).stdout.strip()

        def sanho(*args: str, code: int = 0) -> dict:
            return json.loads(run(app, str(executable), *args, code=code).stdout)

        def head(repo: Path) -> str:
            return git(repo, "rev-parse", "refs/heads/main")

        def record(name: str) -> None:
            passed.append(name)
            print(f"PASS {name}", flush=True)

        def inspect_workspace() -> dict:
            before_calls = git_calls.read_bytes()
            with mock.patch.dict(os.environ, env, clear=True):
                result = inspect_tools.inspect_sanho(
                    app, 30, agent_skill={"present": True}
                )
            native_calls = git_calls.read_bytes()[len(before_calls) :].splitlines()
            require(
                any(int(parent) != os.getpid() for parent in native_calls),
                "native Sanho probes bypassed fixture Git",
            )
            for name in ("status", "doctor"):
                probe = result["probes"][name]
                require(
                    probe["ok"] and probe["contract_valid"],
                    f"native {name} response is not valid",
                )
            return result

        git_version = git(root, "--version")
        require(
            sanho("version", "--json") == {"name": "sanho", "version": "v0.2.10"},
            "the selected executable must report exactly Sanho v0.2.10",
        )
        git(app, "init", "-q", "-b", "main")
        git(app, "config", "user.name", "Compatibility Fixture")
        git(app, "config", "user.email", "fixture@example.test")
        require(
            sanho("status", "--json", code=1)["error"]["code"] == "not_in_workspace",
            "unregistered workspace was not reported",
        )
        require(not (app / ".sanho.json").exists(), "status initialized a workspace")
        record("identity-and-unconfigured-workspace")

        git(root, "init", "-q", "--bare", "-b", "main", str(canonical))
        git(root, "init", "-q", "--bare", "-b", "main", str(remote))
        git(seed, "init", "-q", "-b", "main")
        (seed / "api.md").write_text("base\n")
        git(seed, "add", ".")
        git(seed, "commit", "-qm", "Seed canonical docs")
        git(seed, "remote", "add", "origin", str(canonical))
        git(seed, "push", "-q", "origin", "main")
        (app / "app.txt").write_text("fixture\n")
        git(app, "add", ".")
        git(app, "commit", "-qm", "Seed application")
        hook = app / ".git/hooks/pre-commit"
        hook_marker = root / "foreign-hook-calls"
        foreign = "#!/bin/sh\n" + (
            f"printf 'called\\n' >> {shlex.quote(str(hook_marker))}\n"
        )
        hook.write_text(foreign)
        hook.chmod(0o755)
        run(
            app,
            str(executable),
            "init",
            "--project",
            "compatibility",
            "--docs-repo-url",
            str(canonical),
        )
        git(app, "add", ".")
        git(app, "commit", "-qm", "Adopt canonical docs")
        git(app, "remote", "add", "origin", str(remote))
        git(app, "push", "-q", "origin", "main")
        require(
            foreign in hook.read_text(), "initialization changed foreign hook bytes"
        )
        require(
            os.access(hook, os.X_OK) and hook_marker.is_file(),
            "foreign hook was not executable or did not run",
        )
        require(
            sanho("sync", "--inspect", "--json")["state"] == "none",
            "idle inspection reported an active sync",
        )
        record("initialization-foreign-hooks-and-idle-inspection")

        observed = inspect_workspace()
        require(
            observed["status"] == "configured", "native workspace was not configured"
        )
        raw = json.dumps(
            {"status": sanho("status", "--json"), "doctor": sanho("doctor", "--json")}
        )
        require(
            root.name in raw and "compatibility" in raw,
            "raw privacy fixture did not contain its private values",
        )
        for private in (root.name, "fixture@example.test", "compatibility"):
            require(
                private not in json.dumps(observed["probes"]),
                "adapter leaked private fields",
            )
        record("native-status-doctor-and-redaction")

        original = head(canonical)
        (seed / "guide.md").write_text("upstream guide\n")
        git(seed, "add", ".")
        git(seed, "commit", "-qm", "Add guide")
        git(seed, "push", "-q", "origin", "main")
        require(
            sanho("sync", "--json")["status"] == "synced", "clean sync did not finish"
        )
        base_file = app / ".sanho_base.json"
        saved_base = base_file.read_bytes()
        # Synthetic corruption fixture from the released doctor regression.
        # Never apply this setup to a real workspace.
        base_file.write_text(json.dumps({"version": 2, "commit": original, "tree": ""}))
        (app / "docs/api.md").write_text("work in progress\n")
        doctor = sanho("doctor", "--json")
        require(
            any(c["severity"] == "info" for c in doctor["checks"]),
            "fixture did not reach native informational diagnosis",
        )
        observed = inspect_workspace()
        require(
            doctor["warnings"] == 0
            and observed["probes"]["doctor"]["result"]["warning_check_count"] == 0
            and observed["status"] == "configured",
            "informational checks degraded a valid workspace",
        )
        base_file.write_bytes(saved_base)
        git(app, "restore", "docs/api.md")
        record("native-informational-doctor")

        # Missing hook is a warning, even though doctor exits zero.
        saved_hook = hook.read_bytes()
        hook.write_text(foreign)
        doctor = sanho("doctor", "--json")
        warning_count = sum(c["severity"] == "warning" for c in doctor["checks"])
        require(
            any(
                c["name"] == "hooks" and c["severity"] == "warning"
                for c in doctor["checks"]
            ),
            "missing hook was not diagnosed",
        )
        observed = inspect_workspace()
        require(
            observed["probes"]["doctor"]["result"]["warnings"] == warning_count > 0
            and observed["probes"]["doctor"]["result"]["warning_check_count"]
            == warning_count,
            "adapter did not preserve independently counted warnings",
        )
        require(observed["status"] == "degraded", "warning was treated as healthy")
        hook.write_bytes(saved_hook)
        record("native-warning-degrades-readiness")

        before = head(canonical)
        (app / "docs/api.md").write_text("local edit\n")
        git(app, "add", "docs")
        hook_calls = hook_marker.read_bytes()
        git(app, "commit", "-qm", "Edit local docs")
        require(
            hook_marker.read_bytes() != hook_calls and os.access(hook, os.X_OK),
            "local commit did not execute the preserved foreign hook",
        )
        local_commit = head(app)
        require(head(canonical) == before, "local commit published documentation")
        require(
            "docs-base:" in git(app, "log", "-1", "--format=%B"),
            "commit hook omitted native provenance",
        )
        record("commit-is-local-with-native-provenance")

        (seed / "api.md").write_text("canonical edit\n")
        git(seed, "add", ".")
        git(seed, "commit", "-qm", "Edit canonical docs")
        git(seed, "push", "-q", "origin", "main")
        sanho("status", "--refresh", "--json")
        refs = (head(canonical), head(remote))
        preview = sanho("preview", "--json")
        require(preview["blocked"], "conflicting push preview was not blocked")
        require((head(canonical), head(remote)) == refs, "preview changed remote refs")
        rejected = run(app, "git", "push", "origin", "main", code=1)
        require(
            "sanho:" in rejected.stderr and "sync" in rejected.stderr,
            "push failure did not identify Sanho synchronization refusal",
        )
        require((head(canonical), head(remote)) == refs, "rejected push changed refs")
        record("blocked-preview-and-push-preserve-refs")

        require(
            sanho("sync", "--json")["status"] == "conflicts",
            "conflicting sync did not return conflicts at exit zero",
        )
        inspection = sanho("sync", "--inspect", "--json")
        require(
            inspection["state"] == "active" and not inspection["continuation"]["ready"],
            "unresolved sync was considered ready",
        )
        refusal = sanho("sync", "--json", code=1)["error"]
        require(
            refusal["reason"] == "active_sync"
            and isinstance(refusal["paths"], list)
            and "recovery_id" in refusal,
            "typed refusal evidence is missing",
        )
        blocked = sanho("sync", "--continue", "--json", code=1)["error"]
        require(
            blocked["reason"] == "markers_remaining"
            and "docs/api.md" in blocked["paths"]
            and blocked["recovery_id"] == "sync_finish_resolution",
            "marker refusal lost its typed path or recovery evidence",
        )
        (app / "docs/api.md").write_text("resolved edit\n")
        require(
            not sanho("sync", "--inspect", "--json")["continuation"]["ready"],
            "uncommitted resolution was considered ready",
        )
        git(app, "add", "docs")
        git(app, "commit", "-qm", "Resolve sync conflict")
        require(
            sanho("sync", "--inspect", "--json")["continuation"]["ready"],
            "committed resolution was not ready",
        )
        record("conflict-inspection-and-typed-refusal")

        # An unused external filter must prevent the reader from making a verdict.
        git(app, "config", "filter.fixture.clean", "cat")
        inspection_state = (
            head(app),
            git(app, "status", "--porcelain"),
            head(canonical),
            head(remote),
        )
        unavailable = sanho("sync", "--inspect", "--json", code=1)["error"]
        require(
            unavailable["code"] == "inspection_unavailable",
            "external filter did not produce the native availability refusal",
        )
        require(
            inspection_state
            == (
                head(app),
                git(app, "status", "--porcelain"),
                head(canonical),
                head(remote),
            ),
            "unavailable inspection changed Git state",
        )
        # End this test-only policy fixture; this is not recovery advice.
        git(app, "config", "--unset", "filter.fixture.clean")
        record("inspection-unavailable-without-mutation-fallback")

        require(
            sanho("sync", "--continue", "--json")["status"] == "completed",
            "continue did not complete the resolved sync",
        )
        resolved_commit = head(app)
        git(app, "push", "-q", "origin", "main")
        require(
            head(remote) == resolved_commit and resolved_commit != local_commit,
            "application publication does not match the resolution commit",
        )
        require(
            git(canonical, "show", "main:api.md") == "resolved edit",
            "canonical publication has incorrect content",
        )
        require(
            sanho("sync", "--inspect", "--json")["state"] == "none",
            "successful continue left an active sync",
        )
        require(foreign in hook.read_text(), "foreign hook was lost")
        record("continue-and-publication-to-both-remotes")
        history = sanho("log", "--json")["entries"]
        publication = next(entry for entry in history if entry["kind"] == "publication")
        external = next(entry for entry in history if entry["kind"] == "external")
        require(external["source"] is None, "external commit acquired false provenance")
        require(
            publication["source"]["application_commit"] == resolved_commit,
            "publication provenance names the wrong application commit",
        )
        document = sanho("show", publication["commit"], "--path", "api.md", "--json")
        require(
            document["document"]["content"] == "resolved edit\n",
            "canonical show returned incorrect document content",
        )
        require(
            sanho("check", "--require-published", "--json")["passed"],
            "published policy did not pass after publication",
        )
        record("history-document-and-publication-policy")
        print(
            json.dumps(
                {
                    "version": "v0.2.10",
                    "binary_sha256": binary_digest,
                    "git_version": git_version,
                    "passed": passed,
                }
            )
        )


def main() -> int:
    value = os.environ.get("SANHO_BIN", "")
    binary = Path(value)
    if (
        not value
        or not binary.is_absolute()
        or binary.resolve() != binary
        or not binary.is_file()
        or not os.access(binary, os.X_OK)
    ):
        print(
            "SANHO_BIN must be an absolute physical path to a regular executable",
            file=sys.stderr,
        )
        return 1
    try:
        verify(binary)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"Sanho compatibility failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
