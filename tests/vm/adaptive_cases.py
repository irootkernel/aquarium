"""Development scenarios for the existing manually authorized VM driver.

Only the guest driver invokes providers. Unit checks exercise these oracles with
synthetic observations and never claim installed-agent execution.
"""

import copy
import json
import re
import shlex
import shutil
from pathlib import Path

MANIFEST = Path(__file__).parent / "fixtures/adaptive/cases.json"
MEANINGS = {
    "original-source-audit": "Audit all original Epic sources and compound requirements; expose unmet or unverified product criteria truthfully.",
    "complete-result": "Deliver the complete original audit findings and assessment without inferring achievement from lifecycle or terminal names.",
    "no-product-change": "Preserve every original product-source byte; diagnosis and design do not authorize product implementation.",
    "original-design-requirements": "Deliver a coherent work-specific design tracing original requirements and constraints, including omitted and compound obligations.",
    "faithful-qa": "Preserve actual upstream QA operation outcome separately from its raw verdict, complete findings, local dispositions and original correction owners.",
    "approved-documents": "Apply only the exact user-approved current document proposal, or the explicitly approved reasoned no-change result; preserve approval currency.",
    "no-initialization": "Complete ordinary non-Git project planning without Podway discovery, source rendering, session effects or implicit Git initialization. Ordinary filesystem Git-presence inspection is permitted.",
    "original-symptom": "Retain original expected sample objects and observed intermittent null responses for sequences 0 through 5.",
    "isolated-evidence": "Test competing causal hypotheses in isolated experiments, preserve product bytes and distinguish established conclusions from incomplete/no-work results.",
}


def descriptors(gate):
    value = gate.read_json(MANIFEST)
    gate.require(
        value.get("schema") == "aquarium.vm-adaptive-cases/v1",
        "unsupported case inventory",
    )
    return value["cases"]


def seed(gate, request, root):
    cases = descriptors(gate)
    for name, case in cases.items():
        repository = root / name
        gate.require(
            not repository.exists(), f"preserve existing adaptive fixture: {repository}"
        )
        if case["fixture"] in {"greeting", "delivered-greeting"}:
            shutil.copytree(Path(__file__).parent / "fixtures/greeting", repository)
            if case["fixture"] == "delivered-greeting":
                # A completed ordinary fixture, rather than a fake passed audit.
                roadmap = repository / "docs/roadmap/README.md"
                lines = roadmap.read_text().splitlines(keepends=True)
                for index, line in enumerate(lines):
                    if line.startswith("**Status:**"):
                        lines[index] = "**Status:** `Completed`\n"
                    elif line.startswith("| TASK-"):
                        cells = line.split("|")
                        cells[4] = " Completed "
                        lines[index] = "|".join(cells)
                roadmap.write_text("".join(lines))
        else:
            repository.mkdir(parents=True)
            if case["fixture"] == "diagnosis":
                shutil.copyfile(
                    Path(__file__).parent / "fixtures/adaptive/diagnosis/sampler.py",
                    repository / "sampler.py",
                )
            (repository / "README.md").write_text(case["request"] + "\n")
        (repository / "VM-REQUIREMENTS.json").write_text(
            json.dumps(
                {
                    "request": case["request"],
                    "criteria": [
                        {"id": key, "text": gate.CRITERIA.get(key, MEANINGS.get(key))}
                        for key in case["criteria"]
                    ],
                },
                indent=2,
            )
            + "\n"
        )
        if case["fixture"] != "non-git":
            gate.git(repository, "init", "-q")
            gate.git(repository, "config", "user.name", "VM Fixture")
            gate.git(repository, "config", "user.email", "vm-fixture@example.invalid")
            gate.git(repository, "add", ".")
            gate.git(repository, "commit", "-qm", "[TEST] Establish adaptive fixture")
    return {
        "outcome": "prepared",
        "cases": list(cases),
        "next": "Use installed setup under its normal approvals for Git fixtures; leave adaptive-project without Git or Podway.",
    }


# Only runtime/cache directories are excluded, never arbitrary Git-ignored product files.
IMAGE_EXCLUDES = (
    (".git",),
    (".venv",),
    (".pytest_cache",),
    (".ruff_cache",),
    (".podway", "runtime"),
    (".podway", "procedures", ".local"),
    (".podway", "procedures", ".candidates"),
    (".gaori", "runs"),
)


def original_image(gate, repository):
    image = {}
    tracked = set()
    if (repository / ".git").exists():
        tracked = set(gate.git(repository, "ls-files", "-z").split("\0"))
    for path in repository.rglob("*"):
        relative = path.relative_to(repository)
        if str(relative) not in tracked and (
            "__pycache__" in relative.parts
            or any(relative.parts[: len(prefix)] == prefix for prefix in IMAGE_EXCLUDES)
        ):
            continue
        gate.require(
            not path.is_symlink(),
            "product image contains an unsupported symlink",
            "fail",
        )
        if path.is_file():
            image[str(relative)] = gate.sha256(path)
    return image


def prerequisites(gate, request, case, installed):
    """Use the installed inspector for only selected upstream leaves; no repair."""
    leaves = case["leaves"]
    if not leaves:
        return {"upstream": "not-applicable", "clipboard": "not-applicable"}
    script = installed / "skills/dev-setup-global/scripts/inspect_global_tools.py"
    result = gate.command(
        [request["tools"]["python"], "-B", script, "--component", "ouroboros"],
        check=False,
    )
    gate.require(
        result.returncode == 0, "selected Ouroboros prerequisite inspection unavailable"
    )
    value = json.loads(result.stdout)

    # The current installed inspector owns home/package/registration semantics.
    def readiness(node):
        if isinstance(node, dict):
            if "current_home_readiness" in node:
                return node["current_home_readiness"]
            for child in node.values():
                found = readiness(child)
                if found is not None:
                    return found
        if isinstance(node, list):
            for child in node:
                found = readiness(child)
                if found is not None:
                    return found
        return None

    current = readiness(value)
    gate.require(
        current == "configured"
        or isinstance(current, dict)
        and current.get("status") == "configured",
        "selected current-home Ouroboros prerequisites are incomplete",
    )
    if "pm" in leaves:
        consent = request.get("clipboard_authority", {})
        gate.require(
            consent.get("source") == "user"
            and consent.get("replace") is True
            and consent.get("reference"),
            "PM needs its actual separate clipboard replacement authority",
        )
    return {
        "upstream": value,
        "leaves": leaves,
        "live_runtime": "must be established by the actual selected leaf before its provider operation",
        "clipboard": request.get("clipboard_authority")
        if "pm" in leaves
        else "not-applicable",
    }


def artifact(gate, directory, path):
    path = Path(path)
    gate.require(
        path.is_absolute() and path.resolve().is_relative_to(directory.resolve()),
        "case artifact escaped its own capture directory",
        "fail",
    )
    gate.require(
        path.is_file() and not path.is_symlink(), "missing or unsafe case artifact"
    )
    return path


def reports(gate, observation, evidence, directory, repository, case):
    """Bind real role results to exact current bytes and original due criteria."""
    actors, targets, native_nodes, deliveries = {}, {}, {}, {}
    roles = ["judge"] if case["family"] == "validation" else ["worker", "judge"]
    for role in roles:
        child = gate.correlate_child(observation, evidence[role + "_agent"])
        assignment = gate.read_json(
            artifact(gate, directory, evidence[role + "_assignment"])
        )
        gate.require(
            assignment.get("schema") == "aquarium.assignment/v2"
            and assignment.get("role") == role,
            "missing original assigned role",
        )
        gate.require(
            str(repository) in json.dumps(assignment["work"]),
            "role repository differs",
            "fail",
        )
        gate.require(
            all(
                key in json.dumps(assignment["success_criteria"])
                for key in case["criteria"]
            ),
            "role omits original case criteria",
        )
        filename = role + ("_assessment" if role == "judge" else "_result")
        report = gate.returned_report(
            child,
            artifact(gate, directory, evidence[filename]),
            "aquarium.judge-assessment/v2"
            if role == "judge"
            else "aquarium.worker-handoff/v2",
        )
        image = report.get("target", {}).get("files")
        gate.require(
            isinstance(image, dict) and image,
            "report lacks exact assessed case target bytes",
        )
        for path, digest in image.items():
            target = repository / path
            gate.require(
                not Path(path).is_absolute()
                and ".." not in Path(path).parts
                and target.is_file()
                and not target.is_symlink()
                and gate.sha256(target) == digest,
                "assessed target differs from current case bytes",
                "fail",
            )
        targets[role] = image
        deliveries[role] = {
            "path": str(artifact(gate, directory, evidence[filename])),
            "sha256": gate.sha256(artifact(gate, directory, evidence[filename])),
        }
        if case["fixture"] != "non-git":
            native_nodes[role] = assignment.get("procedure", {}).get("node")
            gate.require(
                isinstance(native_nodes[role], str),
                "actual role assignment lacks its mapped native operation",
            )
        if role == "worker":
            gate.require(
                report.get("results")
                and any(
                    item.get("type") in {"commandExecution", "fileChange"}
                    for item in child["items"]
                ),
                "no actual Worker work/check observation",
            )
        else:
            rows = report.get("criteria", [])
            mapped = {row["id"]: row for row in rows}
            gate.require(len(mapped) == len(rows), "duplicate Judge criterion")
            gate.require(
                report.get("checkpoint_result") == "pass", "due checkpoint did not pass"
            )
            for key in case["criteria"]:
                row = mapped.get(key, {})
                gate.require(
                    row.get("state", row.get("status")) == "met"
                    and row.get("source")
                    and row.get("evidence"),
                    "original due case criterion remains unestablished: " + key,
                )
        actors[role] = child["metadata"]["id"]
    gate.require(
        len(set(actors.values())) == len(actors), "Worker cannot assess itself", "fail"
    )
    if "worker" in targets:
        gate.require(
            targets["worker"] == targets["judge"],
            "Worker/Judge target mismatch",
            "fail",
        )
    return {
        "actors": actors,
        "files": targets["judge"],
        "nodes": native_nodes,
        "deliveries": deliveries,
    }


def user_approval(gate, observation, approval):
    """A saved approval label needs the actual operator turn, not an agent assertion."""
    gate.require(
        isinstance(approval, dict)
        and approval.get("source") == "user"
        and approval.get("decision") == "approved",
        "actual exact application approval is missing",
    )
    proposal = approval.get("proposal")
    gate.require(
        isinstance(proposal, dict)
        and isinstance(proposal.get("diff"), str)
        and isinstance(proposal.get("targets"), dict),
        "exact application proposal missing",
    )
    token = approval.get("reference")
    gate.require(
        isinstance(token, str) and token, "actual approval turn reference missing"
    )
    turns = observation["root"]["turns"]
    messages = [
        item
        for turn in turns
        for item in turn.get("items", [])
        if item.get("type") == "userMessage"
    ]

    def text_parts(message):
        values = []
        for part in message.get("content", []):
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                values.append(part["text"])
        if isinstance(message.get("text"), str):
            values.append(message["text"])
        return "\n".join(values)

    accepted = False
    for message in messages:
        try:
            actual = json.loads(text_parts(message))
        except (ValueError, TypeError):
            continue
        if (
            isinstance(actual, dict)
            and actual.get("schema") == "aquarium.vm-document-decision/v1"
            and actual.get("decision") == "approved"
            and actual.get("reference") == token
            and actual.get("proposal") == proposal
        ):
            accepted = True
    gate.require(
        accepted, "exact approved decision is not present in the actual user delivery"
    )
    return proposal


LEAF_TOOLS = {
    "ouroboros_interview": "interview",
    "ouroboros_pm_interview": "pm",
    "ouroboros_generate_seed": "seed",
    "ouroboros_qa": "qa",
}
EXECUTION_TOOLS = {"ouroboros_execute_seed", "ouroboros_start_execute_seed"}


def public_operations(item):
    """Read actual public calls; inventories and narrative mentions are not calls."""
    if item.get("type") == "mcpToolCall" and item.get("server") == "ouroboros":
        tool = item.get("tool", "").split("__")[-1]
        return [LEAF_TOOLS.get(tool, "execute" if tool in EXECUTION_TOOLS else None)]
    if item.get("type") != "commandExecution":
        return []
    try:
        lexer = shlex.shlex(
            item.get("command", ""), posix=True, punctuation_chars=";&|\n"
        )
        lexer.whitespace_split = True
        words = list(lexer)
    except ValueError:
        return []
    if (
        words
        and Path(words[0]).name in {"sh", "bash", "zsh"}
        and len(words) == 3
        and words[1] in {"-c", "-lc"}
    ):
        return public_operations({"type": "commandExecution", "command": words[2]})
    result, group = [], []
    for token in [*words, ";"]:
        if token and all(character in ";&|\n" for character in token):
            if group and group[0] == "env":
                group.pop(0)
            while group and "=" in group[0] and not group[0].startswith("-"):
                group.pop(0)
            if len(group) >= 2 and Path(group[0]).name == "ooo":
                result.append(
                    group[1]
                    if group[1] in {"interview", "pm", "seed", "qa"}
                    else "execute"
                    if group[1]
                    in {"run", "execute", "execute_seed", "start_execute_seed"}
                    else None
                )
            group = []
        else:
            group.append(token)
    return result


def qa_verdict(gate, raw):
    """Read the delivered QA verdict field, not verdict words in its findings."""
    try:
        value = json.loads(raw)
    except ValueError:
        value = None
    if isinstance(value, dict) and isinstance(value.get("verdict"), str):
        verdicts = [value["verdict"].upper()]
    else:
        verdicts = [
            value.upper()
            for value in re.findall(
                r"^Verdict:\s*(PASS|REVISE|FAIL)\s*$", raw, re.MULTILINE | re.IGNORECASE
            )
        ]
        scores = re.findall(
            r"^Score:[^\n]*\[(PASS|REVISE|FAIL)\]\s*$",
            raw,
            re.MULTILINE | re.IGNORECASE,
        )
        gate.require(
            len(verdicts) == 1
            and all(value.upper() == verdicts[0] for value in scores),
            "QA verdict is absent or contradictory",
        )
    gate.require(
        len(verdicts) == 1 and verdicts[0] in {"PASS", "REVISE", "FAIL"},
        "QA raw verdict is not established",
    )
    return verdicts[0]


def leaf_delivery(gate, observation, evidence, directory, leaves, request):
    actors = [observation["root"], *observation["descendants"]]
    all_items = [item for actor in actors for item in actor["items"]]
    actual = [leaf for item in all_items for leaf in public_operations(item)]
    gate.require(
        "execute" not in actual, "excluded upstream execution occurred", "fail"
    )
    if "pm" in actual:
        authority = request.get("clipboard_authority", {})
        gate.require(
            authority.get("source") == "user"
            and authority.get("replace") is True
            and authority.get("reference"),
            "actual PM use lacks separate clipboard authority",
        )
    used = evidence.get("used_leaves", [])
    gate.require(
        isinstance(used, list)
        and len(set(used)) == len(used)
        and set(leaves) <= set(used) <= set(leaves)
        and {leaf for leaf in actual if leaf} <= set(used),
        "actual selected leaf delivery is incomplete or changed scope",
    )
    deliveries = evidence.get("leaf_results", {})
    result, operations = {}, set()
    for leaf in used:
        row = deliveries.get(leaf, {})
        path = artifact(gate, directory, row.get("path", ""))
        gate.require(
            row.get("sha256") == gate.sha256(path),
            "actual upstream result bytes changed",
            "fail",
        )
        operation = row.get("operation_item_id")
        matching = [item for item in all_items if item.get("id") == operation]
        gate.require(
            len(matching) == 1, "upstream result lacks its actual public operation"
        )
        gate.require(
            operation not in operations,
            "one public operation cannot supply different leaves",
        )
        operations.add(operation)
        item = matching[0]
        if item.get("type") == "mcpToolCall":
            gate.require(
                public_operations(item) == [leaf]
                and item.get("status") == "completed"
                and not item.get("error"),
                "upstream MCP delivery incomplete or wrong leaf",
            )
        elif item.get("type") == "commandExecution":
            gate.require(
                item.get("exitCode") == 0
                and item.get("status") == "completed"
                and public_operations(item) == [leaf],
                "upstream native delivery incomplete or wrong leaf",
            )
        else:
            gate.require(False, "upstream delivery is not an actual native operation")
        # Result linkage is delivery evidence, never agent authentication.
        gate.require(
            str(path) in json.dumps(item)
            or json.dumps(path.read_text(), ensure_ascii=False)[1:-1]
            in json.dumps(item, ensure_ascii=False),
            "actual upstream operation does not deliver the recorded result",
        )
        result[leaf] = {
            "path": str(path),
            "sha256": row["sha256"],
            "operation_item_id": operation,
        }
    quality = evidence.get("quality", {})
    if "qa" in used:
        raw = artifact(gate, directory, deliveries["qa"]["path"]).read_text()
        gate.require(
            quality.get("raw_verdict") == qa_verdict(gate, raw),
            "raw QA verdict is absent from original delivery",
        )
    return {
        "used": used,
        "results": result,
        "runtime": "actual selected native operations observed; prior configuration alone is insufficient",
    }


def oracle(gate, request, repository, case, evidence, observation, before):
    kind = case["oracle"]
    if kind == "uppercase":
        return gate.oracle(request["tools"]["python"], repository)
    after = original_image(gate, repository)
    if kind == "unchanged":
        gate.require(
            after == before, "case changed product bytes outside its authority", "fail"
        )
        return gate.oracle(request["tools"]["python"], repository, uppercase=False)
    proposal = user_approval(gate, observation, evidence.get("application_approval"))
    expected = {}
    for name, image in proposal["targets"].items():
        gate.require(
            not Path(name).is_absolute()
            and ".." not in Path(name).parts
            and Path(name).suffix.lower() == ".md"
            and isinstance(image, dict)
            and image.get("before") == before.get(name)
            and image.get("after") == after.get(name)
            and image.get("before") != image.get("after"),
            "approved document before/after image differs",
            "fail",
        )
        expected[name] = {"before": image.get("before"), "after": image.get("after")}
    changed = {
        name: {"before": before.get(name), "after": after.get(name)}
        for name in before.keys() | after.keys()
        if before.get(name) != after.get(name)
    }
    if proposal.get("no_change") is True:
        gate.require(
            proposal["diff"] == ""
            and not proposal["targets"]
            and not changed
            and isinstance(proposal.get("reason"), str)
            and proposal["reason"].strip(),
            "no-change needs an unchanged image and actual reason",
            "fail",
        )
    else:
        gate.require(
            bool(expected) and changed == expected,
            "case changed bytes beyond exact approved targets",
            "fail",
        )
    if kind == "non-git-documents":
        gate.require(
            not (repository / ".git").exists()
            and not (repository / ".podway").exists(),
            "non-Git project initialized workflow state",
            "fail",
        )
        return {"documents": proposal["targets"], "git": "absent", "podway": "absent"}
    if kind == "diagnosis":
        actual = []
        for index in range(6):
            result = gate.command(
                [request["tools"]["python"], repository / "sampler.py", str(index)]
            )
            actual.append(json.loads(result.stdout))
        gate.require(
            [row is None for row in actual] == [False, False, True, False, False, True],
            "original intermittent symptom changed",
            "fail",
        )
        quality = evidence.get("quality", {})
        gate.require(
            quality.get("operation_outcome") == "pass"
            and quality.get("raw_verdict") in {"PASS", "REVISE", "FAIL"},
            "QA delivery/raw verdict distinction missing",
        )
        experiments = evidence.get("experiments", [])
        gate.require(
            experiments
            and all(
                row.get("command") and row.get("result") and row.get("hypothesis")
                for row in experiments
            ),
            "isolated diagnosis evidence missing",
        )
        return {
            "symptom": actual,
            "product": before,
            "documents": proposal["targets"],
            "experiments": experiments,
        }
    quality = evidence.get("quality", {})
    gate.require(
        quality.get("operation_outcome") == "pass"
        and quality.get("raw_verdict") in {"PASS", "REVISE", "FAIL"},
        "faithful raw QA evidence missing",
    )
    return {"documents": proposal["targets"], "product": before, "qa": quality}


def checkpoint(
    gate, request, repository, directory, case, evidence, installed, roles=None
):
    if case["fixture"] == "non-git":
        gate.require(
            not (repository / ".git").exists()
            and not (repository / ".podway").exists(),
            "non-Git path mutated native state",
            "fail",
        )
        return {
            "status": "not-applicable",
            "reason": "non-Git new-project; no native discovery performed",
        }
    qualification_path = artifact(gate, directory, evidence["qualification"])
    qualification = gate.read_json(qualification_path)
    assignment = qualification["assignment"]
    roots = assignment["authority"]["preparation"]["roots"]
    argv = [
        request["tools"]["python"],
        "-B",
        installed / "shared/manage_adaptive_procedure.py",
        "context",
        "--repository",
        repository,
        "--entrypoint",
        case["entrypoint"],
        "--qualification",
        qualification_path,
        "--podway",
        request["tools"]["podway"],
    ]
    for root in roots:
        argv += ["--root", root]
    result = gate.command(argv, cwd=repository, check=False)
    context = json.loads(result.stdout)
    gate.require(
        result.returncode == 0
        and context.get("status")
        in {
            "dispatch-ready",
            "primary-owned",
            "approval-required",
            "verified-applied",
            "terminal-resolved",
        },
        "adaptive exact context is not established",
    )
    binding_path = Path(context["binding_path"])
    gate.require(
        binding_path.resolve().is_relative_to(repository.resolve())
        and not binding_path.is_symlink(),
        "binding escaped case",
        "fail",
    )
    binding = gate.read_json(binding_path)
    gate.require(
        binding["family"] == case["family"]
        and case["entrypoint"] in binding["entrypoints"],
        "wrong adaptive family",
        "fail",
    )
    source = Path(context["source_path"])
    gate.require(
        source.resolve().is_relative_to(repository.resolve())
        and gate.sha256(source) == binding["procedure"]["source_sha256"],
        "adopted source drift",
        "fail",
    )
    actual = gate.observe(request, repository)
    gate.require(
        actual["status"]["procedure"] == context["procedure"]["procedure"],
        "native tuple changed during semantic checkpoint",
        "fail",
    )
    node = actual["guidance"]["node"]["graph_node_id"]
    gate.require(node in binding["nodes"], "current native node has no exact binding")
    declaration = binding["nodes"][node]
    gate.require(
        declaration["role"] == context.get("role", declaration["role"]),
        "current mapped role differs",
        "fail",
    )
    import yaml

    document = yaml.safe_load(source.read_text())
    canonical_name = {
        "task": "task",
        "goal": "goal",
        "validation": "validation",
        "design": "design",
        "diagnosis": "war-room",
    }[case["family"]]
    canonical = yaml.safe_load(
        (
            installed
            / "assets/podway/procedures"
            / ("aquarium-" + canonical_name + "-v2.yaml")
        ).read_text()
    )
    gate.require(
        structure(document) != structure(canonical),
        "adaptive case has no producer/evidence/Decision structure difference from the canonical regression",
    )
    selected = actual.get("guidance", {}).get("readback", [])
    gate.require(
        selected and any(row.get("items") for row in selected),
        "checkpoint has no selected native work/assessment evidence",
    )
    gate.require(roles is not None, "actual role/evidence linkage is missing")
    for role, placement in roles["nodes"].items():
        gate.require(
            placement in binding["nodes"]
            and binding["nodes"][placement]["role"] == role,
            "actual assigned role differs from its native binding",
            "fail",
        )
    consumed = []
    judge_delivered = False
    workspace = {
        row.get("preconditions", {}).get("workspace_uuid")
        for row in actual.get("mutation_templates", [])
    }
    workspace.discard(None)
    gate.require(len(workspace) == 1, "native evidence read lacks a workspace fence")
    workspace = workspace.pop()
    for row in selected:
        producer = row["source_graph_node_id"]
        gate.require(
            producer in binding["nodes"],
            "native evidence producer missing from binding",
        )
        for item in row.get("items", []):
            digest = item.get("value_digest")
            gate.require(
                isinstance(digest, str) and digest.startswith("sha256:"),
                "selected native evidence has no exact value",
            )
            argv = [
                request["tools"]["podway"],
                "--worktree",
                repository,
                "--json",
                "evidence",
                "read",
                "--source",
                producer,
                "--item",
                item["item_id"],
                "--if-workspace-uuid",
                workspace,
                "--if-session-id",
                actual["status"]["session"]["id"],
            ]
            response = gate.command(argv, cwd=repository)
            envelope = json.loads(response.stdout)
            value = envelope.get("result", {})
            gate.require(
                envelope.get("schema") == "podway.output/v4"
                and envelope.get("command") == "evidence.read"
                and value.get("schema") == "podway.evidence-read-result/v1"
                and value.get("truncated") is False
                and value.get("next_page_token") is None
                and value.get("value_digest") == digest,
                "selected native evidence is unavailable/truncated or changed",
            )
            data = value["page"]["data"]
            serialized = json.dumps(data, sort_keys=True)
            if producer == roles["nodes"]["judge"]:
                report = gate.read_json(roles["deliveries"]["judge"]["path"])
                judge_delivered = (
                    judge_delivered
                    or roles["deliveries"]["judge"]["sha256"] in serialized
                    or data == report
                    or isinstance(data, str)
                    and data == json.dumps(report, sort_keys=True)
                )
            consumed.append(
                {
                    "node": producer,
                    "item": item["item_id"],
                    "digest": digest,
                    "read": value,
                }
            )
    gate.require(
        judge_delivered,
        "actual returned Judge report is not selected by the native checkpoint",
    )
    gate.require(
        any(
            binding["nodes"][row["node"]]["role"] in {"worker", "judge"}
            for row in consumed
        ),
        "no actual mapped work/assessment producer at checkpoint",
    )
    return {
        "context": context,
        "native": actual,
        "selected_evidence": consumed,
        "binding_sha256": gate.sha256(binding_path),
        "source_sha256": gate.sha256(source),
    }


def structure(document):
    """Compare grammar-owned structure, discarding names and narrative text."""
    nodes = {row["id"]: row for row in document["graph"]["nodes"]}
    order, queue = [], [document["graph"]["entry"]]
    while queue:
        current = queue.pop(0)
        if current in order:
            continue
        order.append(current)
        node = nodes[current]
        if node.get("next"):
            queue.append(node["next"])
        definition = document["node_definitions"][node["use"]]
        queue.extend(
            node["routes"][option["id"]]["to"]
            for option in definition.get("options", [])
            if option["id"] in node.get("routes", {})
        )
    order.extend(sorted(set(nodes) - set(order)))
    index = {node: position for position, node in enumerate(order)}
    result = []
    for identifier in order:
        node = nodes[identifier]
        definition = document["node_definitions"][node["use"]]
        item_positions = {
            item["id"]: position
            for position, item in enumerate(definition.get("items", []))
        }
        items = [
            {
                key: value
                for key, value in item.items()
                if key not in {"id", "prompt", "description", "help", "required_when"}
            }
            for item in definition.get("items", [])
        ]
        evidence = []
        for row in node.get("evidence_from", []):
            producer = nodes[row["node"]]
            producer_items = document["node_definitions"][producer["use"]].get(
                "items", []
            )
            positions = {
                item["id"]: position for position, item in enumerate(producer_items)
            }
            evidence.append(
                (
                    index[row["node"]],
                    row.get("required", False),
                    [positions[item] for item in row["items"]]
                    if "items" in row
                    else "all",
                )
            )
        options = []
        assessment = definition.get("assessment", {})
        for option in definition.get("options", []):
            guards = []
            for guard in option.get("guards", []):
                endpoint = guard["evidence"]
                producer = nodes[endpoint["node"]]
                positions = {
                    item["id"]: position
                    for position, item in enumerate(
                        document["node_definitions"][producer["use"]].get("items", [])
                    )
                }
                guards.append(
                    {
                        **{
                            key: value
                            for key, value in guard.items()
                            if key != "evidence"
                        },
                        "evidence": [
                            index[endpoint["node"]],
                            positions[endpoint["item"]],
                        ],
                    }
                )
            route = node.get("routes", {}).get(option["id"])
            options.append(
                {
                    "guards": guards,
                    "outcome": assessment.get("outcomes", {}).get(option["id"]),
                    "route": [index[route["to"]], route["effect"]] if route else None,
                }
            )
        conditions = [
            [
                {**condition, "item": item_positions[condition["item"]]}
                for condition in item.get("required_when", [])
            ]
            for item in definition.get("items", [])
        ]
        result.append(
            {
                "type": definition["type"],
                "items": items,
                "conditions": conditions,
                "evidence": evidence,
                "options": options,
                "next": index.get(node.get("next")),
                "terminal": node.get("terminal", False),
                "assessment": {
                    key: value for key, value in assessment.items() if key != "outcomes"
                }
                if assessment
                else None,
            }
        )
    return result


def run(gate, request, root):
    from native_observation import ObservationError, collect

    candidate = gate.verify_candidate(request["candidate"])
    installed = Path(request["candidate"]["installed_plugin_root"])
    gate.require(
        Path(__file__).resolve()
        == (
            Path(request["candidate"]["source_root"]) / "tests/vm/adaptive_cases.py"
        ).resolve(),
        "mixed candidate development helper",
        "fail",
    )
    combination = gate.versions(request, installed)
    marketplace = Path(
        request["candidate"].get(
            "marketplace_root", request["candidate"]["artifact_root"]
        )
    )
    gate.require(
        gate.files(marketplace) == gate.files(request["candidate"]["artifact_root"]),
        "registered marketplace differs from candidate",
        "fail",
    )
    registration = gate.installed_plugin(request, marketplace, installed)
    cases = descriptors(gate)
    chosen = request.get("development_cases", list(cases))
    gate.require(
        isinstance(chosen, list)
        and chosen
        and len(set(chosen)) == len(chosen)
        and set(chosen) <= cases.keys(),
        "unknown/duplicate development case",
    )
    outcomes = []
    for name in chosen:
        case = copy.deepcopy(cases[name])
        # PM is optional but any actual selected PM use requires its own authority.
        selected_leaves = request.get("case_leaves", {}).get(name, case["leaves"])
        gate.require(
            set(case["leaves"])
            <= set(selected_leaves)
            <= {"interview", "pm", "seed", "qa"},
            "selected case leaves omit required upstream work",
        )
        case["leaves"] = selected_leaves
        repository, directory = root / name, root / (name + "-capture")
        gate.require(
            repository.is_dir() and not repository.is_symlink(),
            "development fixture missing",
        )
        gate.require(
            not directory.is_symlink(), "case capture directory is a symlink", "fail"
        )
        directory.mkdir(exist_ok=True)
        state = root / "adaptive-state" / name
        if list((root / "operations" / name).glob("*.invocation.json")):
            gate.require(
                (state / "candidate-binding.json").is_file()
                and (state / "original-product.json").is_file(),
                "existing invocation lacks its independent original driver basis; preserve its handle",
            )
        state.mkdir(parents=True, exist_ok=True)
        gate.write_once_json(
            state / "candidate-binding.json",
            {
                "candidate": candidate,
                "combination": combination,
                "installed_plugin": registration,
                "case": case,
                "manifest_sha256": gate.sha256(MANIFEST),
                "authority": request["authority"],
            },
        )
        before_path = state / "original-product.json"
        if not before_path.exists():
            gate.write_once_json(before_path, original_image(gate, repository))
        before = gate.read_json(before_path)
        readiness = prerequisites(gate, request, case, installed)
        gate.discover(request, repository, installed, skills=(case["entrypoint"],))
        evidence_file = directory / "semantic-evidence.json"
        prompt = f"""Invoke the normally discovered installed $aquarium:{case["entrypoint"]} {case["request"]} in {repository}.
Original criteria: {json.dumps(case["criteria"])}; full original source: VM-REQUIREMENTS.json and existing repository sources.
Select an adequate existing adaptive definition or prepare a genuinely different work/evidence/Decision structure when needed; do not merely rename canonical nodes or bypass due suitability. Do not choose the fixed canonical regression as this adaptive case. For non-Git new-project use the ordinary no-Podway branch before any native/source discovery.
Use the authorized operator {request["authority"]["observer"]} and scope reference {request["authority"]["reference"]}. Preserve existing review, independent Judge, exact-diff approval and no-implementation boundaries. Ask for actual decisions; do not infer acceptance. Selected upstream leaves: {case["leaves"]}. Establish their actual live readiness before provider use; missing prerequisites remain incomplete. PM may replace the clipboard only with separately supplied explicit authority. No commit, publication or installation is authorized by this case.
Deliver the first complete due semantic result and independent assessment, preserving future gaps. Stop at a mapped native consumer selecting actual original work and Judge evidence, or at the approved document application boundary; do not falsely complete the whole workflow.
Save original role assignments, actual returned v2 reports and current ordinary qualification under {directory}; reports identify exact current assessed files as target.files (relative path to SHA-256 map). Write {evidence_file} with worker_agent,judge_agent,worker_assignment,judge_assignment,worker_result,judge_assessment,qualification paths. A cold validation with no corrective Worker uses only Judge fields. Include used_leaves and leaf_results keyed by leaf with exact path/sha256 and operation_item_id of its actual completed native public MCP/CLI call; keep complete original upstream output. Include faithful quality operation_outcome/raw_verdict, diagnosis experiments (actual hypothesis/command/result), and exact application_approval for document cases. For this VM capture, the actual operator application reply is one JSON object with schema aquarium.vm-document-decision/v1, decision approved, its reference and complete proposal. A rejected/request-changes reply or quoted proposal is not approval; do not synthesize it. Each actual role final result includes its complete report or exact path+SHA. Settle all descendants before returning. These capture files alone do not prove native execution; the driver reads public results, exact current bundles/native evidence and application oracles independently."""
        identifier = gate.invoke(request, root, name, prompt, repository=repository)
        try:
            observation = collect(request["tools"]["codex"], repository, identifier)
        except ObservationError as error:
            raise gate.GateError(str(error)) from error
        gate.write_json(directory / "native-observation.json", observation)
        gate.require(
            evidence_file.is_file(),
            f"case awaits actual operator reply/evidence; resume existing {identifier}",
        )
        evidence = gate.read_json(evidence_file)
        actors = reports(gate, observation, evidence, directory, repository, case)
        upstream = leaf_delivery(
            gate, observation, evidence, directory, case["leaves"], request
        )
        application = oracle(
            gate, request, repository, case, evidence, observation, before
        )
        semantic = checkpoint(
            gate,
            request,
            repository,
            directory,
            case,
            evidence,
            installed,
            roles=actors,
        )
        gate.verify_settlement(observation)
        outcome = {
            "id": name,
            "outcome": "pass",
            "entrypoint": case["entrypoint"],
            "actors": actors,
            "oracle": application,
            "checkpoint": semantic,
            "prerequisites": readiness,
            "upstream": upstream,
        }
        gate.write_json(directory / "result.json", outcome)
        outcomes.append(outcome)
    gate.require(
        gate.versions(request, installed) == combination,
        "installed tool combination changed during cases",
        "fail",
    )
    return {
        "schema": "aquarium.vm-adaptive-result/v1",
        "candidate": candidate,
        "combination": combination,
        "cases": outcomes,
        "outcome": "pass",
    }
