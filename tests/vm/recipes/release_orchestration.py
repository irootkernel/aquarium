"""Explicit guest phases for release-role observations, never a workflow engine."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import recipe_lib as lib
import release_fixture as fixture

SUITE = "release-orchestration"
INVENTORY = "tests/vm/fixtures/release-orchestration/cases.json"
STARTUP_CRITERIA = (
    "baseline",
    "version-mode",
    "notes-scope",
    "outputs",
    "gates-order",
    "environment",
    "authority",
)


def cases(context: Any) -> dict:
    return json.loads((context.checkout / INVENTORY).read_text())["cases"]


def observation(
    context: Any, stage: str, suite: str, *, phase: str | None = None
) -> dict:
    import guest_main
    import podway_upgrade

    skills = guest_main.skill_identity_document(
        context, stage, candidate_profile="podway-candidate"
    )
    if skills.get("comparisons", {}).get("all_passed") is not True:
        raise lib.RecipeError("installed skill identities differ", "incomplete")
    return {
        "candidate_sha": context.inputs["candidate"]["git_sha"],
        "tools": podway_upgrade.observe_tools(context, stage),
        "state": podway_upgrade.restoration_state(skills),
        "skills": skills,
        "inventory": context.snapshot(
            suite,
            phase or ("before" if stage == "prior" else "candidate"),
            profile="stable" if stage == "prior" else "podway-candidate",
        ),
    }


def variant(context: Any, identifier: str, startup: bool = False) -> tuple[str, dict]:
    if startup and identifier == "release-startup":
        return identifier, {
            "id": identifier,
            "objective": "Installed release-handler plan readiness only; stop before settlement commit, pre-QA gates, QA or publication.",
            "order": "before",
            "baseline": "previous",
            "mode": "full",
        }
    for name, case in cases(context).items():
        for row in case["variants"]:
            if row["id"] == identifier:
                return name, row
    raise lib.RecipeError("select a declared release case variant", "incomplete")


def invoke(
    context: Any, world: Path, directory: Path, prompt: str, reply: str | None
) -> dict:
    """Keep original windows and refuse uncertain dispatch instead of replaying it."""
    import run_acceptance as driver

    lib.guard(context.root)
    lib.job_identity()
    if directory.is_relative_to(world) or world.is_relative_to(directory):
        raise fixture.FixtureError("native evidence must be separate from its world")
    writable = [directory, world / "repo/.git", world / "origin.git", world / "hosting"]
    for path in (world, world / "repo", *writable):
        boundary = context.root if path in (world, directory) else world
        if (
            not path.is_absolute()
            or path != path.resolve()
            or path == boundary
            or not path.is_relative_to(boundary)
            or not path.is_dir()
            or path.stat().st_uid != os.getuid()
        ):
            raise fixture.FixtureError(f"unsafe native fixture directory: {path}")
    env = fixture.native_environment(world)
    # Native Codex keeps the authorized guest login; Git remains process-isolated.
    env["HOME"] = str(context.home)
    env["XDG_CONFIG_HOME"] = os.environ.get(
        "XDG_CONFIG_HOME", str(context.home / ".config")
    )
    windows = directory / "operations"
    previous = sorted(windows.glob("*.invocation.json"))
    if len(list(windows.glob("*.jsonl"))) != len(previous) or len(
        list(windows.glob("*.request.json"))
    ) != len(previous):
        raise lib.RecipeError(
            "uncertain native window; reconcile original output", "incomplete"
        )
    if previous and reply is None:
        raise lib.RecipeError(
            "existing native case; capture/reconcile or reply to its same handle",
            "incomplete",
        )
    if reply is not None and not previous:
        raise lib.RecipeError("no existing native handle for reply", "incomplete")
    old = json.loads(previous[-1].read_text()) if previous else {}
    if previous:
        invocation_binding(directory)
    if previous and not old.get("thread_id"):
        raise lib.RecipeError(
            "unsettled native invocation; reconcile same operation", "incomplete"
        )
    windows.mkdir(parents=True, exist_ok=True)
    prefix = windows / f"{len(previous):03d}"
    argv = [
        context.codex,
        "exec",
        "--json",
        "--sandbox",
        "workspace-write",
    ]
    for path in writable:
        argv += ["--add-dir", str(path)]
    argv += [
        "--output-last-message",
        str(prefix) + ".last",
    ]
    argv += (
        ["resume", old["thread_id"], "-"]
        if reply is not None
        else ["-C", str(world / "repo"), "-"]
    )
    value = reply if reply is not None else prompt
    Path(str(prefix) + ".input").write_text(value)
    # Persist intent before launch; a missing receipt remains uncertain on recovery.
    fixture.write_once(
        Path(str(prefix) + ".request.json"),
        {
            "argv": argv,
            "input_sha256": fixture.digest(Path(str(prefix) + ".input")),
            "hosting_sha256": fixture.digest(world / "bin/gh"),
        },
    )
    with (
        Path(str(prefix) + ".jsonl").open("w") as stdout,
        Path(str(prefix) + ".stderr").open("w") as stderr,
    ):
        try:
            process = subprocess.Popen(
                argv,
                cwd=world / "repo",
                env=env,
                stdin=subprocess.PIPE,
                stdout=stdout,
                stderr=stderr,
                text=True,
            )
        except OSError as error:
            fixture.write_once(
                Path(str(prefix) + ".invocation.json"),
                {
                    "argv": argv,
                    "exit": None,
                    "thread_id": old.get("thread_id"),
                    "launch_error": str(error),
                },
            )
            raise lib.RecipeError(
                "native process did not launch", "incomplete"
            ) from error
        try:
            with process:
                process.communicate(value)
        finally:
            stdout.flush()
            handle = driver.thread_id(
                str(prefix) + ".jsonl", missing_ok=True
            ) or old.get("thread_id")
            receipt = {"argv": argv, "exit": process.returncode, "thread_id": handle}
            fixture.write_once(Path(str(prefix) + ".invocation.json"), receipt)
    if process.returncode or not handle:
        raise lib.RecipeError(
            "native invocation incomplete; retain original window and handle",
            "incomplete",
        )
    return receipt


def deliver_case(
    context: Any,
    results: Path,
    identifier: str,
    reply_file: Path | None = None,
    *,
    startup: bool = False,
) -> int:
    case, row = variant(context, identifier, startup)
    world = context.root / "release-worlds" / identifier
    directory = results / "originals" / case / identifier
    if not world.exists():
        world.parent.mkdir(exist_ok=True)
        fixture.seed(
            world,
            order=row.get("order", "before"),
            baseline=row.get("baseline", "previous"),
            mode=row.get("mode", "full"),
            source_root=context.checkout,
        )
    directory.mkdir(parents=True, exist_ok=True)
    prompt = (
        f"Invoke the normally discovered installed $aquarium:release-handler in {world / 'repo'}. "
        f"Observe this original scenario: {json.dumps(row)}. Read the original fixture instructions, "
        f"release policy and {context.checkout / INVENTORY}. Use actual native Executors and an independent "
        "report-only Evaluator, ordinary v3 reports and procedure: null. The authorized fixture operator "
        "supplies actual concrete decisions; this request does not approve unseen proposals, checks or Git effects. "
        "Use only the owned local Git origin and process-only hosting stand-in; never production hosting. "
        f"Save complete original assignments, role reports, actual decisions and command receipts under {directory}. "
        "Role final results must include complete JSON or a report path and its SHA-256 for public-result correlation. "
        "Each role report identifies assessed fixture files as target.files, mapping repository-relative paths to actual SHA-256 values. "
        f"For startup, preserve original due plan obligations under these criterion IDs: {json.dumps(STARTUP_CRITERIA)}. "
        "Keep the original QA verdicts, all four boundaries, actual grants and future gaps. "
        "Write startup-evidence.json using executor_agent, evaluator_agent, executor_assignment, "
        "evaluator_assignment, executor_result and evaluator_assessment, with original files inside this case directory. "
        "Do not submit nested Jobs; host-origin original managed evidence is supplied separately. "
        "Settle modifying descendants before replacement or final capture. "
        + (
            "STOP at plan readiness before settlement commit, pre-QA gates, QA or publication."
            if startup
            else "Stop at the scenario's actual authority boundary and report incomplete obligations truthfully."
        )
    )
    invoke(
        context,
        world,
        directory,
        prompt,
        reply_file.read_text() if reply_file else None,
    )
    return 0


def invocation_binding(directory: Path) -> tuple[dict, dict]:
    """Bind original windows, including partial windows that cannot be settled."""
    windows = directory / "operations"
    receipts = sorted(windows.glob("*.invocation.json"))
    prefixes = {path.name.removesuffix(".invocation.json") for path in receipts}
    if not receipts or any(
        {path.name.removesuffix(suffix) for path in windows.glob("*" + suffix)}
        != prefixes
        for suffix in (".request.json", ".jsonl", ".input", ".stderr")
    ):
        raise lib.RecipeError(
            "uncertain native window; retain original process evidence", "incomplete"
        )
    identities = {}
    for path in sorted(windows.iterdir()):
        identities[path.name] = fixture.digest(fixture.regular(path, windows))
    for path in receipts:
        prefix = path.name.removesuffix(".invocation.json")
        receipt = json.loads(path.read_text())
        request = json.loads((windows / (prefix + ".request.json")).read_text())
        if (
            request.get("argv") != receipt.get("argv")
            or request.get("input_sha256") != identities[prefix + ".input"]
            or type(receipt.get("exit")) is not int
            and not receipt.get("launch_error")
        ):
            raise lib.RecipeError(
                "original native request identity differs", "incomplete"
            )
    return {"latest": receipts[-1].name, "files": identities}, receipt


def verify_native_settlement(observed: dict, handle: str, world: Path) -> None:
    import run_acceptance as driver

    driver.verify_settlement(observed, allow_failed=True)
    root = observed["root"]
    actors = [root, *observed["descendants"]]
    identifiers = {actor["metadata"]["id"] for actor in actors}
    driver.require(
        root["metadata"]["id"] == handle
        and Path(root["metadata"]["cwd"]).resolve() == (world / "repo").resolve(),
        "settlement observed another native operation",
    )
    driver.require(
        len(identifiers) == len(actors)
        and all(
            actor["metadata"].get("parentThreadId") in identifiers
            for actor in observed["descendants"]
        ),
        "native descendant identity is uncertain",
    )
    for actor in actors:
        items = actor["items"] + [
            item for turn in actor["turns"] for item in turn.get("items", [])
        ]
        driver.require(
            all(
                item["agentThreadId"] in identifiers
                for item in items
                if item.get("type") == "subAgentActivity" and item["kind"] == "started"
            ),
            "native descendant observation is missing",
        )
        driver.require(
            actor["metadata"].get("status", {}).get("type") != "active"
            and not any(
                item.get("type") in {"commandExecution", "fileChange"}
                and item.get("status") == "inProgress"
                for item in items
            ),
            "native actors or pending effects remain uncertain",
        )


def invocation_handle(directory: Path) -> str | None:
    import run_acceptance as driver

    handles = set()
    for path in sorted((directory / "operations").glob("*.invocation.json")):
        receipt = json.loads(path.read_text())
        log = path.with_name(path.name.removesuffix(".invocation.json") + ".jsonl")
        handles.update(
            filter(
                None, [receipt.get("thread_id"), driver.thread_id(log, missing_ok=True)]
            )
        )
    if len(handles) > 1:
        raise lib.RecipeError("original native handle differs", "incomplete")
    return next(iter(handles), None)


def reconcile(context: Any, directory: Path, world: Path) -> tuple[dict, dict | None]:
    """Observe the same exited invocation without dispatch or role assessment."""
    import native_observation

    binding, receipt = invocation_binding(directory)
    number = len(list(directory.glob("native-*.request.json")))
    request_path = directory / f"native-{number:03d}.request.json"
    fixture.write_once(request_path, binding)
    handle = invocation_handle(directory)
    observed = None
    value = {
        "candidate_sha": context.inputs["candidate"]["git_sha"],
        "invocation": binding,
        "request": request_path.name,
        "workload_result": "unassessed",
        "settled": True,
    }
    if handle:
        observed = native_observation.collect(context.codex, world / "repo", handle)
        native_path = directory / f"native-{number:03d}.json"
        fixture.write_once(native_path, observed)
        verify_native_settlement(observed, handle, world)
        value.update(
            native_capture=native_path.name,
            native_sha256=fixture.digest(native_path),
            thread_id=handle,
        )
        if any(
            actor["turns"][-1]["status"] != "completed"
            for actor in [observed["root"], *observed["descendants"]]
        ):
            value["workload_result"] = "failed"
    elif not receipt.get("launch_error"):
        raise lib.RecipeError(
            "native no-start or settlement is unproved without a handle", "incomplete"
        )
    if receipt.get("exit") != 0:
        value["workload_result"] = "failed"
    if invocation_binding(directory)[0] != binding:
        raise lib.RecipeError("native window changed during observation", "incomplete")
    fixture.write_once(directory / f"settlement-{number:03d}.json", value)
    return value, observed


def require_settlement(directory: Path, world: Path, candidate: str) -> None:
    binding, receipt = invocation_binding(directory)
    requests = sorted(directory.glob("native-*.request.json"))
    if not requests:
        raise lib.RecipeError(
            "capture or reconcile latest native operation before restoration",
            "incomplete",
        )
    request = requests[-1]
    settlement = lib.read_json_safe(
        directory
        / request.name.replace("native-", "settlement-").replace(
            ".request.json", ".json"
        )
    )
    if (
        not settlement
        or settlement.get("settled") is not True
        or settlement.get("candidate_sha") != candidate
        or settlement.get("invocation") != binding
        or json.loads(request.read_text()) != binding
        or settlement.get("request") != request.name
    ):
        raise lib.RecipeError(
            "latest native settlement is missing or stale", "incomplete"
        )
    if settlement.get("native_capture"):
        if settlement.get("thread_id") != invocation_handle(directory):
            raise lib.RecipeError("native settlement handle differs", "incomplete")
        path = fixture.regular(directory / settlement["native_capture"], directory)
        if fixture.digest(path) != settlement["native_sha256"]:
            raise lib.RecipeError("native settlement evidence changed", "incomplete")
        verify_native_settlement(
            json.loads(path.read_text()), settlement["thread_id"], world
        )
    elif invocation_handle(directory) or not receipt.get("launch_error"):
        raise lib.RecipeError("no recorded native no-start proof", "incomplete")


def capture(
    context: Any, results: Path, identifier: str, *, startup: bool = False
) -> dict:
    import run_acceptance as driver

    case, _row = variant(context, identifier, startup)
    directory = results / "originals" / case / identifier
    settlement, observed = reconcile(
        context, directory, context.root / "release-worlds" / identifier
    )
    _binding, receipt = invocation_binding(directory)
    if receipt.get("exit") != 0 or not receipt.get("thread_id"):
        raise lib.RecipeError("original native operation is incomplete", "incomplete")
    world = context.root / "release-worlds" / identifier
    driver.verify_settlement(observed)
    evidence = json.loads((directory / "startup-evidence.json").read_text())
    actors = {}
    for role, key, schema in [
        ("executor", "executor_result", "aquarium.executor-handoff/v3"),
        ("evaluator", "evaluator_assessment", "aquarium.evaluator-assessment/v3"),
    ]:
        child = driver.correlate_child(observed, evidence[role + "_agent"])
        report_path = fixture.regular(Path(evidence[key]), directory)
        report = driver.returned_report(child, report_path, schema)
        files = report.get("target", {}).get("files")
        if not isinstance(files, dict) or not files:
            raise lib.RecipeError(
                "role report lacks assessed fixture file identities", "incomplete"
            )
        for name, expected in files.items():
            path = fixture.regular(world / "repo" / name, world / "repo")
            if fixture.digest(path) != str(expected).removeprefix("sha256:"):
                raise lib.RecipeError("assessed fixture bytes changed", "incomplete")
        assignment_path = fixture.regular(
            Path(evidence[role + "_assignment"]), directory
        )
        assignment = json.loads(assignment_path.read_text())
        if (
            assignment.get("schema") != "aquarium.assignment/v3"
            or assignment.get("role") != role
            or str(world / "repo") not in json.dumps(assignment.get("work"))
        ):
            raise lib.RecipeError(
                "original role assignment identity differs", "incomplete"
            )
        actors[role] = child["metadata"]["id"]
        if (
            startup
            and role == "evaluator"
            and report.get("checkpoint_result") != "pass"
        ):
            raise lib.RecipeError(
                "startup plan readiness is negative or unverified", "incomplete"
            )
        if startup and role == "evaluator":
            rows = {row["id"]: row for row in report.get("criteria", [])}
            if any(
                rows.get(name, {}).get("state") != "met"
                or not rows[name].get("source")
                or not rows[name].get("evidence")
                for name in STARTUP_CRITERIA
            ):
                raise lib.RecipeError(
                    "startup original due criterion coverage is incomplete",
                    "incomplete",
                )
    if actors["executor"] == actors["evaluator"]:
        raise lib.RecipeError(
            "Executor cannot supply independent assessment", "incomplete"
        )
    value = {
        "candidate_sha": context.inputs["candidate"]["git_sha"],
        "variant": identifier,
        "actors": actors,
        "native_capture": settlement["native_capture"],
        "invocation": settlement["invocation"],
        "state": "recorded",
        "semantic_result": "unverified; authorized fixture operator assesses original obligations",
    }
    fixture.write_once(
        directory / f"capture-{len(list(directory.glob('capture-*.json'))):03d}.json",
        value,
    )
    return value


def archive_pair_valid(archive: Path, manifest: Path) -> bool:
    document = lib.read_json_safe(manifest)
    return (
        archive.is_file()
        and not archive.is_symlink()
        and not manifest.is_symlink()
        and isinstance(document, dict)
        and document.get("schema") == lib.EVIDENCE_ARCHIVE_SCHEMA
        and document.get("sha256") == fixture.digest(archive)
    )


def recover_archive_pair(archive: Path) -> None:
    manifest = archive.with_suffix(".manifest.json")
    saved_archive = archive.with_name(archive.name + ".previous")
    saved_manifest = manifest.with_name(manifest.name + ".previous")
    if saved_archive.exists() or saved_manifest.exists():
        if archive_pair_valid(archive, manifest):
            saved_archive.unlink(missing_ok=True)
            saved_manifest.unlink(missing_ok=True)
            return
        if not archive_pair_valid(saved_archive, saved_manifest):
            raise lib.RecipeError(
                "preserve incomplete archive recovery files", "incomplete"
            )
        for source, target in ((saved_archive, archive), (saved_manifest, manifest)):
            recovery = target.with_name(target.name + ".recovery")
            shutil.copyfile(source, recovery)
            recovery.replace(target)
        if not archive_pair_valid(archive, manifest):
            raise lib.RecipeError("last complete archive recovery failed", "incomplete")
    elif not archive_pair_valid(archive, manifest) and (
        archive.exists() or manifest.exists()
    ):
        pending_manifest = archive.with_suffix(".manifest.json.partial")
        if not archive_pair_valid(archive, pending_manifest):
            raise lib.RecipeError(
                "preserve incomplete archive pair for reconciliation", "incomplete"
            )
        pending_manifest.replace(manifest)


def publish_archive_pair(archive: Path, pending: Path, pending_manifest: Path) -> None:
    manifest = archive.with_suffix(".manifest.json")
    saved_archive = archive.with_name(archive.name + ".previous")
    saved_manifest = manifest.with_name(manifest.name + ".previous")
    if archive_pair_valid(archive, manifest):
        shutil.copyfile(archive, saved_archive)
        shutil.copyfile(manifest, saved_manifest)
        if not archive_pair_valid(saved_archive, saved_manifest):
            raise lib.RecipeError(
                "archive preimage differs before publication", "incomplete"
            )
    try:
        pending.replace(archive)
        pending_manifest.replace(manifest)
    except BaseException:
        # Keep the preimage through both replacements; process death recovers on retry.
        if saved_archive.exists() or saved_manifest.exists():
            recover_archive_pair(archive)
        elif archive.exists() and not manifest.exists():
            # A first failed checkpoint still transports its available originals.
            shutil.copyfile(pending_manifest, manifest)
        raise
    recover_archive_pair(archive)


def stage(context: Any, results: Path) -> int:
    inventory = cases(context)
    index = lib.read_json_safe(results / "case-evidence.json")
    problems = []
    declared = index.get("cases", {}) if isinstance(index, dict) else {}
    if not isinstance(declared, dict):
        declared = {}
    candidate = context.inputs["candidate"]["git_sha"]
    if (
        not isinstance(index, dict)
        or index.get("candidate_sha") != candidate
        or set(declared) != set(inventory)
    ):
        problems.append("missing or wrong-candidate complete case inventory")
    cleanup = lib.read_json_safe(results / "consumer-result.json")
    current_cleanup = lib.read_json_safe(results / "consumer-cleanup.json")
    restored = (
        isinstance(cleanup, dict)
        and cleanup.get("consumer_cleanup") == "verified"
        and cleanup.get("candidate", {}).get("git_sha") == candidate
        and isinstance(current_cleanup, dict)
        and current_cleanup.get("consumer_cleanup") == "verified"
        and current_cleanup.get("candidate_sha") == candidate
    )
    if not restored:
        problems.append("actual consumer restoration receipt is missing")
    aggregate = lib.read_json_safe(results / "inventories.json")
    if not isinstance(aggregate, dict) or not isinstance(
        aggregate.get("inventories"), dict
    ):
        problems.append("preserve missing or invalid restoration inventory")
    old = lib.read_json_safe(results / "stage-evidence.json") or {}
    attempts = old.get("attempts", [])
    current = {
        "ok": False,
        "state": "in-progress",
        "archives": [],
        "problems": problems,
    }
    attempts = [*attempts, current]

    def persist() -> None:
        lib.write_document(
            results / "stage-evidence.json", {**current, "attempts": attempts}
        )

    persist()
    for name in inventory:
        archive = results / f"evidence/{name}.tar"
        try:
            recover_archive_pair(archive)
            directory = results / "originals" / name
            entry = declared.get(name, {})
            required = entry.get("required", []) if isinstance(entry, dict) else []
            if not isinstance(required, list) or not required:
                problems.append(
                    f"{name}: required original artifact closure is missing"
                )
                required = ["missing-original-closure"]
            for relative in required:
                if (
                    not isinstance(relative, str)
                    or Path(relative).is_absolute()
                    or Path(relative).as_posix() != relative
                    or ".." in Path(relative).parts
                ):
                    raise lib.RecipeError("unsafe original reference", "incomplete")
            members = []
            if directory.is_symlink() or (results / "originals").is_symlink():
                raise lib.RecipeError("unsafe original directory", "incomplete")
            for path in directory.rglob("*"):
                if path.is_symlink() or not (path.is_dir() or path.is_file()):
                    raise lib.RecipeError("unsafe original member", "incomplete")
                if path.is_file():
                    members.append(path.relative_to(results).as_posix())
            automatic = {
                "released-baseline": ["prepared.json"],
                "installed-discovery": ["candidate.json"],
                "consumer-restoration": [
                    "consumer-result.json",
                    "consumer-cleanup.json",
                    "inventories.json",
                    "case-evidence.json",
                ],
            }.get(name, [])
            needed = [f"originals/{name}/{item}" for item in required] + automatic
            pending = archive.with_suffix(".tar.partial")
            document = lib.stage_evidence_archive(
                pending, results, members + automatic, needed
            )
            pending_manifest = archive.with_suffix(".manifest.json.partial")
            lib.write_document(pending_manifest, document)
            publish_archive_pair(archive, pending, pending_manifest)
            current["archives"].append({"case": name, **document})
            if document["missing_required"]:
                problems.append(f"{name}: missing required originals")
        except (lib.RecipeError, OSError, ValueError) as error:
            problems.append(f"{name}: {error}")
            # An empty declared archive still carries explicit absence on first staging.
            archive = results / f"evidence/{name}.tar"
            if not archive.exists() and not any(
                path.exists()
                for path in (
                    archive.with_name(archive.name + ".previous"),
                    archive.with_suffix(".manifest.json.previous"),
                )
            ):
                lib.stage_evidence_archive(
                    archive, results, [], [f"originals/{name}/missing-originals"]
                )
        persist()
    current.update(
        ok=not problems,
        state="completed",
        case_index_sha256=fixture.digest(results / "case-evidence.json")
        if (results / "case-evidence.json").is_file()
        else None,
    )
    persist()
    return lib.finish(
        SUITE,
        "pass" if current["ok"] else "incomplete",
        {
            "scope": "original evidence staging only",
            "evidence_staging": current["ok"],
            "functional_cases": "not assessed",
        },
        consumer_cleanup="verified" if restored else "unverified",
        inputs=context.inputs,
        preserve_invalid_inventory=True,
    )


def run(context: Any, phase: str, identifier: str = "") -> int:
    lib.guard(context.root)
    lib.verify_sealed_inputs(context.root)
    results = lib.results_directory(SUITE)
    results.mkdir(parents=True, exist_ok=True)
    candidate = context.inputs["candidate"]["git_sha"]
    if phase in {"prepare", "candidate"}:
        if phase == "candidate" and not (results / "prepared.json").is_file():
            raise lib.RecipeError("capture released baseline first", "incomplete")
        document = observation(
            context, "prior" if phase == "prepare" else "candidate", SUITE
        )
        fixture.write_once(
            results / ("prepared.json" if phase == "prepare" else "candidate.json"),
            document,
        )
        if phase == "prepare":
            fixture.write_once(
                results / "case-evidence.json",
                {
                    "candidate_sha": candidate,
                    "cases": {
                        name: {"required": [], "observations": []}
                        for name in cases(context)
                    },
                },
            )
        return 0
    if phase in {"case", "reply", "capture", "reconcile"}:
        installed = lib.read_json_safe(results / "candidate.json")
        if not installed or installed.get("candidate_sha") != candidate:
            raise lib.RecipeError(
                "capture exact installed candidate before native cases", "incomplete"
            )
        if phase == "capture":
            capture(context, results, identifier)
            return 0
        if phase == "reconcile":
            case, _row = variant(context, identifier)
            reconcile(
                context,
                results / "originals" / case / identifier,
                context.root / "release-worlds" / identifier,
            )
            return 0
        reply = (
            Path(lib.context_value("AQUARIUM_VM_REPLY_FILE"))
            if phase == "reply"
            else None
        )
        return deliver_case(context, results, identifier, reply)
    if phase == "stage-evidence":
        return stage(context, results)
    if phase == "consumer-cleanup":
        aggregate = lib.read_json_safe(results / "inventories.json")
        if (
            not isinstance(aggregate, dict)
            or not isinstance(aggregate.get("inventories"), dict)
            or not isinstance(aggregate.get("failed_cleanup_observations", []), list)
        ):
            raise lib.RecipeError(
                "preserve invalid restoration inventory", "incomplete"
            )
        before = lib.read_json_safe(results / "prepared.json")
        if (
            not before
            or before.get("candidate_sha") != candidate
            or not (results / "candidate.json").is_file()
        ):
            raise lib.RecipeError(
                "missing original baseline/candidate identity", "incomplete"
            )
        for directory in (results / "originals").glob("*/*/operations"):
            require_settlement(
                directory.parent,
                context.root / "release-worlds" / directory.parent.name,
                candidate,
            )
        current = observation(context, "prior", SUITE, phase="post_cleanup")

        def codex_cache(scope: str, path: str) -> bool:
            return (
                scope == "codex-plugin-cache"
                and path.startswith(".codex/plugins/cache/")
                and path.removeprefix(".codex/plugins/cache/").split("/", 1)[0]
                != context.marketplace
            )

        all_changes = lib.postcondition_violations(
            before["inventory"], current["inventory"], lambda _scope, _path: False
        )
        problems = lib.postcondition_violations(
            before["inventory"], current["inventory"], codex_cache
        )
        if (
            current["state"] != before["state"]
            or current["tools"]["binary_sha256"] != before["tools"]["binary_sha256"]
            or current["tools"]["skill_tree_sha256"]
            != before["tools"]["skill_tree_sha256"]
        ):
            problems.append("restored consumer identities differ")
        document = {
            **current,
            "codex_owned_cache_observations": [
                change for change in all_changes if change not in set(problems)
            ],
            "violations": problems,
            "consumer_cleanup": "failed" if problems else "verified",
        }
        target = results / "consumer-cleanup.json"
        if problems:
            history = lib.read_json_safe(results / "inventories.json")
            if not isinstance(history, dict) or not isinstance(
                history.get("inventories"), dict
            ):
                raise lib.RecipeError(
                    "preserve invalid restoration inventory", "incomplete"
                )
            history.setdefault("failed_cleanup_observations", []).append(document)
            lib.write_document(results / "inventories.json", history)
        lib.write_document(target, document)
        code = lib.finish(
            SUITE,
            "fail" if problems else "pass",
            {"scope": "consumer restoration only"},
            consumer_cleanup=document["consumer_cleanup"],
            inputs=context.inputs,
            preserve_invalid_inventory=True,
        )
        if code == 0 and not (results / "consumer-result.json").exists():
            with (results / "consumer-result.json").open("xb") as stream:
                stream.write((results / "result.json").read_bytes())
        return code
    if phase == "complete-template":
        index = lib.read_json_safe(results / "case-evidence.json")
        staged = lib.read_json_safe(results / "stage-evidence.json")
        if (
            not isinstance(index, dict)
            or not isinstance(index.get("cases"), dict)
            or not isinstance(staged, dict)
        ):
            raise lib.RecipeError("invalid original case/staging index", "incomplete")
        staging_current = (
            staged.get("ok") is True
            and index.get("candidate_sha") == candidate
            and staged.get("case_index_sha256")
            == fixture.digest(results / "case-evidence.json")
        )
        rows = []
        for name, case in cases(context).items():
            entry = index["cases"].get(name, {})
            observations = (
                entry.get("observations", []) if isinstance(entry, dict) else []
            )
            if not isinstance(observations, list) or not all(
                isinstance(row, dict) for row in observations
            ):
                observations = []
            by_id = {row.get("variant"): row for row in observations}
            complete = (
                staging_current
                and len(by_id) == len(observations)
                and set(by_id) == {row["id"] for row in case["variants"]}
                and all(
                    by_id.get(row["id"], {}).get("status") == "pass"
                    and by_id[row["id"]].get("decision_reference")
                    and by_id[row["id"]].get("evidence_class")
                    in (
                        ["native-installed", "reused-with-applicability"]
                        if row.get("native_required")
                        else [
                            "native-installed",
                            "fixture-helper",
                            "reused-with-applicability",
                        ]
                    )
                    and (
                        by_id[row["id"]].get("applicability")
                        if by_id[row["id"]].get("evidence_class")
                        == "reused-with-applicability"
                        else True
                    )
                    for row in case["variants"]
                )
            )
            rows.append(
                {
                    "id": name,
                    "status": "pass" if complete else "unobserved",
                    "evidence_references": [
                        f"results/{SUITE}/evidence/{name}.tar",
                        f"results/{SUITE}/evidence/{name}.manifest.json",
                    ],
                }
            )
        lib.write_document(
            results / "manual-complete-template.json",
            {
                "schema": "haepari.manual-result/v1",
                "job_id": context.job["job_id"],
                "installation_id": "<actual installation>",
                "profile_id": context.profile("podway-candidate")["profile_id"],
                "profile_digest": context.profile_digest("podway-candidate"),
                "expected_revision": "<current native revision>",
                "observer": "<authorized fixture operator>",
                "scenarios": rows,
            },
        )
        return 0
    raise lib.RecipeError(f"unknown release-orchestration phase: {phase}", "incomplete")


def startup(context: Any, results: Path, run_root: Path) -> int:
    lib.guard(context.root)
    lib.verify_sealed_inputs(context.root)
    reply_file = os.environ.get("AQUARIUM_VM_REPLY_FILE")
    record = lib.read_json_safe(results / "release-startup.json") or {}
    try:
        if not record.get("invoked") or reply_file:
            deliver_case(
                context,
                run_root,
                "release-startup",
                Path(reply_file) if reply_file else None,
                startup=True,
            )
            record["invoked"] = True
        value = capture(context, run_root, "release-startup", startup=True)
        record.pop("problem", None)
        record.update(
            value, exit=0, outcome="pass", scope="plan-readiness startup only"
        )
    except (
        lib.RecipeError,
        fixture.FixtureError,
        RuntimeError,
        OSError,
        ValueError,
        KeyError,
    ) as error:
        record.update(
            exit=2,
            outcome="incomplete",
            problem=str(error),
            invoked=(
                run_root / "originals/release-startup/release-startup/operations"
            ).exists(),
        )
    from guest_main import _merge_phase_record

    _merge_phase_record(results, "release-startup.json", record)
    return record["exit"]
