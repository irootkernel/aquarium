"""Storage/admission behavior with synthetic native oracles, never execution proof."""

import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SHARED = ROOT / "plugins/aquarium/shared"
sys.path.insert(0, str(SHARED))
import adaptive_admission as admission
import adaptive_bundles as bundles
import adaptive_definitions as definitions

SPEC = importlib.util.spec_from_file_location(
    "selected_inspect_tools",
    ROOT / "plugins/aquarium/skills/dev-setup/scripts/inspect_tools.py",
)
inspector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inspector)


def git(repository, *args):
    return subprocess.run(
        ["git", "-C", str(repository), *args], capture_output=True, check=True
    )


@pytest.fixture
def repository(tmp_path):
    repository = tmp_path / "work tree 한글"
    repository.mkdir()
    git(repository, "init", "-q")
    return repository.resolve()


class Oracle:
    """Synthetic source identity oracle for isolated behavior tests."""

    def __init__(self, repository):
        self.repository = repository
        self.health = Mock(return_value=None)

    def preview(self, path):
        source = bundles.read_regular(self.repository, Path(path))
        value = yaml.safe_load(source)
        if not isinstance(value, dict) or not {"id", "version"} <= value.keys():
            raise bundles.BundleError(
                "native-invalid", "Synthetic native parser rejected source"
            )
        return {
            "procedure_id": value["id"],
            "procedure_version": value["version"],
            "procedure_digest": bundles.sha256(source),
        }

    def identity(self, path):
        value = self.preview(path)
        return tuple(
            value[field]
            for field in ("procedure_id", "procedure_version", "procedure_digest")
        )


@pytest.fixture
def known(repository):
    source = (
        ROOT / "plugins/aquarium/assets/podway/procedures/aquarium-task-v2.yaml"
    ).read_bytes()
    path = repository / "sources/task source.yaml"
    path.parent.mkdir()
    path.write_bytes(source)
    client = Oracle(repository)
    binding = admission.reference_binding(source, client.preview(path))
    return source, path, client, binding


def publish(repository, known, roots=("flows", "other flows"), write_root="flows"):
    source, path, client, binding = known
    return bundles.publish_bundle(
        repository,
        roots,
        write_root,
        source,
        binding,
        qualify=lambda raw, mapping: admission.qualify_known(
            raw, mapping, client.preview(path)
        ),
        native_identity=client.identity,
    )


def test_publish_resolve_and_resume_self_contained(repository, known):
    source, _path, client, binding = known
    result = publish(repository, known)
    assert result["status"] == "resolved"
    assert result["source"] == source
    assert (repository / "flows/.local/.gitignore").read_bytes() == b"*\n"
    assert git(repository, "status", "--porcelain", "--", "flows").stdout == b""
    resolved = admission.resume_selected(
        repository, ["flows", "other flows"], binding["procedure"], client=client
    )
    assert resolved["bundle_id"] == definitions.definition_id(binding)
    assert (
        publish(repository, known, write_root="other flows")["path"] == result["path"]
    )
    assert not (repository / "other flows").exists()


def test_retained_v1_bundle_resolves_without_relabeling(repository):
    source = (ROOT / "tests/fixtures/aquarium-task-v33.yaml").read_bytes()
    path = repository / "task.yaml"
    path.write_bytes(source)
    client = Oracle(repository)
    binding = admission.reference_binding(source, client.preview(path))
    assert binding["schema"] == "aquarium.procedure-binding/v1"
    original = definitions.canonical_json(binding)
    result = publish(repository, (source, path, client, binding))
    resolved = admission.resume_selected(
        repository, ["flows"], binding["procedure"], client=client
    )
    assert resolved["bundle_id"] == result["bundle_id"]
    assert resolved["source"] == source
    assert definitions.canonical_json(resolved["binding"]) == original
    assert (Path(result["path"]) / "binding.json").read_bytes() == original
    with pytest.raises(bundles.BundleError) as caught:
        admission.selection_contract(
            source,
            binding,
            "task-handler",
            route=None,
            qualification={"assignment": {"schema": "aquarium.assignment/v3"}},
        )
    assert caught.value.code == "retained-contract"


def test_identical_aliases_and_native_tuple_verification(repository, known):
    result = publish(repository, known)
    target = repository / "other flows/.local" / result["bundle_id"]
    target.parent.mkdir(parents=True)
    (target.parent / ".gitignore").write_text("*\n")
    shutil.copytree(result["path"], target)
    client = known[2]
    resolved = bundles.resolve_bundle(
        repository,
        ["flows", "other flows"],
        definitions.native_key(known[3]),
        native_identity=client.identity,
    )
    assert resolved["status"] == "resolved" and len(resolved["aliases"]) == 2
    assert (
        bundles.resolve_bundle(repository, ["flows"], definitions.native_key(known[3]))[
            "status"
        ]
        == "not-established"
    )
    mapping = copy.deepcopy(known[3])
    mapping["procedure"]["digest"] = "sha256:" + "0" * 64
    forged = definitions.definition_id(mapping)
    forged_path = repository / "flows/.local" / forged
    forged_path.mkdir()
    (forged_path / "procedure.yaml").write_bytes(known[0])
    (forged_path / "binding.json").write_bytes(definitions.canonical_json(mapping))
    assert (
        bundles.resolve_bundle(
            repository,
            ["flows"],
            definitions.native_key(mapping),
            native_identity=client.identity,
        )["status"]
        == "corrupt"
    )


def test_mapping_conflict_across_roots_stops_without_replacing(repository, known):
    result = publish(repository, known)
    mapping = copy.deepcopy(known[3])
    mapping["parameters"]["extra"] = {
        "type": "text",
        "required": False,
        "description": "Changed mapping",
    }
    target = repository / "other flows/.local" / definitions.definition_id(mapping)
    target.mkdir(parents=True)
    (target.parent / ".gitignore").write_text("*\n")
    (target / "procedure.yaml").write_bytes(known[0])
    (target / "binding.json").write_bytes(definitions.canonical_json(mapping))
    resolved = bundles.resolve_bundle(
        repository,
        ["flows", "other flows"],
        definitions.native_key(mapping),
        native_identity=known[2].identity,
    )
    assert resolved["status"] == "ambiguous"
    with pytest.raises(bundles.BundleError) as error:
        publish(repository, known)
    assert error.value.code == "ambiguous"
    assert Path(result["path"]).is_dir() and target.is_dir()


def test_competing_writers_share_worktree_uniqueness(repository, known):
    with ThreadPoolExecutor(max_workers=2) as executors:
        results = list(
            executors.map(
                lambda root: publish(repository, known, write_root=root),
                ["flows", "other flows"],
            )
        )
    assert results[0]["path"] == results[1]["path"]
    assert len(list(repository.glob("*/.local/" + results[0]["bundle_id"]))) == 1


@pytest.mark.parametrize(
    "damage",
    [
        "source",
        "missing-binding",
        "unknown-schema",
        "compatibility",
        "nonstring-schema",
    ],
)
def test_selected_damage_is_distinct_and_preserves_files(repository, known, damage):
    result = publish(repository, known)
    path = Path(result["path"])
    if damage == "source":
        (path / "procedure.yaml").write_bytes(b"broken source")
    elif damage == "missing-binding":
        (path / "binding.json").unlink()
    else:
        value = json.loads((path / "binding.json").read_bytes())
        value["schema" if damage != "compatibility" else "compatibility"] = (
            []
            if damage == "nonstring-schema"
            else "aquarium.procedure-binding/v999"
            if damage == "unknown-schema"
            else "aquarium.adaptive/v999"
        )
        (path / "binding.json").write_bytes(definitions.canonical_json(value))
    resolved = bundles.resolve_bundle(
        repository,
        ["flows"],
        definitions.native_key(known[3]),
        native_identity=known[2].identity,
    )
    assert resolved["status"] == (
        "unsupported" if damage in {"unknown-schema", "compatibility"} else "corrupt"
    )
    assert path.is_dir()


def test_unrelated_invalid_historical_and_partial_preparation_do_not_block(
    repository, known
):
    result = publish(repository, known)
    local = repository / "flows/.local"
    (local / ".prepare-old").mkdir()
    historical = local / ("f" * 64)
    historical.mkdir()
    (historical / "binding.json").write_text("unreadable historical file")
    resolved = bundles.resolve_bundle(
        repository,
        ["flows"],
        definitions.native_key(known[3]),
        native_identity=known[2].identity,
    )
    assert resolved["status"] == "resolved" and resolved["path"] == result["path"]
    assert resolved["diagnostics"][0]["key_established"] is False
    assert (local / ".prepare-old").is_dir()


@pytest.mark.parametrize("kind", ["root", "bundle", "file"])
def test_symlink_sources_and_aliases_are_not_followed(
    repository, known, tmp_path, kind
):
    result = publish(repository, known)
    if kind == "root":
        (repository / "linked").symlink_to(tmp_path, target_is_directory=True)
        with pytest.raises(bundles.BundleError) as error:
            bundles.resolve_bundle(
                repository,
                ["linked"],
                definitions.native_key(known[3]),
                native_identity=known[2].identity,
            )
        assert error.value.code == "unsafe"
    elif kind == "bundle":
        local = repository / "other flows/.local"
        local.mkdir(parents=True)
        (local / result["bundle_id"]).symlink_to(
            result["path"], target_is_directory=True
        )
        assert (
            bundles.resolve_bundle(
                repository,
                ["flows", "other flows"],
                definitions.native_key(known[3]),
                native_identity=known[2].identity,
            )["status"]
            == "unsafe"
        )
    else:
        path = Path(result["path"]) / "procedure.yaml"
        path.unlink()
        path.symlink_to(known[1])
        assert (
            bundles.resolve_bundle(
                repository,
                ["flows"],
                definitions.native_key(known[3]),
                native_identity=known[2].identity,
            )["status"]
            == "unsafe"
        )


@pytest.mark.parametrize(
    "policy",
    ["custom-conflict", "fake-name-only", "tracked-target", "tracked-good-ignore"],
)
def test_actual_ignore_and_tracking_policy(repository, known, policy):
    local = repository / "flows/.local"
    local.mkdir(parents=True)
    ignore = local / ".gitignore"
    if policy == "custom-conflict":
        ignore.write_text("unrelated\n")
    elif policy == "fake-name-only":
        ignore.write_text("/" + "0" * 64 + "/\n")
    else:
        ignore.write_text("*\n")
        git(repository, "add", "-f", str(ignore))
        if policy == "tracked-target":
            target = local / definitions.definition_id(known[3])
            target.mkdir()
            (target / "procedure.yaml").write_bytes(known[0])
            (target / "binding.json").write_bytes(definitions.canonical_json(known[3]))
            git(repository, "add", "-f", str(target / "procedure.yaml"))
    before = ignore.read_bytes()
    if policy == "tracked-good-ignore":
        assert publish(repository, known)["status"] == "resolved"
    else:
        with pytest.raises(bundles.BundleError) as error:
            publish(repository, known)
        assert error.value.code in {"ignore-conflict", "tracked-conflict"}
    assert ignore.read_bytes() == before


def test_exclusive_publication_preserves_partial_target_and_cleans_owned_draft(
    repository, known, monkeypatch
):
    local = repository / "flows/.local"
    target = local / definitions.definition_id(known[3])
    target.mkdir(parents=True)
    with pytest.raises(bundles.BundleError) as error:
        publish(repository, known)
    assert error.value.code == "corrupt" and target.is_dir()
    target.rmdir()
    original = bundles._rename_exclusive

    def competing(descriptor, source, destination):
        os.mkdir(destination, dir_fd=descriptor)
        original(descriptor, source, destination)

    monkeypatch.setattr(bundles, "_rename_exclusive", competing)
    with pytest.raises(bundles.BundleError) as error:
        publish(repository, known)
    assert error.value.code == "publication-conflict"
    assert target.is_dir()
    assert not list(local.glob(".prepare-*"))


def test_selected_source_requires_health_and_exact_reference_binding(repository, known):
    source, path, client, binding = known
    result = admission.selected_source(
        repository,
        path,
        roots=["flows"],
        entrypoint="task-handler",
        route="herdr",
        client=client,
    )
    assert result["status"] == "ready"
    client.health.assert_called_once()
    with pytest.raises(bundles.BundleError) as error:
        admission.selected_source(
            repository,
            path,
            roots=["flows"],
            entrypoint="task-handler",
            route="herdr",
            client=client,
            runtime_ready=False,
        )
    assert error.value.code == "runtime-unavailable"
    changed = copy.deepcopy(binding)
    changed["nodes"]["record-plan"]["role"] = "evaluator"
    binding_path = repository / "binding.json"
    binding_path.write_bytes(definitions.canonical_json(changed))
    with pytest.raises(bundles.BundleError) as error:
        admission.selected_source(
            repository,
            path,
            roots=["flows"],
            entrypoint="task-handler",
            route="herdr",
            client=client,
            binding_path=binding_path,
        )
    assert error.value.code == "not-established"
    path.write_bytes(source + b"\n")
    with pytest.raises(bundles.BundleError) as error:
        admission.selected_source(
            repository,
            path,
            roots=["flows"],
            entrypoint="task-handler",
            route="herdr",
            client=client,
        )
    assert error.value.code == "not-established"


def test_known_resume_is_independent_of_actual_origin_and_registry_changes(
    repository, known, tmp_path, monkeypatch
):
    assets = tmp_path / "assets"
    shutil.copytree(ROOT / "plugins/aquarium/assets", assets)
    monkeypatch.setattr(admission, "ASSETS", assets)
    result = publish(repository, known)
    before = definitions.canonical_json(result["binding"])
    shutil.rmtree(assets / "podway/procedures")
    (assets / "adaptive/capability-signatures-v2.json").write_text(
        "changed registry is not this mapping's dependency"
    )
    resumed = admission.resume_selected(
        repository, ["flows"], known[3]["procedure"], client=known[2]
    )
    assert definitions.canonical_json(resumed["binding"]) == before


@pytest.mark.parametrize(
    "valid,exit_status,expected",
    [
        (False, 1, "native-invalid"),
        (False, 0, "native-invalid"),
        (True, 1, "native-invalid"),
        ("false", 0, "unsupported-runtime"),
    ],
)
def test_native_check_preserves_authoritative_rejection_and_exit(
    repository, known, monkeypatch, valid, exit_status, expected
):
    output = {
        "schema": "podway.output/v4",
        "command": "procedure.check",
        "result": {"schema": "podway.procedure-diagnostics-result/v1", "valid": valid},
    }
    monkeypatch.setattr(
        admission.subprocess,
        "run",
        Mock(
            return_value=subprocess.CompletedProcess(
                [], exit_status, json.dumps(output).encode(), b""
            )
        ),
    )
    with pytest.raises(bundles.BundleError) as error:
        admission.NativeClient(repository, "fake").preview(known[1])
    assert error.value.code == expected
    if expected == "native-invalid":
        assert error.value.details == {
            "native_exit_status": exit_status,
            "native_valid": valid,
        }


@pytest.mark.parametrize(
    "payload,expected",
    [
        (
            {"schema": "podway.error/v2", "code": "WORKSPACE_CONTRACT_MISMATCH"},
            "WORKSPACE_CONTRACT_MISMATCH",
        ),
        ([], "unsupported-runtime"),
    ],
)
def test_native_error_codes_and_malformed_envelopes(
    repository, monkeypatch, payload, expected
):
    monkeypatch.setattr(
        admission.subprocess,
        "run",
        Mock(
            return_value=subprocess.CompletedProcess(
                [], 5, json.dumps(payload).encode(), b""
            )
        ),
    )
    with pytest.raises(bundles.BundleError) as error:
        admission.NativeClient(repository, "fake").read(
            ["observe"], "session.observe", {"podway.observation-result/v5"}
        )
    assert error.value.code == expected


def test_missing_leaf_beneath_symlinked_ancestor_is_unsafe(repository, known, tmp_path):
    (repository / "linked").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(bundles.BundleError) as error:
        bundles.resolve_bundle(
            repository,
            ["linked/not-created"],
            definitions.native_key(known[3]),
            native_identity=known[2].identity,
        )
    assert error.value.code == "unsafe"
    assert not (tmp_path / "not-created").exists()
    assert (
        bundles.resolve_bundle(
            repository,
            ["safe/not-created"],
            definitions.native_key(known[3]),
            native_identity=known[2].identity,
        )["status"]
        == "missing"
    )


def test_unknown_rename_outcome_preserves_published_bytes(
    repository, known, monkeypatch
):
    original = bundles._rename_exclusive

    def unknown(descriptor, source, destination):
        original(descriptor, source, destination)
        raise InterruptedError("simulated response loss after rename")

    monkeypatch.setattr(bundles, "_rename_exclusive", unknown)
    with pytest.raises(InterruptedError):
        publish(repository, known)
    result = bundles.resolve_bundle(
        repository,
        ["flows"],
        definitions.native_key(known[3]),
        native_identity=known[2].identity,
    )
    assert result["status"] == "resolved" and result["source"] == known[0]


def test_same_key_comment_variant_reuses_original_bytes_but_changed_mapping_stops(
    repository, known
):
    result = publish(repository, known)
    source = known[0] + b"\n# Different authoring bytes\n"
    mapping = copy.deepcopy(known[3])
    mapping["procedure"]["source_sha256"] = bundles.sha256(source)
    identity = lambda path: definitions.native_key(known[3])
    reused = bundles.publish_bundle(
        repository,
        ["flows", "other flows"],
        "other flows",
        source,
        mapping,
        qualify=lambda raw, binding: None,
        native_identity=identity,
    )
    assert reused["path"] == result["path"] and reused["source"] == known[0]
    mapping["origins"] = [
        {
            "id": "changed-origin",
            "version": "1",
            "sha256": "sha256:" + "d" * 64,
            "source": "optional-library",
        }
    ]
    with pytest.raises(bundles.BundleError) as error:
        bundles.publish_bundle(
            repository,
            ["flows"],
            "flows",
            source,
            mapping,
            qualify=lambda raw, binding: None,
            native_identity=identity,
        )
    assert error.value.code == "ambiguous"


def test_selected_inspector_is_independent_of_aggregate_library_and_provider_health(
    repository, known, monkeypatch
):
    tool = {
        "executable": "synthetic-oracle",
        "runtime_readiness": {
            "state": "ready",
            "session_procedure": None,
            "session_lifecycle": None,
        },
        "managed_procedures": [
            {
                "path": ".podway/procedures/aquarium-design-v2.yaml",
                "update_explanation": "missing",
            }
        ],
        "readiness_status": "degraded",
    }
    monkeypatch.setattr(inspector, "inspect_podway", lambda *args: tool)
    monkeypatch.setattr(admission, "NativeClient", lambda *args: known[2])
    result = inspector.inspect_selected_podway(
        repository,
        30,
        source=known[1],
        roots=["flows"],
        entrypoint="task-handler",
        route="herdr",
    )
    assert result["selected_procedure"]["status"] == "ready"
    assert result["tools"]["podway"]["readiness_status"] == "degraded"
    assert set(result["tools"]) == {"podway"}
    tool["runtime_readiness"]["session_procedure"] = {
        "id": "another-source",
        "version": "1",
        "digest": "sha256:" + "b" * 64,
    }
    tool["runtime_readiness"]["session_lifecycle"] = "running"
    result = inspector.inspect_selected_podway(
        repository,
        30,
        source=known[1],
        roots=["flows"],
        entrypoint="task-handler",
        route="herdr",
    )
    assert result["selected_procedure"]["status"] == "session-conflict"
    assert result["selected_procedure"]["work_identity_reconciliation_required"] is True


def test_missing_adopted_bundle_has_no_legacy_resume_fallback(
    repository, known, monkeypatch
):
    tool = {
        "executable": "synthetic-oracle",
        "runtime_readiness": {
            "state": "ready",
            "session_procedure": known[3]["procedure"],
            "session_lifecycle": "prepared",
        },
        "managed_procedures": [],
    }
    monkeypatch.setattr(inspector, "inspect_podway", lambda *args: tool)
    monkeypatch.setattr(admission, "NativeClient", lambda *args: known[2])
    result = inspector.inspect_selected_podway(
        repository,
        30,
        roots=["flows"],
        entrypoint="task-handler",
        route="herdr",
        resume=True,
    )
    assert result["selected_procedure"]["status"] == "missing"


def test_standalone_missing_dependencies_reports_interpreter_without_native_work(
    repository,
):
    result = subprocess.run(
        [
            sys.executable,
            "-S",
            "-B",
            str(SHARED / "manage_adaptive_procedure.py"),
            "inspect",
            "--repository",
            str(repository),
            "--root",
            "flows",
            "--entrypoint",
            "task-handler",
            "--source",
            "not-created",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    value = json.loads(result.stdout)
    assert value["status"] == "missing-prerequisite" and value["dependency"] in {
        "yaml",
        "jsonschema",
    }
    assert value["interpreter"]
    assert not (repository / ".podway").exists()


@pytest.mark.parametrize(
    "entrypoint,route,expected",
    [
        ("new-project", "herdr", "incompatible"),
        ("task-handler", None, "route-unavailable"),
        ("task-handler", "absent-route", "route-unavailable"),
        ("task-handler", "independent-review", "route-unavailable"),
    ],
)
def test_selected_entrypoint_and_route_are_required(
    repository, known, entrypoint, route, expected
):
    with pytest.raises(bundles.BundleError) as error:
        admission.selected_source(
            repository,
            known[1],
            roots=["flows"],
            entrypoint=entrypoint,
            route=route,
            client=known[2],
        )
    assert error.value.code == expected


def test_same_family_customization_is_disclosed_without_unrelated_template_policy(
    repository, known, monkeypatch
):
    tool = {
        "executable": "oracle",
        "runtime_readiness": {"state": "ready", "session_procedure": None},
        "managed_procedures": [
            {
                "path": ".podway/procedures/aquarium-task-v2.yaml",
                "update_explanation": "local_customization",
            },
            {
                "path": ".podway/procedures/aquarium-design-v2.yaml",
                "update_explanation": "local_customization",
            },
        ],
    }
    monkeypatch.setattr(inspector, "inspect_podway", lambda *args: tool)
    monkeypatch.setattr(admission, "NativeClient", lambda *args: known[2])
    kwargs = {
        "source": known[1],
        "roots": ["flows"],
        "entrypoint": "task-handler",
        "route": "herdr",
    }
    assert (
        inspector.inspect_selected_podway(repository, 30, **kwargs)[
            "selected_procedure"
        ]["status"]
        == "not-established"
    )
    result = inspector.inspect_selected_podway(
        repository,
        30,
        customization_basis="Existing approved envelope preserves the local Task obligation",
        **kwargs,
    )["selected_procedure"]
    assert result["status"] == "ready"
    assert len(result["adopted_customizations"]) == 1
    assert result["adopted_customizations"][0]["path"].endswith("aquarium-task-v2.yaml")


def test_native_reads_bind_cwd_and_respect_authoring_request_contract(
    repository, monkeypatch
):
    run = Mock(
        return_value=subprocess.CompletedProcess(
            [],
            0,
            json.dumps(
                {
                    "schema": "podway.output/v4",
                    "command": "version",
                    "result": {"schema": "version"},
                }
            ).encode(),
            b"",
        )
    )
    monkeypatch.setattr(admission.subprocess, "run", run)
    client = admission.NativeClient(repository, "fake")
    client.read(["version", "--identity"], "version", None)
    assert run.call_args.kwargs["cwd"] == repository
    assert "--worktree" not in run.call_args.args[0]
    run.return_value.stdout = json.dumps(
        {"schema": "podway.output/v4", "command": "procedure.preview", "result": {}}
    ).encode()
    client.read(["procedure", "preview", "source.yaml"], "procedure.preview", None)
    assert "--worktree" not in run.call_args.args[0]
    run.return_value.stdout = json.dumps(
        {"schema": "podway.output/v4", "command": "session.observe", "result": {}}
    ).encode()
    client.read(["observe"], "session.observe", None)
    assert run.call_args.args[0][1:3] == ["--worktree", str(repository)]


def test_known_contract_covers_current_sources_and_stays_stable_when_extended(
    repository, known, tmp_path, monkeypatch
):
    contract = json.loads(
        (admission.ASSETS / "adaptive/known-sources-v2.json").read_text()
    )
    for path in (admission.ASSETS / "podway/procedures").glob("*.yaml"):
        source = path.read_bytes()
        record, document = admission.known_source(source)
        assert record["source_sha256"] == bundles.sha256(source)
        assert set(record["definitions"]) == set(document["node_definitions"])
    assets = tmp_path / "assets"
    (assets / "adaptive").mkdir(parents=True)
    before = admission.reference_binding(known[0], known[2].preview(known[1]))
    contract["sources"].append({"source_sha256": "sha256:" + "0" * 64})
    (assets / "adaptive/known-sources-v2.json").write_text(json.dumps(contract))
    monkeypatch.setattr(admission, "ASSETS", assets)
    assert admission.reference_binding(known[0], known[2].preview(known[1])) == before


@pytest.mark.parametrize(
    "family,version,entrypoint",
    [
        ("task", "32", "task-handler"),
        ("goal", "35", "epic-handler"),
        ("validation", "34", "epic-validator"),
    ],
)
def test_subagent_route_preserves_prior_sources_without_reinterpreting_them(
    family,
    version,
    entrypoint,
):
    current = (
        admission.ASSETS / f"podway/procedures/aquarium-{family}-v2.yaml"
    ).read_bytes()
    prior = (ROOT / f"tests/fixtures/aquarium-{family}-v{version}.yaml").read_bytes()
    admission.selection_contract(
        current,
        admission.reference_mapping(current),
        entrypoint,
        "subagent-review",
        None,
    )
    binding = admission.reference_mapping(prior)
    assert admission.known_source(prior)[0]["version"] == version
    for adaptive in (False, True):
        for route in ("independent-review", "subagent-review"):
            qualification = (
                {"assignment": {"authority": {"review": {"route": route}}}}
                if adaptive
                else None
            )
            with pytest.raises(bundles.BundleError) as error:
                admission.selection_contract(
                    prior, binding, entrypoint, route, qualification
                )
            assert error.value.code == "route-unavailable"
        qualification = (
            {"assignment": {"authority": {"review": {"route": "herdr"}}}}
            if adaptive
            else None
        )
        admission.selection_contract(prior, binding, entrypoint, "herdr", qualification)


@pytest.mark.parametrize(
    "logical,signature",
    [
        ("review-route", "aquarium.goal.review-routing/v2"),
        ("effective-review-route", "aquarium.task.review-routing/v2"),
    ],
)
@pytest.mark.parametrize("aliases", ["default", "current", "history"])
def test_adaptive_route_checks_actual_choices_without_reinterpreting_history(
    logical, signature, aliases
):
    alias = logical if aliases == "default" else "selected-provider"
    prior = logical if aliases == "history" else "prior-review-route"
    document = {
        "node_definitions": {
            "review": {
                "items": [
                    {"id": alias, "type": "choice", "choices": ["independent-review"]},
                    {
                        "id": prior,
                        "type": "choice",
                        "choices": ["independent-review"],
                    },
                ]
            }
        },
        "graph": {"nodes": [{"id": "custom-review", "use": "review"}]},
    }
    binding = {
        "family": "task",
        "entrypoints": ["task-handler"],
        "nodes": {
            "custom-review": {
                "capabilities": [
                    {
                        "signature": signature,
                        "fields": {}
                        if aliases == "default"
                        else {logical: alias, "prior-review-route": prior},
                    }
                ]
            },
        },
    }
    qualification = {
        "assignment": {"authority": {"review": {"route": "subagent-review"}}}
    }

    def select():
        admission.selection_contract(
            yaml.safe_dump(document).encode(),
            binding,
            "task-handler",
            "subagent-review",
            qualification,
        )

    with pytest.raises(bundles.BundleError) as error:
        select()
    assert error.value.code == "route-unavailable"
    document["node_definitions"]["review"]["items"][0]["choices"] = ["subagent-review"]
    select()


@pytest.mark.parametrize("name", ["review-route", "effective-review-route", "example"])
@pytest.mark.parametrize("signature", [None, "aquarium.task.approval/v2"])
def test_adaptive_route_ignores_bookkeeping_names_and_unrelated_capability_aliases(
    name, signature
):
    document = {
        "node_definitions": {
            "example": {
                "items": [
                    {
                        "id": name,
                        "type": "choice",
                        "choices": ["example-a", "example-b"],
                    }
                ]
            }
        },
        "graph": {"nodes": [{"id": "example", "use": "example"}]},
    }
    binding = {
        "family": "task",
        "entrypoints": ["task-handler"],
        "nodes": {
            "example": {
                "capabilities": []
                if signature is None
                else [{"signature": signature, "fields": {"review-route": name}}]
            }
        },
    }
    admission.selection_contract(
        yaml.safe_dump(document).encode(),
        binding,
        "task-handler",
        "subagent-review",
        {"assignment": {"authority": {"review": {"route": "subagent-review"}}}},
    )


def test_renamed_operations_keep_established_effects_and_prior_contracts():
    registry = json.loads(
        (admission.ASSETS / "adaptive/operation-contracts-v1.json").read_bytes()
    )
    for family, version in (("task", 32), ("goal", 35), ("validation", 34)):
        before = yaml.safe_load(
            (ROOT / f"tests/fixtures/aquarium-{family}-v{version}.yaml").read_bytes()
        )
        successor = {"task": 33, "goal": 36, "validation": 35}[family]
        after = yaml.safe_load(
            (ROOT / f"tests/fixtures/aquarium-{family}-v{successor}.yaml").read_bytes()
        )
        changed = []
        for name, definition in before["node_definitions"].items():
            old = bundles.sha256(definitions.canonical_json(definition))
            new = bundles.sha256(
                definitions.canonical_json(after["node_definitions"][name])
            )
            if old == new or old not in registry:
                continue
            assert registry[new]["basis"]["native_version"] == after["version"]
            for field in ("native_id", "definition"):
                assert registry[new]["basis"][field] == registry[old]["basis"][field]
            assert {k: v for k, v in registry[new].items() if k != "basis"} == {
                k: v for k, v in registry[old].items() if k != "basis"
            }
            changed.append(name)
        assert changed


def test_renamed_forged_tuple_blocks_actual_key_even_beside_intact_alias(
    repository, known
):
    valid = publish(repository, known)
    forged = copy.deepcopy(known[3])
    forged["procedure"]["digest"] = "sha256:" + "d" * 64
    path = repository / "other flows/.local" / definitions.definition_id(forged)
    path.mkdir(parents=True)
    (path.parent / ".gitignore").write_text("*\n")
    (path / "binding.json").write_bytes(definitions.canonical_json(forged))
    (path / "procedure.yaml").write_bytes(known[0])
    for key in (definitions.native_key(known[3]), definitions.native_key(forged)):
        result = bundles.resolve_bundle(
            repository, ["flows", "other flows"], key, native_identity=known[2].identity
        )
        assert result["status"] == "corrupt"
        assert any(
            item["path"] == str(path) and item["key_established"]
            for item in result["diagnostics"]
        )
    assert Path(valid["path"]).is_dir()
    assert (path / "binding.json").read_bytes() == definitions.canonical_json(forged)
    other_source = (
        ROOT / "plugins/aquarium/assets/podway/procedures/aquarium-goal-v2.yaml"
    ).read_bytes()
    other_path = repository / "sources/goal.yaml"
    other_path.write_bytes(other_source)
    other_binding = admission.reference_binding(
        other_source, known[2].preview(other_path)
    )
    other = bundles.publish_bundle(
        repository,
        ["flows", "other flows"],
        "flows",
        other_source,
        other_binding,
        qualify=lambda raw, mapping: admission.qualify_known(
            raw, mapping, known[2].preview(other_path)
        ),
        native_identity=known[2].identity,
    )
    result = bundles.resolve_bundle(
        repository,
        ["flows", "other flows"],
        definitions.native_key(other_binding),
        native_identity=known[2].identity,
    )
    assert result["status"] == "resolved" and result["path"] == other["path"]


def test_publication_requires_native_proof_before_writes(repository, known):
    qualify = Mock()
    with pytest.raises(bundles.BundleError) as error:
        bundles.publish_bundle(
            repository, ["flows"], "flows", known[0], known[3], qualify=qualify
        )
    assert error.value.code == "not-established"
    qualify.assert_not_called()
    assert not (repository / "flows").exists()
    assert not (repository / ".git/aquarium-adapt.lock").exists()


def test_staged_native_mismatch_preserves_no_final_bundle(repository, known):
    mapping = copy.deepcopy(known[3])
    mapping["procedure"]["digest"] = "sha256:" + "d" * 64
    seen = []

    def actual_identity(path):
        seen.append(path)
        return known[2].identity(path)

    with pytest.raises(bundles.BundleError) as error:
        bundles.publish_bundle(
            repository,
            ["flows"],
            "flows",
            known[0],
            mapping,
            qualify=lambda raw, binding: None,
            native_identity=actual_identity,
        )
    assert error.value.code == "corrupt"
    assert any(path.parent.name.startswith(".prepare-") for path in seen)
    assert sorted(path.name for path in (repository / "flows/.local").iterdir()) == [
        ".gitignore"
    ]
    assert not (
        repository / "flows/.local" / definitions.definition_id(mapping)
    ).exists()


def bounded_storage_read(repository, *, path=None, key=None):
    script = """
import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import yaml
import adaptive_bundles as bundles
request=json.loads(sys.argv[2])
repository=Path(request['repository'])
def identity(path):
    source=bundles.read_regular(repository,path)
    value=yaml.safe_load(source)
    return value['id'],value['version'],bundles.sha256(source)
try:
    if request['path'] is not None:
        result={'sha256':bundles.sha256(bundles.read_regular(repository,Path(request['path'])))}
    else:
        result=bundles.resolve_bundle(repository,['flows'],request['key'],native_identity=identity)
        result.pop('source',None)
except bundles.BundleError as error:
    result={'status':error.code}
print(json.dumps(result))
"""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            script,
            str(SHARED),
            json.dumps(
                {
                    "repository": str(repository),
                    "path": str(path) if path is not None else None,
                    "key": key,
                }
            ),
        ],
        capture_output=True,
        check=True,
        timeout=10,
        cwd=repository,
    )
    return json.loads(result.stdout)


def test_regular_source_read_still_returns_exact_bytes(repository, known):
    result = bounded_storage_read(repository, path=known[1])
    assert result["sha256"] == bundles.sha256(known[0])


def test_selected_source_fifo_is_rejected_without_writer(repository, known):
    known[1].unlink()
    os.mkfifo(known[1])
    assert bounded_storage_read(repository, path=known[1])["status"] == "unsafe"
    assert known[1].exists()


@pytest.mark.parametrize("filename", ["procedure.yaml", "binding.json"])
def test_selected_bundle_fifo_is_rejected_without_writer(repository, known, filename):
    published = publish(repository, known)
    path = Path(published["path"]) / filename
    path.unlink()
    os.mkfifo(path)
    result = bounded_storage_read(repository, key=definitions.native_key(known[3]))
    assert result["status"] == "unsafe"
    assert path.exists()


@pytest.mark.parametrize("filename", ["procedure.yaml", "binding.json"])
def test_unrelated_historical_fifo_does_not_block_valid_selected_bundle(
    repository, known, filename
):
    published = publish(repository, known)
    historical = repository / "flows/.local" / ("f" * 64)
    historical.mkdir()
    if filename == "procedure.yaml":
        (historical / "binding.json").write_text("unassociated historical binding")
    os.mkfifo(historical / filename)
    result = bounded_storage_read(repository, key=definitions.native_key(known[3]))
    assert result["status"] == "resolved" and result["path"] == published["path"]
    assert any(
        item["path"] == str(historical) and item["key_established"] is False
        for item in result["diagnostics"]
    )
    assert (historical / filename).exists()


@pytest.mark.parametrize("missing", ["procedure.yaml", "binding.json", "both"])
@pytest.mark.parametrize("write_root", ["flows", "other flows"])
def test_associated_loss_stops_selection_and_retention_before_writes(
    repository, known, missing, write_root
):
    result = publish(repository, known)
    for name in ("procedure.yaml", "binding.json") if missing == "both" else (missing,):
        (Path(result["path"]) / name).unlink()
    before = {
        str(path.relative_to(repository)): path.read_bytes()
        for path in repository.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(repository).parts
    }
    for action in (
        lambda: admission.selected_source(
            repository,
            known[1],
            roots=["flows", "other flows"],
            entrypoint="task-handler",
            route="herdr",
            client=known[2],
        ),
        lambda: admission.retain_selected(
            repository,
            known[1],
            roots=["flows", "other flows"],
            write_root=write_root,
            entrypoint="task-handler",
            route="herdr",
            client=known[2],
        ),
        lambda: publish(repository, known, write_root=write_root),
    ):
        with pytest.raises(bundles.BundleError) as error:
            action()
        assert error.value.code == "corrupt"
    after = {
        str(path.relative_to(repository)): path.read_bytes()
        for path in repository.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(repository).parts
    }
    assert before == after
    assert not (repository / "other flows").exists()


@pytest.mark.parametrize("write_root", ["flows", "other flows"])
def test_empty_candidate_directory_stops_before_policy_or_lock_writes(
    repository, known, write_root
):
    selected = repository / "flows/.local" / definitions.definition_id(known[3])
    selected.mkdir(parents=True)
    for action in (
        lambda: admission.selected_source(
            repository,
            known[1],
            roots=["flows", "other flows"],
            entrypoint="task-handler",
            route="herdr",
            client=known[2],
        ),
        lambda: publish(repository, known, write_root=write_root),
    ):
        with pytest.raises(bundles.BundleError) as error:
            action()
        assert error.value.code == "corrupt"
    assert list(selected.iterdir()) == []
    assert not (selected.parent / ".gitignore").exists()
    assert not (repository / ".git/aquarium-adapt.lock").exists()
    assert not (repository / "other flows").exists()


def test_unrelated_empty_historical_directory_remains_diagnostic(repository, known):
    historical = repository / "flows/.local" / ("f" * 64)
    historical.mkdir(parents=True)
    selected = admission.selected_source(
        repository,
        known[1],
        roots=["flows"],
        entrypoint="task-handler",
        route="herdr",
        client=known[2],
    )
    assert selected["retention"]["status"] == "missing"
    assert selected["retention"]["diagnostics"][0]["key_established"] is False
    assert publish(repository, known)["status"] == "resolved"
    assert historical.is_dir() and list(historical.iterdir()) == []


@pytest.mark.parametrize("root", ["-custom flows 한글", ":(bad)", "square[1]"])
def test_safe_custom_root_names_preserve_literal_git_paths(repository, known, root):
    result = publish(repository, known, roots=[root], write_root=root)
    assert result["status"] == "resolved"
    assert Path(result["path"]).is_relative_to(repository / root)
    assert (
        bundles.resolve_bundle(
            repository,
            [root],
            definitions.native_key(known[3]),
            native_identity=known[2].identity,
        )["status"]
        == "resolved"
    )


def native_identity_payload():
    return {
        "schema": "podway.version-result/v2",
        "product": "podway",
        "version": "v0.2.14",
        "target": "aarch64-apple-darwin",
        "build_identity": "sha256:" + "a" * 64,
        "source_commit": "b" * 40,
        "contract_manifest_schema": "podway.contract-manifest/v2",
        "contract_manifest_digest": "sha256:" + "c" * 64,
    }


@pytest.fixture
def runtime_probes(repository, monkeypatch):
    (repository / ".podway").mkdir()
    (repository / ".podway/config.yaml").write_text("fixture configuration")
    scenario = {"procedure": None, "doctor_error": None, "doctor_timeout": False}
    monkeypatch.setattr(inspector.shutil, "which", lambda name: "/synthetic/podway")
    monkeypatch.setattr(inspector.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(inspector.platform, "machine", lambda: "arm64")

    def probe(arguments, *args, **kwargs):
        request = arguments[1:]
        result = {
            "attempted": True,
            "ok": True,
            "exit_code": 0,
            "timed_out": False,
            "stdout": "",
            "stderr": "",
        }
        if request == ["version", "--json"]:
            result["result"] = {"name": "podway", "version": "v0.2.14"}
            return result
        if request == ["--json", "version", "--identity"]:
            command = "version"
            value = native_identity_payload()
        elif request == ["doctor", "--json"]:
            command = "workspace.doctor"
            value = {"healthy": True}
            if scenario["doctor_timeout"]:
                return {**result, "ok": False, "exit_code": None, "timed_out": True}
            if scenario["doctor_error"]:
                return {
                    **result,
                    "ok": False,
                    "exit_code": 5,
                    "result": {
                        "schema": "podway.error/v2",
                        "command": command,
                        "code": scenario["doctor_error"],
                    },
                }
        elif request == ["--json", "status"]:
            command = "session.status"
            if scenario["procedure"] is None:
                return {
                    **result,
                    "ok": False,
                    "exit_code": 1,
                    "result": {
                        "schema": "podway.error/v2",
                        "command": command,
                        "code": "SESSION_NOT_FOUND",
                    },
                }
            value = {
                "schema": "podway.status-result/v5",
                "procedure": {"schema": "podway.procedure/v2", **scenario["procedure"]},
                "session": {
                    "id": "00000000-0000-4000-8000-000000000001",
                    "lifecycle": "prepared",
                    "revision": 0,
                },
                "current": None,
                "delegation": None,
            }
        else:
            pytest.fail(f"Unexpected native probe: {request}")
        result["result"] = {
            "schema": "podway.output/v4",
            "command": command,
            "result": value,
        }
        return result

    monkeypatch.setattr(inspector, "json_probe", probe)
    return scenario


@pytest.mark.parametrize(
    "identity,version",
    [("aquarium-adapt-task-probe", "1"), ("foreign-procedure", "release.1")],
)
def test_actual_inspector_runtime_accepts_native_identity_without_managed_allowlist(
    repository, runtime_probes, identity, version
):
    procedure = {"id": identity, "version": version, "digest": "sha256:" + "a" * 64}
    runtime_probes["procedure"] = procedure
    result = inspector.inspect_podway(repository, 30)
    assert result["runtime_readiness"] == {
        "state": "ready",
        "session_procedure": procedure,
        "session_lifecycle": "prepared",
        "session_contract_supported": True,
    }
    assert result["readiness_status"] != "ready"


@pytest.mark.parametrize(
    "failure", ["WORKSPACE_CONTRACT_MISMATCH", "WORKSPACE_BUSY", "timeout"]
)
def test_actual_selected_runtime_failure_keeps_native_probe_details(
    repository, known, runtime_probes, failure
):
    runtime_probes["doctor_error"] = None if failure == "timeout" else failure
    runtime_probes["doctor_timeout"] = failure == "timeout"
    result = inspector.inspect_selected_podway(
        repository,
        30,
        source=known[1],
        roots=["flows"],
        entrypoint="task-handler",
        route="herdr",
    )
    selected = result["selected_procedure"]
    assert selected["status"] == "runtime-unavailable"
    assert selected["details"]["runtime_readiness"]["state"] == "degraded"
    doctor = selected["details"]["probes"]["doctor"]
    assert (
        doctor["timed_out"] if failure == "timeout" else doctor["error_code"] == failure
    )


def test_actual_no_session_resume_returns_missing_session(repository, runtime_probes):
    result = inspector.inspect_selected_podway(
        repository,
        30,
        roots=["flows"],
        entrypoint="task-handler",
        route="herdr",
        resume=True,
    )
    assert result["selected_procedure"]["status"] == "missing-session"
    assert (
        result["tools"]["podway"]["runtime_readiness"]["session_contract_supported"]
        is True
    )


def test_unavailable_and_not_checked_runtime_fields_are_explicit(
    repository, runtime_probes, monkeypatch
):
    monkeypatch.setattr(inspector.shutil, "which", lambda name: None)
    unavailable = inspector.inspect_podway(repository, 30)["runtime_readiness"]
    assert (
        unavailable["state"] == "unavailable"
        and unavailable["session_contract_supported"] is None
    )
    monkeypatch.setattr(inspector.shutil, "which", lambda name: "/synthetic/podway")
    (repository / ".podway/config.yaml").unlink()
    unchecked = inspector.inspect_podway(repository, 30)["runtime_readiness"]
    assert (
        unchecked["state"] == "degraded"
        and unchecked["session_contract_supported"] is None
    )


def test_real_native_client_health_machine_envelopes(
    repository, runtime_probes, monkeypatch
):
    responses = [
        {
            "schema": "podway.output/v4",
            "command": "version",
            "result": native_identity_payload(),
        },
        {
            "schema": "podway.output/v4",
            "command": "workspace.doctor",
            "result": {"healthy": True},
        },
        {
            "schema": "podway.output/v4",
            "command": "session.observe",
            "result": {
                "schema": "podway.observation-result/v5",
                "status": {
                    "procedure": {
                        "id": "foreign",
                        "version": "release.1",
                        "digest": "sha256:" + "a" * 64,
                    },
                    "session": {"lifecycle": "prepared"},
                },
            },
        },
    ]
    monkeypatch.setattr(
        admission.subprocess,
        "run",
        Mock(
            side_effect=[
                subprocess.CompletedProcess([], 0, json.dumps(value).encode(), b"")
                for value in responses
            ]
        ),
    )
    result = admission.NativeClient(repository, "synthetic").health()
    assert result["status"]["procedure"]["version"] == "release.1"


def test_native_preview_escapes_safe_dash_leading_paths(repository, known, monkeypatch):
    path = repository / "-root" / "-known.yaml"
    path.parent.mkdir()
    path.write_bytes(known[0])
    payloads = [
        {
            "schema": "podway.output/v4",
            "command": "procedure.check",
            "result": {
                "schema": "podway.procedure-diagnostics-result/v1",
                "valid": True,
            },
        },
        {
            "schema": "podway.output/v4",
            "command": "procedure.preview",
            "result": {
                "schema": "podway.procedure-preview-result/v2",
                "admissible": True,
                "procedure_id": "aquarium-task-v2",
                "procedure_version": "32",
                "procedure_digest": known[3]["procedure"]["digest"],
            },
        },
    ]
    run = Mock(
        side_effect=[
            subprocess.CompletedProcess([], 0, json.dumps(value).encode(), b"")
            for value in payloads
        ]
    )
    monkeypatch.setattr(admission.subprocess, "run", run)
    admission.NativeClient(repository, "synthetic").preview(path)
    assert all(
        call.args[0][-2:] == ["--", "-root/-known.yaml"] for call in run.call_args_list
    )


@pytest.fixture
def launcher(monkeypatch):
    from types import SimpleNamespace

    spec = importlib.util.spec_from_file_location(
        "adaptive_launcher", SHARED / "manage_adaptive_procedure.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(
        module.importlib.util,
        "spec_from_file_location",
        lambda *args: SimpleNamespace(
            loader=SimpleNamespace(exec_module=lambda value: None)
        ),
    )
    monkeypatch.setattr(
        module.importlib.util, "module_from_spec", lambda spec: inspector
    )
    return module


def launch(launcher, repository, known, monkeypatch, action="inspect"):
    arguments = [
        "manage_adaptive_procedure",
        action,
        "--repository",
        str(repository),
        "--root",
        "flows",
        "--entrypoint",
        "task-handler",
        "--review-route",
        "herdr",
        "--source",
        str(known[1]),
        "--podway",
        "/synthetic/podway",
    ]
    if action == "retain":
        arguments.extend(["--write-root", "flows"])
    monkeypatch.setattr(sys, "argv", arguments)
    monkeypatch.setattr(admission, "NativeClient", lambda *args: known[2])
    return launcher.main()


@pytest.mark.parametrize("action", ["inspect", "retain"])
def test_launcher_success_paths_use_selected_runtime_and_expose_recovery(
    repository, known, runtime_probes, launcher, monkeypatch, capsys, action
):
    historical = repository / "flows/.local" / ("f" * 64)
    historical.mkdir(parents=True)
    assert launch(launcher, repository, known, monkeypatch, action) == 0
    value = json.loads(capsys.readouterr().out)
    assert value["status"] == ("retained" if action == "retain" else "ready")
    assert value["session"]["state"] == "none"
    retention = value if action == "retain" else value["retention"]
    assert any(
        item["path"] == str(historical) and item["key_established"] is False
        for item in retention["diagnostics"]
    )


@pytest.mark.parametrize(
    "failure", ["WORKSPACE_CONTRACT_MISMATCH", "timeout", "conflict"]
)
def test_launcher_preserves_runtime_failures_and_conflicting_session(
    repository, known, runtime_probes, launcher, monkeypatch, capsys, failure
):
    if failure == "conflict":
        runtime_probes["procedure"] = {
            "id": "foreign-procedure",
            "version": "release.1",
            "digest": "sha256:" + "a" * 64,
        }
    elif failure == "timeout":
        runtime_probes["doctor_timeout"] = True
    else:
        runtime_probes["doctor_error"] = failure
    assert launch(launcher, repository, known, monkeypatch) == 2
    captured = capsys.readouterr()
    assert captured.err == ""
    value = json.loads(captured.out)
    if failure == "conflict":
        assert value["status"] == "session-conflict"
        assert value["details"]["session"]["procedure"] == runtime_probes["procedure"]
        assert value["details"]["session"]["state"] == "prepared"
    else:
        assert value["status"] == "runtime-unavailable"
        doctor = value["details"]["probes"]["doctor"]
        assert (
            doctor["timed_out"]
            if failure == "timeout"
            else doctor["error_code"] == failure
        )


def test_launcher_inspection_timeout_has_typed_json_boundary(
    repository, known, runtime_probes, launcher, monkeypatch, capsys
):
    original = inspector.run_command

    def command(arguments, *args, **kwargs):
        if arguments[:2] == ["git", "status"]:
            return {
                "attempted": True,
                "ok": False,
                "timed_out": True,
                "exit_code": None,
                "stdout": "",
                "stderr": "",
            }
        return original(arguments, *args, **kwargs)

    monkeypatch.setattr(inspector, "run_command", command)
    assert launch(launcher, repository, known, monkeypatch) == 2
    captured = capsys.readouterr()
    assert captured.err == ""
    value = json.loads(captured.out)
    assert value["status"] == "git_status_failed"
    assert value["details"]["inspection_exit_code"] == 1


@pytest.mark.parametrize("missing", [False, True])
def test_launcher_invalid_repository_is_json_before_native_work(tmp_path, missing):
    repository = tmp_path / "not-git"
    if not missing:
        repository.mkdir()
    result = subprocess.run(
        [
            sys.executable,
            str(SHARED / "manage_adaptive_procedure.py"),
            "inspect",
            "--repository",
            str(repository),
            "--root",
            "flows",
            "--source",
            "source.yaml",
            "--entrypoint",
            "task-handler",
            "--review-route",
            "herdr",
            "--podway",
            "uninvoked-podway",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 2 and result.stderr == ""
    assert json.loads(result.stdout)["status"] == (
        "invalid_repository_path" if missing else "not_a_git_repository"
    )


def test_empty_equivalent_alias_has_established_selected_damage(repository, known):
    result = publish(repository, known)
    alias = repository / "other flows/.local" / result["bundle_id"]
    alias.mkdir(parents=True)
    resolved = bundles.resolve_bundle(
        repository,
        ["flows", "other flows"],
        definitions.native_key(known[3]),
        native_identity=known[2].identity,
    )
    assert resolved["status"] == "corrupt"
    assert any(
        item["path"] == str(alias)
        and item["code"] == "corrupt"
        and item["key_established"] is True
        for item in resolved["diagnostics"]
    )
