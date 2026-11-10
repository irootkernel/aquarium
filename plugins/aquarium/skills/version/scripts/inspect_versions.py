#!/usr/bin/env python3
"""Report local versions and official GitHub release metadata without setup."""

from __future__ import annotations

import argparse
import http.client
import importlib.util
import json
import re
import shutil
import socket
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
# Reuse the bootstrap inspector's version syntax without running setup probes.
spec = importlib.util.spec_from_file_location(
    "aquarium_version_parsers",
    PLUGIN_ROOT / "skills/dev-setup/scripts/inspect_tools.py",
)
parsers = importlib.util.module_from_spec(spec)
previous_bytecode = sys.dont_write_bytecode
sys.dont_write_bytecode = True
try:
    spec.loader.exec_module(parsers)
finally:
    sys.dont_write_bytecode = previous_bytecode
SEMVER = parsers.CANONICAL_SEMVER
# Sources follow references/tool-catalog.md; no supported-version policy is copied here.
REPOSITORIES = {
    "aquarium": "irootkernel/aquarium",
    **{
        name: f"irootkernel/{name}"
        for name in (
            "sanho",
            "dolgorae",
            "mulgae",
            "gaori",
            "sorage",
            "podway",
            "haepari",
        )
    },
    "herdr": "herdrdev/herdr",
    "ouroboros": "Q00/ouroboros",
    "lora": "tmdgusya/lora",
    "deslop": "cursor/plugins",
    "humanizer": "blader/humanizer",
    "im-not-ai": "epoko77-ai/im-not-ai",
}
SKILLS = {
    "lora": ("lore-commits", "lore-query"),
    "deslop": ("deslop",),
    "humanizer": ("humanizer",),
    "im-not-ai": ("humanize-korean",),
}


def valid_version(value):
    if not isinstance(value, str):
        return None
    version, separator, build = value.partition("+")
    if separator and not re.fullmatch(r"[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*", build):
        return None
    return value if SEMVER.fullmatch(version) else None


def ouroboros_version(output):
    core = parsers.ouroboros_version_from_output(output)
    if core is None:
        return None
    # The setup parser returns a core version; retain the inventory's full identity.
    plain = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", output)
    match = re.search(
        rf"\bOuroboros\b.*?\bversion\s+v?({re.escape(core)}[^\s]*)",
        plain,
        re.IGNORECASE | re.DOTALL,
    )
    return valid_version(match.group(1)) if match else None


def local_plugin(root):
    path = root / ".codex-plugin/plugin.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        value = (
            valid_version(manifest.get("version"))
            if manifest.get("name") == "aquarium"
            else None
        )
        return {
            "status": "observed" if value else "invalid_metadata",
            "version": value,
            "path": str(path),
        }
    except (OSError, ValueError, AttributeError):
        return {"status": "unavailable", "version": None, "path": str(path)}


def local_cli(name):
    executable = shutil.which("ooo" if name == "ouroboros" else name)
    if executable is None:
        return {"status": "not_installed", "version": None, "path": None}
    executable = str(Path(executable).absolute())
    args = ["--version"] if name in {"herdr", "ouroboros"} else ["version", "--json"]
    if name == "podway":
        args = ["--contract-generation", "2", *args]
    result = {"version": None, "path": executable}
    try:
        probe = subprocess.run(
            [executable, *args],
            cwd="/",
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if probe.returncode:
            return {
                **result,
                "status": "command_failed",
                "reason": "nonzero_exit",
                "exit_code": probe.returncode,
            }
        if name == "ouroboros":
            value = ouroboros_version(probe.stdout + "\n" + probe.stderr)
        elif name == "herdr":
            plain = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", probe.stdout)
            match = re.fullmatch(
                rf"\s*{name}(?:\s+version)?\s+(v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)\s*",
                plain,
                re.IGNORECASE,
            )
            value = valid_version(match.group(1)) if match else None
        else:
            payload = json.loads(probe.stdout)
            if name == "haepari":
                payload = (
                    payload.get("data", {})
                    if payload.get("ok") is True
                    and payload.get("schema") == "haepari.envelope/v1"
                    and payload.get("operation") == "version"
                    else {}
                )
            value = parsers.version_from_probe({"result": payload})
            if name != "haepari" and payload.get("name", name) != name:
                value = None
        return {
            **result,
            "status": "observed" if value else "invalid_response",
            "version": value,
            **({} if value else {"reason": "invalid_version_response"}),
        }
    except subprocess.TimeoutExpired:
        return {**result, "status": "timeout", "reason": "timeout"}
    except (OSError, UnicodeError):
        return {**result, "status": "command_failed", "reason": "execution_failed"}
    except (ValueError, AttributeError, TypeError, RecursionError):
        return {
            **result,
            "status": "invalid_response",
            "reason": "invalid_version_response",
        }


def skill_metadata(path):
    """Accept only explicit scalar version fields in the frontmatter."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    front = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.DOTALL)
    if not front:
        return None
    # Read top-level version and metadata.version without needing a YAML runtime.
    values = []
    in_metadata = False
    for line in front.group(1).splitlines():
        if line and not line[0].isspace():
            in_metadata = line == "metadata:"
        match = re.fullmatch(
            r"( *)version: *['\"]?(v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?)['\"]? *",
            line,
        )
        if match and (not match.group(1) or (in_metadata and len(match.group(1)) == 2)):
            values.append(match.group(2))
    return valid_version(values[0]) if len(values) == 1 else None


def local_skills(name):
    roots = parsers.humanizer_skill_roots()
    installations = []
    for skill in SKILLS[name]:
        for root in roots:
            path = root / skill / "SKILL.md"
            if path.is_file():
                installations.append(
                    {"skill": skill, "path": str(path), "version": skill_metadata(path)}
                )
    if not installations:
        return {"status": "not_installed", "version": None, "installations": []}
    complete = all(
        sum(row["skill"] == skill for row in installations) == 1
        for skill in SKILLS[name]
    )
    versions = {row["version"] for row in installations}
    value = next(iter(versions)) if complete and len(versions) == 1 else None
    return {
        "status": "observed" if value else "version_unverifiable",
        "version": value,
        "installations": installations,
    }


def github_json(repository, suffix):
    url = f"https://api.github.com/repos/{repository}/{suffix}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "aquarium-version",
        },
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        raw = response.read(2_000_001)
    if len(raw) > 2_000_000:
        raise ValueError("response_too_large")
    return json.loads(raw)


def commit_reference(repository):
    payload = github_json(repository, "commits/main")
    sha = payload.get("sha")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("invalid_commit")
    return {
        "status": "observed",
        "version": None,
        "reference": sha,
        "kind": "commit",
        "url": f"https://github.com/{repository}/commit/{sha}",
    }


def latest(name):
    repository = REPOSITORIES[name]
    try:
        if name == "deslop":
            return commit_reference(repository)
        if name == "lora":
            # Lora's distribution uses stable tags, then the disclosed main ref.
            tags = []
            page = 1
            while True:
                batch = github_json(repository, f"tags?per_page=100&page={page}")
                if not isinstance(batch, list):
                    raise TypeError("invalid_tags")
                tags.extend(
                    row["name"]
                    for row in batch
                    if isinstance(row, dict) and canonical_stable(row.get("name"))
                )
                if len(batch) < 100:
                    break
                page += 1
            if not tags:
                return commit_reference(repository)
            tag = max(
                tags,
                key=lambda value: tuple(map(int, value.removeprefix("v").split("."))),
            )
            return {
                "status": "observed",
                "version": tag,
                "kind": "tag",
                "url": f"https://github.com/{repository}/tree/{tag}",
            }
        payload = github_json(repository, "releases/latest")
        value = valid_version(payload.get("tag_name"))
        if (
            not value
            or payload.get("draft") is not False
            or payload.get("prerelease") is not False
        ):
            raise ValueError("invalid_stable_release")
        tag = payload["tag_name"]
        return {
            "status": "observed",
            "version": value,
            "kind": "release",
            "url": f"https://github.com/{repository}/releases/tag/{tag}",
        }
    except urllib.error.HTTPError as error:
        if error.code == 404 and name not in {"lora", "deslop"}:
            try:
                return release_absence(repository)
            except (
                OSError,
                ValueError,
                TypeError,
                AttributeError,
                RecursionError,
                http.client.HTTPException,
            ) as fallback_error:
                return lookup_failure(fallback_error)
        return lookup_failure(error)
    except (
        OSError,
        ValueError,
        TypeError,
        AttributeError,
        RecursionError,
        http.client.HTTPException,
    ) as error:
        return lookup_failure(error)


def canonical_stable(value):
    return bool(valid_version(value) and re.fullmatch(r"v?\d+\.\d+\.\d+", value))


def release_absence(repository):
    """A latest-404 alone does not prove an accessible repo has no stable release."""
    page = 1
    while True:
        batch = github_json(repository, f"releases?per_page=100&page={page}")
        if not isinstance(batch, list) or any(
            not isinstance(row, dict)
            or type(row.get("draft")) is not bool
            or type(row.get("prerelease")) is not bool
            for row in batch
        ):
            raise ValueError("invalid_release_list")
        if any(not row["draft"] and not row["prerelease"] for row in batch):
            return {
                "status": "lookup_failed",
                "version": None,
                "reason": "latest_release_unavailable",
                "http_status": 404,
            }
        if len(batch) < 100:
            return {
                "status": "no_release",
                "version": None,
                "reason": "no_stable_release",
            }
        page += 1


def lookup_failure(error):
    result = {"status": "lookup_failed", "version": None}
    if isinstance(error, urllib.error.HTTPError):
        result["http_status"] = error.code
        reason = (
            "rate_limited"
            if error.code == 429
            or (
                error.code == 403
                and (error.headers or {}).get("X-RateLimit-Remaining") == "0"
            )
            else "http_error"
        )
    else:
        cause = error.reason if isinstance(error, urllib.error.URLError) else error
        if isinstance(cause, TimeoutError):
            reason = "timeout"
        elif isinstance(cause, ssl.SSLError):
            reason = "tls_error"
        elif isinstance(cause, socket.gaierror):
            reason = "dns_error"
        elif isinstance(cause, (json.JSONDecodeError, RecursionError)):
            reason = "invalid_json"
        elif isinstance(cause, http.client.HTTPException):
            reason = "http_protocol_error"
        elif isinstance(cause, ValueError) and str(cause) in {
            "response_too_large",
            "invalid_commit",
            "invalid_stable_release",
            "invalid_release_list",
        }:
            reason = str(cause)
        elif isinstance(cause, (ValueError, TypeError, AttributeError)):
            reason = "invalid_metadata"
        else:
            reason = "network_error"
    return {**result, "reason": reason}


def comparison(local, remote):
    if local["status"] == "not_installed":
        return "not_installed"
    left, right = local.get("version"), remote.get("version")
    if not left or not right:
        return "unverifiable"
    left, right = left.removeprefix("v"), right.removeprefix("v")
    if left == right:
        return "current"
    if not re.fullmatch(r"\d+\.\d+\.\d+", left) or not re.fullmatch(
        r"\d+\.\d+\.\d+", right
    ):
        return "unverifiable"
    return (
        "update_available"
        if tuple(map(int, left.split("."))) < tuple(map(int, right.split(".")))
        else "local_newer"
    )


def report(offline=False):
    rows = []
    for name, repository in REPOSITORIES.items():
        try:
            local = (
                local_plugin(PLUGIN_ROOT)
                if name == "aquarium"
                else local_skills(name)
                if name in SKILLS
                else local_cli(name)
            )
        except (OSError, RuntimeError) as error:
            local = {
                "status": "inspection_failed",
                "version": None,
                "reason": "local_inspection_failed",
                "error_type": type(error).__name__,
            }
        remote = (
            {"status": "not_requested", "version": None} if offline else latest(name)
        )
        rows.append(
            {
                "name": name,
                "repository": f"https://github.com/{repository}",
                "local": local,
                "latest": remote,
                "comparison": comparison(local, remote),
            }
        )
    return {
        "schema": "aquarium-version-report/v1",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "components": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Report local versions without network access",
    )
    args = parser.parse_args()
    print(json.dumps(report(args.offline), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
