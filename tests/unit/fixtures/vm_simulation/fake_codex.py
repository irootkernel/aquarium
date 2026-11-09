#!/usr/bin/env python3
"""Facts-shaped fake Codex for the offline guest simulation (test fixture).

Beyond the marketplace/plugin surface, `codex exec` models the public thread
store the driver reads: every session records user messages, command
executions and child-agent activity that the app-server serves through
`thread/read`, `thread/items/list`, `thread/turns/list`, `thread/list` and
`skills/list`. The runtime-update session never approves itself: the first
turn returns a proposal, and the installer runs only on a resumed turn
whose input carries the operator reply.
"""

import json
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

arguments = sys.argv[1:]


def require_absolute_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value or not os.path.isabs(value):
        raise SystemExit(f"{name} must be a non-empty absolute path")
    return value


home = require_absolute_env("AQUARIUM_GUEST_HOME")
with open(require_absolute_env("FAKE_CODEX_STATE")) as stream:
    state = json.load(stream)
state.setdefault("sessions", {})


def save():
    with open(os.environ["FAKE_CODEX_STATE"], "w") as stream:
        json.dump(state, stream)


def registration(name):
    return next((row for row in state["marketplaces"] if row["name"] == name), None)


def installed_plugin_root():
    for row in state["installed"]:
        current = registration(row["marketplaceName"])
        if current is not None:
            return os.path.join(
                home,
                ".codex/plugins/cache",
                row["marketplaceName"],
                "aquarium",
                row["version"],
            )
    return "/synthetic/plugin"


def skills_list(params):
    cwd = (params.get("cwds") or [home])[0]
    # Fixture-side faults for the restoration regression: a native read
    # that drifts an existing per-home skill's content or executable bit
    # while the planted tree is under observation.
    drift = os.path.join(home, ".codex/skills/ouroboros-orca/SKILL.md")
    if os.environ.get("FAKE_CODEX_DRIFT_SKILLS") and os.path.isfile(drift):
        with open(drift, "a") as stream:
            stream.write("drift\n")
    if os.environ.get("FAKE_CODEX_CHMOD_SKILLS") and os.path.isfile(drift):
        os.chmod(drift, 0o755)
    if os.environ.get("FAKE_CODEX_DRIFT_RULES"):
        rules = os.path.join(home, ".codex/rules/ouroboros.md")
        if os.path.isfile(rules):
            with open(rules, "a") as stream:
                stream.write("drift\n")
    if os.environ.get("FAKE_CODEX_FLIP_PLUGIN"):
        config = os.path.join(home, ".codex/config.toml")
        if os.path.isfile(config):
            with open(config, "a") as stream:
                stream.write('\n[plugins."drifted@example-market"]\nenabled = true\n')
    if os.environ.get("FAKE_CODEX_REORDER_PLUGINS_AND_COMMENT"):
        config = os.path.join(home, ".codex/config.toml")
        if os.path.isfile(config):
            with open(config, "w") as stream:
                stream.write(
                    "# harmless comment added during native read\n"
                    'notify = ["noop"]\n\n'
                    '[plugins."formatter@openai-bundled"]\n'
                    "enabled = false # inline comment\n\n"
                    '[plugins."aquarium@root-kernel"]\n'
                    "enabled = true\n\n"
                    "[features]\n"
                    "shell = true\n\n"
                    '[projects."/Users/synthetic/plugins/repo"]\n'
                    'trust_level = "trusted"\n\n'
                    "[mcp_servers.plugin_helper]\n"
                    "enabled = true\n"
                )
    if os.environ.get("FAKE_CODEX_CORRUPT_CONFIG"):
        config = os.path.join(home, ".codex/config.toml")
        with open(config, "w") as stream:
            stream.write("[broken\nenabled = true\n")
    if os.environ.get("FAKE_CODEX_DRIFT_BUNDLED_CACHE"):
        bundled = os.path.join(home, ".codex/plugins/cache/openai-bundled/plugin.txt")
        if os.path.isfile(bundled):
            with open(bundled, "a") as stream:
                stream.write("bundled-drift\n")
    if os.environ.get("FAKE_CODEX_DRIFT_ROOT_KERNEL_CACHE"):
        rk_skill = os.path.join(installed_plugin_root(), "skills/task-handler/SKILL.md")
        if os.path.isfile(rk_skill):
            with open(rk_skill, "a") as stream:
                stream.write("root-kernel-drift\n")
    rows = []
    plugin_root = installed_plugin_root()
    for name in ("dev-setup", "task-handler", "epic-handler"):
        path = os.path.join(plugin_root, "skills", name)
        if os.environ.get("FAKE_CODEX_SHADOW") and name == "task-handler":
            planted = os.path.join(home, ".codex/skills", "task-handler")
            if os.path.isdir(planted):
                path = planted
        rows.append({"name": f"aquarium:{name}", "enabled": True, "path": path})
    if not os.environ.get("FAKE_CODEX_IGNORE_SCOPE"):
        # Per-home skills load under their own un-namespaced names.
        scope = os.path.join(home, ".codex/skills")
        if os.path.isdir(scope):
            for entry in sorted(os.listdir(scope)):
                if os.path.isdir(os.path.join(scope, entry)):
                    rows.append(
                        {
                            "name": entry,
                            "enabled": True,
                            "path": os.path.join(scope, entry),
                        }
                    )
    return {"data": [{"cwd": cwd, "skills": rows}]}


def new_session(cwd, source="cli", parent=None, role=None):
    identifier = "thread-" + uuid.uuid4().hex[:16]
    session = {
        "metadata": {
            "id": identifier,
            "parentThreadId": parent,
            "cwd": str(cwd),
            "source": source,
            "status": "completed",
            "cliVersion": "0.164.0",
            "agentRole": role,
        },
        "items": [],
        "turns": [],
    }
    state["sessions"][identifier] = session
    return session


def add_item(session, item):
    item = {"id": f"{session['metadata']['id']}-{len(session['items'])}", **item}
    session["items"].append(item)
    return item


def close_turn(session, items, status="completed", error=None):
    session["turns"].append(
        {
            "id": f"turn-{len(session['turns'])}",
            "status": status,
            "error": error,
            "items": items,
        }
    )


def procedure_trees():
    trees = {}
    for kind in ("artifact", "prior-artifact"):
        root = os.path.join(
            home,
            ".aquarium-vm-marketplaces",
            kind,
            "plugins/aquarium/assets/podway/procedures",
        )
        if os.path.isdir(root):
            trees[kind] = root
    return trees


PROCEDURE_NAMES = tuple(
    f"aquarium-{name}-v2.yaml"
    for name in ("task", "goal", "validation", "design", "war-room")
)


def apply_managed_sources(cwd):
    """The installed dev-setup swaps managed Procedure bytes.

    A customized file (equal to neither sealed tree) is preserved.
    """
    installed = os.path.join(installed_plugin_root(), "assets/podway/procedures")
    if not os.path.isdir(installed):
        return []
    trees = procedure_trees()
    changed = []
    for name in PROCEDURE_NAMES:
        source = os.path.join(installed, name)
        if not os.path.isfile(source):
            continue
        destination = Path(cwd) / ".podway/procedures" / name
        payload = Path(source).read_bytes()
        if destination.is_file():
            current = destination.read_bytes()
            if current == payload:
                continue
            sealed = any(
                current == (Path(root) / name).read_bytes()
                for root in trees.values()
                if (Path(root) / name).is_file()
            )
            if not sealed:
                continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)
        changed.append(name)
    return changed


def run_exec() -> int:
    index = 1
    cwd = os.getcwd()
    last_message = None
    while index < len(arguments):
        flag = arguments[index]
        if flag == "--json":
            index += 1
        elif flag == "--sandbox":
            if arguments[index + 1] not in {
                "read-only",
                "workspace-write",
                "danger-full-access",
            }:
                return 2
            index += 2
        elif flag == "--add-dir":
            index += 2
        elif flag in {"-c", "--config"}:
            if "=" not in arguments[index + 1]:
                return 2
            index += 2
        elif flag == "-C":
            cwd = arguments[index + 1]
            index += 2
        elif flag == "--output-last-message":
            last_message = arguments[index + 1]
            index += 2
        elif flag == "resume":
            return resume_session(arguments[index + 1], last_message)
        elif flag == "-":
            return new_turn(cwd, last_message)
        else:
            print(f"unsupported exec flag: {flag}", file=sys.stderr)
            return 2
    print("exec needs an input", file=sys.stderr)
    return 2


PYTHON_RUNTIME_APPROVAL = "Approve the proposed aquarium-python preparation."
# Offline stand-in for the approved aquarium-python preparation: the
# candidate's own runtime CLI runs unchanged, except that pip is replaced by
# copies of the simulation interpreter's already installed packages.
OFFLINE_PYTHON_INSTALL = r"""
import importlib, runpy, shutil, subprocess, sys, venv
from pathlib import Path

runtime = sys.argv[1]
real_run = subprocess.run
real_create = venv.EnvBuilder.create


def create(builder, path):
    builder.with_pip = False
    return real_create(builder, path)


def run(command, *args, **kwargs):
    if list(command[1:4]) == ["-I", "-m", "pip"]:
        if command[4] == "install":
            environment = Path(command[0]).parents[1]
            site = next((environment / "lib").glob("python*/site-packages"))
            for name in (
                "yaml", "jsonschema", "attrs", "attr", "referencing", "rpds",
                "jsonschema_specifications", "typing_extensions",
            ):
                path = Path(importlib.import_module(name).__file__)
                if path.name == "__init__.py":
                    shutil.copytree(
                        path.parent,
                        site / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                    )
                else:
                    shutil.copy2(path, site / path.name)
        return subprocess.CompletedProcess(command, 0, "", "")
    return real_run(command, *args, **kwargs)


venv.EnvBuilder.create = create
subprocess.run = run
sys.argv = [runtime, "install", "--approve-install"]
runpy.run_path(runtime, run_name="__main__")
"""


def read_prompt() -> str:
    return sys.stdin.read()


def emit(session, events):
    for event in events:
        sys.stdout.write(json.dumps(event) + "\n")
    sys.stdout.flush()


def finish(session, text, last_message):
    if last_message:
        with open(last_message, "w") as stream:
            stream.write(text)
    save()


def new_turn(cwd, last_message) -> int:
    prompt = read_prompt()
    if "user-global aquarium-status runtime" in prompt:
        session = new_session(cwd, role="dev-setup-global-continuation")
        add_item(session, {"type": "userMessage", "text": prompt})
        add_item(
            session,
            {
                "type": "agentMessage",
                "phase": "final_answer",
                "text": (
                    "Proposal: managed update of the user-global "
                    "aquarium-status runtime through the "
                    "$aquarium:dev-setup-global continuation. Awaiting the "
                    "operator's actual approval."
                ),
            },
        )
        close_turn(session, list(session["items"]))
        finish(session, "runtime proposal", last_message)
        emit(
            session,
            [{"type": "thread.started", "thread_id": session["metadata"]["id"]}],
        )
        return 0
    if "aquarium-python component" in prompt:
        session = new_session(cwd, role="dev-setup-global-python")
        add_item(session, {"type": "userMessage", "text": prompt})
        add_item(
            session,
            {
                "type": "agentMessage",
                "phase": "final_answer",
                "text": (
                    "Proposal: prepare the shared aquarium-python environment "
                    "under ~/.aquarium/python-runtime/ from the pinned, "
                    "hash-checked requirements. Awaiting the operator's "
                    "actual approval."
                ),
            },
        )
        close_turn(session, list(session["items"]))
        finish(session, "python runtime proposal", last_message)
        emit(
            session,
            [{"type": "thread.started", "thread_id": session["metadata"]["id"]}],
        )
        return 0
    if "$aquarium:dev-setup" in prompt:
        return run_setup_turn(prompt, cwd, last_message)
    session = new_session(cwd)
    add_item(session, {"type": "userMessage", "text": prompt})
    add_item(
        session,
        {"type": "agentMessage", "phase": "final_answer", "text": "acknowledged"},
    )
    close_turn(session, list(session["items"]))
    finish(session, "acknowledged", last_message)
    emit(session, [{"type": "thread.started", "thread_id": session["metadata"]["id"]}])
    return 0


def resume_session(thread_id, last_message) -> int:
    session = state["sessions"].get(thread_id)
    if session is None:
        print(f"unknown thread {thread_id}", file=sys.stderr)
        return 2
    prompt = read_prompt()
    add_item(session, {"type": "userMessage", "text": prompt})
    if session["metadata"].get("agentRole") == "dev-setup":
        # A reply executes the approved decision: the managed sources
        # change inside this resumed turn.
        apply_managed_sources(session["metadata"].get("cwd") or os.getcwd())
        source = installed_plugin_root()
        add_item(
            session,
            {
                "type": "commandExecution",
                "status": "completed",
                "exitCode": 0,
                "command": os.path.join(source, "skills/dev-setup/SKILL.md")
                + " --apply-decision",
            },
        )
        add_item(
            session,
            {
                "type": "agentMessage",
                "phase": "final_answer",
                "text": "The approved managed update completed.",
            },
        )
        close_turn(session, session["items"][-2:])
        finish(session, "managed update completed", last_message)
        return 0
    if session["metadata"].get("agentRole") == "dev-setup-global-python":
        # Closed fixture sentinel, not an approval parser: any other reply,
        # including "do not approve", leaves the proposal pending.
        if prompt.strip() != PYTHON_RUNTIME_APPROVAL:
            add_item(
                session,
                {
                    "type": "agentMessage",
                    "phase": "final_answer",
                    "text": "The proposal still awaits an actual approval.",
                },
            )
            close_turn(session, [session["items"][-1]])
            finish(session, "awaiting approval", last_message)
            return 0
        runtime = os.path.join(
            home,
            ".aquarium-vm-marketplaces/artifact/plugins/aquarium/tools/"
            "aquarium-python/runtime.py",
        )
        result = subprocess.run(
            [
                os.environ["FAKE_PYTHON_REAL"],
                "-B",
                "-c",
                OFFLINE_PYTHON_INSTALL,
                runtime,
            ],
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, "HOME": home},
        )
        add_item(
            session,
            {
                "type": "commandExecution",
                "status": "completed",
                "exitCode": result.returncode,
                "command": runtime + " install --approve-install",
            },
        )
        add_item(
            session,
            {
                "type": "agentMessage",
                "phase": "final_answer",
                "text": "The approved aquarium-python preparation completed.",
            },
        )
        close_turn(session, session["items"][-2:])
        finish(session, "python runtime prepared", last_message)
        return 0 if result.returncode == 0 else 1
    if "aquarium-status runtime" in session["items"][0].get("text", ""):
        if os.environ.get("FAKE_CODEX_RUNTIME_NO_INSTALL"):
            # Fixture-side control: the resumed turn returns without
            # running the installer, so an unrelated runtime state stays
            # observable after the reply.
            add_item(
                session,
                {
                    "type": "agentMessage",
                    "phase": "final_answer",
                    "text": "The approved runtime update completed.",
                },
            )
            close_turn(session, [session["items"][-1]])
            finish(session, "runtime updated", last_message)
            return 0
        if "approve" not in prompt.lower():
            add_item(
                session,
                {
                    "type": "agentMessage",
                    "phase": "final_answer",
                    "text": "The proposal still awaits an actual approval.",
                },
            )
            close_turn(session, [session["items"][-1]])
            finish(session, "awaiting approval", last_message)
            return 0
        # The installer runs only on this resumed, approved turn; the first
        # turn never self-approves.
        source = os.path.join(
            home,
            ".aquarium-vm-marketplaces/artifact/plugins/aquarium/tools/aquarium-status",
        )
        result = subprocess.run(
            [
                os.environ["AQUARIUM_GUEST_PYTHON"],
                "-B",
                os.path.join(source, "install.py"),
                "install",
                "--source",
                source,
                "--approve-install",
                "--approve-launcher",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        add_item(
            session,
            {
                "type": "commandExecution",
                "status": "completed",
                "exitCode": result.returncode,
                "command": os.path.join(source, "install.py") + " install",
            },
        )
        add_item(
            session,
            {
                "type": "agentMessage",
                "phase": "final_answer",
                "text": "The approved runtime update completed.",
            },
        )
        close_turn(session, session["items"][-2:])
        finish(session, "runtime updated", last_message)
        if os.environ.get("FAKE_CODEX_FAIL_RUNTIME_REPLY"):
            return 1
        return 0 if result.returncode == 0 else 1
    add_item(
        session,
        {"type": "agentMessage", "phase": "final_answer", "text": "continued"},
    )
    close_turn(session, [session["items"][-1]])
    finish(session, "continued", last_message)
    return 0


def run_setup_turn(prompt, cwd, last_message) -> int:
    decision = os.environ.get("FAKE_CODEX_SETUP_DECISION", "")
    if decision and decision in cwd:
        # First turn is a completed proposal with no execution and no
        # managed-source change: the reply executes the decision.
        session = new_session(cwd, role="dev-setup")
        add_item(session, {"type": "userMessage", "text": prompt})
        add_item(
            session,
            {
                "type": "agentMessage",
                "phase": "final_answer",
                "text": "Proposal: update the managed sources. Awaiting the "
                "operator's actual decision.",
            },
        )
        close_turn(session, list(session["items"]))
        finish(session, "awaiting decision", last_message)
        emit(
            session,
            [{"type": "thread.started", "thread_id": session["metadata"]["id"]}],
        )
        return 0
    changed = apply_managed_sources(cwd)
    session = new_session(cwd, role="dev-setup")
    add_item(session, {"type": "userMessage", "text": prompt})
    source = installed_plugin_root()
    add_item(
        session,
        {
            "type": "commandExecution",
            "status": "completed",
            "exitCode": 0,
            "command": os.path.join(source, "skills/dev-setup/SKILL.md") + " --check",
        },
    )
    add_item(
        session,
        {
            "type": "agentMessage",
            "phase": "final_answer",
            "text": (
                "dev-setup completed the managed configuration update"
                + (f" ({', '.join(changed)})" if changed else "")
                + "."
            ),
        },
    )
    close_turn(session, list(session["items"]))
    finish(session, "dev-setup completed", last_message)
    emit(session, [{"type": "thread.started", "thread_id": session["metadata"]["id"]}])
    return 0


if arguments == ["--version"]:
    print("codex-cli 0.164.0")
    raise SystemExit(0)

if arguments == ["login", "status"]:
    print("Logged in using ChatGPT", file=sys.stderr)
    raise SystemExit(0)

if arguments[:3] == ["plugin", "marketplace", "list"] and "--json" in arguments:
    print(json.dumps({"marketplaces": state["marketplaces"]}))
    raise SystemExit(0)

if arguments[:3] == ["plugin", "marketplace", "add"] and len(arguments) >= 4:
    directory = arguments[3]
    with open(os.path.join(directory, ".agents/plugins/marketplace.json")) as stream:
        name = json.load(stream)["name"]
    existing = registration(name)
    if existing is not None and existing.get("root") != directory:
        print(
            f"Error: marketplace '{name}' is already added from a different "
            "source; remove it before adding this source",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if existing is None:
        state["marketplaces"].append(
            {
                "name": name,
                "root": directory,
                "marketplaceSource": {
                    "sourceType": "local",
                    "source": directory,
                },
            }
        )
        save()
    print(
        json.dumps(
            {
                "marketplaceName": name,
                "installedRoot": directory,
                "alreadyAdded": existing is not None,
            }
        )
    )
    raise SystemExit(0)

if arguments[:3] == ["plugin", "marketplace", "remove"] and len(arguments) >= 4:
    state["marketplaces"] = [
        row for row in state["marketplaces"] if row["name"] != arguments[3]
    ]
    save()
    raise SystemExit(0)

if arguments[:2] == ["plugin", "list"]:
    marketplace = arguments[arguments.index("--marketplace") + 1]
    installed = []
    for row in state["installed"]:
        if row["marketplaceName"] != marketplace:
            continue
        current = registration(marketplace)
        if current is None:
            continue
        installed.append(
            {
                "pluginId": row["pluginId"],
                "name": row["name"],
                "marketplaceName": marketplace,
                "version": row["version"],
                "installed": True,
                "enabled": True,
                "source": {
                    "source": "local",
                    "path": os.path.join(current["root"], "plugins/aquarium"),
                },
                "marketplaceSource": {
                    "sourceType": "local",
                    "source": current["root"],
                },
                "installPolicy": "AVAILABLE",
                "authPolicy": "ON_INSTALL",
            }
        )
    print(json.dumps({"installed": installed, "available": []}))
    raise SystemExit(0)

if arguments[:2] == ["plugin", "add"] and len(arguments) == 3:
    plugin, marketplace = arguments[2].split("@")
    current = registration(marketplace)
    if current is None:
        print(f"marketplace {marketplace} is not registered", file=sys.stderr)
        raise SystemExit(1)
    plugin_root = os.path.join(current["root"], "plugins", plugin)
    with open(os.path.join(plugin_root, ".codex-plugin/plugin.json")) as stream:
        version = json.load(stream)["version"]
    cache = os.path.join(home, ".codex/plugins/cache", marketplace, plugin)
    if os.path.isdir(cache):
        shutil.rmtree(cache)
    shutil.copytree(plugin_root, os.path.join(cache, version))
    if os.environ.get("FAKE_CODEX_PLANT_SYMLINK"):
        # Fixture-side fault: a foreign symlink inside the installed
        # marketplace root, outside plugins/, breaks byte-identity with the
        # sealed artifact for the ownership checks.
        planted = os.path.join(current["root"], "planted-link")
        if not os.path.exists(planted) and not os.path.islink(planted):
            os.symlink("plugins/aquarium", planted)
    if os.environ.get("FAKE_CODEX_DANGLING_SIDECAR"):
        # Fixture-side fault: replace the candidate marketplace's owner
        # sidecar with a dangling symlink, a residue form only a
        # type-independent absence check can see.
        sidecar = os.path.join(os.path.dirname(current["root"]), "artifact.owner.json")
        if os.path.islink(sidecar) or os.path.exists(sidecar):
            os.unlink(sidecar)
        os.symlink("nonexistent-sidecar-target", sidecar)
    # Real Codex mutates its internal app-server state on plugin operations;
    # that tree is the Codex component's own state, outside the plugin-cache
    # inventory scope.
    appserver = os.path.join(home, ".codex/plugins/.plugin-appserver/codex-cli")
    os.makedirs(appserver, exist_ok=True)
    with open(os.path.join(appserver, "last-install.json"), "w") as stream:
        stream.write(json.dumps({"plugin": plugin, "version": version}) + "\n")
    state["installed"] = [
        row for row in state["installed"] if row["marketplaceName"] != marketplace
    ]
    state["installed"].append(
        {
            "pluginId": f"{plugin}@{marketplace}",
            "name": plugin,
            "marketplaceName": marketplace,
            "version": version,
        }
    )
    save()
    raise SystemExit(0)

if arguments[:2] == ["plugin", "remove"]:
    marketplace = arguments[arguments.index("--marketplace") + 1]
    cache = os.path.join(home, ".codex/plugins/cache", marketplace, "aquarium")
    if os.path.isdir(cache):
        shutil.rmtree(cache)
    state["installed"] = [
        row for row in state["installed"] if row["marketplaceName"] != marketplace
    ]
    save()
    raise SystemExit(0)

if arguments[:1] == ["exec"]:
    raise SystemExit(run_exec())

if arguments[:1] == ["app-server"]:
    # Minimal stdio app-server for the real discovery and thread readers.
    for line in sys.stdin:
        try:
            message = json.loads(line)
        except ValueError:
            continue
        method = message.get("method", "")
        request_id = message.get("id")
        params = message.get("params", {})
        if method == "initialize":
            reply = {"id": request_id, "result": {"ok": True}}
        elif method == "skills/list":
            reply = {"id": request_id, "result": skills_list(params)}
        elif method == "thread/read":
            thread = state["sessions"].get(params.get("threadId", ""))
            reply = (
                {"id": request_id, "result": {"thread": thread["metadata"]}}
                if thread
                else {"id": request_id, "error": {"message": "unknown thread"}}
            )
        elif method in {"thread/items/list", "thread/turns/list"}:
            thread = state["sessions"].get(params.get("threadId", ""))
            if thread is None:
                reply = {"id": request_id, "error": {"message": "unknown thread"}}
            elif method == "thread/items/list":
                reply = {"id": request_id, "result": {"data": thread["items"]}}
            else:
                reply = {"id": request_id, "result": {"data": thread["turns"]}}
        elif method == "thread/list":
            ancestor = params.get("ancestorThreadId", "")
            data = [
                session["metadata"]
                for session in state["sessions"].values()
                if session["metadata"].get("parentThreadId") == ancestor
            ]
            reply = {"id": request_id, "result": {"data": data}}
        else:
            reply = {"id": request_id, "result": {}}
        sys.stdout.write(json.dumps(reply) + "\n")
        sys.stdout.flush()
    raise SystemExit(0)

print(json.dumps({"error": f"unsupported: {arguments}"}), file=sys.stderr)
raise SystemExit(2)
