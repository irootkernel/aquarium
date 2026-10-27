"""Observe a separately authorized manual Podway upgrade and restoration.

The operator owns installation, original-writer settlement, runtime discard and
native skill execution. These phases never install, reset or dispatch an agent.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import recipe_lib as lib


def observe_tools(context: Any, stage: str) -> dict[str, Any]:
    profile = context.profile("stable" if stage == "prior" else "podway-candidate")
    components = {row["name"]: row for row in profile["components"]}
    executable = Path(lib.context_value("AQUARIUM_GUEST_PODWAY"))
    if executable.is_symlink() or not executable.is_file():
        raise lib.RecipeError(
            "Podway must be a regular installed executable", "incomplete"
        )
    actual = "sha256:" + lib.sha256_file(executable)
    if actual != components["podway"]["executable_sha256"]:
        raise lib.RecipeError(
            "installed Podway differs from the selected profile; it was not executed",
            "incomplete",
        )
    skill = context.home / ".agents/skills/use-podway"
    digest = lib.skill_tree_digest(context.checkout, skill)
    if digest != components["use-podway"]["skill_tree"]["sha256"]:
        raise lib.RecipeError(
            "installed use-podway tree differs from the selected profile", "incomplete"
        )
    # Original-writer observation deliberately uses its release's grammar.
    generation = [] if stage == "prior" else ["--contract-generation", "2"]
    output = lib.run(
        [str(executable), *generation, "--json", "version", "--identity"], timeout=30
    )
    identity = json.loads(output.stdout)
    result = identity.get("result", {})
    if (
        output.returncode
        or identity.get("schema") != "podway.output/v4"
        or result.get("schema") != "podway.version-result/v2"
        or result.get("version") != components["podway"]["version"]
    ):
        raise lib.RecipeError("installed Podway identity is unavailable", "incomplete")
    if stage == "candidate":
        release = context.inputs["podway_upgrade"]
        if any(
            result.get(key) != release[key]
            for key in ("source_commit", "contract_manifest_digest")
        ):
            raise lib.RecipeError(
                "candidate Podway source or manifest differs", "incomplete"
            )
    return {"identity": identity, "binary_sha256": actual, "skill_tree_sha256": digest}


def restoration_state(skills: dict[str, Any]) -> dict[str, Any]:
    configuration = skills.get("effective_configuration")
    scopes = skills.get("scopes")
    rules = (
        [
            row
            for row in scopes
            if isinstance(row, dict) and row.get("scope") == "codex-rules"
        ]
        if isinstance(scopes, list)
        else []
    )
    if (
        not isinstance(configuration, dict)
        or not isinstance(configuration.get("marketplaces"), dict)
        or not isinstance(configuration.get("installed_plugin"), dict)
        or len(rules) != 1
    ):
        raise lib.RecipeError(
            "restoration needs native configuration, registration and rules observations",
            "incomplete",
        )
    return {"configuration": configuration, "rules": rules[0]}


def run(
    context: Any, phase: str, skill_identity: Callable[[str], dict[str, Any]]
) -> int:
    lib.verify_guest_identity()
    lib.verify_sealed_inputs(context.root)
    release = context.inputs.get("podway_upgrade")
    if not isinstance(release, dict) or release.get("contract_generation") != 2:
        raise lib.RecipeError(
            "manual Podway upgrade requires its sealed release input", "incomplete"
        )
    lib.guard(context.root)
    results = lib.results_directory("podway-upgrade")
    targets = {
        "prepare": "prepared.json",
        "candidate": "candidate.json",
        "consumer-cleanup": "consumer-cleanup.json",
    }
    if phase not in targets:
        raise lib.RecipeError(f"unknown podway-upgrade phase: {phase}")
    target = results / targets[phase]
    if target.exists():
        raise lib.RecipeError(
            "preserve the existing phase observation; do not recapture it", "incomplete"
        )
    if phase != "prepare" and not (results / "prepared.json").is_file():
        raise lib.RecipeError("prepare the released baseline first", "incomplete")
    if phase != "prepare":
        baseline = lib.read_json_safe(results / "prepared.json")
        if (
            not isinstance(baseline, dict)
            or baseline.get("candidate_sha") != context.inputs["candidate"]["git_sha"]
        ):
            raise lib.RecipeError("baseline belongs to another candidate", "incomplete")
    if phase == "consumer-cleanup" and not (results / "candidate.json").is_file():
        raise lib.RecipeError(
            "capture the installed candidate before restoration", "incomplete"
        )
    stage = "candidate" if phase == "candidate" else "prior"
    tools = observe_tools(context, stage)
    skills = skill_identity(stage)
    if skills.get("comparisons", {}).get("all_passed") is not True:
        raise lib.RecipeError(
            "installed skill identity comparison failed", "incomplete"
        )
    current_state = restoration_state(skills)
    inventory = context.snapshot(
        "podway-upgrade",
        "candidate"
        if stage == "candidate"
        else "before"
        if phase == "prepare"
        else "post_cleanup",
        profile="podway-candidate" if stage == "candidate" else "stable",
    )
    document = {
        "candidate_sha": context.inputs["candidate"]["git_sha"],
        "phase": phase,
        "tools": tools,
        "skills": skills,
        "inventory": inventory,
        "functional_cases": "unverified; supply original observations through native manual completion",
    }
    if phase == "consumer-cleanup":
        before = lib.read_json_safe(results / "prepared.json")
        if (
            not isinstance(before, dict)
            or before.get("candidate_sha") != document["candidate_sha"]
        ):
            raise lib.RecipeError(
                "restoration lacks the original candidate-bound baseline", "incomplete"
            )
        problems = lib.postcondition_violations(
            before["inventory"], inventory, lambda _scope, _path: False
        )
        if restoration_state(before.get("skills", {})) != current_state:
            problems.append(
                "effective configuration, native registration or Codex rules differ from the baseline"
            )
        # Identity envelopes include fresh request IDs and timestamps.
        for key in ("binary_sha256", "skill_tree_sha256"):
            if before["tools"].get(key) != tools.get(key):
                problems.append(f"restored {key} differs from the baseline")
        if problems:
            raise lib.RecipeError(
                "consumer restoration failed: " + "; ".join(problems), "incomplete"
            )
        document["consumer_cleanup"] = "verified"
    lib.write_document(target, document)
    if phase == "consumer-cleanup":
        return lib.finish(
            "podway-upgrade",
            "pass",
            {
                "phase": phase,
                "scope": "consumer restoration only",
                "functional_cases": "not assessed; native manual completion owns their verdict",
            },
            consumer_cleanup="verified",
        )
    return 0
