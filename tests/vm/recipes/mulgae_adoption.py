"""Capture Mulgae upgrade/restoration observations in one held manual Job."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Any

import recipe_lib as lib

SUITE = "mulgae-adoption"
RELEASE_SKILL_TREE = "a3d11762fa5f1069df60cd64ef9cf2efd538e8e1ebd1b60e61a717c7e4697085"


def observe(context: Any) -> dict[str, Any]:
    executable = shutil.which("mulgae")
    if not executable:
        raise lib.RecipeError("installed Mulgae is required", "incomplete")
    binary = Path(executable).resolve(strict=True)
    before = lib.sha256_file(binary)
    result = lib.run([str(binary), "version", "--json"], timeout=30)
    try:
        version = json.loads(result.stdout)
    except ValueError as error:
        raise lib.RecipeError(
            "invalid Mulgae version response", "incomplete"
        ) from error
    if (
        result.returncode
        or not isinstance(version, dict)
        or version.get("name") != "mulgae"
        or before != lib.sha256_file(binary)
    ):
        raise lib.RecipeError("Mulgae identity is unavailable or changed", "incomplete")
    return {
        "version": version.get("version"),
        "binary_sha256": before,
        "skill_tree_sha256": lib.skill_tree_digest(
            context.checkout, context.home / ".agents/skills/use-mulgae"
        ),
    }


def run(context: Any, phase: str) -> int:
    lib.verify_guest_identity()
    lib.verify_sealed_inputs(context.root)
    lib.guard(context.root)
    if phase not in {"ready", "prepare", "candidate", "consumer-cleanup"}:
        raise lib.RecipeError("unknown Mulgae observation phase", "incomplete")
    results = lib.results_directory(SUITE)
    target = results / f"{phase}.json"
    if target.exists():
        raise lib.RecipeError("preserve the original phase observation", "incomplete")
    candidate = context.inputs["candidate"]["git_sha"]
    if phase == "ready":
        lib.write_document(
            target,
            {
                "candidate_sha": candidate,
                "state": "awaiting authorized manual preparation",
            },
        )
        return 0
    baseline = lib.read_json_safe(results / "prepare.json")
    if phase != "prepare" and (
        not isinstance(baseline, dict)
        or baseline.get("candidate_sha") != candidate
        or not baseline.get("inventory")
    ):
        raise lib.RecipeError(
            "original candidate-bound baseline is required", "incomplete"
        )
    if phase == "consumer-cleanup":
        installed = lib.read_json_safe(results / "candidate.json")
        if (
            not isinstance(installed, dict)
            or installed.get("candidate_sha") != candidate
            or installed.get("tools", {}).get("version") != "v0.1.27"
            or installed.get("tools", {}).get("skill_tree_sha256") != RELEASE_SKILL_TREE
        ):
            raise lib.RecipeError(
                "installed candidate observation is required", "incomplete"
            )
    tools = observe(context)
    if phase == "prepare" and tools["version"] != "v0.1.26":
        raise lib.RecipeError(
            "observe the released v0.1.26 baseline first", "incomplete"
        )
    if phase == "candidate" and (
        tools["version"] != "v0.1.27"
        or tools["skill_tree_sha256"] != RELEASE_SKILL_TREE
    ):
        raise lib.RecipeError("Mulgae release or complete skill differs", "incomplete")
    aggregate_path = results / "inventories.json"
    aggregate = lib.read_json_safe(aggregate_path)
    if aggregate_path.exists() and (
        not isinstance(aggregate, dict)
        or aggregate.get("schema") != "aquarium.vm-suite-inventories/v1"
        or not isinstance(aggregate.get("inventories"), dict)
    ):
        raise lib.RecipeError("preserve the invalid inventory history", "incomplete")
    capture = (
        phase if phase != "consumer-cleanup" else f"consumer-cleanup-{uuid.uuid4().hex}"
    )
    inventory = context.snapshot(
        SUITE,
        phase,
        profile="candidate" if phase == "candidate" else "stable",
        capture=capture,
    )
    document = {
        "candidate_sha": candidate,
        "tools": tools,
        "inventory": inventory,
        "functional_cases": "unverified; native manual completion owns their verdict",
    }
    if phase == "consumer-cleanup":
        problems = lib.postcondition_violations(
            baseline["inventory"], inventory, lambda _scope, _path: False
        )
        if baseline["tools"] != tools:
            problems.append("Mulgae binary or complete skill differs from baseline")
        if problems:
            lib.write_document(
                results / f"{capture}.json", {**document, "violations": problems}
            )
            raise lib.RecipeError(
                "consumer restoration failed: " + "; ".join(problems), "incomplete"
            )
        document["consumer_cleanup"] = "verified"
    lib.write_document(target, document)
    if phase == "consumer-cleanup":
        return lib.finish(
            SUITE,
            "pass",
            {"scope": "consumer restoration only", "functional_cases": "unverified"},
            consumer_cleanup="verified",
        )
    return 0
