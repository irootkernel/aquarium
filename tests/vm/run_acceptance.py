"""Execute manually authorized, guest-only upgrade and startup acceptance."""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import argparse
import base64
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path

REQUEST_SCHEMA = "aquarium.vm-acceptance-request/v1"
PROCEDURES = tuple(
    f"aquarium-{name}-v2.yaml"
    for name in ("task", "goal", "validation", "design", "war-room")
)
CASE_IDS = {"task": "VM-TASK-START-01", "epic": "VM-EPIC-START-01"}
FIXTURES = ("task", "epic", "preservation")
CRITERIA = {
    "uppercase-default": "--uppercase prints HELLO, WORLD! followed by one newline.",
    "uppercase-name": "--uppercase Ada prints HELLO, ADA! followed by one newline.",
    "existing-behavior": "Default and named greetings retain their original bytes.",
}


class GateError(RuntimeError):
    def __init__(self, message, outcome="incomplete"):
        super().__init__(message)
        self.outcome = outcome


def require(condition, message, outcome="incomplete"):
    if not condition:
        raise GateError(message, outcome)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def write_once_json(path, value):
    encoded = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(path.read_text() == encoded, "immutable observation changed", "fail")
    else:
        with path.open("x") as stream:
            stream.write(encoded)


def command(argv, cwd=None, *, check=True):
    result = subprocess.run(
        [str(part) for part in argv],
        cwd=cwd,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        capture_output=True,
        text=True,
        check=False,
    )
    if check:
        require(result.returncode == 0, f"command failed: {argv}: {result.stderr}")
    return result


def sha256(path):
    return "sha256:" + hashlib.sha256(Path(path).read_bytes()).hexdigest()


def matches_sha256(path, digest):
    expected = sha256(path)
    return digest in (expected, expected.removeprefix("sha256:"))


def files(root):
    root = Path(root)
    require(
        root.is_dir() and not root.is_symlink(), f"unsafe or missing directory: {root}"
    )
    result = {}
    for path in sorted(root.rglob("*")):
        require(not path.is_symlink(), f"symlink in payload: {path}")
        if path.is_dir():
            continue
        require(path.is_file(), f"nonregular payload: {path}")
        result[path.relative_to(root).as_posix()] = sha256(path)
    return result


def plugin_files(root):
    payload = files(root)
    for relative in list(payload):
        path = Path(root) / relative
        if path.parent.name != "__pycache__" or path.suffix != ".pyc":
            continue
        try:
            source = Path(importlib.util.source_from_cache(str(path)))
        except ValueError:
            continue
        if source.is_file() and source.suffix == ".py":
            del payload[relative]
    return payload


def artifact_digest(root):
    digest = hashlib.sha256()
    for name, value in sorted(files(root).items()):
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(bytes.fromhex(value.removeprefix("sha256:")) + b"\n")
    return "sha256:" + digest.hexdigest()


def guest_guard(expected_uuid):
    require(
        platform.system() == "Darwin", "a dedicated macOS guest is required", "fail"
    )
    flag = command(["/usr/sbin/sysctl", "-n", "kern.hv_vmm_present"], check=False)
    require(flag.returncode == 0, "native hypervisor identity is unavailable")
    require(flag.stdout.strip() == "1", "physical-host execution is rejected", "fail")
    require(
        isinstance(expected_uuid, str) and expected_uuid.strip(),
        "expected guest UUID is required",
    )
    identity = command(["/usr/sbin/ioreg", "-rd1", "-c", "IOPlatformExpertDevice"])
    match = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', identity.stdout)
    require(match is not None, "guest hardware UUID is unavailable")
    require(
        match[1].casefold() == expected_uuid.casefold(),
        "dedicated guest identity mismatch",
        "fail",
    )
    return {"platform": "Darwin", "hypervisor_present": 1, "hardware_uuid": match[1]}


def load_request(path):
    request = read_json(path)
    require(
        request.get("schema") == REQUEST_SCHEMA,
        f"request schema must be {REQUEST_SCHEMA}",
    )
    require(
        request.get("suite", "release") in {"release", "adaptive-development"},
        "unknown VM suite",
    )
    # This guard precedes directory creation, local imports and native dispatch.
    identity = guest_guard(request.get("expected_guest_uuid"))
    authority = request.get("authority", {})
    require(
        authority.get("kind") in {"explicit-vm-test", "release-handler"},
        "VM execution authority is missing",
    )
    require(
        authority.get("reference") and authority.get("observer"),
        "authority reference and observer are required",
    )
    root = Path(request["run_root"])
    require(
        root.is_absolute() and not root.is_symlink(),
        "run_root must be an absolute regular directory",
    )
    for parent in root.parents:
        require(not parent.is_symlink(), "run_root has a symlink ancestor")
    require(
        not root.is_relative_to(Path(__file__).resolve().parents[2]),
        "keep run outputs outside the candidate source checkout",
    )
    for name in ("codex", "podway", "python"):
        executable = Path(request["tools"][name])
        require(
            executable.is_absolute()
            and executable.is_file()
            and os.access(executable, os.X_OK),
            f"missing {name} executable",
        )
    return request, root, identity


def versions(request, plugin):
    observed = {
        "aquarium": read_json(Path(plugin) / ".codex-plugin/plugin.json")["version"]
    }
    for name, executable in request["tools"].items():
        if name == "python":
            continue
        argv = (
            [executable, "--json", "version", "--identity"]
            if name == "podway"
            else [executable, "--version"]
        )
        output = command(argv).stdout.strip()
        if name == "podway":
            envelope = json.loads(output)
            require(
                envelope.get("schema") == "podway.output/v4"
                and envelope["result"].get("schema") == "podway.version-result/v2",
                "Podway version identity is unavailable",
            )
            observed[name] = envelope["result"]["version"]
        else:
            prefix = "codex-cli " if name == "codex" else name + " "
            require(
                output.startswith(prefix), f"unsupported native version output: {name}"
            )
            observed[name] = output.removeprefix(prefix)
    return observed


def installed_plugin(request, marketplace, plugin):
    marketplace = Path(marketplace).resolve()
    catalog = read_json(marketplace / ".agents/plugins/marketplace.json")
    native = json.loads(
        command(
            [
                request["tools"]["codex"],
                "plugin",
                "list",
                "--marketplace",
                catalog["name"],
                "--json",
            ]
        ).stdout
    )
    matches = [
        row
        for row in native["installed"]
        if row.get("name") == "aquarium"
        and row.get("marketplaceName") == catalog["name"]
    ]
    require(len(matches) == 1, "native installed Aquarium identity is unavailable")
    row = matches[0]
    expected = read_json(Path(plugin) / ".codex-plugin/plugin.json")["version"]
    require(
        row.get("installed") is True
        and row.get("enabled") is True
        and row.get("version") == expected,
        "native Aquarium installation is disabled or has another version",
        "fail",
    )
    source = row.get("source", {})
    require(
        source.get("source") == "local"
        and Path(source.get("path", "")).resolve() == marketplace / "plugins/aquarium",
        "native Aquarium source differs from the selected marketplace",
        "fail",
    )
    origin = row.get("marketplaceSource", {})
    require(
        origin.get("sourceType") and origin.get("source"),
        "native marketplace origin is unavailable",
    )
    if origin["sourceType"] == "local":
        require(
            Path(origin["source"]).resolve() == marketplace,
            "native local marketplace registration differs from selected source",
            "fail",
        )
    require(
        files(marketplace / "plugins/aquarium") == plugin_files(plugin),
        "native registered source and installed cache bytes differ",
        "fail",
    )
    return row


def discover(
    request, fixture, plugin, *, skills=("dev-setup", "task-handler", "epic-handler")
):
    from native_observation import ObservationError
    from native_observation import discover as native_discover

    try:
        result = native_discover(request["tools"]["codex"], fixture)
    except ObservationError as error:
        raise GateError(str(error)) from error
    available = {
        skill["name"]: skill for row in result["data"] for skill in row["skills"]
    }
    for name in skills:
        skill = available.get(f"aquarium:{name}", {})
        require(skill.get("enabled") is True, f"installed skill unavailable: {name}")
        path = Path(skill["path"]).resolve()
        require(
            path.is_relative_to(Path(plugin).resolve()),
            f"stale or shadowed installed skill: {name}",
            "fail",
        )
    return result


def git(root, *arguments):
    return command(["git", "-C", root, *arguments]).stdout


def seed(request, root):
    template = Path(__file__).parent / "fixtures/greeting"
    for name in ("task", "epic"):
        target = root / name
        require(not target.exists(), f"fixture already exists; preserve it: {target}")
        shutil.copytree(template, target)
        git(target, "init", "-q")
        git(target, "config", "user.name", "VM Fixture")
        git(target, "config", "user.email", "vm-fixture@example.invalid")
        git(target, "add", ".")
        git(target, "commit", "-qm", "[TEST] Establish greeting fixture")
    return {
        "outcome": "prepared",
        "next": "Run released installed dev-setup for task, epic and preservation; then capture baseline.",
    }


def observe(request, repository, *, optional=False):
    output = command(
        [request["tools"]["podway"], "--worktree", repository, "--json", "observe"],
        check=False,
    )
    payload = json.loads(output.stdout)
    if optional and payload.get("code") == "SESSION_NOT_FOUND":
        return None
    require(
        output.returncode == 0 and payload.get("schema") == "podway.output/v4",
        "Podway observation unavailable",
    )
    result = payload["result"]
    require(
        result.get("schema") == "podway.observation-result/v5",
        "unsupported Podway observation",
    )
    return result


def snapshot(request, repository, plugin):
    tracked = git(repository, "ls-files", "-z").split("\0")
    untracked = git(
        repository, "ls-files", "--others", "--exclude-standard", "-z"
    ).split("\0")
    protected = {}
    custom = {}
    for name in set(tracked + untracked) - {""}:
        path = repository / name
        require(
            path.is_file() and not path.is_symlink(), f"unsafe baseline file: {path}"
        )
        if name.startswith(".podway/procedures/") and path.name in PROCEDURES:
            source = Path(plugin) / "assets/podway/procedures" / path.name
            if source.is_file() and sha256(source) != sha256(path):
                custom[name] = sha256(path)
        else:
            protected[name] = sha256(path)
    return {
        "git_head": git(repository, "rev-parse", "HEAD").strip(),
        "git_status": git(repository, "status", "--porcelain=v1"),
        "index": git(repository, "ls-files", "--stage"),
        "protected": protected,
        "custom": custom,
        "observation": observe(request, repository, optional=True),
    }


def baseline(request, root):
    require(
        not (root / "baseline.json").exists(),
        "baseline already captured; preserve its original observation",
    )
    plugin = Path(request["released_plugin_root"])
    observed = versions(request, plugin)
    require(
        observed == request["baseline_combination"],
        "guest released baseline differs from selected host combination",
    )
    require(
        "dev" not in observed["aquarium"], "baseline plugin must be a released version"
    )
    snapshots = {}
    setup = {}
    for name in ("task", "epic", "preservation"):
        repository = root / name
        require((repository / ".git").exists(), f"missing baseline repository: {name}")
        for procedure in PROCEDURES:
            path = repository / ".podway/procedures" / procedure
            require(
                path.is_file() and not path.is_symlink(),
                f"missing released managed source: {path}",
            )
            command(
                [
                    request["tools"]["podway"],
                    "--json",
                    "procedure",
                    "check",
                    "--warnings-as-errors",
                    path,
                ],
                cwd=repository,
            )
        snapshots[name] = snapshot(request, repository, plugin)
        setup[name] = verify_setup(
            request, root, name, request["baseline_setup"][name], plugin=plugin
        )
    preservation = snapshots["preservation"]
    require(
        preservation["custom"], "preservation fixture needs a customized managed source"
    )
    require(
        preservation["observation"] is not None,
        "preservation fixture needs a released admitted session",
    )
    require(
        preservation["git_status"].strip(),
        "preservation fixture needs meaningful existing Git work",
    )
    result = {
        "schema": "aquarium.vm-baseline/v1",
        "combination": observed,
        "installed_plugin": installed_plugin(
            request, request["released_marketplace_root"], plugin
        ),
        "released_plugin_files": plugin_files(plugin),
        "cache_projection": "shipped payload; source-associated Python bytecode excluded",
        "fixtures": snapshots,
        "discovery": discover(request, root / "task", plugin),
        "authority": request["authority"],
        "setup": setup,
    }
    write_json(root / "baseline.json", result)
    return {
        "outcome": "baseline-captured",
        "baseline_sha256": sha256(root / "baseline.json"),
        "next": "Install the exact candidate through the authorized native path; then run make test-vm.",
    }


def verify_candidate(candidate, driver_path=None):
    source = Path(candidate["source_root"])
    require(source.is_absolute(), "candidate source_root must be absolute")
    require(
        git(source, "rev-parse", "HEAD").strip() == candidate["git_sha"],
        "test checkout HEAD differs from candidate",
        "fail",
    )
    require(
        not git(source, "status", "--porcelain=v1").strip(),
        "candidate test checkout is not clean",
    )
    actual_driver = Path(driver_path or __file__).resolve()
    require(
        actual_driver == (source / "tests/vm/run_acceptance.py").resolve(),
        "run the committed candidate-matched guest driver",
        "fail",
    )
    artifact = Path(candidate["artifact_root"])
    manifest = read_json(candidate["artifact_manifest"])
    require(
        manifest.get("schema") == "aquarium-dev-artifact-manifest/v1"
        and manifest.get("git_sha") == candidate["git_sha"],
        "artifact manifest has the wrong candidate",
    )
    require(
        artifact_digest(artifact) == manifest.get("sha256"),
        "candidate artifact digest mismatch",
        "fail",
    )
    packaged = artifact / "plugins/aquarium"
    installed = Path(candidate["installed_plugin_root"])
    require(
        files(packaged) == plugin_files(installed),
        "installed candidate bytes differ from artifact",
        "fail",
    )
    package_manifest = read_json(packaged / ".codex-plugin/plugin.json")
    require(
        "v" + package_manifest["version"] == manifest["development_version"],
        "installed version differs from artifact manifest",
        "fail",
    )
    entries = git(
        source,
        "ls-tree",
        "-r",
        "--name-only",
        "HEAD",
        "--",
        ".agents/plugins/marketplace.json",
        "plugins/aquarium",
    ).splitlines()
    require(
        set(entries) == set(files(artifact)),
        "artifact inventory differs from committed plugin sources",
        "fail",
    )
    for name in entries:
        committed = subprocess.check_output(
            ["git", "-C", str(source), "show", f"HEAD:{name}"]
        )
        delivered = (artifact / name).read_bytes()
        if name == "plugins/aquarium/.codex-plugin/plugin.json":
            original = json.loads(committed)
            expected_version = f"{original['version']}-dev.{candidate['git_sha'][:12]}"
            require(
                package_manifest["version"] == expected_version,
                "development version does not bind the candidate",
                "fail",
            )
            original["version"] = expected_version
            require(
                original == package_manifest,
                "candidate plugin metadata changed beyond its development version",
                "fail",
            )
        else:
            require(
                committed == delivered,
                f"artifact differs from committed source: {name}",
                "fail",
            )
    return {
        "git_sha": candidate["git_sha"],
        "artifact_sha256": manifest["sha256"],
        "installed_plugin_root": str(installed),
    }


def protected_index(value, paths):
    return sorted(
        line for line in value.splitlines() if line.split("\t", 1)[-1] in paths
    )


def verify_preservation(request, root, original, installed):
    observed = {}
    for name, before in original["fixtures"].items():
        repository = root / name
        for relative, expected in {**before["protected"], **before["custom"]}.items():
            path = repository / relative
            require(
                path.is_file() and sha256(path) == expected,
                f"upgrade changed preserved bytes: {name}/{relative}",
                "fail",
            )
        protected_paths = set(before["protected"]) | set(before["custom"])
        require(
            git(repository, "rev-parse", "HEAD").strip() == before["git_head"],
            f"upgrade changed preserved Git HEAD: {name}",
            "fail",
        )
        require(
            protected_index(git(repository, "ls-files", "--stage"), protected_paths)
            == protected_index(before["index"], protected_paths),
            f"upgrade changed preserved Git staging: {name}",
            "fail",
        )
        for filename in PROCEDURES:
            relative = ".podway/procedures/" + filename
            if relative not in before["custom"]:
                expected = Path(installed) / "assets/podway/procedures" / filename
                require(
                    sha256(repository / relative) == sha256(expected),
                    f"managed update is incomplete: {name}/{filename}",
                )
        if before["observation"] is not None:
            after = observe(request, repository)
            old_status = before["observation"]["status"]
            for key in ("id", "revision", "lifecycle"):
                require(
                    after["status"]["session"].get(key)
                    == old_status["session"].get(key),
                    f"upgrade changed admitted session {key}",
                    "fail",
                )
            require(
                after["status"]["procedure"]["digest"]
                == old_status["procedure"]["digest"],
                "upgrade changed immutable Procedure snapshot",
                "fail",
            )
        observed[name] = snapshot(request, repository, installed)
    return observed


def oracle(python, repository, *, uppercase=True, repeat=False):
    examples = [([], "Hello, world!\n"), (["Ada"], "Hello, Ada!\n")]
    if uppercase:
        examples += [
            (["--uppercase"], "HELLO, WORLD!\n"),
            (["--uppercase", "Ada"], "HELLO, ADA!\n"),
        ]
    if repeat:
        examples += [
            (["--repeat", "3", "Ada"], "Hello, Ada!\n" * 3),
            (["--uppercase", "--repeat", "2", "Ada"], "HELLO, ADA!\n" * 2),
        ]
    outcomes = []
    for arguments, expected in examples:
        result = command(
            [python, "-B", repository / "greet.py", *arguments],
            cwd=repository,
            check=False,
        )
        outcomes.append(
            {
                "arguments": arguments,
                "exit": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        require(
            result.returncode == 0 and result.stdout == expected,
            f"greeting oracle failed: {arguments}: {result.stdout!r}",
            "fail",
        )
    if repeat:
        for value in ("0", "-1", "invalid"):
            result = command(
                [python, "-B", repository / "greet.py", "--repeat", value],
                cwd=repository,
                check=False,
            )
            require(
                result.returncode != 0,
                f"invalid repeat count was accepted: {value}",
                "fail",
            )
    return outcomes


def thread_id(log, *, missing_ok=False):
    for line in Path(log).read_text().splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("type") == "thread.started":
            return item["thread_id"]
    if missing_ok:
        return None
    raise GateError(f"native invocation has no public thread handle: {log}")


def save_setup_observation(root, name, phase, observation):
    encoded = json.dumps(observation, indent=2, ensure_ascii=False) + "\n"
    digest = hashlib.sha256(encoded.encode()).hexdigest()
    path = root / "setup-observations" / phase / name / f"{digest}.json"
    write_once_json(path, observation)
    return {"public_observation": str(path), "observation_sha256": "sha256:" + digest}


def verify_setup(request, root, name, handle, *, plugin, before=None, observation=None):
    from native_observation import ObservationError, collect

    identifier = thread_id(handle) if Path(handle).is_file() else handle
    if observation is None:
        try:
            observation = collect(request["tools"]["codex"], root / name, identifier)
        except ObservationError as error:
            raise GateError(str(error)) from error
    actual = observation["root"]
    require(
        Path(actual["metadata"]["cwd"]).resolve() == (root / name).resolve(),
        "setup used the wrong fixture",
        "fail",
    )
    inputs = [item for item in actual["items"] if item.get("type") == "userMessage"]
    require(
        "aquarium:dev-setup" in json.dumps(inputs),
        "setup has no actual installed dev-setup invocation",
    )
    require(
        actual["turns"]
        and actual["turns"][-1]["status"] == "completed"
        and not any(turn["status"] == "inProgress" for turn in actual["turns"]),
        "setup invocation has unfinished work",
    )
    require(final_text(actual).strip(), "setup returned no actual result")
    if before is not None:
        require(
            sha256(before["public_observation"]) == before["observation_sha256"],
            "original setup observation changed",
            "fail",
        )
    turns = [
        turn
        for turn in actual["turns"]
        if turn["status"] == "completed" and turn.get("error") is None
    ]
    if before is not None and before["thread_id"] == actual["metadata"]["id"]:
        turns = [
            turn for turn in turns if turn["id"] not in before["completed_turn_ids"]
        ]
    require(
        turns, "managed update has no new completed public operation after baseline"
    )
    items = [item for turn in turns for item in turn.get("items", [])]
    if before is not None and before["thread_id"] == actual["metadata"]["id"]:
        items = [item for item in items if item["id"] not in before["item_ids"]]
    if before is not None:
        current_inputs = [
            item
            for item in actual["items"]
            if item.get("type") == "userMessage"
            and (
                before["thread_id"] != actual["metadata"]["id"]
                or item["id"] not in before["item_ids"]
            )
        ]
        require(
            "aquarium:dev-setup" in json.dumps(current_inputs),
            "candidate setup lacks an actual current-phase installed dev-setup invocation",
        )
    commands = [
        item
        for item in items
        if item.get("type") == "commandExecution"
        and item.get("status") == "completed"
        and item.get("exitCode") == 0
    ]
    source = str(Path(plugin).resolve())
    require(
        any(source + "/" in str(item.get("command", "")) for item in commands),
        "setup lacks actual execution against the selected installed source",
    )
    phase = "update" if before is not None else "baseline"
    capture = save_setup_observation(root, name, phase, observation)
    return {
        "thread_id": actual["metadata"]["id"],
        "completed_turn_ids": [
            turn["id"] for turn in actual["turns"] if turn["status"] == "completed"
        ],
        "item_ids": [item["id"] for item in actual["items"]],
        "installed_source": source,
        "managed_sources": {
            filename: sha256(root / name / ".podway/procedures" / filename)
            for filename in PROCEDURES
        },
        **capture,
    }


def invoke(
    request, root, case, prompt, *, reply=None, resume_thread=None, repository=None
):
    directory = root / "operations" / case
    previous = sorted(directory.glob("*.invocation.json")) if directory.exists() else []
    logs = sorted(directory.glob("*.jsonl")) if directory.exists() else []
    require(
        len(logs) == len(previous),
        f"uncertain previous invocation; reconcile its existing public log before dispatch: {logs}",
    )
    if previous and reply is None:
        receipt = read_json(previous[-1])
        require(
            receipt.get("exit") == 0,
            f"previous native invocation failed; reconcile its existing handle: {receipt}",
        )
        return receipt["thread_id"]
    require(
        reply is None or previous,
        "cannot resume a case without an actual native handle",
    )
    require(not (resume_thread and previous), "initial resume already dispatched")
    directory.mkdir(parents=True, exist_ok=True)
    prefix = directory / f"{len(previous):03d}"
    repository = repository or root / (
        "epic"
        if "epic" in case
        else "preservation"
        if "preservation" in case
        else "task"
    )
    argv = [
        request["tools"]["codex"],
        "exec",
        "--json",
        *request.get("codex_args", []),
        "--add-dir",
        str(root / (case + "-capture"))
        if case.startswith("adaptive-")
        else str(root / case)
        if case.endswith("-startup")
        else str(root),
        "--output-last-message",
        str(prefix) + ".last",
    ]
    resumed = resume_thread
    if reply is not None:
        resumed = read_json(previous[-1])["thread_id"]
        require(
            resumed, "existing native handle is unavailable; reconcile without replay"
        )
    if resume_thread is not None:
        argv += ["resume", resume_thread, "-"]
    elif reply is None:
        argv += ["-C", str(repository), "-"]
    else:
        argv += ["resume", resumed, "-"]
    value = prompt if reply is None else reply
    Path(str(prefix) + ".input").write_text(value)
    with (
        Path(str(prefix) + ".jsonl").open("w") as stdout,
        Path(str(prefix) + ".stderr").open("w") as stderr,
    ):
        process = subprocess.run(
            argv,
            input=value,
            cwd=repository,
            stdout=stdout,
            stderr=stderr,
            text=True,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
    observed_id = thread_id(str(prefix) + ".jsonl", missing_ok=True)
    receipt = {
        "argv": argv,
        "exit": process.returncode,
        "input_sha256": sha256(str(prefix) + ".input"),
        "observer": request["authority"]["observer"],
        "thread_id": observed_id or resumed,
        "handle_source": "cli-event"
        if observed_id
        else "known-resume"
        if resumed
        else "unavailable",
    }
    write_json(Path(str(prefix) + ".invocation.json"), receipt)
    require(
        process.returncode == 0,
        f"native invocation failed; preserve and reconcile {receipt['thread_id']}",
    )
    require(
        receipt["thread_id"],
        "native invocation has no public handle; reconcile without replay",
    )
    return receipt["thread_id"]


def managed_image(repository):
    image = {}
    for filename in PROCEDURES:
        path = repository / ".podway/procedures" / filename
        require(
            path.is_file() and not path.is_symlink(), "managed target is unavailable"
        )
        content = path.read_bytes()
        image[filename] = {
            "sha256": "sha256:" + hashlib.sha256(content).hexdigest(),
            "bytes_base64": base64.b64encode(content).decode("ascii"),
        }
    return image


def image_hashes(image):
    hashes = {}
    require(set(image) == set(PROCEDURES), "managed image inventory differs")
    for filename, entry in image.items():
        content = base64.b64decode(entry["bytes_base64"], validate=True)
        digest = "sha256:" + hashlib.sha256(content).hexdigest()
        require(digest == entry["sha256"], "captured managed bytes changed", "fail")
        hashes[filename] = digest
    return hashes


def update_binding(request, root):
    candidate = request["candidate"]
    installed = Path(candidate["installed_plugin_root"])
    marketplace = candidate.get("marketplace_root", candidate["artifact_root"])
    native = installed_plugin(request, marketplace, installed)
    return {
        "candidate": verify_candidate(candidate),
        "baseline_sha256": sha256(root / "baseline.json"),
        "combination": versions(request, installed),
        "installed_plugin": native,
    }


def setup_after(directory, prefix):
    path = directory / (prefix + ".setup-after.json")
    after = read_json(path)
    reconciled = sorted(directory.glob(prefix + ".reconciled-*.json"))
    if reconciled:
        after = read_json(reconciled[-1])
        require(
            after["original_after_sha256"] == sha256(path),
            "original setup capture changed",
            "fail",
        )
    basis = after.get("setup") or after.get("settlement")
    if basis:
        require(
            sha256(basis["public_observation"]) == basis["observation_sha256"],
            "setup observation changed",
            "fail",
        )
    return after


def reconcile_setup(request, root, name, binding, original):
    from native_observation import ObservationError, collect

    directory = root / "operations" / (name + "-setup")
    receipts = sorted(directory.glob("*.invocation.json"))
    require(receipts, "setup has no owned invocation to reconcile")
    prefix = receipts[-1].name.removesuffix(".invocation.json")
    receipt = read_json(receipts[-1])
    before = read_json(directory / (prefix + ".setup-before.json"))
    original_after = directory / (prefix + ".setup-after.json")
    after = read_json(original_after)
    require(
        before["binding"] == after["binding"] == binding,
        "setup reconciliation has another candidate or baseline",
    )
    require(
        receipt.get("thread_id"),
        "setup has no existing public handle; do not replay unknown work",
    )
    require(
        image_hashes(managed_image(root / name))
        == image_hashes(after["managed_image"]),
        "managed targets changed after the captured operation",
    )
    try:
        observation = collect(
            request["tools"]["codex"], root / name, receipt["thread_id"]
        )
    except ObservationError as error:
        raise GateError(str(error)) from error
    actual = observation["root"]
    require(
        actual["metadata"]["id"] == receipt["thread_id"]
        and Path(actual["metadata"]["cwd"]).resolve() == (root / name).resolve(),
        "setup reconciliation used another native operation",
        "fail",
    )
    capture = save_setup_observation(root, name, "recovery", observation)
    verify_settlement(observation, allow_failed=True)
    prior = before.get("basis", original["setup"][name])
    prior_turns = read_json(prior["public_observation"])["root"]["turns"]
    new_turns = [
        turn
        for turn in actual["turns"]
        if actual["metadata"]["id"] != prior["thread_id"]
        or turn["id"] not in {item["id"] for item in prior_turns}
    ]
    require(
        new_turns
        or image_hashes(after["managed_image"])
        == image_hashes(before["managed_image"]),
        "managed bytes changed without an observed native turn",
    )
    settled = {
        "thread_id": actual["metadata"]["id"],
        "completed_turn_ids": [
            turn["id"] for turn in actual["turns"] if turn["status"] == "completed"
        ],
        "native_status": actual["turns"][-1]["status"] if new_turns else "no-new-turn",
        **capture,
    }
    recovered = {
        **after,
        "thread_id": receipt["thread_id"],
        "invocation_exit": receipt["exit"],
        "original_after_sha256": sha256(original_after),
        "settlement": settled,
    }
    recovered.pop("setup", None)
    if any(turn["status"] == "completed" for turn in new_turns):
        try:
            recovered["setup"] = verify_setup(
                request,
                root,
                name,
                receipt["thread_id"],
                plugin=request["candidate"]["installed_plugin_root"],
                before=original["setup"][name],
                observation=observation,
            )
        except GateError as error:
            recovered.pop("setup", None)
            recovered["reconciliation_problem"] = str(error)
    ordinal = len(list(directory.glob(prefix + ".reconciled-*.json")))
    write_once_json(directory / f"{prefix}.reconciled-{ordinal:03d}.json", recovered)
    return recovered


def verify_managed_update(request, root, name, binding, original):
    directory = root / "operations" / (name + "-setup")
    receipts = sorted(directory.glob("*.invocation.json"))
    require(receipts, "candidate setup needs a captured native operation window")
    require(
        len(list(directory.glob("*.setup-before.json")))
        == len(list(directory.glob("*.setup-after.json")))
        == len(receipts),
        "candidate setup has an uncertain operation; preserve and reconcile it without replay",
    )
    expected = original["setup"][name]["managed_sources"]
    basis = original["setup"][name]
    windows = []
    for receipt_path in receipts:
        prefix = receipt_path.name.removesuffix(".invocation.json")
        before_path = directory / (prefix + ".setup-before.json")
        after_path = directory / (prefix + ".setup-after.json")
        before = read_json(before_path)
        after = setup_after(directory, prefix)
        receipt = read_json(receipt_path)
        require(
            before["binding"] == after["binding"] == binding,
            "setup window has another candidate or baseline",
        )
        require(
            image_hashes(before["managed_image"]) == expected,
            "unexplained managed change before native setup",
        )
        require(
            receipt["thread_id"] == after["thread_id"],
            "native setup handle differs from captured operation",
        )
        require(
            receipt["input_sha256"] == sha256(directory / (prefix + ".input")),
            "setup input changed",
            "fail",
        )
        current = after.get("setup") or after.get("settlement")
        require(
            current,
            "setup public observation is incomplete; reconcile its existing handle",
        )
        require(
            sha256(current["public_observation"]) == current["observation_sha256"],
            "setup capture changed",
            "fail",
        )
        if after.get("setup"):
            require(
                current["thread_id"] != basis["thread_id"]
                or set(current["completed_turn_ids"])
                - set(basis["completed_turn_ids"]),
                "setup window has no new completed native operation",
            )
        else:
            require(after.get("settlement"), "failed setup operation is not settled")
        expected = image_hashes(after["managed_image"])
        basis = current
        windows.append(
            {
                "before": str(before_path),
                "after": str(after_path),
                "invocation_exit": receipt["exit"],
                "settlement": after.get("settlement"),
            }
        )
    require(
        receipt["exit"] == 0 and after.get("setup"),
        "final candidate setup needs a successful native operation and assessment",
    )
    installed = Path(request["candidate"]["installed_plugin_root"])
    custom = original["fixtures"][name]["custom"]
    target = {
        filename: custom.get(".podway/procedures/" + filename)
        or sha256(installed / "assets/podway/procedures" / filename)
        for filename in PROCEDURES
    }
    require(
        expected == target,
        f"candidate setup for {name} needs an actual operator decision or further work; resume {basis['thread_id']}",
    )
    require(
        image_hashes(managed_image(root / name)) == expected,
        "managed targets changed outside captured native setup",
    )
    current = verify_setup(
        request,
        root,
        name,
        basis["thread_id"],
        plugin=installed,
        before=original["setup"][name],
    )
    verify_settlement(read_json(current["public_observation"]))
    return {"thread_id": basis["thread_id"], "windows": windows, "setup": current}


def setup_update(request, root, name, *, reply=None, resume_thread=None):
    binding = update_binding(request, root)
    original = read_json(root / "baseline.json")
    directory = root / "operations" / (name + "-setup")
    receipts = sorted(directory.glob("*.invocation.json"))
    require(
        len(list(directory.glob("*.setup-before.json")))
        == len(list(directory.glob("*.setup-after.json")))
        == len(receipts),
        "uncertain setup window requires reconciliation before dispatch",
    )
    if receipts and reply is None:
        return {
            "outcome": "managed-update-observed",
            **verify_managed_update(request, root, name, binding, original),
        }
    require(reply is None or receipts, "setup reply has no owned native handle")
    require(
        resume_thread is None or resume_thread == original["setup"][name]["thread_id"],
        "initial setup resume must use its actual released baseline handle",
    )
    expected = original["setup"][name]["managed_sources"]
    if receipts:
        last = setup_after(
            directory, receipts[-1].name.removesuffix(".invocation.json")
        )
        if not (last.get("setup") or last.get("settlement")):
            last = reconcile_setup(request, root, name, binding, original)
        require(
            last["binding"] == binding
            and (last.get("setup") or last.get("settlement")),
            "previous setup window is unresolved",
        )
        expected = image_hashes(last["managed_image"])
    image = managed_image(root / name)
    require(
        image_hashes(image) == expected,
        "unexplained managed change before native setup",
    )
    discovery = discover(
        request, root / name, request["candidate"]["installed_plugin_root"]
    )
    prefix = directory / f"{len(receipts):03d}"
    basis = (
        (last.get("setup") or last["settlement"])
        if receipts
        else original["setup"][name]
    )
    write_once_json(
        Path(str(prefix) + ".setup-before.json"),
        {
            "binding": binding,
            "managed_image": image,
            "discovery": discovery,
            "basis": basis,
        },
    )
    prompt = f"""Invoke the normally discovered installed $aquarium:dev-setup for {root / name}, scoped only to Podway managed configuration and sources.
Use the current installed source and normal concrete proposal/approval boundary.
The authorized fixture operator is {request["authority"]["observer"]}; existing scope authority is {request["authority"]["reference"]}.
Preserve custom sources, original admitted sessions, Git work and reports. Ask
for any actual required decision; this request does not accept an unseen proposal.
Settle native agents and return the actual result. Do not commit or publish.
"""
    after = {"binding": binding}
    try:
        identifier = invoke(
            request,
            root,
            name + "-setup",
            prompt,
            reply=reply,
            resume_thread=resume_thread,
        )
        after["thread_id"] = identifier
        current = verify_setup(
            request,
            root,
            name,
            identifier,
            plugin=request["candidate"]["installed_plugin_root"],
            before=original["setup"][name],
        )
        require(
            current["thread_id"] != basis["thread_id"]
            or set(current["completed_turn_ids"]) - set(basis["completed_turn_ids"]),
            "setup window has no new completed native operation",
        )
        verify_settlement(read_json(current["public_observation"]))
        after["setup"] = current
    except Exception as error:
        after["problem"] = str(error)
        raise
    finally:
        receipt_path = Path(str(prefix) + ".invocation.json")
        if receipt_path.exists():
            receipt = read_json(receipt_path)
            after["thread_id"] = receipt["thread_id"]
            after["invocation_exit"] = receipt["exit"]
        after["managed_image"] = managed_image(root / name)
        write_once_json(Path(str(prefix) + ".setup-after.json"), after)
    return {
        "outcome": "managed-update-observed",
        **verify_managed_update(request, root, name, binding, original),
    }


def final_text(child):
    return "\n".join(
        item.get("text", "")
        for item in child["items"]
        if item.get("type") == "agentMessage" and item.get("phase") == "final_answer"
    )


def correlate_child(observation, handle):
    by_id = {child["metadata"]["id"]: child for child in observation["descendants"]}
    links = [
        item
        for item in observation["root"]["items"]
        if item.get("type") == "subAgentActivity"
    ]
    for child in observation["descendants"]:
        links.extend(
            item for item in child["items"] if item.get("type") == "subAgentActivity"
        )
    matching = {
        item["agentThreadId"]
        for item in links
        if handle in (item["agentThreadId"], item["agentPath"])
    }
    require(
        len(matching) == 1,
        f"role handle lacks one actual public native child: {handle}",
    )
    identifier = matching.pop()
    require(identifier in by_id, f"child result is missing: {identifier}")
    child = by_id[identifier]
    parents = {observation["root"]["metadata"]["id"], *by_id}
    require(
        child["metadata"]["parentThreadId"] in parents,
        "native child parent mismatch",
        "fail",
    )
    require(
        any(
            item["agentThreadId"] == identifier and item["kind"] == "completed"
            for item in links
        ),
        f"native child completion is unavailable: {identifier}",
    )
    require(
        child["turns"]
        and child["turns"][-1]["status"] == "completed"
        and child["turns"][-1].get("error") is None,
        f"child turn is incomplete: {identifier}",
    )
    require(final_text(child).strip(), f"child returned no actual result: {identifier}")
    return child


def verify_settlement(observation, *, allow_failed=False):
    actors = [observation["root"], *observation["descendants"]]
    terminal = {"completed", "failed", "interrupted"} if allow_failed else {"completed"}
    require(
        all(
            actor["turns"] and actor["turns"][-1]["status"] in terminal
            for actor in actors
        ),
        "cleanup cannot establish latest native turn completion",
    )
    require(
        not any(
            turn["status"] == "inProgress"
            for actor in actors
            for turn in actor["turns"]
        ),
        "cleanup has an active native turn",
    )
    activities = [
        item
        for actor in actors
        for item in actor["items"]
        if item.get("type") == "subAgentActivity"
    ]
    started = {
        item["agentThreadId"] for item in activities if item["kind"] == "started"
    }
    completed = {
        item["agentThreadId"] for item in activities if item["kind"] == "completed"
    }
    require(started.issubset(completed), "cleanup has unsettled native descendants")


def returned_report(child, path, schema):
    document = read_json(path)
    require(document.get("schema") == schema, f"missing {schema} report")
    text = final_text(child)
    decoder = json.JSONDecoder()
    for position, character in enumerate(text):
        if character != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(text[position:])
        except json.JSONDecodeError:
            continue
        if candidate == document:
            return document
    require(
        str(path) in text and sha256(path) in text,
        f"actual child output does not bind report bytes: {path}",
    )
    return document


def case_artifact(repository, value):
    directory = repository.parent / (repository.name + "-startup")
    require(
        directory.is_dir() and not directory.is_symlink(),
        "case artifact directory is unavailable",
    )
    path = Path(value)
    require(
        path.is_absolute()
        and path.is_file()
        and not path.is_symlink()
        and path.resolve().is_relative_to(directory.resolve()),
        "startup artifact belongs outside its case directory",
    )
    return path


def validate_native_case(observation, evidence, repository):
    paths = {
        key: case_artifact(repository, evidence[key])
        for key in (
            "worker_assignment",
            "judge_assignment",
            "worker_result",
            "judge_assessment",
        )
    }
    worker = correlate_child(observation, evidence["worker_agent"])
    judge = correlate_child(observation, evidence["judge_agent"])
    require(
        worker["metadata"]["id"] != judge["metadata"]["id"],
        "Worker cannot assess itself as Judge",
        "fail",
    )
    for role in ("worker", "judge"):
        assignment = read_json(paths[role + "_assignment"])
        require(
            assignment.get("schema") == "aquarium.assignment/v2"
            and assignment.get("role") == role,
            f"missing original {role} assignment",
        )
        require(
            str(repository) in json.dumps(assignment["work"]),
            f"{role} assignment has the wrong repository",
            "fail",
        )
        require(
            all(key in json.dumps(assignment["success_criteria"]) for key in CRITERIA),
            f"{role} assignment omits original smoke criteria",
        )
    handoff = returned_report(
        worker, paths["worker_result"], "aquarium.worker-handoff/v2"
    )
    assessment = returned_report(
        judge, paths["judge_assessment"], "aquarium.judge-assessment/v2"
    )
    require(
        handoff.get("changed_artifacts") and handoff.get("results"),
        "Worker report lacks actual delivery/check results",
    )
    require(
        any(
            item.get("type") in {"commandExecution", "fileChange"}
            for item in worker["items"]
        ),
        "Worker has no actual execution or file-change observation",
    )
    for report in (handoff, assessment):
        require(
            matches_sha256(
                repository / "greet.py", report.get("target", {}).get("greet_sha256")
            ),
            "role report does not identify the current greeting source",
            "fail",
        )
    rows = {row["id"]: row for row in assessment.get("criteria", [])}
    require(set(CRITERIA).issubset(rows), "Judge omitted original due criteria")
    for identifier in CRITERIA:
        row = rows[identifier]
        require(
            row.get("source") and row.get("evidence"),
            f"Judge lacks original source/evidence for {identifier}",
        )
        state = row.get("state", row.get("assessment"))
        require(
            state == "met",
            f"Judge did not establish {identifier}: {state}",
            "fail" if state == "unmet" else "incomplete",
        )
    require(
        assessment.get("checkpoint_result") == "pass",
        "delivery assessment did not pass",
        "fail",
    )
    # Global future obligations may remain unverified during this partial smoke.
    return {
        "worker_thread": worker["metadata"]["id"],
        "judge_thread": judge["metadata"]["id"],
    }


def verify_startup_state(name, current):
    expected = {
        "task": ("aquarium-task-v2", "document"),
        "epic": ("aquarium-goal-v2", "record-evidence"),
    }
    procedure, node = expected[name]
    require(
        current["status"]["procedure"]["id"] == procedure,
        f"{name} startup entered the wrong Procedure",
        "fail",
    )
    actual = current["guidance"]["node"]["graph_node_id"]
    require(
        actual == node,
        f"{name} first delivery semantic progression is unverified at node {actual}",
    )


def smoke(request, root, name):
    from native_observation import ObservationError, collect

    repository = root / name
    case_root = root / (name + "-startup")
    require(not case_root.is_symlink(), "case artifact directory is a symlink")
    case_root.mkdir(parents=True, exist_ok=True)
    evidence_file = case_root / "startup-evidence.json"
    handler = (
        "task-handler for TASK-001" if name == "task" else "epic-handler for EPIC-001"
    )
    prompt = f"""Invoke the normally discovered installed $aquarium:{handler} in {repository}.
Use the original roadmap/dossier and normal approval boundaries. The authorized
fixture operator is {request["authority"]["observer"]}; scope authority is
{request["authority"]["reference"]}. Select native Codex three-agent Independent
Review. Ask for the ready plan/exact-result decisions when required; do not
infer approval or Master acceptance from this prompt.
This release smoke requests actual first-member uppercase delivery, refinement,
checks, independent Judge assessment and the first semantic progression. Stop
at a safe partial boundary after that delivery assessment; do not claim full
Task/Epic completion, execute the repeat member, commit or publish.
Explicitly select the released canonical {"aquarium-task-v2" if name == "task" else "aquarium-goal-v2"} source for this fixed regression; do not use adaptive generation here.
Original due smoke criterion IDs and meanings: {json.dumps(CRITERIA)}.
Preserve every applicable original criterion and future global gap in ordinary
v2 reports. Save original Worker/Judge assignments and actual JSON role reports
under {case_root}. Keep this case's evidence and every assignment/report inside
that directory; preserve other cases' files. Each role's actual final result must include its complete JSON
report or its report path and sha256 digest, for this test's result collection.
Write {evidence_file} with worker_agent and judge_agent (available native paths
or UUIDs), worker_assignment, judge_assignment, worker_result, judge_assessment
(absolute artifact paths). These files and assertions alone cannot prove work;
the test independently reads public native child results, artifacts and Podway.
Settle your native agents before returning and retain the unfinished workflow
truthfully. Missing telemetry, child user messages or formal accepted-task
digests are not ordinary startup requirements.
The Primary saves the returned reports; the Judge remains report-only. Include
the actual current greet.py SHA-256 as target.greet_sha256 in each delivery
report, so this test can compare the assessed bytes without native attestation.
"""
    identifier = invoke(request, root, name + "-startup", prompt)
    try:
        observation = collect(request["tools"]["codex"], repository, identifier)
    except ObservationError as error:
        raise GateError(str(error)) from error
    write_json(root / f"{name}-native-observation.json", observation)
    require(
        evidence_file.is_file(),
        f"{CASE_IDS[name]} needs operator reply or missing evidence; resume actual thread {identifier}",
    )
    actors = validate_native_case(
        observation, read_json(case_artifact(repository, evidence_file)), repository
    )
    outcomes = oracle(request["tools"]["python"], repository)
    source_before_checks = sha256(repository / "greet.py")
    checks = command(["make", "test"], cwd=repository, check=False)
    write_json(
        root / f"{name}-checks.json",
        {
            "exit": checks.returncode,
            "stdout": checks.stdout,
            "stderr": checks.stderr,
            "oracle": outcomes,
        },
    )
    require(checks.returncode == 0, f"{name} fixture Make gate failed", "fail")
    require(
        sha256(repository / "greet.py") == source_before_checks,
        "fixture formatting changed the assessed source; obtain fresh applicable assessment",
    )
    current = observe(request, repository)
    verify_startup_state(name, current)
    verify_settlement(observation)
    return {
        "id": CASE_IDS[name],
        "outcome": "pass",
        "actors": actors,
        "podway": current,
        "cleanup": "native invocation and reader ended; completed child work observed; partial fixture retained for inspection",
    }


def run_gate(request, root):
    candidate = request["candidate"]
    binding = verify_candidate(candidate)
    original = read_json(root / "baseline.json")
    require(
        original.get("schema") == "aquarium.vm-baseline/v1",
        "released baseline was not captured",
    )
    installed = Path(candidate["installed_plugin_root"])
    marketplace = Path(candidate.get("marketplace_root", candidate["artifact_root"]))
    require(
        files(marketplace) == files(candidate["artifact_root"]),
        "registered marketplace payload differs from the candidate artifact",
        "fail",
    )
    result = {
        "schema": "aquarium.vm-acceptance-result/v1",
        "candidate": binding,
        "baseline_sha256": sha256(root / "baseline.json"),
        "combination": versions(request, installed),
        "installed_plugin": installed_plugin(request, marketplace, installed),
        "cache_projection": "shipped payload; source-associated Python bytecode excluded",
        "authority": request["authority"],
        "cases": [],
    }
    update_identity = {
        key: result[key]
        for key in ("candidate", "baseline_sha256", "combination", "installed_plugin")
    }
    try:
        upgrade_path = root / "upgrade-observation.json"
        if upgrade_path.exists():
            upgrade = read_json(upgrade_path)
            require(
                upgrade["candidate"] == binding
                and upgrade["baseline_sha256"] == result["baseline_sha256"]
                and upgrade["combination"] == result["combination"],
                "upgrade evidence belongs to another candidate/baseline/combination",
            )
            require(
                set(upgrade["fixtures"]) == set(original["fixtures"]),
                "upgrade lacks original post-update preservation observations",
            )
            # Smoke changes Task/Epic intentionally; the preservation repo stays intact.
            verify_preservation(
                request,
                root,
                {"fixtures": {"preservation": original["fixtures"]["preservation"]}},
                installed,
            )
        else:
            preserved = verify_preservation(request, root, original, installed)
            upgrade = {
                "id": "VM-UPGRADE-01",
                "outcome": "pass",
                "candidate": binding,
                "baseline_sha256": result["baseline_sha256"],
                "combination": result["combination"],
                "fixtures": preserved,
                "setup": {
                    name: verify_managed_update(
                        request, root, name, update_identity, original
                    )
                    for name in FIXTURES
                },
                "discovery": discover(request, root / "task", installed),
            }
            write_json(upgrade_path, upgrade)
        result["cases"].append(upgrade)
        for name in CASE_IDS:
            result["cases"].append(smoke(request, root, name))
        result["outcome"] = "pass"
    except GateError as error:
        result["outcome"] = error.outcome
        result["problem"] = str(error)
        result["cleanup"] = (
            "preserved owned artifacts and existing native handles; unresolved work is not claimed settled"
        )
    write_json(root / "result.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation",
        choices=(
            "guard",
            "seed",
            "seed-development",
            "development",
            "baseline",
            "setup",
            "reconcile",
            "run",
            "reply",
        ),
    )
    parser.add_argument("--request", default=os.environ.get("AQUARIUM_VM_REQUEST"))
    parser.add_argument(
        "--case",
        choices=(
            "task-startup",
            "epic-startup",
            *(name + "-setup" for name in FIXTURES),
            "adaptive-task",
            "adaptive-epic",
            "adaptive-validation",
            "adaptive-feature",
            "adaptive-project",
            "adaptive-refactor",
            "adaptive-diagnosis",
        ),
    )
    parser.add_argument("--fixture", choices=FIXTURES)
    parser.add_argument("--resume-thread")
    parser.add_argument("--reply-file", type=Path)
    args = parser.parse_args()
    root = None
    try:
        require(args.request, "AQUARIUM_VM_REQUEST or --request is required")
        request, root, identity = load_request(args.request)
        if args.operation == "guard":
            result = {"outcome": "guest-verified", "identity": identity}
        elif args.operation == "seed":
            result = seed(request, root)
        elif args.operation in {"seed-development", "development"}:
            import adaptive_cases

            result = (
                adaptive_cases.seed(sys.modules[__name__], request, root)
                if args.operation == "seed-development"
                else adaptive_cases.run(sys.modules[__name__], request, root)
            )
        elif args.operation == "baseline":
            result = baseline(request, root)
        elif args.operation == "setup":
            require(args.fixture, "setup requires a fixture")
            result = setup_update(
                request, root, args.fixture, resume_thread=args.resume_thread
            )
        elif args.operation == "reconcile":
            require(args.fixture, "reconcile requires a fixture")
            binding = update_binding(request, root)
            original = read_json(root / "baseline.json")
            reconcile_setup(request, root, args.fixture, binding, original)
            result = {
                "outcome": "managed-update-observed",
                **verify_managed_update(request, root, args.fixture, binding, original),
            }
        elif args.operation == "reply":
            require(
                args.case and args.reply_file,
                "reply requires case and an actual operator reply file",
            )
            if args.case.endswith("-setup"):
                result = setup_update(
                    request,
                    root,
                    args.case.removesuffix("-setup"),
                    reply=args.reply_file.read_text(),
                )
            else:
                identifier = invoke(
                    request,
                    root,
                    args.case,
                    "",
                    reply=args.reply_file.read_text(),
                    repository=root / args.case
                    if args.case.startswith("adaptive-")
                    else None,
                )
                result = {"outcome": "reply-delivered", "thread_id": identifier}
        else:
            require(
                request.get("suite") != "adaptive-development",
                "run/test-vm requires the release suite; use development explicitly",
            )
            result = run_gate(request, root)
    except Exception as error:  # noqa: BLE001 - classify malformed report shapes at the CLI boundary
        result = {
            "schema": "aquarium.vm-adaptive-result/v1"
            if args.operation in {"development", "seed-development"}
            else "aquarium.vm-acceptance-result/v1",
            "outcome": getattr(error, "outcome", "incomplete"),
            "problem": str(error),
        }
    if args.operation in {"run", "development"} and root is not None:
        write_json(
            root
            / (
                "adaptive-result.json"
                if args.operation == "development"
                else "result.json"
            ),
            result,
        )
    print(json.dumps(result, ensure_ascii=False))
    return {"fail": 1, "incomplete": 2}.get(result["outcome"], 0)


if __name__ == "__main__":
    raise SystemExit(main())
