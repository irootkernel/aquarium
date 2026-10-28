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
    context: Any,
    phase: str,
    skill_identity: Callable[[str], dict[str, Any]],
    *,
    suite: str = "podway-upgrade",
) -> int:
    lib.verify_guest_identity()
    lib.verify_sealed_inputs(context.root)
    release = context.inputs.get("podway_upgrade")
    if not isinstance(release, dict) or release.get("contract_generation") != 2:
        raise lib.RecipeError(
            "manual Podway upgrade requires its sealed release input", "incomplete"
        )
    lib.guard(context.root)
    results = lib.results_directory(suite)
    if suite == "epic-squad" and phase == "stage-evidence":
        return stage_squad_evidence(context, results)
    targets = {
        "prepare": "prepared.json",
        "candidate": "candidate.json",
        "consumer-cleanup": "consumer-cleanup.json",
    }
    if phase not in targets:
        raise lib.RecipeError(f"unknown podway-upgrade phase: {phase}")
    if phase == "consumer-cleanup":
        aggregate_path = results / "inventories.json"
        aggregate = lib.read_json_safe(aggregate_path)
        if not aggregate_path.exists():
            aggregate = {
                "schema": "aquarium.vm-suite-inventories/v1",
                "inventories": {},
            }
        if (
            not isinstance(aggregate, dict)
            or aggregate.get("schema") != "aquarium.vm-suite-inventories/v1"
            or not isinstance(aggregate.get("inventories"), dict)
            or not isinstance(aggregate.get("failed_cleanup_observations", []), list)
        ):
            # The driver's generic error handler rewrites malformed aggregates.
            result = {
                "schema": lib.RESULT_SCHEMA,
                "suite": suite,
                "outcome": "incomplete",
                "consumer_cleanup": "unverified",
                "candidate": context.inputs["candidate"],
                "problem": "preserve the invalid cleanup history",
            }
            lib.write_document(results / "result.json", result)
            print(json.dumps(result))
            return lib.OUTCOME_EXITS["incomplete"]
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
        suite,
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

        def codex_cache(scope: str, path: str) -> bool:
            prefix = ".codex/plugins/cache/"
            if scope != "codex-plugin-cache" or not path.startswith(prefix):
                return False
            marketplace = path.removeprefix(prefix).split("/", 1)[0]
            return bool(marketplace) and marketplace != context.marketplace

        all_changes = lib.postcondition_violations(
            before["inventory"], inventory, lambda _scope, _path: False
        )
        problems = lib.postcondition_violations(
            before["inventory"], inventory, codex_cache
        )
        document["codex_owned_cache_observations"] = [
            change for change in all_changes if change not in set(problems)
        ]
        if restoration_state(before.get("skills", {})) != current_state:
            problems.append(
                "effective configuration, native registration or Codex rules differ from the baseline"
            )
        # Identity envelopes include fresh request IDs and timestamps.
        for key in ("binary_sha256", "skill_tree_sha256"):
            if before["tools"].get(key) != tools.get(key):
                problems.append(f"restored {key} differs from the baseline")
        if problems:
            aggregate.setdefault("failed_cleanup_observations", []).append(
                {**document, "violations": problems}
            )
            lib.write_document(aggregate_path, aggregate)
            raise lib.RecipeError(
                "consumer restoration failed: " + "; ".join(problems), "incomplete"
            )
        document["consumer_cleanup"] = "verified"
    lib.write_document(target, document)
    if phase == "consumer-cleanup":
        outcome = lib.finish(
            suite,
            "pass",
            {
                "phase": phase,
                "scope": "consumer restoration only",
                "functional_cases": "not assessed; native manual completion owns their verdict",
            },
            consumer_cleanup="verified",
            **({"inputs": context.inputs} if suite == "epic-squad" else {}),
        )
        if suite == "epic-squad" and outcome == 0:
            receipt = results / "consumer-result.json"
            if not receipt.exists():
                with receipt.open("xb") as stream:
                    stream.write((results / "result.json").read_bytes())
        return outcome
    return 0


def stage_squad_evidence(context: Any, results: Path) -> int:
    """Stage original case files as fixed outputs before native collection."""
    cases = json.loads(
        (context.checkout / "tests/vm/fixtures/squad/cases.json").read_bytes()
    )["cases"]
    index = lib.read_json_safe(results / "case-evidence.json")
    declared = index.get("cases", {}) if isinstance(index, dict) else {}
    if not isinstance(declared, dict):
        declared = {}
    problems = []
    candidate = context.inputs["candidate"]["git_sha"]
    if not isinstance(index, dict) or index.get("candidate_sha") != candidate:
        problems.append(
            "case evidence index is missing or belongs to another candidate"
        )
    if set(declared) != set(cases):
        problems.append("case evidence index must inventory every declared case")
    cleanup = lib.read_json_safe(results / "consumer-cleanup.json")
    restored = (
        isinstance(cleanup, dict)
        and cleanup.get("candidate_sha") == candidate
        and cleanup.get("consumer_cleanup") == "verified"
    )
    if not restored:
        problems.append("capture actual verified consumer cleanup before staging")
    receipt = results / "consumer-result.json"
    original_result = lib.read_json_safe(receipt)
    receipt_current = (
        isinstance(original_result, dict)
        and original_result.get("outcome") == "pass"
        and original_result.get("consumer_cleanup") == "verified"
        and isinstance(original_result.get("candidate"), dict)
        and original_result["candidate"].get("git_sha") == candidate
    )
    if not receipt_current:
        problems.append("the original consumer result is missing or not current")
    aggregate_path = results / "inventories.json"
    aggregate = lib.read_json_safe(aggregate_path)
    invalid_inventory = aggregate_path.exists() and (
        not isinstance(aggregate, dict)
        or aggregate.get("schema") != "aquarium.vm-suite-inventories/v1"
        or not isinstance(aggregate.get("inventories"), dict)
        or not isinstance(aggregate.get("failed_cleanup_observations", []), list)
    )
    if invalid_inventory:
        problems.append("preserve the invalid cleanup history")
    history_path = results / "stage-evidence.json"
    previous = lib.read_json_safe(history_path)
    history = previous.get("attempts", []) if isinstance(previous, dict) else []
    current = {
        "ok": False,
        "state": "in-progress",
        "candidate_sha": candidate,
        "archives": [],
        "problems": problems,
    }
    # Persist the attempt before any archive write. Its partial facts survive retry.
    history = [*history, current]

    def persist():
        pending_history = history_path.with_suffix(".json.partial")
        lib.write_document(pending_history, {**current, "attempts": history})
        pending_history.replace(history_path)

    persist()
    total = 0
    try:
        for case in cases:
            directory = results / "originals" / case
            members = []
            gaps = []
            required = (
                declared.get(case, {}).get("required", [])
                if isinstance(declared.get(case), dict)
                else []
            )
            if not isinstance(required, list) or not required:
                gaps.append("complete required original artifact inventory is missing")
                required = []
            safe_required = []
            for name in required:
                if (
                    not isinstance(name, str)
                    or not name
                    or name == "."
                    or Path(name).is_absolute()
                    or ".." in Path(name).parts
                    or Path(name).as_posix() != name
                ):
                    gaps.append("required original artifact path is unsafe")
                else:
                    safe_required.append(f"originals/{case}/{name}")
            if (results / "originals").is_symlink() or directory.is_symlink():
                gaps.append("original case directory is a symlink")
            elif directory.is_dir():
                for path in directory.rglob("*"):
                    if path.is_symlink() or not (path.is_file() or path.is_dir()):
                        gaps.append(f"unsafe original: {path.relative_to(results)}")
                    elif path.is_file():
                        members.append(path.relative_to(results).as_posix())
            automatic = {
                "released-baseline": ["prepared.json"],
                "installed-discovery": ["candidate.json"],
                "consumer-restoration": [
                    "consumer-cleanup.json",
                    "consumer-result.json",
                    "inventories.json",
                    "case-evidence.json",
                ],
            }.get(case, [])
            required = safe_required + automatic
            archive = results / f"evidence/{case}.tar"
            temporary = archive.with_suffix(".tar.partial")
            current["current_case"] = case
            persist()
            document = lib.stage_evidence_archive(
                temporary, results, members + automatic, required
            )
            size = temporary.stat().st_size
            if (
                size > lib.EVIDENCE_ARCHIVE_BYTES_BOUND
                or total + size > lib.EVIDENCE_TOTAL_BYTES_BOUND
            ):
                gaps.append("evidence exceeds the existing archive collection bounds")
            document["gaps"] = gaps
            pending_manifest = archive.with_suffix(".manifest.json.partial")
            lib.write_document(pending_manifest, document)
            current["publishing"] = {"case": case, **document}
            persist()
            temporary.replace(archive)
            pending_manifest.replace(archive.with_suffix(".manifest.json"))
            total += size
            current["archives"].append({"case": case, **document})
            current.pop("publishing", None)
            if gaps or document["missing_required"]:
                problems.append(f"{case}: original evidence is incomplete")
            persist()
    except BaseException as error:
        current["state"] = "error"
        current["problems"].append(f"{case}: {type(error).__name__}: {error}")
        temporary = results / f"evidence/{case}.tar.partial"
        current["partial_archive"] = {
            "path": temporary.relative_to(results).as_posix(),
            "bytes": temporary.stat().st_size if temporary.is_file() else None,
            "sha256": lib.sha256_file(temporary) if temporary.is_file() else None,
        }
        persist()
        raise
    current.pop("current_case", None)
    current.update(
        state="completed",
        ok=not problems,
        total_archive_bytes=total,
        case_index_sha256=lib.sha256_file(results / "case-evidence.json")
        if (results / "case-evidence.json").is_file()
        else None,
        bounds={
            "per_archive": lib.EVIDENCE_ARCHIVE_BYTES_BOUND,
            "total_archives": lib.EVIDENCE_TOTAL_BYTES_BOUND,
        },
    )
    persist()
    if invalid_inventory:
        result = {
            "schema": lib.RESULT_SCHEMA,
            "suite": "epic-squad",
            "outcome": "incomplete",
            "consumer_cleanup": "unverified",
            "candidate": context.inputs["candidate"],
            "evidence_staging": False,
            "functional_cases": "not assessed; native manual completion owns their verdict",
            "problem": "preserve the invalid cleanup history",
        }
        lib.write_document(results / "result.json", result)
        print(json.dumps(result))
        return lib.OUTCOME_EXITS["incomplete"]
    return lib.finish(
        "epic-squad",
        "pass" if current["ok"] else "incomplete",
        {
            "scope": "consumer restoration and original evidence staging only",
            "evidence_staging": current["ok"],
            "functional_cases": "not assessed; native manual completion owns their verdict",
        },
        consumer_cleanup="verified" if restored else "unverified",
        inputs=context.inputs,
    )
