"""Isolated local Git, hosting and gate fixtures. Never invokes a provider."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


class FixtureError(RuntimeError):
    pass


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def regular(path: Path, root: Path) -> Path:
    if (
        not path.is_absolute()
        or path != path.resolve()
        or not path.is_relative_to(root)
    ):
        raise FixtureError(f"unsafe fixture path: {path}")
    if not path.is_file():
        raise FixtureError(f"missing regular fixture file: {path}")
    return path


def write_once(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2) + "\n")


def environment(root: Path) -> dict[str, str]:
    """Git and hosting configuration belongs only to this disposable world."""
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("GIT_", "GH_", "GITHUB_"))
    }
    env.update(
        HOME=str(root / "home"),
        XDG_CONFIG_HOME=str(root / "home/config"),
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_TERMINAL_PROMPT="0",
        GIT_CONFIG_COUNT="1",
        GIT_CONFIG_KEY_0="core.hooksPath",
        GIT_CONFIG_VALUE_0=str(root / "hooks"),
        PYTHONDONTWRITEBYTECODE="1",
        AQUARIUM_RELEASE_FIXTURE_ROOT=str(root),
        AQUARIUM_RELEASE_FIXTURE_DRIVER=str(Path(__file__).resolve()),
        PATH=str(root / "bin") + os.pathsep + os.environ.get("PATH", ""),
    )
    return env


def git(root: Path, *arguments: str, bare: bool = False) -> str:
    repo = root / ("origin.git" if bare else "repo")
    result = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        env=environment(root),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise FixtureError(result.stderr.strip())
    return result.stdout.strip()


def load(root: Path) -> dict:
    regular(root / "world.json", root)
    document = json.loads((root / "world.json").read_text())
    if document["root"] != str(root):
        raise FixtureError("fixture root identity differs")
    if git(root, "remote", "get-url", "origin") != str(root / "origin.git"):
        raise FixtureError("fixture origin is not its owned local bare remote")
    return document


def native_environment(root: Path) -> dict[str, str]:
    world = load(root)
    env = environment(root)
    resolved = shutil.which("gh", path=env["PATH"])
    expected = root / "bin/gh"
    if (
        resolved != str(expected)
        or regular(expected, root) != expected
        or not os.access(expected, os.X_OK)
        or digest(expected) != world["gh_sha256"]
        or digest(Path(__file__).resolve()) != world["driver_sha256"]
    ):
        raise FixtureError("fixture hosting executable identity differs; no invocation")
    return env


def seed(
    root: Path, *, order: str, baseline: str, mode: str, source_root: Path | None = None
) -> dict:
    if root != root.resolve() or root.exists():
        raise FixtureError("preserve existing or nonphysical fixture destination")
    root.mkdir(mode=0o700)
    for name in ("repo", "origin.git", "home", "bin", "hooks", "hosting"):
        (root / name).mkdir()
    template = (
        source_root or Path(__file__).resolve().parents[3]
    ) / "tests/vm/fixtures/release-orchestration"
    source = template.parent / "greeting/greet.py"
    for name in (
        "AGENTS.md",
        "Makefile",
        "TESTING.md",
        "CHANGELOG.md",
        "manifest.json",
    ):
        text = (template / name).read_text()
        text = text.replace("@GATE_ORDER@", order).replace("@MODE@", mode)
        if name == "CHANGELOG.md" and baseline == "first":
            text = text.split("## v1.0.0", 1)[0]
        (root / "repo" / name).write_text(text)
    shutil.copyfile(source, root / "repo/greet.py")
    git(root, "init", "-b", "main")
    git(root, "config", "user.name", "Release Fixture")
    git(root, "config", "user.email", "fixture@example.invalid")
    git(root, "init", "--bare", bare=True)
    git(root, "remote", "add", "origin", str(root / "origin.git"))
    git(root, "add", ".")
    git(root, "commit", "-m", "[TEST] Establish local release baseline")
    if baseline == "previous":
        git(root, "tag", "-a", "v1.0.0", "-m", "Fixture baseline")
    git(root, "push", "-u", "origin", "main")
    if baseline == "previous":
        git(root, "push", "origin", "v1.0.0")
    product = root / "repo/greet.py"
    text = (
        product.read_text()
        .replace(
            "args = parser.parse_args()",
            'parser.add_argument("--uppercase", action="store_true")\n    args = parser.parse_args()',
        )
        .replace(
            "print(greeting(args.name))",
            "print(greeting(args.name).upper() if args.uppercase else greeting(args.name))",
        )
    )
    product.write_text(text)
    git(root, "commit", "-am", "[FEAT] Add uppercase greetings")
    executable = root / "bin/gh"
    executable.write_text(
        "#!/bin/sh\nexec "
        + shlex.quote(sys.executable)
        + " -B "
        + shlex.quote(str(Path(__file__).resolve()))
        + " hosting --root "
        + shlex.quote(str(root))
        + ' -- "$@"\n'
    )
    executable.chmod(0o700)
    world = {
        "root": str(root),
        "order": order,
        "baseline": baseline,
        "mode": mode,
        "version": "v1.0.1",
        "gh_sha256": digest(executable),
        "driver_sha256": digest(Path(__file__).resolve()),
        "candidate": git(root, "rev-parse", "HEAD"),
    }
    write_once(root / "world.json", world)
    if baseline == "previous":
        hosting(
            root,
            [
                "release",
                "create",
                "v1.0.0",
                "--target",
                git(root, "rev-parse", "v1.0.0^{commit}"),
                "--notes",
                "Fixture baseline",
            ],
        )
    return world


def gate(root: Path, stage: str) -> dict:
    world = load(root)
    repo = root / "repo"
    if world["order"] == "after" and git(root, "status", "--porcelain"):
        raise FixtureError("commit-before-gate requires the exact clean commit")
    manifest = json.loads((repo / "manifest.json").read_text())
    if (
        os.environ.get("RELEASE_TAG") != world["version"]
        or "v" + manifest["version"] != world["version"]
    ):
        raise FixtureError("release tag/metadata mismatch")
    if os.environ.get("AQUARIUM_FIXTURE_FAIL_STAGE") == stage:
        raise FixtureError(f"disclosed fixture failure: {stage}")
    checks = {
        "prepare": [],
        "metadata": [],
        "unit": [([], "Hello, world!\n")],
        "int": [(["Ada"], "Hello, Ada!\n")],
        "e2e": [(["--uppercase", "Ada"], "HELLO, ADA!\n")],
    }
    if stage not in checks:
        raise FixtureError("unknown public fixture checkpoint")
    before = git(root, "status", "--porcelain")
    for arguments, expected in checks[stage]:
        result = subprocess.run(
            [sys.executable, "-B", str(repo / "greet.py"), *arguments],
            env=environment(root),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode or result.stdout != expected:
            raise FixtureError(
                f"fixture behavior failed: {arguments}: {result.stdout!r}"
            )
    if git(root, "status", "--porcelain") != before:
        raise FixtureError("gate changed tracked fixture state")
    return {
        "stage": stage,
        "head": git(root, "rev-parse", "HEAD"),
        "tree": git(root, "rev-parse", "HEAD^{tree}"),
        "status": before,
    }


def option(arguments: list[str], flag: str, default: str | None = None) -> str | None:
    return arguments[arguments.index(flag) + 1] if flag in arguments else default


def hosting(root: Path, arguments: list[str]) -> object:
    load(root)
    if option(arguments, "--repo", "fixture/release") != "fixture/release":
        raise FixtureError("unknown fixture hosting repository")
    if arguments[:2] == ["repo", "view"]:
        return {"nameWithOwner": "fixture/release"}
    if arguments[:2] == ["release", "list"]:
        return [
            json.loads(path.read_text())
            for path in sorted((root / "hosting").glob("release-*.json"))
        ]
    if len(arguments) < 3 or arguments[:2] not in (
        ["release", "view"],
        ["release", "create"],
    ):
        raise FixtureError(
            "unsupported fixture hosting command; no production fallback"
        )
    tag = arguments[2]
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise FixtureError("unsupported fixture tag")
    path = root / "hosting" / f"release-{tag}.json"
    if arguments[1] == "view":
        if not path.is_file():
            raise FixtureError("fixture release absent")
        return json.loads(path.read_text())
    target = option(arguments, "--target")
    if target is None:
        raise FixtureError("exact fixture target is required")
    target = git(root, "rev-parse", target + "^{commit}")
    if git(root, "rev-parse", f"refs/tags/{tag}^{{commit}}", bare=True) != target:
        raise FixtureError("remote annotated target must exist before hosted release")
    if git(root, "cat-file", "-t", f"refs/tags/{tag}", bare=True) != "tag":
        raise FixtureError("fixture publication tag is not annotated")
    body = option(arguments, "--notes", "")
    notes_file = option(arguments, "--notes-file")
    if notes_file:
        body = regular(Path(os.path.abspath(notes_file)), root).read_text()
    document = {
        "tagName": tag,
        "targetCommitish": target,
        "body": body,
        "name": option(arguments, "--title", tag),
        "isDraft": "--draft" in arguments,
        "isPrerelease": "--prerelease" in arguments,
    }
    write_once(path, document)
    with (root / "hosting/effects.jsonl").open("a") as stream:
        stream.write(
            json.dumps({"action": "create", "tag": tag, "target": target}) + "\n"
        )
    if os.environ.get("AQUARIUM_FIXTURE_LOST_REPLY") == "1":
        raise FixtureError(
            "disclosed reply loss after fixture mutation; read back before replay"
        )
    return document


def observe(root: Path) -> dict:
    load(root)
    return {
        "local_main": git(root, "rev-parse", "main"),
        "remote_main": git(root, "rev-parse", "main", bare=True),
        "remote_tags": git(root, "show-ref", "--tags", bare=True)
        if git(root, "tag", bare=True)
        else "",
        "hosting": hosting(root, ["release", "list"]),
        "status": git(root, "status", "--porcelain"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("seed", "gate", "hosting", "observe"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--order", choices=("before", "after"), default="before")
    parser.add_argument("--baseline", choices=("previous", "first"), default="previous")
    parser.add_argument("--mode", choices=("full", "light"), default="full")
    parser.add_argument("--stage", default="prepare")
    args, remaining = parser.parse_known_args(argv)
    try:
        if remaining and args.operation != "hosting":
            raise FixtureError("unexpected fixture arguments")
        if args.operation == "seed":
            value = seed(
                args.root, order=args.order, baseline=args.baseline, mode=args.mode
            )
        elif args.operation == "gate":
            value = gate(args.root, args.stage)
        elif args.operation == "hosting":
            value = hosting(
                args.root, remaining[1:] if remaining[:1] == ["--"] else remaining
            )
        else:
            value = observe(args.root)
        print(json.dumps(value))
        return 0
    except (FixtureError, OSError, ValueError, KeyError, IndexError) as error:
        print(json.dumps({"error": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
