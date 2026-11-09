"""Exercise released Gaori v0.1.20 with disposable Aquarium consumer fixtures."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins/aquarium/skills/dev-setup/scripts"))
import inspect_tools


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def signature_hashes(records: list[dict]) -> list[str]:
    return sorted(digest(row["signature"].encode()) for row in records)


def require_excerpt(excerpt: bytes, block: bytes) -> None:
    header = block.splitlines()[0].replace(b"token=secret", b"token=<redacted>")
    require(
        header in excerpt and b"token=secret" not in excerpt,
        "excerpt missing its redacted failure header",
    )


def verify(binary: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="aquarium-gaori-", dir="/tmp") as temporary:
        root = Path(temporary).resolve()
        repo, home, bin_dir = root / "repo", root / "home", root / "bin"
        for directory in (repo, home, bin_dir):
            directory.mkdir()
        executable = bin_dir / "gaori"
        shutil.copy2(binary, executable)
        binary_digest = digest(executable.read_bytes())
        env = {
            "HOME": str(home),
            "PATH": str(bin_dir) + os.pathsep + os.defpath,
            "CODEX_HOME": str(home / ".codex"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CEILING_DIRECTORIES": str(root),
            "GIT_OPTIONAL_LOCKS": "0",
            "TMPDIR": str(root),
        }
        # An enclosing repository makes accidental upward Git discovery observable.
        (root / "sentinel").write_text("enclosing repository fixture\n")
        for args in (
            ("init", "-q"),
            ("add", "sentinel"),
            (
                "-c",
                "user.name=Compatibility Fixture",
                "-c",
                "user.email=fixture@example.test",
                "-c",
                "core.hooksPath=/dev/null",
                "commit",
                "--allow-empty",
                "-qm",
                "fixture",
            ),
        ):
            subprocess.run(
                ["git", "-C", str(root), *args],
                cwd=root,
                env=env,
                capture_output=True,
                check=True,
                timeout=30,
            )
        parent_index = root / ".git/index"
        index_before = parent_index.read_bytes()
        passed = []

        def run(*args: str, code: int = 0) -> dict:
            result = subprocess.run(
                [str(executable), "--json", "--repo", str(repo), *args],
                cwd=repo,
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            require(
                result.returncode == code,
                f"{args[:2]}: expected exit {code}, got {result.returncode}: "
                f"{result.stderr[:1000]}",
            )
            return json.loads(result.stdout) if result.stdout.strip() else {}

        def record(name: str) -> None:
            passed.append(name)
            print(f"PASS {name}", flush=True)

        require(run("version")["version"] == "v0.1.20", "expected Gaori v0.1.20")
        config = repo / ".gaori/tester.yaml"
        config.parent.mkdir()
        argv = [
            sys.executable,
            "-c",
            "import pathlib,sys; sys.stdout.buffer.write(pathlib.Path('input.log').read_bytes()); sys.exit(7)",
        ]
        # JSON is valid YAML; use it to preserve the exact fixture child argv.
        config.write_text(
            json.dumps(
                {
                    "version": 2,
                    "commands": {
                        "unit": {
                            "command": argv,
                            "tags": ["unit"],
                            "parser": "generic",
                            "timeout_sec": 30,
                        }
                    },
                    "redaction": {
                        "patterns": [
                            {
                                "name": "token",
                                "regex": "token=secret",
                                "replace": "token=<redacted>",
                            }
                        ]
                    },
                }
            )
        )
        with mock.patch.dict(os.environ, env, clear=True):
            tool = inspect_tools.inspect_gaori(repo, 5.0)
        require(
            tool["version_supported"] and tool["status"] == "configured",
            "Aquarium adapter rejected the release/config",
        )
        record("release-version-and-aquarium-adapter")

        noise = b"neutral filler\n" * 25000
        blocks = [
            b"TypeError: early\nsrc/early.ts:1:2\n\n",
            b"TypeError: middle\nsrc/middle.ts:2:3\n\n",
            b"TypeError: late token=secret\nsrc/late.ts:3:4\n",
        ]
        raw = noise.join(blocks)
        source = repo / "input.log"
        source.write_bytes(raw)

        def artifacts(result: dict, expected: bytes) -> tuple[dict, dict, Path]:
            summary_path = repo / result["summary_json"]
            summary_bytes = summary_path.read_bytes()
            summary = json.loads(summary_bytes)
            status = json.loads((repo / result["status_json"]).read_bytes())
            copied = repo / summary["raw_log"]
            require(copied.read_bytes() == expected, "raw bytes changed")
            require(
                summary["raw_log_sha256"] == digest(expected), "raw digest mismatch"
            )
            require(
                status["summary_sha256"] == digest(summary_bytes),
                "summary digest mismatch",
            )
            for kind in ("failure", "warning"):
                hashes = signature_hashes(summary[kind + "s"] or [])
                require(
                    status[kind + "_signatures"] == hashes, "decoded signature mismatch"
                )
            require(
                not summary.get("git_revision") and summary.get("git_dirty") is None,
                "fixture inherited enclosing Git provenance",
            )
            require(
                parent_index.read_bytes() == index_before, "enclosing Git index changed"
            )
            return summary, status, summary_path

        for name, args, code in (
            ("configured", ("run", "unit"), 7),
            ("ad-hoc", ("run", "--parser", "generic", "--tag", "unit", "--", *argv), 7),
            ("summarize", ("summarize", "input.log"), 0),
        ):
            summary, _, path = artifacts(run(*args, code=code), raw)
            require(
                summary["status"] == "failed"
                and summary["exit_code"] == (7 if name != "summarize" else 1),
                "child/inferred result mismatch",
            )
            require(
                summary["extractor_status"] != "degraded"
                and summary["failure_count"] == 3,
                "complete-log extraction lost a failure",
            )
            for failure, block in zip(summary["failures"], blocks, strict=True):
                span = failure["raw_span"]
                start, end = span["start_byte"], span["end_byte"]
                require(
                    0 <= start <= raw.index(block) < end <= len(raw)
                    and block.splitlines()[0] in raw[start:end]
                    and span["start_line"] == raw[:start].count(b"\n") + 1,
                    "incorrect absolute span",
                )
                excerpt = (path.parent / failure["excerpt"]).read_bytes()
                require_excerpt(excerpt, block)
            record(name + "-complete-log-evidence")

        before = sorted(p.relative_to(repo) for p in repo.rglob("*"))
        detected = run("parsers", "detect", "input.log")
        require(
            detected["scanned_bytes"] == len(raw) == detected["total_bytes"]
            and not detected["truncated"],
            "parser detection did not read complete log",
        )
        sample = run("config", "check", "--sample", "input.log")["redaction_sample"]
        require(
            sample["sample_bytes"] == len(raw) and sample["total_matches"] == 1,
            "redaction sample count mismatch",
        )
        require(
            before == sorted(p.relative_to(repo) for p in repo.rglob("*")),
            "read-only diagnosis created artifacts",
        )
        record("full-log-detection-and-redaction-sample")

        source.write_bytes(noise)
        summary, _, _ = artifacts(run("summarize", "input.log"), noise)
        require(
            summary["status"] == "passed" and summary["extractor_status"] == "no_match",
            "size degraded a passing log",
        )
        dense = b"".join(
            f"TypeError: failure {i}\nsrc/a.ts:{i + 1}:2\n\n".encode()
            for i in range(60)
        )
        source.write_bytes(dense)
        summary, _, _ = artifacts(run("summarize", "input.log"), dense)
        require(
            summary["failures_truncated"]
            and summary["failure_count"] <= 50
            and summary["extractor_status"] == "degraded",
            "record cap lost its degradation",
        )
        record("size-only-no-match-and-record-truncation")

        malformed = (
            b"neutral\nneutral\nneutral\nTypeError: bad \xff\xfe\nsrc/bad.ts:1:2\n\nwarning: bad \xff\n"
            + noise
        )
        source.write_bytes(malformed)
        result = run("run", "unit", code=7)
        summary, _, _ = artifacts(result, malformed)
        require(
            summary["failure_count"] == 1 and summary["warning_count"] == 1,
            "malformed signature fixture did not extract both kinds",
        )
        run(
            "rules", "propose", "--summary", result["summary_json"], "--failure", "F001"
        )
        stats = run("runs", "stats", "unit")
        require(
            stats["observed_terminal_count"] == 2 and stats["skipped_runs"] == 0,
            "insights rejected a configured run",
        )
        record("malformed-utf8-hashes-proposal-and-insights")

        source.write_bytes(raw)
        proposal = run(
            "rules",
            "propose",
            "--parser",
            "generic",
            "--tag",
            "unit",
            "--raw-log",
            "input.log",
            "--span",
            "1:2",
        )
        rule = yaml.safe_load((repo / proposal["path"]).read_text())
        rule_id = rule["id"]
        rule["match"]["start"]["regex"] = "^TypeError:"
        rule_file = repo / "overmatch-rule.json"
        rule_file.write_text(json.dumps(rule))
        run("rules", "create", "--file", str(rule_file))
        matched = run(
            "rules",
            "test",
            "--rule",
            rule_id,
            "--log",
            "input.log",
            "--expect-span",
            "1:2",
            code=4,
        )
        require(
            matched["failure_count"] == 3 and not matched["passed"],
            "rule test missed late overmatches",
        )
        proposals = sorted((repo / ".gaori/rule-proposals").rglob("*"))
        source.write_bytes(b"x" * (256 * 1024 + 1) + b"\n")
        run(
            "rules",
            "propose",
            "--parser",
            "generic",
            "--tag",
            "unit",
            "--raw-log",
            "input.log",
            "--span",
            "1:1",
            code=2,
        )
        require(
            proposals == sorted((repo / ".gaori/rule-proposals").rglob("*")),
            "oversized selection wrote a proposal",
        )
        record("large-rule-source-overmatch-and-selection-limit")
        record("enclosing-git-repository-isolation")
        print(
            json.dumps(
                {"version": "v0.1.20", "binary_sha256": binary_digest, "passed": passed}
            )
        )


def main() -> int:
    value = os.environ.get("GAORI_BIN", "")
    binary = Path(value)
    if (
        not value
        or not binary.is_absolute()
        or binary.resolve() != binary
        or not binary.is_file()
        or not os.access(binary, os.X_OK)
    ):
        print(
            "GAORI_BIN must be an absolute physical path to a regular executable",
            file=sys.stderr,
        )
        return 1
    try:
        verify(binary)
    except (
        OSError,
        ValueError,
        KeyError,
        RuntimeError,
        subprocess.TimeoutExpired,
        subprocess.CalledProcessError,
    ) as error:
        print(f"Gaori compatibility failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
