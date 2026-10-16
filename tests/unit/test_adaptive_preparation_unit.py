"""Selection and source preparation controls; synthetic oracles are not native proof."""

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SHARED = ROOT / "plugins/aquarium/shared"
sys.path.insert(0, str(SHARED))
import adaptive_admission as admission
import adaptive_bundles as bundles
import adaptive_preparation as prep
from adaptive_definitions import canonical_json


@pytest.fixture
def repository(tmp_path):
    path = tmp_path / "work 한글"
    path.mkdir()
    subprocess.run(["git", "-C", str(path), "init", "-q"], check=True)
    return path


def action(title, items):
    return {"type": "action", "title": title, "intent": title, "items": items}


def text(identifier):
    return {
        "id": identifier,
        "type": "text",
        "prompt": identifier,
        "required": True,
        "min_length": 1,
        "max_length": 2000,
    }


def authored(performance=False):
    """Two different source/evidence/Decision structures from explicit work inputs."""
    defs = {
        "deliver": action("Document approved API migration", [text("documentation")]),
        "assess": action(
            "Independently assess original requirements", [text("assessment")]
        ),
        "outcome": {
            "type": "decision",
            "title": "Determine original goal achievement",
            "objective": "Use the independent assessment",
            "prompt": "What did the assessment establish?",
            "options": [
                {"id": key, "label": key, "criteria": reason}
                for key, reason in [
                    ("pass", "Every original requirement is established."),
                    ("fail", "At least one original requirement is unmet."),
                    ("stopped", "Work is stopped before achievement is established."),
                    (
                        "superseded",
                        "A consented replacement has preserved the original history.",
                    ),
                ]
            ],
            "reason": {
                "required": True,
                "prompt": "Cite original requirements and assessment evidence.",
            },
            "assessment": {
                "target": "session_goal",
                "outcomes": {
                    "pass": "achieved",
                    "fail": "not_achieved",
                    "stopped": "not_achieved",
                    "superseded": "superseded",
                },
            },
        },
        "finish": action(
            "Deliver complete result and acceptance boundary", [text("result")]
        ),
    }
    nodes = [
        {"id": "deliver", "use": "deliver", "next": "assess"},
        {
            "id": "assess",
            "use": "assess",
            "evidence_from": [
                {"node": "deliver", "items": ["documentation"], "required": True}
            ],
            "next": "outcome",
        },
        {
            "id": "outcome",
            "use": "outcome",
            "evidence_from": [
                {"node": "assess", "items": ["assessment"], "required": True}
            ],
            "routes": {
                key: {"to": "finish", "effect": "advance"}
                for key in ["pass", "fail", "stopped", "superseded"]
            },
        },
        {"id": "finish", "use": "finish", "terminal": True},
    ]
    entry = "deliver"
    producer_item = "documentation"
    if performance:
        defs["measure"] = action(
            "Measure current query latency",
            [
                {
                    "id": "latency",
                    "type": "integer",
                    "prompt": "Record measured milliseconds",
                    "required": True,
                    "minimum": 0,
                    "maximum": 100000,
                }
            ],
        )
        defs["classify"] = {
            "type": "decision",
            "title": "Classify measured latency",
            "objective": "Choose the applicable tuning strategy",
            "prompt": "Does measured latency exceed the approved budget?",
            "options": [
                {
                    "id": "tune",
                    "label": "Tune slow query",
                    "criteria": "Latency exceeds the 100 ms work budget.",
                    "guards": [
                        {
                            "evidence": {"node": "measure", "item": "latency"},
                            "at_least": 101,
                        }
                    ],
                },
                {
                    "id": "preserve",
                    "label": "Preserve fast query",
                    "criteria": "Latency is within the 100 ms work budget.",
                    "guards": [
                        {
                            "evidence": {"node": "measure", "item": "latency"},
                            "at_most": 100,
                        }
                    ],
                },
            ],
            "reason": {
                "required": True,
                "prompt": "Cite measurements and selected strategy.",
            },
        }
        defs["deliver"] = action(
            "Implement the approved query policy", [text("query-policy")]
        )
        nodes[0]["evidence_from"] = [
            {"node": "measure", "items": ["latency"], "required": True},
            {"node": "classify", "required": True},
        ]
        defs["preserve"] = action(
            "Preserve the measured fast query", [text("baseline-policy")]
        )
        nodes[1]["evidence_from"] = [
            {"node": "measure", "items": ["latency"], "required": True},
            {"node": "deliver", "items": ["query-policy"], "required": False},
            {"node": "preserve", "items": ["baseline-policy"], "required": False},
        ]
        nodes.append(
            {
                "id": "preserve",
                "use": "preserve",
                "next": "assess",
                "evidence_from": [
                    {"node": "measure", "items": ["latency"], "required": True},
                    {"node": "classify", "required": True},
                ],
            }
        )
        nodes[:0] = [
            {"id": "measure", "use": "measure", "next": "classify"},
            {
                "id": "classify",
                "use": "classify",
                "evidence_from": [
                    {"node": "measure", "items": ["latency"], "required": True}
                ],
                "routes": {
                    key: {
                        "to": "deliver" if key == "tune" else "preserve",
                        "effect": "advance",
                    }
                    for key in ["tune", "preserve"]
                },
            },
        ]
        entry, producer_item = "measure", "query-policy"
    native = {
        "schema": "podway.procedure/v2",
        "id": "draft-source",
        "version": "1",
        "name": "Approved query policy"
        if performance
        else "API migration documentation",
        "purpose": "Prepare the actual bounded work definition; suitability remains independently assessed.",
        "goal_tracking": True,
        "manual_rework": {"allowed_targets": [entry]},
        "node_definitions": defs,
        "graph": {"entry": entry, "nodes": nodes},
    }
    mapping = {
        "schema": "aquarium.procedure-binding/v1",
        "compatibility": "aquarium.adaptive/v1",
        "family": "task",
        "entrypoints": ["task-handler"],
        "nodes": {
            node["id"]: {
                "kind": defs[node["use"]]["type"],
                "role": "judge"
                if node["id"] == "assess"
                else "worker"
                if node["id"] in {"measure", "deliver"}
                else "orchestrator",
                "effects": ["work"] if node["id"] in {"measure", "deliver"} else [],
                "capabilities": [],
            }
            for node in nodes
        },
        "parameters": {},
        "obligations": {
            "original-work": {
                "source": "Original approved work requirements",
                "applicability": "This bounded work definition",
                "producers": (
                    [
                        {"node": "deliver", "item": producer_item},
                        {"node": "preserve", "item": "baseline-policy"},
                    ]
                    if performance
                    else [{"node": "deliver", "item": producer_item}]
                ),
                "evidence": [{"node": "assess", "item": "assessment"}],
                "assessor": "assess",
                "decision": "outcome",
                "effects": ["work"],
            }
        },
        "goal_assessments": [
            {"node": "outcome", "outcomes": defs["outcome"]["assessment"]["outcomes"]}
        ],
        "closeout": [{"node": "finish", "kind": "shared", "requires": ["outcome"]}],
        "origins": [],
    }
    return native, mapping


def assignment(repository, *, mode="plan-only", performance=False):
    original = {
        "criteria": [
            {
                "id": "delivery",
                "text": "Deliver the approved change and verify its original contract.",
                "parts": [
                    {"id": "deliver", "text": "Deliver the approved change."},
                    {"id": "verify", "text": "Verify the original contract."},
                ],
            },
            {"id": "omitted", "text": "Preserve backwards compatibility."},
        ]
    }
    path = repository / "requirements.json"
    path.write_text(json.dumps(original))
    native, mapping = authored(performance)
    coverage = [
        {
            "criterion": "original:" + row["id"],
            "part": part["id"],
            "obligation": "original-work",
            "reason": part["text"],
        }
        for row in original["criteria"]
        for part in row.get("parts", [{"id": "whole", "text": row["text"]}])
    ]
    return {
        "schema": "aquarium.assignment/v2",
        "role": "worker",
        "purpose": "Prepare the exact work definition",
        "instructions": "Preserve original criteria and authority; do no product work.",
        "checkpoint": "Before independent suitability qualification",
        "procedure": None,
        "native": {"harness": "Codex", "available_handle": "synthetic-test"},
        "deliverables": ["Exact source/binding and original-source coverage plan"],
        "evidence": [],
        "gaps": ["Independent semantic sufficiency remains due"],
        "work": {
            "requirement_sources": [
                {
                    "id": "original",
                    "path": path.name,
                    "sha256": bundles.sha256(path.read_bytes()),
                    "format": "json",
                }
            ]
        },
        "target": {
            "procedure_plan": {
                "family": "task",
                "entrypoint": "task-handler",
                "mode": mode,
                "effects": ["work"],
                "review": {"route": "not-applicable", "team": [], "transmission": []},
                "discovery_roots": ["definitions"],
                "source_dispositions": {
                    "aquarium-task-v2.yaml": "The actual work requires a documentation-only producer without implementation/refinement obligations."
                },
                "candidates": [],
                "drafts": [
                    {
                        "kind": "author",
                        "document": native,
                        "mapping": mapping,
                        "coverage": coverage,
                        "reason": "The work needs this actual producer and assessment structure.",
                    }
                ],
            }
        },
        "success_criteria": ["original:delivery"],
        "authority": {
            "allowed": ["Disclosed source-only preparation"],
            "excluded": ["Product work", "Session operations"],
            "effects": ["work"],
            "review": {"route": "not-applicable", "team": [], "transmission": []},
            "preparation": {
                "native_authoring": True,
                "roots": ["definitions"],
                "write_root": "definitions",
            },
        },
    }


class Oracle:
    """Synthetic formatter/identity behavior, explicitly not actual Podway evidence."""

    def __init__(self, repository):
        self.repository = repository
        self.read = Mock(side_effect=self._read)
        self.health = Mock(
            side_effect=AssertionError(
                "Source-only preparation must not inspect native state"
            )
        )

    def _read(self, argv, command, schemas):
        if command == "procedure.format" and "--check" not in argv:
            return {
                "document": bundles.read_regular(
                    self.repository, self.repository / argv[-1]
                ).decode()
            }
        return {"synthetic": True, "command": command}

    def preview(self, path):
        raw = bundles.read_regular(self.repository, path)
        value = yaml.safe_load(raw)
        return {
            "procedure_id": value["id"],
            "procedure_version": value["version"],
            "procedure_digest": bundles.sha256(canonical_json(value)),
        }

    def identity(self, path):
        preview = self.preview(path)
        return tuple(
            preview[key]
            for key in ["procedure_id", "procedure_version", "procedure_digest"]
        )


def known_candidate(repository, value):
    path = repository / "definitions/custom name.yml"
    path.parent.mkdir(exist_ok=True)
    raw = (
        ROOT / "plugins/aquarium/assets/podway/procedures/aquarium-task-v2.yaml"
    ).read_bytes()
    path.write_bytes(raw)
    mapping = admission.reference_mapping(raw)
    obligation = next(iter(mapping["obligations"]))
    plan = value["target"]["procedure_plan"]
    plan["effects"] = sorted(
        {effect for node in mapping["nodes"].values() for effect in node["effects"]}
    )
    value["authority"]["effects"] = plan["effects"][:]
    plan["candidates"] = [
        {
            "path": str(path.relative_to(repository)),
            "sha256": bundles.sha256(raw),
            "coverage": [
                {**row, "obligation": obligation}
                for row in plan["drafts"][0]["coverage"]
            ],
            "reason": "The existing full Task contract is adequate for this implementation.",
        }
    ]
    return path


def assert_code(code, call):
    with pytest.raises(bundles.BundleError) as caught:
        call()
    assert caught.value.code == code


def test_plan_only_never_writes_or_calls_native(repository):
    value = assignment(repository)
    snapshot = {
        str(path.relative_to(repository)): ("file", path.read_bytes())
        if path.is_file()
        else ("directory", None)
        for path in repository.rglob("*")
    }
    client = Oracle(repository)
    result = prep.prepare(repository, value, client=client)
    assert result["status"] == "planned"
    assert result["selection"]["kind"] == "author"
    assert result["writes"] == []
    client.read.assert_not_called()
    client.health.assert_not_called()
    assert snapshot == {
        str(path.relative_to(repository)): ("file", path.read_bytes())
        if path.is_file()
        else ("directory", None)
        for path in repository.rglob("*")
    }


def test_known_reuse_precedes_generation_without_exhaustive_optional_dispositions(
    repository,
):
    value = assignment(repository)
    known_candidate(repository, value)
    value["target"]["procedure_plan"]["source_dispositions"] = {}
    assert prep.select(repository, value)["kind"] == "reuse"


def test_generation_does_not_silently_bypass_known_default(repository):
    value = assignment(repository)
    value["target"]["procedure_plan"]["source_dispositions"] = {}
    assert_code("not-established", lambda: prep.select(repository, value))


@pytest.mark.parametrize("performance", [False, True])
def test_prepares_complete_ignored_selfcontained_candidates_without_adopting(
    repository, performance
):
    value = assignment(repository, mode="prepare", performance=performance)
    original = copy.deepcopy(value)
    result = prep.prepare(repository, value, client=Oracle(repository))
    target = result["assignment"]["target"]["prepared_definition"]
    retained = bundles.verified_bundle(repository, Path(target["path"]))
    assert retained["binding"] == result["binding"]
    assert retained["binding"]["procedure"]["id"].startswith("aquarium-adapt-task-")
    assert retained["binding"]["procedure"]["version"] == "1"
    assert target["source_path"] == str(Path(target["path"]) / "procedure.yaml")
    assert target["binding_path"] == str(Path(target["path"]) / "binding.json")
    bundles.local_status(repository, Path(target["path"]))
    assert not (repository / "definitions/.local").exists()
    assert target["assessment"] == "TASK-141-exact-target-suitability-required"
    assert target["adoption"] == "not-performed"
    assert value == original
    assert result["assignment"]["authority"] == original["authority"]
    assert result["assignment"]["work"] == original["work"]
    assert len(yaml.safe_load(retained["source"])["graph"]["nodes"]) == (
        7 if performance else 4
    )


def test_custom_filename_reuse_returns_exact_complete_copy_and_preserves_checkpoint(
    repository,
):
    value = assignment(repository, mode="prepare")
    source = known_candidate(repository, value)
    client = Oracle(repository)
    binding = admission.reference_binding(source.read_bytes(), client.preview(source))
    elsewhere = repository / "a binding.json"
    elsewhere.write_bytes(canonical_json(binding))
    value["target"]["procedure_plan"]["candidates"][0]["binding"] = {
        "path": elsewhere.name,
        "sha256": bundles.sha256(elsewhere.read_bytes()),
    }
    result = prep.prepare(repository, value, client=client)
    target = result["assignment"]["target"]["prepared_definition"]
    assert Path(target["source_path"]).read_bytes() == source.read_bytes()
    assert Path(target["binding_path"]).read_bytes() == elsewhere.read_bytes()
    assert target["assessment"] == "preserve-original-checkpoints"
    source.unlink()
    elsewhere.unlink()
    assert (
        bundles.verified_bundle(repository, Path(target["path"]))["binding"] == binding
    )


@pytest.mark.parametrize(
    "mutator,code",
    [
        (
            lambda value: value["target"]["procedure_plan"]["drafts"][0][
                "coverage"
            ].pop(),
            "not-established",
        ),
        (
            lambda value: value["target"]["procedure_plan"]["drafts"][0][
                "coverage"
            ].__setitem__(
                0,
                {
                    **value["target"]["procedure_plan"]["drafts"][0]["coverage"][0],
                    "part": "invented",
                },
            ),
            "not-established",
        ),
        (
            lambda value: value["authority"].__setitem__("effects", []),
            "authority-required",
        ),
        (
            lambda value: value["target"]["procedure_plan"]["review"].__setitem__(
                "transmission", ["unapproved-provider"]
            ),
            "authority-required",
        ),
        (
            lambda value: value["target"]["procedure_plan"]["drafts"][0]["mapping"][
                "nodes"
            ]["deliver"].__setitem__("effects", ["publish"]),
            "incompatible",
        ),
        (
            lambda value: value["target"]["procedure_plan"]["drafts"][0]["mapping"][
                "obligations"
            ]["original-work"]["evidence"][0].__setitem__("item", "missing"),
            "incompatible",
        ),
    ],
)
def test_original_coverage_review_effects_and_endpoints(repository, mutator, code):
    value = assignment(repository)
    mutator(value)
    assert_code(code, lambda: prep.select(repository, value))


def test_no_preparation_authority_stops_before_any_write_or_native_call(repository):
    value = assignment(repository, mode="prepare")
    value["authority"].pop("preparation")
    client = Oracle(repository)
    assert_code(
        "authority-required", lambda: prep.prepare(repository, value, client=client)
    )
    assert not (repository / "definitions").exists()
    client.read.assert_not_called()


def test_source_drift_stops_before_preparation(repository):
    value = assignment(repository, mode="prepare")
    (repository / "requirements.json").write_text("{}")
    assert_code(
        "source-drift",
        lambda: prep.prepare(repository, value, client=Oracle(repository)),
    )
    assert not (repository / "definitions").exists()


def test_unqualified_adopted_customizations_remain_due(repository):
    value = assignment(repository)
    source = copy.deepcopy(value["work"]["requirement_sources"][0])
    source.update(id="custom", role="adopted-customization")
    value["work"]["requirement_sources"].append(source)
    assert_code("not-established", lambda: prep.select(repository, value))
    coverage = value["target"]["procedure_plan"]["drafts"][0]["coverage"]
    coverage.extend(
        {**row, "criterion": row["criterion"].replace("original:", "custom:")}
        for row in coverage[:]
    )
    assert_code("not-established", lambda: prep.select(repository, value))
    value["target"]["procedure_plan"]["customization_disposition"] = (
        "Preserve the currently adopted scope; no changed obligation is authorized."
    )
    assert len(prep.select(repository, value)["plan"]["criteria"]) == 4


def test_optional_template_sources_are_not_requirements_or_startup_dependencies(
    repository,
):
    value = assignment(repository)
    value["work"]["requirement_sources"].append(
        {
            "id": "optional",
            "role": "historical",
            "path": "absent.yaml",
            "sha256": "absent",
        }
    )
    assert prep.select(repository, value)["kind"] == "author"


def test_markdown_retains_paragraph_nested_and_compound_original_text(repository):
    value = assignment(repository)
    text_value = "# Goal\nMandatory paragraph.\n- Deliver change and preserve old API.\n  - Retain error semantics.\n"
    path = repository / "original.md"
    path.write_text(text_value)
    value["work"]["requirement_sources"] = [
        {
            "id": "markdown",
            "path": path.name,
            "sha256": bundles.sha256(path.read_bytes()),
            "section": "# Goal",
        }
    ]
    value["success_criteria"] = ["markdown:whole"]
    value["target"]["procedure_plan"]["drafts"][0]["coverage"] = [
        {
            "criterion": "markdown:whole",
            "part": "whole",
            "obligation": "original-work",
            "reason": "Assess the complete original section, including compound clauses.",
        }
    ]
    selected = prep.select(repository, value)
    assert (
        "Mandatory paragraph." in selected["plan"]["criteria"]["markdown:whole"]["text"]
    )
    assert (
        "Retain error semantics."
        in selected["plan"]["criteria"]["markdown:whole"]["text"]
    )
    assert (
        selected["plan"]["semantic_completeness"]
        == "requires-independent-original-source-assessment"
    )


def test_strategy_preference_and_composition_boundary(repository):
    value = assignment(repository)
    plan = value["target"]["procedure_plan"]
    base = repository / "base.yaml"
    base.write_text(yaml.safe_dump(plan["drafts"][0]["document"]))
    adapt = {
        **copy.deepcopy(plan["drafts"][0]),
        "kind": "adapt",
        "base": {"path": base.name, "sha256": bundles.sha256(base.read_bytes())},
    }
    plan["drafts"].append(adapt)
    assert prep.select(repository, value)["kind"] == "adapt"
    plan["drafts"] = [plan["drafts"][0], {"kind": "compose"}]
    assert_code("not-established", lambda: prep.select(repository, value))


def test_malformed_unrelated_history_is_diagnostic_and_does_not_block_identity_allocation(
    repository,
):
    value = assignment(repository, mode="prepare")
    root = repository / "definitions"
    root.mkdir()
    (root / "broken.yaml").write_text("schema: [")
    result = prep.prepare(repository, value, client=Oracle(repository))
    assert any(row["status"] == "native-invalid" for row in result["considered"])


def test_existing_tracked_ignore_conflict_precedes_source_bytes(repository):
    value = assignment(repository, mode="prepare")
    root = repository / "definitions/.candidates"
    root.mkdir(parents=True)
    (root / ".gitignore").write_text("unrelated\n")
    subprocess.run(
        ["git", "-C", str(repository), "add", "definitions/.candidates/.gitignore"],
        check=True,
    )
    client = Oracle(repository)
    assert_code(
        "ignore-conflict", lambda: prep.prepare(repository, value, client=client)
    )
    assert list(root.iterdir()) == [root / ".gitignore"]
    client.read.assert_not_called()


def test_formatter_replacement_symlink_is_not_followed(repository):
    path = repository / "stage.yaml"
    path.write_text("placeholder")
    victim = repository / "victim"
    victim.write_text("preserve")
    client = Oracle(repository)
    original = client._read

    def replace(argv, command, schemas):
        result = original(argv, command, schemas)
        if command == "procedure.format" and "--check" not in argv:
            path.unlink()
            path.symlink_to(victim)
        return result

    client.read.side_effect = replace
    with pytest.raises(OSError):
        prep.author_checks(client, path, format_source=True)
    assert victim.read_text() == "preserve"


def test_cli_plan_only_and_invalid_input_json_boundary(repository):
    value = assignment(repository)
    command = [
        sys.executable,
        str(SHARED / "prepare_adaptive_procedure.py"),
        "--repository",
        str(repository),
        "--assignment",
        "-",
    ]
    result = subprocess.run(
        command, input=json.dumps(value), text=True, capture_output=True, check=False
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["status"] == "planned"
    failed = subprocess.run(
        command, input="{}", text=True, capture_output=True, check=False
    )
    assert failed.returncode == 2
    assert json.loads(failed.stdout)["status"] == "invalid-input"


def test_explicit_malformed_selection_is_native_invalid_json(repository):
    value = assignment(repository)
    path = repository / "broken.yml"
    path.write_text("schema: [")
    value["target"]["procedure_plan"]["candidates"] = [
        {
            "path": path.name,
            "sha256": bundles.sha256(path.read_bytes()),
            "coverage": [],
            "reason": "Explicit source inspection",
        }
    ]
    command = [
        sys.executable,
        str(SHARED / "prepare_adaptive_procedure.py"),
        "--repository",
        str(repository),
        "--assignment",
        "-",
    ]
    result = subprocess.run(
        command, input=json.dumps(value), text=True, capture_output=True, check=False
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "native-invalid"
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize("operation", ["format", "validate", "vet", "lint"])
@pytest.mark.parametrize("valid", [False, True])
def test_native_authoring_nonzero_diagnostic_gate_preserves_original_result(
    repository, monkeypatch, operation, valid
):
    payload = {
        "schema": "podway.procedure-diagnostics-result/v1",
        "valid": valid,
        "diagnostics": [{"code": "AUTHORING_SCHEMA_INVALID", "severity": "error"}],
    }
    envelope = {
        "schema": "podway.output/v4",
        "command": "procedure." + operation,
        "result": payload,
    }
    monkeypatch.setattr(
        admission.subprocess,
        "run",
        Mock(
            return_value=subprocess.CompletedProcess(
                [], 1, stdout=json.dumps(envelope).encode(), stderr=b""
            )
        ),
    )
    client = admission.NativeClient(repository, "explicit-synthetic-binary")
    with pytest.raises(bundles.BundleError) as caught:
        client.read(
            ["procedure", operation, "--", "source.yaml"],
            "procedure." + operation,
            None,
        )
    assert caught.value.code == "native-invalid"
    assert caught.value.details["native_result"] == payload
    assert caught.value.details["native_exit_status"] == 1


def test_native_authoring_malformed_machine_output_and_missing_process_are_distinct(
    repository, monkeypatch
):
    envelope = {
        "schema": "podway.output/v4",
        "command": "procedure.vet",
        "result": {
            "schema": "podway.procedure-diagnostics-result/v1",
            "valid": "false",
        },
    }
    monkeypatch.setattr(
        admission.subprocess,
        "run",
        Mock(
            return_value=subprocess.CompletedProcess(
                [], 0, stdout=json.dumps(envelope).encode(), stderr=b""
            )
        ),
    )
    client = admission.NativeClient(repository, "synthetic")
    assert_code(
        "unsupported-runtime",
        lambda: client.read(["procedure", "vet"], "procedure.vet", None),
    )
    monkeypatch.setattr(
        admission.subprocess, "run", Mock(side_effect=FileNotFoundError())
    )
    assert_code(
        "runtime-failure",
        lambda: client.read(["procedure", "vet"], "procedure.vet", None),
    )


def test_typed_review_route_alias_is_supported_without_claiming_control_continuity(
    repository,
):
    value = assignment(repository)
    plan = value["target"]["procedure_plan"]
    draft = plan["drafts"][0]
    draft["document"]["node_definitions"]["deliver"]["items"].append(
        {
            "id": "selected-provider",
            "type": "choice",
            "prompt": "Record the approved route",
            "required": True,
            "choices": ["herdr"],
        }
    )
    draft["mapping"]["nodes"]["deliver"]["capabilities"] = [
        {
            "signature": "aquarium.task.review-routing/v1",
            "fields": {"effective-review-route": "selected-provider"},
        }
    ]
    plan["review"] = {
        "route": "herdr",
        "team": ["Claude"],
        "transmission": ["approved exact source"],
    }
    value["authority"]["review"] = copy.deepcopy(plan["review"])
    assert prep.select(repository, value)["kind"] == "author"
    draft["document"]["node_definitions"]["deliver"]["items"][-1]["choices"] = [
        "mulgae"
    ]
    assert_code("incompatible", lambda: prep.select(repository, value))


def test_identity_collision_and_positive_revision_use_discovered_custom_extensions(
    repository, monkeypatch
):
    assignment(repository)
    root = repository / "definitions"
    root.mkdir()
    native, _ = authored()
    native["id"] = "aquarium-adapt-task-existing"
    native["version"] = "9"
    path = root / "history.custom"
    path.write_text(yaml.safe_dump(native))
    revision = {
        "revision_of": {
            "path": str(path.relative_to(repository)),
            "sha256": bundles.sha256(path.read_bytes()),
        }
    }
    assert prep.allocate_identity(repository, [root], "task", revision) == (
        native["id"],
        "10",
    )
    sequence = iter(["existing", "fresh"])
    monkeypatch.setattr(
        prep.uuid, "uuid4", lambda: type("Token", (), {"hex": next(sequence)})()
    )
    assert prep.allocate_identity(repository, [root], "task", {}) == (
        "aquarium-adapt-task-fresh",
        "1",
    )


def test_generated_candidates_cannot_enter_known_source_admission(repository):
    value = assignment(repository, mode="prepare")
    client = Oracle(repository)
    result = prep.prepare(repository, value, client=client)
    target = result["assignment"]["target"]["prepared_definition"]
    assert_code(
        "not-established",
        lambda: admission.known_source(Path(target["source_path"]).read_bytes()),
    )
    assert (
        bundles.resolve_bundle(
            repository,
            ["definitions"],
            tuple(target["procedure"][key] for key in ["id", "version", "digest"]),
            native_identity=client.identity,
        )["status"]
        == "missing"
    )


def test_adaptive_structures_differ_in_actual_production_evidence_and_guards(
    repository,
):
    produced = []
    for performance_work in [False, True]:
        result = prep.prepare(
            repository,
            assignment(repository, mode="prepare", performance=performance_work),
            client=Oracle(repository),
        )
        target = result["assignment"]["target"]["prepared_definition"]
        produced.append(
            (
                yaml.safe_load(Path(target["source_path"]).read_bytes()),
                result["binding"],
            )
        )
        assert target["procedure"]["digest"] != target["procedure"]["source_sha256"]
    (documentation, documentation_mapping), (performance, performance_mapping) = (
        produced
    )
    assert (
        documentation["node_definitions"]["deliver"]["items"][0]["id"]
        == "documentation"
    )
    assert performance["node_definitions"]["measure"]["items"][0]["type"] == "integer"
    branch = next(
        node for node in performance["graph"]["nodes"] if node["id"] == "classify"
    )
    assert branch["routes"]["tune"]["to"] != branch["routes"]["preserve"]["to"]
    options = performance["node_definitions"]["classify"]["options"]
    assert options[0]["guards"][0]["at_least"] == 101
    assert options[1]["guards"][0]["at_most"] == 100
    assert len(documentation_mapping["obligations"]["original-work"]["producers"]) == 1
    assert len(performance_mapping["obligations"]["original-work"]["producers"]) == 2
    assessment = next(
        node for node in performance["graph"]["nodes"] if node["id"] == "assess"
    )
    assert {row["node"] for row in assessment["evidence_from"]} == {
        "measure",
        "deliver",
        "preserve",
    }


def test_ordinary_v2_contract_is_required_and_existing_goal_checkpoint_is_preserved(
    repository,
):
    value = assignment(repository)
    value.pop("native")
    assert_code("incompatible", lambda: prep.select(repository, value))
    value = assignment(repository)
    filename = "aquarium-goal-v2.yaml"
    raw = (ROOT / "plugins/aquarium/assets/podway/procedures" / filename).read_bytes()
    mapping = admission.reference_mapping(raw)
    plan = value["target"]["procedure_plan"]
    plan.update(family="goal", entrypoint="epic-handler")
    plan["effects"] = sorted(
        {effect for node in mapping["nodes"].values() for effect in node["effects"]}
    )
    value["authority"]["effects"] = plan["effects"][:]
    plan["candidates"] = [
        {
            "installed": filename,
            "sha256": bundles.sha256(raw),
            "coverage": [
                {**row, "obligation": next(iter(mapping["obligations"]))}
                for row in plan["drafts"][0]["coverage"]
            ],
            "reason": "The existing Goal member/final assessment boundary fits this Epic.",
        }
    ]
    selected = prep.select(repository, value)
    assert selected["assessment"] == "preserve-original-checkpoints"
    assert selected["source"] == raw
    assert selected["mapping"] == mapping


@pytest.mark.parametrize("grant", [False, "true", None])
def test_preparation_permission_is_explicit_boolean(repository, grant):
    value = assignment(repository, mode="prepare")
    value["authority"]["preparation"]["native_authoring"] = grant
    client = Oracle(repository)
    assert_code(
        "authority-required", lambda: prep.prepare(repository, value, client=client)
    )
    client.read.assert_not_called()
    assert not (repository / "definitions").exists()


def test_known_reuse_does_not_acquire_new_authoring_gates(repository):
    value = assignment(repository, mode="prepare")
    known_candidate(repository, value)
    client = Oracle(repository)
    result = prep.prepare(repository, value, client=client)
    assert (
        result["assignment"]["target"]["prepared_definition"]["assessment"]
        == "preserve-original-checkpoints"
    )
    assert [call.args[1] for call in client.read.call_args_list] == ["version"]


@pytest.mark.parametrize(
    "changed,exit_status,code",
    [
        (True, 1, "native-invalid"),
        (True, 0, "native-invalid"),
        ("true", 0, "unsupported-runtime"),
    ],
)
def test_native_format_check_typed_source_gate(
    repository, monkeypatch, changed, exit_status, code
):
    payload = {
        "schema": "podway.procedure-source-result/v1",
        "changed": changed,
        "target_schema": "podway.procedure/v2",
    }
    envelope = {
        "schema": "podway.output/v4",
        "command": "procedure.format",
        "result": payload,
    }
    monkeypatch.setattr(
        admission.subprocess,
        "run",
        Mock(
            return_value=subprocess.CompletedProcess(
                [], exit_status, stdout=json.dumps(envelope).encode(), stderr=b""
            )
        ),
    )
    client = admission.NativeClient(repository, "synthetic")
    assert_code(
        code,
        lambda: client.read(
            ["procedure", "format", "--check", "--", "source.yaml"],
            "procedure.format",
            {"podway.procedure-source-result/v1"},
        ),
    )


def test_authoring_checks_require_supported_result_schemas(repository):
    native, _ = authored()
    path = repository / "source.yaml"
    path.write_text(yaml.safe_dump(native))
    client = Oracle(repository)
    prep.author_checks(client, path, format_source=True)
    calls = {call.args[1]: call.args[2] for call in client.read.call_args_list}
    assert calls["procedure.format"] == {
        "podway.procedure-source-result/v1",
        "podway.procedure-diagnostics-result/v1",
    }
    for operation in ["validate", "vet", "lint"]:
        assert calls["procedure." + operation] == {
            "podway.procedure-diagnostics-result/v1"
        }


@pytest.mark.parametrize(
    "invalid", [None, [], {"schema": "aquarium.assignment/v2", "role": "judge"}]
)
def test_library_rejects_invalid_ordinary_assignment_without_attribute_errors(
    repository, invalid
):
    assert_code("incompatible", lambda: prep.select(repository, invalid))


def test_boolean_adequacy_or_limitation_is_not_current_fit_evidence(repository):
    value = assignment(repository)
    value["target"]["procedure_plan"]["source_dispositions"][
        "aquarium-task-v2.yaml"
    ] = True
    assert_code("not-established", lambda: prep.select(repository, value))


def select_herdr(value):
    review = {
        "route": "herdr",
        "team": ["Claude"],
        "transmission": ["approved exact source"],
    }
    value["authority"]["review"] = copy.deepcopy(review)
    value["target"]["procedure_plan"]["review"] = review


def test_provider_specialized_source_without_route_choice_can_be_prepared(repository):
    value = assignment(repository, mode="prepare")
    select_herdr(value)
    value["target"]["procedure_plan"]["drafts"][0]["document"]["node_definitions"][
        "deliver"
    ]["instructions"] = [
        "Preserve the selected Herdr Claude review; independent continuity qualification remains due."
    ]
    result = prep.prepare(repository, value, client=Oracle(repository))
    target = result["assignment"]["target"]["prepared_definition"]
    assert target["coverage_plan"]["review"] == value["authority"]["review"]
    assert target["coverage_plan"]["review_continuity"]["status"] == "not-established"
    assert target["assessment"] == "TASK-141-exact-target-suitability-required"
    assert result["assignment"]["authority"] == value["authority"]


def test_unrelated_same_name_choice_is_bookkeeping_not_a_route_capability(repository):
    value = assignment(repository)
    select_herdr(value)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    draft["document"]["node_definitions"]["finish"]["items"].append(
        {
            "id": "review-route",
            "type": "choice",
            "required": True,
            "prompt": "Classify a historical example in the delivered document",
            "choices": ["example-a", "example-b"],
        }
    )
    selected = prep.select(repository, value)
    assert selected["plan"]["review_continuity"]["declarations_checked"] == []
    assert selected["plan"]["review_continuity"]["status"] == "not-established"


def test_actual_mapped_route_contradiction_rejects_at_owning_placement(repository):
    value = assignment(repository)
    select_herdr(value)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    draft["mapping"]["nodes"]["deliver"]["capabilities"] = [
        {
            "signature": "aquarium.task.review-routing/v1",
            "fields": {"effective-review-route": "provider"},
        }
    ]
    draft["document"]["node_definitions"]["deliver"]["items"].append(
        {
            "id": "provider",
            "type": "choice",
            "required": True,
            "prompt": "Select the current technical reviewer",
            "choices": ["mulgae"],
        }
    )
    assert_code("incompatible", lambda: prep.select(repository, value))
    draft["document"]["node_definitions"]["deliver"]["items"][-1]["choices"] = ["herdr"]
    selected = prep.select(repository, value)
    assert selected["plan"]["review_continuity"]["declarations_checked"] == [
        {"node": "deliver", "item": "provider"}
    ]
    assert selected["plan"]["review_continuity"]["status"] == "not-established"


@pytest.mark.parametrize(
    "identifier,version",
    [
        (["broken"], "1"),
        ("foreign-source", ["1"]),
        (True, "1"),
        ("foreign-source", None),
        ("foreign-source", 1),
    ],
)
def test_invalid_historical_identity_types_are_diagnostic_not_authoring_blockers(
    repository, identifier, version
):
    value = assignment(repository, mode="prepare")
    root = repository / "definitions"
    root.mkdir()
    (root / "broken.old").write_text(
        yaml.safe_dump(
            {"schema": "podway.procedure/v2", "id": identifier, "version": version}
        )
    )
    result = prep.prepare(repository, value, client=Oracle(repository))
    assert result["status"] == "prepared"
    assert any(
        row.get("path") == "definitions/broken.old"
        and row["status"] == "native-invalid"
        for row in result["considered"]
    )


def test_foreign_nondigit_native_versions_remain_valid_discovery_identities(repository):
    assignment(repository)
    root = repository / "definitions"
    root.mkdir()
    native, _ = authored()
    native.update(id="foreign-source", version="stable+한글")
    path = root / "foreign.old"
    path.write_text(yaml.safe_dump(native))
    found, diagnostics = prep.discover(repository, {"discovery_roots": ["definitions"]})
    assert any(
        row["id"] == native["id"] and row["version"] == native["version"]
        for row in found
    )
    assert diagnostics == []
    identifier, version = prep.allocate_identity(repository, [root], "task", {})
    assert identifier.startswith("aquarium-adapt-task-")
    assert version == "1"


def test_known_reuse_preserves_structural_review_contract_without_extra_suitability(
    repository,
):
    value = assignment(repository)
    known_candidate(repository, value)
    selected = prep.select(repository, value)
    assert selected["plan"]["review_continuity"]["status"] == "known-contract-preserved"
    assert selected["assessment"] == "preserve-original-checkpoints"


def test_unknown_operation_field_names_do_not_establish_review_semantics(repository):
    value = assignment(repository)
    select_herdr(value)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    draft["mapping"]["nodes"]["deliver"]["capabilities"] = [
        {
            "signature": "example.unknown-operation/v1",
            "fields": {"review-route": "historical-provider"},
        }
    ]
    draft["document"]["node_definitions"]["deliver"]["items"].append(
        {
            "id": "historical-provider",
            "type": "choice",
            "required": True,
            "prompt": "Classify the historical sample",
            "choices": ["mulgae"],
        }
    )
    selected = prep.select(repository, value)
    assert selected["plan"]["review_continuity"]["status"] == "not-established"
    assert selected["plan"]["review_continuity"]["declarations_checked"] == []


def managed_custom(repository):
    path = repository / ".podway/procedures/aquarium-task-v2.yaml"
    path.parent.mkdir(parents=True)
    native = yaml.safe_load(
        (
            ROOT / "plugins/aquarium/assets/podway/procedures/aquarium-task-v2.yaml"
        ).read_bytes()
    )
    native["node_definitions"]["plan-record"]["instructions"].append(
        "Preserve the repository-specific API error guarantee."
    )
    path.write_text(yaml.safe_dump(native, sort_keys=False))
    return path


@pytest.mark.parametrize("reuse", [False, True])
def test_actual_managed_custom_authority_precedes_fit_even_outside_discovery_roots(
    repository, reuse
):
    value = assignment(repository)
    path = managed_custom(repository)
    if reuse:
        known_candidate(repository, value)
    assert_code("not-established", lambda: prep.select(repository, value))
    value["target"]["procedure_plan"]["customization_disposition"] = (
        "Preserve the repository-specific API error guarantee through the original-source assessment and delivery obligation; no retirement is approved."
    )
    selected = prep.select(repository, value)
    authority = selected["plan"]["source_authority"]
    assert authority["managed_sources"][0]["classification"] == "local_customization"
    assert authority["managed_sources"][0]["sha256"] == bundles.sha256(
        path.read_bytes()
    )
    assert authority["managed_sources"][0]["original_text"] == path.read_text()
    assert (
        authority["semantic_completeness"]
        == "requires-independent-original-source-assessment"
    )
    assert selected["kind"] == ("reuse" if reuse else "author")


def test_meaningful_managed_preservation_basis_permits_approved_preparation(repository):
    value = assignment(repository, mode="prepare")
    managed_custom(repository)
    value["target"]["procedure_plan"]["customization_disposition"] = (
        "Retain the custom API error guarantee in delivery and independently assess its complete original source; no obligation is removed."
    )
    result = prep.prepare(repository, value, client=Oracle(repository))
    assert result["status"] == "prepared"
    assert (
        result["assignment"]["target"]["prepared_definition"]["coverage_plan"][
            "source_authority"
        ]["managed_sources"][0]["classification"]
        == "local_customization"
    )


def test_arbitrary_same_id_template_is_not_adopted_authority(repository):
    value = assignment(repository)
    path = repository / "definitions/templates/aquarium-task-v2.yaml"
    path.parent.mkdir(parents=True)
    raw = (
        ROOT / "plugins/aquarium/assets/podway/procedures/aquarium-task-v2.yaml"
    ).read_bytes()
    path.write_bytes(raw + b"\n# Optional template example\n")
    assert (
        prep.select(repository, value)["plan"]["source_authority"]["managed_sources"]
        == []
    )


@pytest.mark.parametrize("variant", ["current", "prior", "workaround"])
def test_static_managed_provenance_preserves_canonical_history(repository, variant):
    value = assignment(repository)
    path = repository / ".podway/procedures/aquarium-task-v2.yaml"
    path.parent.mkdir(parents=True)
    raw = (
        ROOT / "plugins/aquarium/assets/podway/procedures/aquarium-task-v2.yaml"
    ).read_bytes()
    if variant == "prior":
        raw = (ROOT / "tests/fixtures/aquarium-task-v31.yaml").read_bytes()
    elif variant == "workaround":
        raw = raw.replace(
            b"        max_item_length: 1200\n        max_total_length: 1000000\n",
            b"        max_item_length: 1000\n",
            1,
        )
    path.write_bytes(raw)
    classification = prep.select(repository, value)["plan"]["source_authority"][
        "managed_sources"
    ][0]["classification"]
    assert (
        classification
        == {
            "current": "current_canonical",
            "prior": "prior_canonical",
            "workaround": "podway_v0.2.5_workaround",
        }[variant]
    )


def run_preparation_cli(repository, raw, *, podway=None):
    return subprocess.run(
        [
            sys.executable,
            str(SHARED / "prepare_adaptive_procedure.py"),
            "--repository",
            str(repository),
            "--assignment",
            "-",
            *(["--podway", str(podway)] if podway is not None else []),
        ],
        input=raw,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.parametrize("invalid", [5, [{}], [], 0, False])
@pytest.mark.parametrize("reference", ["base", "revision_of"])
def test_malformed_source_references_return_public_json_errors(
    repository, reference, invalid
):
    value = assignment(
        repository, mode="prepare" if reference == "revision_of" else "plan-only"
    )
    draft = value["target"]["procedure_plan"]["drafts"][0]
    if reference == "base":
        draft["kind"] = "adapt"
    draft[reference] = invalid
    before = {path.relative_to(repository) for path in repository.rglob("*")}
    result = run_preparation_cli(
        repository,
        json.dumps(value),
        podway=repository / "must-not-run" if reference == "revision_of" else None,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "invalid-input"
    assert result.stderr == ""
    assert {path.relative_to(repository) for path in repository.rglob("*")} == before


def test_valid_adaptation_and_revision_references_prepare_normally(repository):
    value = assignment(repository, mode="prepare")
    root = repository / "definitions"
    root.mkdir()
    native, _ = authored()
    native["id"] = "aquarium-adapt-task-existing"
    native["version"] = "9"
    source = root / "previous.custom"
    source.write_text(yaml.safe_dump(native))
    reference = {
        "path": str(source.relative_to(repository)),
        "sha256": bundles.sha256(source.read_bytes()),
    }
    draft = value["target"]["procedure_plan"]["drafts"][0]
    draft.update(kind="adapt", base=reference, revision_of=reference)
    result = prep.prepare(repository, value, client=Oracle(repository))
    prepared = result["assignment"]["target"]["prepared_definition"]
    produced = yaml.safe_load(Path(prepared["source_path"]).read_bytes())
    assert produced["id"] == native["id"]
    assert produced["version"] == "10"


def test_null_optional_revision_preserves_new_identity_preparation(repository):
    value = assignment(repository, mode="prepare")
    value["target"]["procedure_plan"]["drafts"][0]["revision_of"] = None
    result = prep.prepare(repository, value, client=Oracle(repository))
    target = result["assignment"]["target"]["prepared_definition"]
    produced = yaml.safe_load(Path(target["source_path"]).read_bytes())
    assert produced["id"].startswith("aquarium-adapt-task-")
    assert produced["version"] == "1"


@pytest.mark.parametrize(
    "field,invalid",
    [
        ("source_dispositions", None),
        ("source_dispositions", []),
        ("criterion_links", None),
        ("criterion_links", []),
    ],
)
def test_malformed_optional_containers_return_typed_json(repository, field, invalid):
    value = assignment(repository)
    value["target"]["procedure_plan"][field] = invalid
    result = run_preparation_cli(repository, json.dumps(value))
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "invalid-input"
    assert result.stderr == ""


@pytest.mark.parametrize("case", ["source", "candidate", "mapping-nodes", "section"])
def test_nested_malformed_assignment_is_json_failure(repository, case):
    value = assignment(repository)
    plan = value["target"]["procedure_plan"]
    if case == "source":
        value["work"]["requirement_sources"] = ["not-an-object"]
    elif case == "candidate":
        plan["candidates"] = ["not-an-object"]
    elif case == "mapping-nodes":
        plan["drafts"][0]["mapping"]["nodes"] = []
    else:
        value["work"]["requirement_sources"][0].pop("format")
        value["work"]["requirement_sources"][0]["section"] = ["unsupported"]
    result = run_preparation_cli(repository, json.dumps(value))
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "invalid-input"
    assert result.stderr == ""


def test_deep_json_parser_returns_typed_json_without_numeric_caps(repository):
    result = run_preparation_cli(repository, "[" * 2000 + "]" * 2000)
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "invalid-input"
    assert result.stderr == ""


@pytest.mark.parametrize("fence", ["```", "~~~~"])
def test_markdown_section_preserves_fenced_heading_text_and_real_boundaries(fence):
    body = (
        "First obligation.\n"
        + fence
        + "\n# Run the migration\nAcceptance\n----------\n"
        + fence
        + "\nSecond obligation.\n### Details\nPreserve errors.\n"
    )
    text_value = (
        "# Scope\nUnselected.\n## Acceptance\n" + body + "## Following\nOutside.\n"
    )
    assert prep.markdown_section(text_value, "## Acceptance") == body


def test_markdown_duplicate_heading_is_ambiguous_and_setext_selector_is_supported():
    assert_code(
        "not-established",
        lambda: prep.markdown_section(
            "## Acceptance\nA\n## Acceptance\nB\n", "## Acceptance"
        ),
    )
    assert (
        prep.markdown_section(
            "Goal\n====\nFirst.\nSubgoal\n-------\nSecond.\nNext\n====\nOutside.\n",
            "Goal",
        )
        == "First.\nSubgoal\n-------\nSecond.\n"
    )
    assert (
        prep.markdown_section("  ## Goal\nBody.\n## Next\nOutside.\n", "## Goal")
        == "Body.\n"
    )
    assert_code(
        "not-established", lambda: prep.markdown_section("No headings here.", "Goal")
    )


@pytest.mark.parametrize("role", ["adopted_customization", "adopted", None, []])
def test_unknown_requirement_role_cannot_silently_drop_source(repository, role):
    value = assignment(repository)
    value["work"]["requirement_sources"][0]["role"] = role
    assert_code("invalid-input", lambda: prep.select(repository, value))


@pytest.mark.parametrize("family", ["Task", "unknown", []])
def test_unknown_requirement_family_cannot_silently_drop_source(repository, family):
    value = assignment(repository)
    value["work"]["requirement_sources"][0]["family"] = family
    assert_code("invalid-input", lambda: prep.select(repository, value))


def test_recognized_optional_and_other_family_sources_remain_conditional(repository):
    value = assignment(repository)
    for role, family in [
        ("template", None),
        ("historical", "task"),
        ("requirements", "design"),
    ]:
        value["work"]["requirement_sources"].append(
            {
                "id": role + str(family),
                "path": "absent.optional",
                "sha256": "absent",
                "role": role,
                "family": family,
            }
        )
    assert prep.select(repository, value)["kind"] == "author"


@pytest.mark.parametrize("disposition", [True, ["preserve"], {"preserve": True}])
def test_truthy_custom_disposition_is_not_preservation_basis(repository, disposition):
    value = assignment(repository)
    managed_custom(repository)
    value["target"]["procedure_plan"]["customization_disposition"] = disposition
    assert_code("not-established", lambda: prep.select(repository, value))


@pytest.mark.parametrize(
    "invalid",
    [
        "reviewed: 2023-02-29\n",
        "value: !!int nope\n",
        "value: !!float nope\n",
        "value: " + "[" * 2000 + "]" * 2000,
    ],
)
def test_constructor_and_depth_failures_are_per_file_history_diagnostics(
    repository, invalid
):
    value = assignment(repository)
    path = repository / "definitions/old.invalid"
    path.parent.mkdir()
    path.write_text(invalid)
    selected = prep.select(repository, value)
    assert any(
        row.get("path") == "definitions/old.invalid"
        and row["status"] == "native-invalid"
        for row in selected["considered"]
    )
    assert prep.allocate_identity(repository, [path.parent], "task", {})[1] == "1"
    assert_code(
        "native-invalid",
        lambda: prep.document(
            repository,
            {
                "path": str(path.relative_to(repository)),
                "sha256": bundles.sha256(path.read_bytes()),
            },
        ),
    )


def drift_setup(repository, case):
    value = assignment(repository, mode="prepare")
    if case in {"candidate", "binding"}:
        source = known_candidate(repository, value)
        if case == "candidate":
            return value, source
        client = Oracle(repository)
        path = repository / "binding.json"
        path.write_bytes(
            canonical_json(
                admission.reference_binding(source.read_bytes(), client.preview(source))
            )
        )
        value["target"]["procedure_plan"]["candidates"][0]["binding"] = {
            "path": path.name,
            "sha256": bundles.sha256(path.read_bytes()),
        }
        return value, path
    if case == "base":
        draft = value["target"]["procedure_plan"]["drafts"][0]
        path = repository / "base.yaml"
        path.write_text(yaml.safe_dump(draft["document"]))
        draft.update(
            kind="adapt",
            base={"path": path.name, "sha256": bundles.sha256(path.read_bytes())},
        )
        return value, path
    return value, repository / "requirements.json"


@pytest.mark.parametrize("case", ["candidate", "binding", "base"])
def test_candidate_binding_and_base_drift_stop_before_writes(repository, case):
    value, path = drift_setup(repository, case)
    path.write_bytes(path.read_bytes() + b"\n")
    assert_code(
        "source-drift",
        lambda: prep.prepare(repository, value, client=Oracle(repository)),
    )
    assert not (repository / "definitions/.candidates").exists()


@pytest.mark.parametrize("case", ["candidate", "binding", "base", "requirements"])
def test_mid_preparation_original_basis_drift_cleans_owned_stage(repository, case):
    value, path = drift_setup(repository, case)
    client = Oracle(repository)
    original = client._read

    def mutate(argv, command, schemas):
        result = original(argv, command, schemas)
        if command == "version":
            path.write_bytes(path.read_bytes() + b"\n")
        return result

    client.read.side_effect = mutate
    assert_code("source-drift", lambda: prep.prepare(repository, value, client=client))
    assert not list((repository / "definitions/.candidates").glob(".prepare-*"))


@pytest.mark.parametrize("change", ["tuple", "source"])
def test_native_tuple_and_raw_source_currency_are_distinct(repository, change):
    value = assignment(repository, mode="prepare")
    client = Oracle(repository)
    original = client.identity

    def mutate(path):
        key = original(path)
        if change == "tuple":
            return key[:2] + ("sha256:" + "0" * 64,)
        Path(path).write_bytes(
            Path(path).read_bytes() + b"\n# Source bytes changed after preview\n"
        )
        return key

    client.identity = mutate
    assert_code("source-drift", lambda: prep.prepare(repository, value, client=client))
    assert not list((repository / "definitions/.candidates").glob(".prepare-*"))


def test_identical_known_candidate_reuses_existing_exact_bundle(repository):
    value = assignment(repository, mode="prepare")
    known_candidate(repository, value)
    first = prep.prepare(repository, value, client=Oracle(repository))
    second = prep.prepare(repository, value, client=Oracle(repository))
    assert (
        first["assignment"]["target"]["prepared_definition"]["path"]
        == second["assignment"]["target"]["prepared_definition"]["path"]
    )
    assert first["binding"] == second["binding"]
    assert (
        len(
            [
                path
                for path in (repository / "definitions/.candidates").iterdir()
                if path.is_dir()
            ]
        )
        == 1
    )


def test_valid_judge_assignment_reaches_worker_role_boundary(repository):
    value = assignment(repository)
    value["role"] = "judge"
    spec = importlib.util.spec_from_file_location(
        "role_boundary_assignment",
        ROOT / "plugins/aquarium/skills/goal-judge/scripts/ordinary_assignment.py",
    )
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    assert validator.prepare(value) == value
    assert_code("incompatible", lambda: prep.select(repository, value))


def test_retention_parent_identity_change_cannot_redirect_publication(
    repository, monkeypatch
):
    value = assignment(repository, mode="prepare")
    client = Oracle(repository)
    original = prep.author_checks
    saved = repository / "saved-candidates"

    def replace_parent(*args, **kwargs):
        result = original(*args, **kwargs)
        stage = Path(args[1]).parent
        local = stage.parent
        local.rename(saved)
        local.mkdir()
        replacement = local / stage.name
        replacement.mkdir()
        (replacement / "procedure.yaml").write_bytes(
            (saved / stage.name / "procedure.yaml").read_bytes()
        )
        (replacement / "sentinel").write_text("preserve replacement")
        return result

    monkeypatch.setattr(prep, "author_checks", replace_parent)
    assert_code("unsafe", lambda: prep.prepare(repository, value, client=client))
    assert list((repository / "definitions/.candidates").glob(".prepare-*/sentinel"))
    assert not list(saved.glob(".prepare-*"))


def test_unowned_stage_replacement_is_never_cleaned_or_published(repository):
    value = assignment(repository, mode="prepare")
    client = Oracle(repository)
    original = client.identity
    replaced = []

    def replace_stage(path):
        key = original(path)
        stage = Path(path).parent
        if not replaced and stage.name.startswith(".prepare-"):
            moved = stage.with_name(stage.name + "-owned")
            stage.rename(moved)
            stage.mkdir()
            (stage / "procedure.yaml").write_bytes(
                (moved / "procedure.yaml").read_bytes()
            )
            (stage / "sentinel").write_text("unowned replacement")
            replaced.append(stage)
        return key

    client.identity = replace_stage
    assert_code("unsafe", lambda: prep.prepare(repository, value, client=client))
    assert (replaced[0] / "sentinel").read_text() == "unowned replacement"
    assert (replaced[0] / "procedure.yaml").is_file()


def test_competing_publication_target_is_preserved_with_typed_conflict(
    repository, monkeypatch
):
    value = assignment(repository, mode="prepare")
    original = prep._rename_exclusive
    targets = []

    def compete(parent, temporary, candidate):
        path = repository / "definitions/.candidates" / candidate
        path.mkdir()
        (path / "sentinel").write_text("competing target")
        targets.append(path)
        return original(parent, temporary, candidate)

    monkeypatch.setattr(prep, "_rename_exclusive", compete)
    assert_code(
        "publication-conflict",
        lambda: prep.prepare(repository, value, client=Oracle(repository)),
    )
    assert (targets[0] / "sentinel").read_text() == "competing target"
    assert not list((repository / "definitions/.candidates").glob(".prepare-*"))


def test_postpublication_bundle_bytes_are_verified_before_success(
    repository, monkeypatch
):
    value = assignment(repository, mode="prepare")
    original = prep._rename_exclusive

    def corrupt(parent, temporary, candidate):
        result = original(parent, temporary, candidate)
        path = repository / "definitions/.candidates" / candidate / "procedure.yaml"
        path.write_bytes(path.read_bytes() + b"\n# Changed after publication\n")
        return result

    monkeypatch.setattr(prep, "_rename_exclusive", corrupt)
    assert_code(
        "corrupt", lambda: prep.prepare(repository, value, client=Oracle(repository))
    )


def test_cleanup_failure_is_explicit_and_preserves_original_failure(
    repository, monkeypatch
):
    value = assignment(repository, mode="prepare")
    client = Oracle(repository)
    client.read.side_effect = bundles.BundleError(
        "native-invalid", "Synthetic authoring rejection"
    )
    original = prep.os.unlink

    def fail_cleanup(path, *args, **kwargs):
        if path == "procedure.yaml" and "dir_fd" in kwargs:
            raise PermissionError("Synthetic cleanup denial")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(prep.os, "unlink", fail_cleanup)
    with pytest.raises(bundles.BundleError) as caught:
        prep.prepare(repository, value, client=client)
    assert caught.value.code == "runtime-failure"
    assert caught.value.details["preparation_failure"] == "native-invalid"
    assert list(
        (repository / "definitions/.candidates").glob(".prepare-*/procedure.yaml")
    )


def test_markdown_closing_fence_followed_by_thematic_break_preserves_whole_body():
    body = "First obligation.\n\n```text\n# Example\n```\n---\nSecond obligation.\n\n"
    assert (
        prep.markdown_section("## Target\n" + body + "## Next\nOther.\n", "## Target")
        == body
    )
    assert (
        prep.markdown_section(
            "Target\n------\nFirst.\n\nNext\n----\nOther.\n", "Target"
        )
        == "First.\n\n"
    )


@pytest.mark.parametrize(
    "previous", ["### Nested", "- List item", "> Quoted heading", "***"]
)
def test_markdown_block_structure_is_not_a_setext_paragraph_title(previous):
    body = previous + "\n---\nSecond obligation.\n"
    assert (
        prep.markdown_section("## Target\n" + body + "## Next\nOther.\n", "## Target")
        == body
    )


@pytest.mark.parametrize(
    "case",
    [
        "obligations-list",
        "definition-scalar",
        "obligation-scalar",
        "capability-fields-list",
        "definition-items-scalar",
    ],
)
def test_consumed_fit_containers_fail_as_public_json_input_errors(repository, case):
    value = assignment(repository)
    draft = value["target"]["procedure_plan"]["drafts"][0]
    if case == "obligations-list":
        draft["mapping"]["obligations"] = []
    elif case == "definition-scalar":
        draft["document"]["node_definitions"]["deliver"] = 5
    elif case == "obligation-scalar":
        draft["mapping"]["obligations"]["original-work"] = 5
    elif case == "capability-fields-list":
        draft["mapping"]["nodes"]["deliver"]["capabilities"] = [
            {"signature": "unknown", "fields": []}
        ]
    else:
        draft["document"]["node_definitions"]["deliver"]["items"] = 5
    result = run_preparation_cli(repository, json.dumps(value))
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "invalid-input"
    assert result.stderr == ""
