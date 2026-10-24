#!/usr/bin/env python3
"""Facts-shaped fake Codex for the offline guest simulation (test fixture)."""

import json
import os
import shutil
import sys

arguments = sys.argv[1:]


def require_absolute_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value or not os.path.isabs(value):
        raise SystemExit(f"{name} must be a non-empty absolute path")
    return value


home = require_absolute_env("AQUARIUM_GUEST_HOME")
with open(require_absolute_env("FAKE_CODEX_STATE")) as stream:
    state = json.load(stream)


def save():
    with open(os.environ["FAKE_CODEX_STATE"], "w") as stream:
        json.dump(state, stream)


def registration(name):
    return next((row for row in state["marketplaces"] if row["name"] == name), None)


if arguments == ["--version"]:
    print("codex-cli 0.164.0")
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

if arguments[:1] == ["app-server"]:
    # Minimal stdio app-server for the real discovery reader.
    for line in sys.stdin:
        try:
            message = json.loads(line)
        except ValueError:
            continue
        method = message.get("method", "")
        request_id = message.get("id")
        if method == "initialize":
            reply = {"id": request_id, "result": {"ok": True}}
        elif method == "skills/list":
            plugin_root = "/synthetic/plugin"
            for row in state["marketplaces"]:
                installed = [
                    item
                    for item in state["installed"]
                    if item["marketplaceName"] == row["name"]
                ]
                if installed:
                    plugin_root = os.path.join(row["root"], "plugins/aquarium")
                    break
            reply = {
                "id": request_id,
                "result": {
                    "data": [
                        {
                            "cwd": home or "/",
                            "skills": [
                                {
                                    "name": "aquarium:dev-setup",
                                    "enabled": True,
                                    "path": os.path.join(
                                        plugin_root, "skills/dev-setup"
                                    ),
                                }
                            ],
                        }
                    ]
                },
            }
        else:
            reply = {"id": request_id, "result": {}}
        sys.stdout.write(json.dumps(reply) + "\n")
        sys.stdout.flush()
    raise SystemExit(0)

print(json.dumps({"error": f"unsupported: {arguments}"}), file=sys.stderr)
raise SystemExit(2)
