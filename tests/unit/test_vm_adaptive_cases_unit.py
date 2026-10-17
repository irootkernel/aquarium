"""Objective guest-driver oracles; synthetic public deliveries are rejection controls."""

import copy
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests/vm"))
import adaptive_cases as cases
import run_acceptance as gate


def test_seven_entrypoints_seed_without_implicit_non_git_initialization(tmp_path):
    result = cases.seed(gate, {}, tmp_path)
    assert len(result["cases"]) == 7
    assert {row["entrypoint"] for row in cases.descriptors(gate).values()} == {
        "task-handler",
        "epic-handler",
        "epic-validator",
        "new-feature",
        "new-project",
        "refactor",
        "war-room",
    }
    plain = tmp_path / "adaptive-project"
    assert not (plain / ".git").exists() and not (plain / ".podway").exists()
    assert (tmp_path / "adaptive-diagnosis/sampler.py").is_file()
    assert (tmp_path / "adaptive-task/.git").is_dir()
    with pytest.raises(gate.GateError):
        cases.seed(gate, {}, tmp_path)


def test_intermittent_fixture_has_reproducible_original_counterexamples(tmp_path):
    path = ROOT / "tests/vm/fixtures/adaptive/diagnosis/sampler.py"
    values = [
        json.loads(subprocess.check_output([sys.executable, "-B", path, str(index)]))
        for index in range(6)
    ]
    assert [row is None for row in values] == [False, False, True, False, False, True]


def test_structure_discards_rename_but_retains_producer_evidence_decision_changes():
    source = ROOT / "plugins/aquarium/assets/podway/procedures/aquarium-task-v2.yaml"
    original = yaml.safe_load(source.read_text())
    renamed = copy.deepcopy(original)
    for node in renamed["graph"]["nodes"]:
        node["id"] = "x-" + node["id"]
        if "next" in node:
            node["next"] = "x-" + node["next"]
        for row in node.get("evidence_from", []):
            row["node"] = "x-" + row["node"]
        for row in node.get("routes", {}).values():
            row["to"] = "x-" + row["to"]
    renamed["graph"]["entry"] = "x-" + renamed["graph"]["entry"]
    for definition in renamed["node_definitions"].values():
        for option in definition.get("options", []):
            for guard in option.get("guards", []):
                guard["evidence"]["node"] = "x-" + guard["evidence"]["node"]
    assert cases.structure(renamed) == cases.structure(original)
    node = next(row for row in renamed["graph"]["nodes"] if row.get("evidence_from"))
    node["evidence_from"].pop()
    assert cases.structure(renamed) != cases.structure(original)


def test_approval_requires_actual_user_delivery_with_exact_proposal():
    proposal = {
        "diff": "fixture exact change",
        "targets": {"docs/result.md": {"before": None, "after": "sha256:" + "1" * 64}},
    }
    approval = {
        "source": "user",
        "decision": "approved",
        "proposal": proposal,
        "reference": "operator-decision-1",
    }
    observation = {
        "root": {
            "turns": [
                {
                    "items": [
                        {
                            "type": "agentMessage",
                            "text": json.dumps(
                                {
                                    "schema": "aquarium.vm-document-decision/v1",
                                    "decision": "approved",
                                    "reference": approval["reference"],
                                    "proposal": proposal,
                                }
                            ),
                        }
                    ]
                }
            ]
        }
    }
    with pytest.raises(gate.GateError):
        cases.user_approval(gate, observation, approval)
    observation["root"]["turns"][0]["items"][0]["type"] = "userMessage"
    assert cases.user_approval(gate, observation, approval) == proposal
    actual = observation["root"]["turns"][0]["items"][0]
    accepted_text = actual["text"]
    for rejected in ("rejected", "request-changes"):
        payload = json.loads(accepted_text)
        payload["decision"] = rejected
        actual["text"] = json.dumps(payload)
        with pytest.raises(gate.GateError):
            cases.user_approval(gate, observation, approval)
    actual["text"] = "The following was rejected: " + accepted_text
    with pytest.raises(gate.GateError):
        cases.user_approval(gate, observation, approval)
    actual["text"] = accepted_text
    changed = copy.deepcopy(approval)
    changed["proposal"]["diff"] += " changed"
    with pytest.raises(gate.GateError):
        cases.user_approval(gate, observation, changed)


@pytest.mark.parametrize("ready", [None, "degraded", "not_configured"])
def test_selected_upstream_missing_remains_incomplete(monkeypatch, tmp_path, ready):
    monkeypatch.setattr(
        gate,
        "command",
        lambda *a, **k: SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {"tools": {"ouroboros": {"current_home_readiness": ready}}}
            ),
        ),
    )
    with pytest.raises(gate.GateError) as caught:
        cases.prerequisites(
            gate, {"tools": {"python": sys.executable}}, {"leaves": ["qa"]}, tmp_path
        )
    assert caught.value.outcome == "incomplete"


def test_pm_authority_is_conditional_and_current_home_not_other_home(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        gate,
        "command",
        lambda *a, **k: SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "tools": {
                        "ouroboros": {
                            "current_home_readiness": "configured",
                            "other_home": "degraded",
                        }
                    }
                }
            ),
        ),
    )
    request = {"tools": {"python": sys.executable}}
    assert (
        cases.prerequisites(gate, request, {"leaves": ["qa"]}, tmp_path)["clipboard"]
        == "not-applicable"
    )
    with pytest.raises(gate.GateError):
        cases.prerequisites(gate, request, {"leaves": ["pm", "qa"]}, tmp_path)
    request["clipboard_authority"] = {
        "source": "user",
        "replace": True,
        "reference": "synthetic VM operator scope",
    }
    assert (
        cases.prerequisites(gate, request, {"leaves": ["pm", "qa"]}, tmp_path)[
            "clipboard"
        ]
        == request["clipboard_authority"]
    )


def test_non_git_checkpoint_never_calls_native_or_imports_runtime(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        gate, "command", lambda *a, **k: pytest.fail("no command on non-Git path")
    )
    monkeypatch.setattr(
        gate, "observe", lambda *a, **k: pytest.fail("no Podway discovery")
    )
    assert (
        cases.checkpoint(
            gate, {}, tmp_path, tmp_path, {"fixture": "non-git"}, {}, tmp_path
        )["status"]
        == "not-applicable"
    )
    (tmp_path / ".podway").mkdir()
    with pytest.raises(gate.GateError):
        cases.checkpoint(
            gate, {}, tmp_path, tmp_path, {"fixture": "non-git"}, {}, tmp_path
        )


def test_artifact_must_stay_inside_current_case(tmp_path):
    capture = tmp_path / "capture"
    capture.mkdir()
    report = tmp_path / "outside.json"
    report.write_text("{}")
    with pytest.raises(gate.GateError):
        cases.artifact(gate, capture, report)
    link = capture / "link.json"
    link.symlink_to(report)
    with pytest.raises(gate.GateError):
        cases.artifact(gate, capture, link)


@pytest.fixture
def checkpoint_case(tmp_path, monkeypatch):
    sys.path.insert(0, str(ROOT / "tests/unit"))
    from test_adaptive_preparation_unit import authored

    repository, directory = tmp_path / "repository", tmp_path / "capture"
    repository.mkdir()
    directory.mkdir()
    document, binding = authored()
    source = repository / "local/procedure.yaml"
    source.parent.mkdir()
    source.write_text(yaml.safe_dump(document))
    binding["procedure"] = {
        "id": "foreign-valid-source",
        "version": "1",
        "digest": "sha256:" + "5" * 64,
        "source_sha256": gate.sha256(source),
    }
    binding_path = source.parent / "binding.json"
    binding_path.write_text(json.dumps(binding))
    qualifier = directory / "qualification.json"
    qualifier.write_text(
        json.dumps({"assignment": {"authority": {"preparation": {"roots": ["local"]}}}})
    )
    report = directory / "judge.json"
    report.write_text(
        json.dumps(
            {
                "schema": "aquarium.judge-assessment/v2",
                "target": {"files": {"product.py": "sha256:original"}},
            }
        )
    )
    roles = {
        "nodes": {"worker": "deliver", "judge": "assess"},
        "deliveries": {"judge": {"path": str(report), "sha256": gate.sha256(report)}},
    }
    current = {
        "status": {
            "procedure": binding["procedure"],
            "session": {"id": "actual-session", "lifecycle": "running"},
        },
        "guidance": {
            "node": {"graph_node_id": "outcome"},
            "readback": [
                {
                    "source_graph_node_id": "assess",
                    "items": [
                        {"item_id": "assessment", "value_digest": "sha256:" + "6" * 64}
                    ],
                }
            ],
        },
        "mutation_templates": [
            {"preconditions": {"workspace_uuid": "actual-workspace"}}
        ],
    }
    context = {
        "status": "primary-owned",
        "source_path": str(source),
        "binding_path": str(binding_path),
        "procedure": current["status"],
        "role": "orchestrator",
    }
    native = {
        "schema": "podway.output/v4",
        "command": "evidence.read",
        "result": {
            "schema": "podway.evidence-read-result/v1",
            "truncated": False,
            "next_page_token": None,
            "value_digest": "sha256:" + "6" * 64,
            "page": {"data": {"sha256": gate.sha256(report)}},
        },
    }
    calls = []

    def command(argv, **kwargs):
        calls.append([str(value) for value in argv])
        return SimpleNamespace(
            returncode=0, stdout=json.dumps(native if "evidence" in argv else context)
        )

    monkeypatch.setattr(gate, "command", command)
    monkeypatch.setattr(gate, "observe", lambda *_: copy.deepcopy(current))
    return (
        repository,
        directory,
        {"tools": {"python": sys.executable, "podway": "/explicit/native"}},
        {"fixture": "greeting", "family": "task", "entrypoint": "task-handler"},
        {"qualification": str(qualifier)},
        ROOT / "plugins/aquarium",
        roles,
        native,
        current,
        binding_path,
        calls,
    )


def test_adaptive_checkpoint_accepts_actual_distinct_graph_and_reads_selected_judge(
    checkpoint_case,
):
    (
        repo,
        directory,
        request,
        case,
        evidence,
        installed,
        roles,
        _native,
        _current,
        _binding,
        calls,
    ) = checkpoint_case
    result = cases.checkpoint(
        gate, request, repo, directory, case, evidence, installed, roles=roles
    )
    assert result["selected_evidence"][0]["node"] == "assess"
    assert calls[-1][-4:] == [
        "--if-workspace-uuid",
        "actual-workspace",
        "--if-session-id",
        "actual-session",
    ]


@pytest.mark.parametrize(
    "damage",
    ["wrong-family", "missing-producer", "wrong-report", "truncated", "wrong-role"],
)
def test_adaptive_checkpoint_rejects_broken_native_or_report_connections(
    checkpoint_case, damage
):
    (
        repo,
        directory,
        request,
        case,
        evidence,
        installed,
        roles,
        native,
        current,
        binding_path,
        _calls,
    ) = checkpoint_case
    if damage == "wrong-family":
        binding = json.loads(binding_path.read_text())
        binding["family"] = "design"
        binding_path.write_text(json.dumps(binding))
    elif damage == "missing-producer":
        current["guidance"]["readback"][0]["source_graph_node_id"] = "missing"
    elif damage == "wrong-report":
        native["result"]["page"]["data"] = {"sha256": "sha256:" + "0" * 64}
    elif damage == "truncated":
        native["result"]["truncated"] = True
    else:
        roles["nodes"]["judge"] = "deliver"
    with pytest.raises(gate.GateError):
        cases.checkpoint(
            gate, request, repo, directory, case, evidence, installed, roles=roles
        )


def test_leaf_results_need_the_actual_completed_operation_and_conditional_pm_authority(
    tmp_path,
):
    path = tmp_path / "raw-qa.txt"
    path.write_text("Score: 0.9 / 1.00 [PASS]\nVerdict: pass\nOriginal QA output\n")
    item = {
        "id": "qa-operation",
        "type": "mcpToolCall",
        "server": "ouroboros",
        "tool": "ouroboros_qa",
        "status": "completed",
        "result": {"path": str(path)},
    }
    observation = {"root": {"items": [item]}, "descendants": []}
    evidence = {
        "used_leaves": ["qa"],
        "leaf_results": {
            "qa": {
                "path": str(path),
                "sha256": gate.sha256(path),
                "operation_item_id": "qa-operation",
            }
        },
        "quality": {"operation_outcome": "pass", "raw_verdict": "PASS"},
    }
    assert cases.leaf_delivery(gate, observation, evidence, tmp_path, ["qa"], {})[
        "used"
    ] == ["qa"]
    item["status"] = "failed"
    with pytest.raises(gate.GateError):
        cases.leaf_delivery(gate, observation, evidence, tmp_path, ["qa"], {})
    item["status"] = "completed"
    evidence["leaf_results"]["qa"]["sha256"] = "sha256:" + "0" * 64
    with pytest.raises(gate.GateError):
        cases.leaf_delivery(gate, observation, evidence, tmp_path, ["qa"], {})


def aliased_decisions(document, selected=None):
    """Rename options, routes and assessment keys while reversing lexical order."""
    document = copy.deepcopy(document)
    mappings = {}
    for key, definition in document["node_definitions"].items():
        identifiers = sorted(option["id"] for option in definition.get("options", []))
        aliases = {
            identifier: "alias-" + chr(122 - index)
            if selected is None or key in selected
            else identifier
            for index, identifier in enumerate(identifiers)
        }
        mappings[key] = aliases
        for option in definition.get("options", []):
            option["id"] = aliases[option["id"]]
        if "assessment" in definition:
            definition["assessment"]["outcomes"] = {
                aliases[key]: value
                for key, value in definition["assessment"]["outcomes"].items()
            }
    for node in document["graph"]["nodes"]:
        if "routes" in node:
            node["routes"] = {
                mappings[node["use"]][key]: value
                for key, value in node["routes"].items()
            }
    return document


def branched_structure():
    sys.path.insert(0, str(ROOT / "tests/unit"))
    from test_adaptive_preparation_unit import authored

    return authored(performance=True)[0]


def test_decision_and_assessment_aliases_with_changed_lexical_route_order_are_equivalent():
    original = branched_structure()
    renamed = aliased_decisions(original)
    assert cases.structure(renamed) == cases.structure(original)
    # Reversing serialization order alone cannot supply a structural difference.
    for node in renamed["graph"]["nodes"]:
        if "routes" in node:
            node["routes"] = dict(reversed(list(node["routes"].items())))
    assert cases.structure(renamed) == cases.structure(original)


@pytest.mark.parametrize(
    "change", ["native-outcome", "guard", "route", "producer", "evidence"]
)
def test_aliased_graph_still_distinguishes_actual_behavior(change):
    original = branched_structure()
    changed = aliased_decisions(original)
    definitions = changed["node_definitions"]
    if change == "native-outcome":
        outcome = definitions["outcome"]["assessment"]["outcomes"]
        outcome[next(key for key, value in outcome.items() if value == "achieved")] = (
            "not_achieved"
        )
    elif change == "guard":
        definitions["classify"]["options"][0]["guards"][0]["at_least"] = 102
    elif change == "route":
        node = next(row for row in changed["graph"]["nodes"] if row["id"] == "classify")
        first = definitions["classify"]["options"][0]["id"]
        node["routes"][first] = {"to": "measure", "effect": "rework"}
    elif change == "producer":
        definitions["measure"]["items"][0]["maximum"] = 99999
    else:
        node = next(row for row in changed["graph"]["nodes"] if row["id"] == "assess")
        node["evidence_from"].pop()
    assert cases.structure(changed) != cases.structure(original)


@pytest.mark.parametrize("family", ["task", "goal", "validation", "design", "war-room"])
def test_canonical_option_aliases_preserve_actual_assessment_outcomes(family):
    source = (
        ROOT
        / "plugins/aquarium/assets/podway/procedures"
        / ("aquarium-" + family + "-v2.yaml")
    )
    original = yaml.safe_load(source.read_text())
    assert cases.structure(aliased_decisions(original)) == cases.structure(original)


@pytest.mark.parametrize("selected", [{"classify"}, {"outcome"}])
def test_route_traversal_and_assessment_alias_facets_are_independently_equivalent(
    selected,
):
    original = branched_structure()
    renamed = aliased_decisions(original, selected=selected)
    if selected == {"classify"}:
        before = next(
            row for row in original["graph"]["nodes"] if row["id"] == "classify"
        )["routes"]
        after = next(
            row for row in renamed["graph"]["nodes"] if row["id"] == "classify"
        )["routes"]
        assert [route["to"] for _, route in sorted(before.items())] == list(
            reversed([route["to"] for _, route in sorted(after.items())])
        )
        assert len({route["to"] for route in before.values()}) == 2
    assert cases.structure(renamed) == cases.structure(original)


def test_completed_seed_preserves_lifecycle_definitions_and_exact_status_cells(
    tmp_path,
):
    cases.seed(gate, {}, tmp_path)
    original = (ROOT / "tests/vm/fixtures/greeting/docs/roadmap/README.md").read_text()
    seeded = (tmp_path / "adaptive-validation/docs/roadmap/README.md").read_text()
    assert seeded.split("## EPIC-001:")[0] == original.split("## EPIC-001:")[0]
    assert "**Status:** `Completed`" in seeded
    task_rows = [
        line.split("|") for line in seeded.splitlines() if line.startswith("| TASK-")
    ]
    assert len(task_rows) == 2 and all(
        row[4].strip() == "Completed" for row in task_rows
    )
    untouched = (tmp_path / "adaptive-task/docs/roadmap/README.md").read_text()
    assert untouched == original


@pytest.mark.parametrize(
    "filename",
    [
        "aquarium-task-v2.yaml",
        "aquarium-goal-v2.yaml",
        "aquarium-validation-v2.yaml",
        "aquarium-design-v2.yaml",
        "aquarium-war-room-v2.yaml",
    ],
)
def test_narrative_item_help_and_aliases_do_not_establish_adaptation(filename):
    document = yaml.safe_load(
        (ROOT / "plugins/aquarium/assets/podway/procedures" / filename).read_text()
    )
    changed = copy.deepcopy(document)
    for definition in changed["node_definitions"].values():
        for item in definition.get("items", []):
            item["help"] = (
                "A different explanation with exactly the same operation and constraints."
            )
    assert cases.structure(changed) == cases.structure(document)
    # Reuse the settled namespace-only transformation with changed narrative.
    for node in changed["graph"]["nodes"]:
        node["id"] = "alias-" + node["id"]
        if node.get("next"):
            node["next"] = "alias-" + node["next"]
        for selector in node.get("evidence_from", []):
            selector["node"] = "alias-" + selector["node"]
        for route in node.get("routes", {}).values():
            route["to"] = "alias-" + route["to"]
    changed["graph"]["entry"] = "alias-" + changed["graph"]["entry"]
    for definition in changed["node_definitions"].values():
        for option in definition.get("options", []):
            for guard in option.get("guards", []):
                guard["evidence"]["node"] = "alias-" + guard["evidence"]["node"]
    assert cases.structure(changed) == cases.structure(document)


def approved(observation, proposal):
    approval = {
        "source": "user",
        "decision": "approved",
        "reference": "fixture-user",
        "proposal": proposal,
    }
    observation["root"]["turns"] = [
        {
            "items": [
                {
                    "type": "userMessage",
                    "text": json.dumps(
                        {
                            "schema": "aquarium.vm-document-decision/v1",
                            "decision": "approved",
                            "reference": "fixture-user",
                            "proposal": proposal,
                        }
                    ),
                }
            ]
        }
    ]
    return approval


@pytest.fixture
def document_case(tmp_path):
    repository = tmp_path / "product"
    repository.mkdir()
    (repository / "nested").mkdir()
    (repository / "nested/product.txt").write_text("preserve original")
    (repository / "docs").mkdir()
    (repository / "docs/result.md").write_text("original document")
    before = cases.original_image(gate, repository)
    (repository / "docs/result.md").write_text("approved document")
    proposal = {
        "diff": "exact fixture change",
        "targets": {
            "docs/result.md": {
                "before": before["docs/result.md"],
                "after": gate.sha256(repository / "docs/result.md"),
            }
        },
    }
    observation = {"root": {}}
    evidence = {
        "application_approval": approved(observation, proposal),
        "quality": {"operation_outcome": "pass", "raw_verdict": "REVISE"},
    }
    return repository, before, proposal, observation, evidence


def test_document_oracle_accepts_only_entire_approved_diff(document_case):
    repository, before, _, observation, evidence = document_case
    result = cases.oracle(
        gate, {}, repository, {"oracle": "documents"}, evidence, observation, before
    )
    assert result["qa"]["raw_verdict"] == "REVISE"
    assert result["product"] == before


@pytest.mark.parametrize(
    "mutation",
    [
        "nested",
        "other-doc",
        "add",
        "delete",
        "before",
        "after",
        "no-change",
        "no-reason",
    ],
)
def test_document_oracle_rejects_unapproved_complete_image_changes(
    document_case, mutation
):
    repository, before, proposal, observation, evidence = document_case
    if mutation == "nested":
        (repository / "nested/product.txt").write_text("unapproved implementation")
    elif mutation == "other-doc":
        (repository / "docs/other.md").write_text("unapproved")
    elif mutation == "add":
        (repository / "new.toml").write_text("unapproved")
    elif mutation == "delete":
        (repository / "nested/product.txt").unlink()
    elif mutation in {"before", "after"}:
        proposal["targets"]["docs/result.md"][mutation] = "sha256:" + "0" * 64
    else:
        proposal.update(targets={}, no_change=True)
        if mutation == "no-change":
            proposal["reason"] = "synthetic no-change assertion"
        else:
            (repository / "docs/result.md").write_text("original document")
    evidence["application_approval"] = approved(observation, proposal)
    with pytest.raises(gate.GateError) as caught:
        cases.oracle(
            gate, {}, repository, {"oracle": "documents"}, evidence, observation, before
        )
    assert caught.value.outcome == "fail"


def test_no_change_requires_actual_empty_recursive_diff(document_case):
    repository, before, _, observation, evidence = document_case
    (repository / "docs/result.md").write_text("original document")
    proposal = {
        "diff": "",
        "targets": {},
        "no_change": True,
        "reason": "Existing document covers the exact fixture requirements",
    }
    evidence["application_approval"] = approved(observation, proposal)
    assert (
        cases.oracle(
            gate, {}, repository, {"oracle": "documents"}, evidence, observation, before
        )["documents"]
        == {}
    )


@pytest.mark.parametrize("initialize", [".git", ".podway", "src/implementation.js"])
def test_non_git_oracle_rejects_initialization_and_nested_implementation(
    tmp_path, initialize
):
    before = cases.original_image(gate, tmp_path)
    proposal = {
        "diff": "",
        "targets": {},
        "no_change": True,
        "reason": "ordinary fixture no-change",
    }
    observation = {"root": {}}
    evidence = {"application_approval": approved(observation, proposal)}
    target = tmp_path / initialize
    target.parent.mkdir(parents=True, exist_ok=True)
    if initialize.startswith("."):
        target.mkdir()
    else:
        target.write_text("implementation")
    with pytest.raises(gate.GateError):
        cases.oracle(
            gate,
            {},
            tmp_path,
            {"oracle": "non-git-documents"},
            evidence,
            observation,
            before,
        )


def test_recursive_image_preserves_tracked_managed_and_ignored_product_files(tmp_path):
    gate.git(tmp_path, "init", "-q")
    managed = tmp_path / ".podway/procedures/known.yaml"
    managed.parent.mkdir(parents=True)
    managed.write_text("managed original")
    (tmp_path / ".gitignore").write_text("ignored-product.txt\n.podway/runtime/\n")
    (tmp_path / "ignored-product.txt").write_text("product")
    runtime = tmp_path / ".podway/runtime/state"
    runtime.parent.mkdir()
    runtime.write_text("live state")
    gate.git(tmp_path, "add", ".podway/procedures/known.yaml")
    image = cases.original_image(gate, tmp_path)
    assert ".podway/procedures/known.yaml" in image and "ignored-product.txt" in image
    assert ".podway/runtime/state" not in image
    gate.git(tmp_path, "add", "-f", ".podway/runtime/state")
    assert ".podway/runtime/state" in cases.original_image(gate, tmp_path)


def leaf_case(tmp_path, tool="ouroboros_qa", leaf="qa"):
    path = tmp_path / "upstream.txt"
    path.write_text(
        "Score: 0.7 / 1.00 [REVISE]\nVerdict: revise\nPASS requires correcting the complete findings.\n"
    )
    item = {
        "id": "actual-call",
        "type": "mcpToolCall",
        "server": "ouroboros",
        "tool": tool,
        "status": "completed",
        "result": {"content": [{"text": path.read_text()}]},
    }
    observation = {"root": {"items": [item]}, "descendants": []}
    evidence = {
        "used_leaves": [leaf],
        "leaf_results": {
            leaf: {
                "path": str(path),
                "sha256": gate.sha256(path),
                "operation_item_id": item["id"],
            }
        },
        "quality": {"operation_outcome": "pass", "raw_verdict": "REVISE"},
    }
    return path, item, observation, evidence


@pytest.mark.parametrize("verdict", ["REVISE", "FAIL"])
def test_actual_qa_raw_verdict_is_distinct_from_successful_operation(tmp_path, verdict):
    path, item, observation, evidence = leaf_case(tmp_path)
    path.write_text(
        f"Score: 0.5 / 1.00 [{verdict}]\nVerdict: {verdict.lower()}\nPASS requires correcting the findings.\n"
    )
    item["result"]["content"][0]["text"] = path.read_text()
    evidence["leaf_results"]["qa"]["sha256"] = gate.sha256(path)
    evidence["quality"]["raw_verdict"] = verdict
    assert cases.leaf_delivery(gate, observation, evidence, tmp_path, ["qa"], {})[
        "used"
    ] == ["qa"]
    evidence["quality"]["raw_verdict"] = "PASS"
    with pytest.raises(gate.GateError):
        cases.leaf_delivery(gate, observation, evidence, tmp_path, ["qa"], {})


@pytest.mark.parametrize(
    "tool,leaf",
    [
        ("ouroboros_pm_interview", "interview"),
        ("ouroboros_execute_seed", "seed"),
        ("ouroboros_start_execute_seed", "seed"),
    ],
)
def test_wrong_or_excluded_actual_operation_cannot_supply_selected_leaf(
    tmp_path, tool, leaf
):
    _, _, observation, evidence = leaf_case(tmp_path, tool, leaf)
    with pytest.raises(gate.GateError):
        cases.leaf_delivery(gate, observation, evidence, tmp_path, [leaf], {})


def test_undeclared_actual_pm_requires_clipboard_authority_and_delivery(tmp_path):
    _, _, observation, evidence = leaf_case(tmp_path)
    observation["root"]["items"].append(
        {
            "id": "pm-call",
            "type": "mcpToolCall",
            "server": "ouroboros",
            "tool": "ouroboros_pm_interview",
            "status": "completed",
        }
    )
    with pytest.raises(gate.GateError):
        cases.leaf_delivery(gate, observation, evidence, tmp_path, ["qa"], {})
    request = {
        "clipboard_authority": {
            "source": "user",
            "replace": True,
            "reference": "fixture authority",
        }
    }
    with pytest.raises(gate.GateError):
        cases.leaf_delivery(gate, observation, evidence, tmp_path, ["qa"], request)


@pytest.mark.parametrize(
    "command,expected",
    [
        ("ooo seed input.yaml", ["seed"]),
        ("/tools/ooo pm goal", ["pm"]),
        ("/bin/zsh -lc 'ooo qa doc.md'", ["qa"]),
        ("echo 'ooo seed'", []),
        ("ooo execute_seed seed.yaml", ["execute"]),
        ("ooo run seed.yaml", ["execute"]),
    ],
)
def test_public_cli_operations_use_executable_and_exact_subcommand(command, expected):
    assert (
        cases.public_operations({"type": "commandExecution", "command": command})
        == expected
    )


@pytest.mark.parametrize(
    "operation,expected_schema",
    [
        ("development", "aquarium.vm-adaptive-result/v1"),
        ("run", "aquarium.vm-acceptance-result/v1"),
    ],
)
def test_development_and_release_result_contracts_remain_separate(
    tmp_path, monkeypatch, capsys, operation, expected_schema
):
    monkeypatch.setattr(
        gate,
        "load_request",
        lambda *_: ({"suite": "adaptive-development"}, tmp_path, {}),
    )
    monkeypatch.setattr(sys, "argv", ["driver", operation, "--request", "fixture"])
    monkeypatch.setattr(
        cases,
        "run",
        lambda *_: (_ for _ in ()).throw(gate.GateError("fixture incomplete")),
    )
    monkeypatch.setattr(
        gate,
        "run_gate",
        lambda *_: pytest.fail("adaptive request cannot enter release gate"),
    )
    assert gate.main() == 2
    result = json.loads(capsys.readouterr().out)
    assert result["schema"] == expected_schema
    filename = "adaptive-result.json" if operation == "development" else "result.json"
    assert gate.read_json(tmp_path / filename) == result
    assert not (
        tmp_path
        / ("result.json" if operation == "development" else "adaptive-result.json")
    ).exists()


def test_release_run_still_invokes_original_gate(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(gate, "load_request", lambda *_: ({}, tmp_path, {}))
    monkeypatch.setattr(
        gate,
        "run_gate",
        lambda *_: {"schema": "aquarium.vm-acceptance-result/v1", "outcome": "pass"},
    )
    monkeypatch.setattr(sys, "argv", ["driver", "run", "--request", "fixture"])
    assert gate.main() == 0
    assert (
        json.loads(capsys.readouterr().out)["schema"]
        == "aquarium.vm-acceptance-result/v1"
    )


@pytest.fixture
def report_case(tmp_path):
    repository, directory = tmp_path / "repository", tmp_path / "capture"
    repository.mkdir()
    directory.mkdir()
    product = repository / "product.txt"
    product.write_text("current product")
    observation = {"root": {"metadata": {"id": "root"}, "items": []}, "descendants": []}
    evidence = {}
    for role in ["worker", "judge"]:
        assignment = {
            "schema": "aquarium.assignment/v2",
            "role": role,
            "work": {"repository": str(repository)},
            "success_criteria": ["required-original"],
            "procedure": {"node": role + "-node"},
        }
        report = {
            "schema": "aquarium.worker-handoff/v2"
            if role == "worker"
            else "aquarium.judge-assessment/v2",
            "target": {"files": {"product.txt": gate.sha256(product)}},
            "results": [{"exit": 0}],
            "checkpoint_result": "pass",
            "criteria": [
                {
                    "id": "required-original",
                    "state": "met",
                    "source": "original fixture source",
                    "evidence": ["actual fixture bytes"],
                }
            ],
        }
        apath, rpath = (
            directory / (role + "-assignment.json"),
            directory / (role + "-report.json"),
        )
        apath.write_text(json.dumps(assignment))
        rpath.write_text(json.dumps(report))
        evidence[role + "_assignment"] = str(apath)
        evidence[role + "_agent"] = "/root/" + role
        evidence["worker_result" if role == "worker" else "judge_assessment"] = str(
            rpath
        )
        observation["root"]["items"].extend(
            {
                "type": "subAgentActivity",
                "kind": kind,
                "agentThreadId": role,
                "agentPath": "/root/" + role,
            }
            for kind in ["started", "completed"]
        )
        observation["descendants"].append(
            {
                "metadata": {
                    "id": role,
                    "parentThreadId": "root",
                    "agentRole": None,
                    "status": {"type": "notLoaded"},
                },
                "turns": [{"status": "completed", "error": None}],
                "items": [
                    {"type": "commandExecution", "status": "completed"},
                    {
                        "type": "agentMessage",
                        "phase": "final_answer",
                        "text": json.dumps(report),
                    },
                ],
            }
        )
    return (
        repository,
        directory,
        observation,
        evidence,
        {"family": "task", "fixture": "greeting", "criteria": ["required-original"]},
    )


@pytest.mark.parametrize(
    "damage",
    [
        None,
        "self-assessment",
        "target-drift",
        "missing-criterion",
        "unmet-criterion",
        "no-worker-work",
    ],
)
def test_reports_bind_actual_distinct_roles_current_targets_and_due_criteria(
    report_case, damage
):
    repository, directory, observation, evidence, case = report_case
    if damage == "self-assessment":
        evidence["judge_agent"] = evidence["worker_agent"]
    elif damage == "target-drift":
        (repository / "product.txt").write_text("changed after assessment")
    elif damage in {"missing-criterion", "unmet-criterion"}:
        path = Path(evidence["judge_assessment"])
        report = gate.read_json(path)
        if damage == "missing-criterion":
            report["criteria"] = []
        else:
            report["criteria"][0]["state"] = "unverified"
        path.write_text(json.dumps(report))
        observation["descendants"][1]["items"][-1]["text"] = json.dumps(report)
    elif damage == "no-worker-work":
        observation["descendants"][0]["items"].pop(0)
    if damage:
        with pytest.raises(gate.GateError):
            cases.reports(gate, observation, evidence, directory, repository, case)
    else:
        result = cases.reports(gate, observation, evidence, directory, repository, case)
        assert result["actors"] == {"worker": "worker", "judge": "judge"}
        assert result["nodes"] == {"worker": "worker-node", "judge": "judge-node"}


@pytest.mark.parametrize("damage", [None, "symptom", "experiments"])
def test_diagnosis_oracle_preserves_symptom_and_isolated_experiments(
    document_case, monkeypatch, damage
):
    repository, before, _, observation, evidence = document_case
    evidence["experiments"] = [
        {
            "hypothesis": "fixture cause",
            "command": "isolated probe",
            "result": "counterexample",
        }
    ]

    def probe(argv):
        index = int(argv[-1])
        return SimpleNamespace(
            stdout=json.dumps(
                None if damage != "symptom" and index in {2, 5} else {"sample": index}
            )
        )

    monkeypatch.setattr(gate, "command", probe)
    if damage == "experiments":
        evidence["experiments"] = []
    if damage:
        with pytest.raises(gate.GateError):
            cases.oracle(
                gate,
                {"tools": {"python": sys.executable}},
                repository,
                {"oracle": "diagnosis"},
                evidence,
                observation,
                before,
            )
    else:
        assert (
            len(
                cases.oracle(
                    gate,
                    {"tools": {"python": sys.executable}},
                    repository,
                    {"oracle": "diagnosis"},
                    evidence,
                    observation,
                    before,
                )["symptom"]
            )
            == 6
        )


def run_gate_double(monkeypatch, tmp_path):
    monkeypatch.setattr(gate, "verify_candidate", lambda *_: {"sha": "fixture"})
    monkeypatch.setattr(gate, "versions", lambda *_: {"fixture": "tools"})
    monkeypatch.setattr(gate, "files", lambda *_: {})
    monkeypatch.setattr(gate, "installed_plugin", lambda *_: {"fixture": "installed"})
    return {
        "tools": {"codex": "/synthetic/codex", "python": sys.executable},
        "candidate": {
            "source_root": str(ROOT),
            "installed_plugin_root": str(ROOT / "plugins/aquarium"),
            "artifact_root": str(tmp_path / "artifact"),
        },
        "authority": {"observer": "Fixture operator", "reference": "synthetic scope"},
    }


@pytest.mark.parametrize("chosen", [["unknown"], ["adaptive-task", "adaptive-task"]])
def test_run_rejects_unknown_duplicate_cases_before_dispatch(
    tmp_path, monkeypatch, chosen
):
    request = run_gate_double(monkeypatch, tmp_path)
    request["development_cases"] = chosen
    monkeypatch.setattr(
        gate, "invoke", lambda *_args, **_kwargs: pytest.fail("invalid case dispatched")
    )
    with pytest.raises(gate.GateError):
        cases.run(gate, request, tmp_path)


def test_run_rejects_missing_required_leaf_before_effects(tmp_path, monkeypatch):
    request = run_gate_double(monkeypatch, tmp_path)
    request.update(
        development_cases=["adaptive-feature"], case_leaves={"adaptive-feature": ["qa"]}
    )
    monkeypatch.setattr(
        gate, "invoke", lambda *_args, **_kwargs: pytest.fail("missing leaf dispatched")
    )
    with pytest.raises(gate.GateError):
        cases.run(gate, request, tmp_path)
    assert not (tmp_path / "adaptive-feature-capture").exists()


def test_run_keeps_driver_originals_outside_agent_capture_on_resume(
    tmp_path, monkeypatch
):
    import native_observation

    request = run_gate_double(monkeypatch, tmp_path)
    request["development_cases"] = ["adaptive-task"]
    repository = tmp_path / "adaptive-task"
    repository.mkdir()
    product = repository / "product.txt"
    product.write_text("original")
    monkeypatch.setattr(cases, "prerequisites", lambda *_: {})
    monkeypatch.setattr(gate, "discover", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        gate, "invoke", lambda *_args, **_kwargs: "actual-existing-thread"
    )
    monkeypatch.setattr(
        native_observation, "collect", lambda *_: {"fixture": "observation"}
    )
    # Initial missing-delivery stop still preserves independently captured original bytes.
    with pytest.raises(gate.GateError):
        cases.run(gate, request, tmp_path)
    baseline = gate.read_json(
        tmp_path / "adaptive-state/adaptive-task/original-product.json"
    )
    assert baseline == {"product.txt": gate.sha256(product)}
    capture = tmp_path / "adaptive-task-capture"
    assert not (capture / "original-product.json").exists()
    product.write_text("changed")
    (capture / "original-product.json").write_text(
        json.dumps({"product.txt": gate.sha256(product)})
    )
    (capture / "semantic-evidence.json").write_text("{}")
    monkeypatch.setattr(cases, "reports", lambda *_: {})
    monkeypatch.setattr(cases, "leaf_delivery", lambda *_: {})
    observed = []
    monkeypatch.setattr(
        cases, "oracle", lambda *_args: observed.append(_args[-1]) or {}
    )
    monkeypatch.setattr(cases, "checkpoint", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(gate, "verify_settlement", lambda *_: None)
    assert cases.run(gate, request, tmp_path)["outcome"] == "pass"
    assert observed == [baseline]


@pytest.mark.parametrize(
    "case,relative",
    [
        ("adaptive-feature", "adaptive-feature-capture"),
        ("task-startup", "task-startup"),
    ],
)
def test_native_invocation_and_same_thread_reply_keep_exact_capture_scope(
    tmp_path, case, relative
):
    repository = tmp_path / "repository"
    repository.mkdir()
    native = tmp_path / "codex-fixture"
    native.write_text(
        f"#!{sys.executable}\nimport json,sys\nsys.stdin.read()\nprint(json.dumps({{'type':'thread.started','thread_id':'fixture-thread'}}))\n"
    )
    native.chmod(0o755)
    request = {
        "tools": {"codex": str(native)},
        "authority": {"observer": "Synthetic operator"},
    }
    assert (
        gate.invoke(request, tmp_path, case, "fixture prompt", repository=repository)
        == "fixture-thread"
    )
    assert (
        gate.invoke(
            request,
            tmp_path,
            case,
            "",
            reply="fixture actual reply",
            repository=repository,
        )
        == "fixture-thread"
    )
    receipts = sorted((tmp_path / "operations" / case).glob("*.invocation.json"))
    assert len(receipts) == 2
    for receipt in receipts:
        argv = gate.read_json(receipt)["argv"]
        assert argv[argv.index("--add-dir") + 1] == str(tmp_path / relative)
        assert str(tmp_path) not in argv
    assert gate.read_json(receipts[-1])["argv"][-3:] == [
        "resume",
        "fixture-thread",
        "-",
    ]


@pytest.mark.parametrize(
    "raw",
    [
        "REVISE: PASS is possible",
        "Verdict: revise\nScore: 1.00 [PASS]",
        "Verdict: pass\nVerdict: fail",
    ],
)
def test_unestablished_or_conflicting_qa_raw_field_remains_incomplete(raw):
    with pytest.raises(gate.GateError) as caught:
        cases.qa_verdict(gate, raw)
    assert caught.value.outcome == "incomplete"


def test_selected_pm_is_a_distinct_real_operation_with_conditional_authority(tmp_path):
    _, item, observation, evidence = leaf_case(tmp_path, "ouroboros_pm_interview", "pm")
    request = {
        "clipboard_authority": {
            "source": "user",
            "replace": True,
            "reference": "synthetic PM authority",
        }
    }
    assert cases.leaf_delivery(gate, observation, evidence, tmp_path, ["pm"], request)[
        "used"
    ] == ["pm"]
    evidence["used_leaves"] = ["interview", "pm"]
    evidence["leaf_results"]["interview"] = copy.deepcopy(
        evidence["leaf_results"]["pm"]
    )
    with pytest.raises(gate.GateError):
        cases.leaf_delivery(
            gate, observation, evidence, tmp_path, ["interview", "pm"], request
        )
    item["tool"] = "ouroboros_interview"
    evidence["used_leaves"] = ["interview"]
    assert cases.leaf_delivery(
        gate, observation, evidence, tmp_path, ["interview"], {}
    )["used"] == ["interview"]


def test_existing_invocation_cannot_recapture_a_missing_original_basis(
    tmp_path, monkeypatch
):
    request = run_gate_double(monkeypatch, tmp_path)
    request["development_cases"] = ["adaptive-task"]
    (tmp_path / "adaptive-task").mkdir()
    operations = tmp_path / "operations/adaptive-task"
    operations.mkdir(parents=True)
    (operations / "000.invocation.json").write_text(
        json.dumps({"thread_id": "existing", "exit": 0})
    )
    monkeypatch.setattr(
        gate,
        "invoke",
        lambda *_args, **_kwargs: pytest.fail("missing original basis dispatched"),
    )
    with pytest.raises(gate.GateError):
        cases.run(gate, request, tmp_path)
    assert not (
        tmp_path / "adaptive-state/adaptive-task/original-product.json"
    ).exists()


@pytest.mark.parametrize("target", ["sampler.py", "src/implementation.js"])
def test_actual_document_approval_cannot_authorize_product_code(tmp_path, target):
    repository = tmp_path / "product"
    repository.mkdir()
    if target == "sampler.py":
        source = ROOT / "tests/vm/fixtures/adaptive/diagnosis/sampler.py"
        (repository / target).write_bytes(source.read_bytes())
    before = cases.original_image(gate, repository)
    path = repository / target
    path.parent.mkdir(parents=True, exist_ok=True)
    if target == "sampler.py":
        path.write_text(
            path.read_text()
            + "\n# Unapproved product byte change, behavior unchanged.\n"
        )
        # A behavior-preserving product edit still violates the independent byte boundary.
        for index in range(6):
            expected = subprocess.check_output(
                [sys.executable, "-B", source, str(index)]
            )
            actual = subprocess.check_output([sys.executable, "-B", path, str(index)])
            assert actual == expected
    else:
        path.write_text("export function greet() { return 'Hello'; }\n")
    proposal = {
        "diff": "operator explicitly approved this fixture change",
        "targets": {target: {"before": before.get(target), "after": gate.sha256(path)}},
    }
    observation = {"root": {}}
    evidence = {
        "application_approval": approved(observation, proposal),
        "quality": {"operation_outcome": "pass", "raw_verdict": "PASS"},
        "experiments": [
            {
                "hypothesis": "fixture",
                "command": "probe",
                "result": "unchanged behavior",
            }
        ],
    }
    with pytest.raises(gate.GateError) as caught:
        cases.oracle(
            gate,
            {"tools": {"python": sys.executable}},
            repository,
            {"oracle": "diagnosis" if target == "sampler.py" else "non-git-documents"},
            evidence,
            observation,
            before,
        )
    assert caught.value.outcome == "fail"


@pytest.mark.parametrize("name", ["README.md", "custom documents/한글/design.md"])
def test_document_only_fixture_preserves_approved_custom_markdown_locations(
    tmp_path, name
):
    before = cases.original_image(gate, tmp_path)
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("Approved project design\n")
    proposal = {
        "diff": "approved Markdown addition",
        "targets": {name: {"before": None, "after": gate.sha256(path)}},
    }
    observation = {"root": {}}
    evidence = {"application_approval": approved(observation, proposal)}
    result = cases.oracle(
        gate,
        {},
        tmp_path,
        {"oracle": "non-git-documents"},
        evidence,
        observation,
        before,
    )
    assert result["documents"] == proposal["targets"]
    assert result["git"] == "absent" and result["podway"] == "absent"


@pytest.mark.parametrize("diff", ["unapplied claimed diff", None, {}, 5])
def test_no_change_requires_empty_string_diff_in_actual_approved_proposal(
    document_case, diff
):
    repository, before, _, observation, evidence = document_case
    (repository / "docs/result.md").write_text("original document")
    proposal = {
        "diff": diff,
        "targets": {},
        "no_change": True,
        "reason": "Existing documentation meets this fixture requirement",
    }
    evidence["application_approval"] = approved(observation, proposal)
    with pytest.raises(gate.GateError):
        cases.oracle(
            gate, {}, repository, {"oracle": "documents"}, evidence, observation, before
        )


@pytest.mark.parametrize("diff", [None, {}, 5])
def test_changed_document_proposal_also_requires_string_diff(document_case, diff):
    repository, before, proposal, observation, evidence = document_case
    proposal["diff"] = diff
    evidence["application_approval"] = approved(observation, proposal)
    with pytest.raises(gate.GateError):
        cases.oracle(
            gate, {}, repository, {"oracle": "documents"}, evidence, observation, before
        )
