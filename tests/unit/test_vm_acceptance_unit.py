"""Executable VM-helper checks, without providers or installed workflow claims."""

import copy
import importlib.util
import json
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tests/vm/run_acceptance.py"
SPEC = importlib.util.spec_from_file_location("vm_acceptance", SCRIPT)
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def test_host_rejection_does_not_create_results_or_fixture(tmp_path):
    output = tmp_path / "must-not-exist"
    request = tmp_path / "request.json"
    write_json(
        request,
        {
            "schema": gate.REQUEST_SCHEMA,
            "expected_guest_uuid": "different-from-every-real-guest",
            "run_root": str(output),
        },
    )
    result = subprocess.run(
        [sys.executable, "-B", str(SCRIPT), "run", "--request", str(request)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert json.loads(result.stdout)["outcome"] in {"fail", "incomplete"}
    assert not output.exists()


@pytest.mark.parametrize(
    "flag,exit_code,uuid,expected",
    [
        ("0", 0, "guest", "fail"),
        ("", 1, "guest", "incomplete"),
        ("1", 0, "other", "fail"),
    ],
)
def test_native_guard_failure_classification(
    monkeypatch, flag, exit_code, uuid, expected
):
    monkeypatch.setattr(gate.platform, "system", lambda: "Darwin")

    def fake_command(argv, **_):
        if "sysctl" in argv[0]:
            return SimpleNamespace(returncode=exit_code, stdout=flag)
        return SimpleNamespace(returncode=0, stdout=f'"IOPlatformUUID" = "{uuid}"')

    monkeypatch.setattr(gate, "command", fake_command)
    with pytest.raises(gate.GateError) as caught:
        gate.guest_guard("guest")
    assert caught.value.outcome == expected


def test_guest_guard_uses_external_identity_without_hypervisor_model(monkeypatch):
    monkeypatch.setattr(gate.platform, "system", lambda: "Darwin")
    replies = iter(
        [
            SimpleNamespace(returncode=0, stdout="1\n"),
            SimpleNamespace(
                returncode=0, stdout='"IOPlatformUUID" = "Any-Dedicated-Guest"'
            ),
        ]
    )
    monkeypatch.setattr(gate, "command", lambda *_args, **_kwargs: next(replies))
    assert gate.guest_guard("any-dedicated-guest")["hypervisor_present"] == 1


def test_versions_use_each_native_public_contract(tmp_path, monkeypatch):
    write_json(tmp_path / ".codex-plugin/plugin.json", {"version": "0.1.19"})
    responses = {
        ("/tools/codex", "--version"): "codex-cli 0.162.1\n",
        ("/tools/podway", "--json", "version", "--identity"): json.dumps(
            {
                "schema": "podway.output/v4",
                "result": {
                    "schema": "podway.version-result/v2",
                    "version": "v0.2.14",
                    "source_commit": "released-source",
                    "contract_manifest_schema": "podway.contract-manifest/v2",
                },
            }
        ),
        ("/tools/gaori", "--version"): "gaori v0.1.18\n",
        ("/tools/mulgae", "--version"): "mulgae v0.1.24\n",
    }
    monkeypatch.setattr(
        gate, "command", lambda argv: SimpleNamespace(stdout=responses[tuple(argv)])
    )
    result = gate.versions(
        {
            "tools": {
                name: "/tools/" + name
                for name in ("codex", "podway", "gaori", "mulgae")
            }
        },
        tmp_path,
    )
    assert result == {
        "aquarium": "0.1.19",
        "codex": "0.162.1",
        "podway": "v0.2.14",
        "gaori": "v0.1.18",
        "mulgae": "v0.1.24",
    }


@pytest.fixture
def candidate(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    write_json(source / ".agents/plugins/marketplace.json", {"name": "fixture"})
    write_json(
        source / "plugins/aquarium/.codex-plugin/plugin.json",
        {"name": "aquarium", "version": "0.1.20"},
    )
    (source / "plugins/aquarium/role.txt").write_text("Committed role bytes.\n")
    (source / "plugins/aquarium/helper.py").write_text("VALUE = 'shipped source'\n")
    driver = source / "tests/vm/run_acceptance.py"
    driver.parent.mkdir(parents=True)
    shutil.copyfile(SCRIPT, driver)
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    subprocess.run(["git", "-C", str(source), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(source),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "Fixture",
        ],
        check=True,
    )
    revision = gate.git(source, "rev-parse", "HEAD").strip()
    artifact = tmp_path / "marketplace"
    shutil.copytree(source / ".agents", artifact / ".agents")
    shutil.copytree(source / "plugins", artifact / "plugins")
    version = f"0.1.20-dev.{revision[:12]}"
    write_json(
        artifact / "plugins/aquarium/.codex-plugin/plugin.json",
        {"name": "aquarium", "version": version},
    )
    installed = tmp_path / "installed"
    shutil.copytree(artifact / "plugins/aquarium", installed)
    manifest = tmp_path / "artifact.json"
    write_json(
        manifest,
        {
            "schema": "aquarium-dev-artifact-manifest/v1",
            "git_sha": revision,
            "development_version": "v" + version,
            "sha256": gate.artifact_digest(artifact),
        },
    )
    return {
        "git_sha": revision,
        "source_root": str(source),
        "artifact_root": str(artifact),
        "artifact_manifest": str(manifest),
        "installed_plugin_root": str(installed),
    }


def verify(candidate):
    return gate.verify_candidate(
        candidate, Path(candidate["source_root"]) / "tests/vm/run_acceptance.py"
    )


def test_candidate_binding_reads_real_git_and_installed_bytes(candidate):
    assert verify(candidate)["git_sha"] == candidate["git_sha"]


def test_artifact_digest_interoperates_with_canonical_prefix_directory_order(
    tmp_path, monkeypatch
):
    monkeypatch.syspath_prepend(str(ROOT / "plugins/aquarium/tools/aquarium-dev"))
    from dev_manager import artifact_digest as producer_digest

    for name in ("dev-setup", "dev-setup-bundle"):
        path = tmp_path / "skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text(name)
    assert gate.artifact_digest(tmp_path) == producer_digest(tmp_path)


def test_normal_generated_bytecode_does_not_block_candidate_resume(candidate):
    installed = Path(candidate["installed_plugin_root"])
    py_compile.compile(str(installed / "helper.py"), doraise=True)
    assert verify(candidate)["git_sha"] == candidate["git_sha"]
    (installed / "__pycache__/unshipped.cpython-314.pyc").write_bytes(b"unrelated")
    with pytest.raises(gate.GateError) as caught:
        verify(candidate)
    assert caught.value.outcome == "fail"


@pytest.mark.parametrize("mismatch", [None, "disabled", "version", "source", "origin"])
def test_native_plugin_registration_binds_enabled_version_and_source(
    candidate, monkeypatch, mismatch
):
    marketplace = Path(candidate["artifact_root"])
    plugin = Path(candidate["installed_plugin_root"])
    row = {
        "pluginId": "aquarium@fixture",
        "name": "aquarium",
        "marketplaceName": "fixture",
        "version": gate.read_json(plugin / ".codex-plugin/plugin.json")["version"],
        "installed": True,
        "enabled": True,
        "source": {"source": "local", "path": str(marketplace / "plugins/aquarium")},
        "marketplaceSource": {"sourceType": "local", "source": str(marketplace)},
    }
    if mismatch == "disabled":
        row["enabled"] = False
    elif mismatch == "version":
        row["version"] = "previous-release"
    elif mismatch == "source":
        row["source"]["path"] = str(marketplace / "another-plugin")
    elif mismatch == "origin":
        row["marketplaceSource"]["source"] = str(marketplace / "another-catalog")

    def native(argv):
        assert argv == [
            "/tools/codex",
            "plugin",
            "list",
            "--marketplace",
            "fixture",
            "--json",
        ]
        return SimpleNamespace(stdout=json.dumps({"installed": [row], "available": []}))

    monkeypatch.setattr(gate, "command", native)
    request = {"tools": {"codex": "/tools/codex"}}
    if mismatch:
        with pytest.raises(gate.GateError) as caught:
            gate.installed_plugin(request, marketplace, plugin)
        assert caught.value.outcome == "fail"
    else:
        assert gate.installed_plugin(request, marketplace, plugin) == row


@pytest.mark.parametrize("surface", ["source", "artifact", "installed", "manifest"])
def test_candidate_identity_mismatch_cannot_pass(candidate, surface):
    if surface == "source":
        Path(candidate["source_root"], "tests/vm/run_acceptance.py").write_text(
            "Changed test bytes"
        )
    elif surface == "artifact":
        Path(candidate["artifact_root"], "plugins/aquarium/role.txt").write_text(
            "Changed payload"
        )
    elif surface == "installed":
        Path(candidate["installed_plugin_root"], "role.txt").write_text(
            "Stale installed payload"
        )
    else:
        document = gate.read_json(candidate["artifact_manifest"])
        document["git_sha"] = "0" * 40
        write_json(Path(candidate["artifact_manifest"]), document)
    with pytest.raises(gate.GateError):
        verify(candidate)


def test_artifact_manifest_cannot_relabel_different_committed_source(candidate):
    artifact = Path(candidate["artifact_root"])
    installed = Path(candidate["installed_plugin_root"])
    for path in (artifact / "plugins/aquarium/role.txt", installed / "role.txt"):
        path.write_text("Wrong but mutually matching bytes")
    document = gate.read_json(candidate["artifact_manifest"])
    document["sha256"] = gate.artifact_digest(artifact)
    write_json(Path(candidate["artifact_manifest"]), document)
    with pytest.raises(gate.GateError) as caught:
        verify(candidate)
    assert caught.value.outcome == "fail"


def test_oracle_executes_behavior_and_rejects_missing_uppercase(tmp_path):
    shutil.copyfile(ROOT / "tests/vm/fixtures/greeting/greet.py", tmp_path / "greet.py")
    assert len(gate.oracle(sys.executable, tmp_path, uppercase=False)) == 2
    with pytest.raises(gate.GateError) as caught:
        gate.oracle(sys.executable, tmp_path)
    assert caught.value.outcome == "fail"
    (tmp_path / "greet.py").write_text(
        "import argparse\np=argparse.ArgumentParser()\np.add_argument('--uppercase',action='store_true')\np.add_argument('name',nargs='?',default='world')\na=p.parse_args()\ns=f'Hello, {a.name}!'\nprint(s.upper() if a.uppercase else s)\n"
    )
    assert len(gate.oracle(sys.executable, tmp_path)) == 4


@pytest.fixture
def native_case(tmp_path):
    repository = tmp_path / "task"
    repository.mkdir()
    case_root = tmp_path / "task-startup"
    case_root.mkdir()
    (repository / "greet.py").write_text("Assessed source bytes")
    evidence = {
        "executor_agent": "/root/executor",
        "evaluator_agent": "/root/evaluator",
    }
    reports = {}
    for role in ("executor", "evaluator"):
        assignment = case_root / f"{role}-assignment.json"
        write_json(
            assignment,
            {
                "schema": "aquarium.assignment/v3",
                "role": role,
                "work": {"repository": str(repository)},
                "success_criteria": list(gate.CRITERIA),
            },
        )
        evidence[role + "_assignment"] = str(assignment)
    target = {"greet_sha256": gate.sha256(repository / "greet.py")}
    reports["executor"] = {
        "schema": "aquarium.executor-handoff/v3",
        "changed_artifacts": ["greet.py"],
        "results": [{"command": "make test", "exit": 0}],
        "target": target,
    }
    reports["evaluator"] = {
        "schema": "aquarium.evaluator-assessment/v3",
        "target": target,
        "checkpoint_result": "pass",
        "verdict": "evidence-needed",
        "criteria": [
            {
                "id": key,
                "state": "met",
                "source": "original dossier",
                "evidence": ["actual source and checks"],
            }
            for key in gate.CRITERIA
        ]
        + [{"id": "future-repeat", "state": "unverified"}],
    }
    observation = {
        "root": {
            "metadata": {"id": "root"},
            "items": [],
            "turns": [{"status": "completed"}],
        },
        "descendants": [],
    }
    for role in ("executor", "evaluator"):
        path = case_root / f"{role}-report.json"
        write_json(path, reports[role])
        evidence[
            "executor_result" if role == "executor" else "evaluator_assessment"
        ] = str(path)
        observation["root"]["items"].extend(
            {
                "type": "subAgentActivity",
                "kind": kind,
                "agentThreadId": role,
                "agentPath": "/root/" + role,
            }
            for kind in ("started", "completed")
        )
        observation["descendants"].append(
            {
                "metadata": {
                    "id": role,
                    "parentThreadId": "root",
                    "agentRole": None,
                    "status": {"type": "notLoaded"},
                },
                "turns": [{"id": role + "-turn", "status": "completed", "error": None}],
                "items": [
                    {"type": "commandExecution", "status": "completed"},
                    {
                        "type": "agentMessage",
                        "phase": "final_answer",
                        "text": json.dumps(reports[role]),
                    },
                ],
            }
        )
    return observation, evidence, repository


def test_public_native_roles_allow_null_metadata_and_future_global_gap(native_case):
    assert gate.validate_native_case(*native_case) == {
        "executor_thread": "executor",
        "evaluator_thread": "evaluator",
    }


@pytest.mark.parametrize("role", ["executor", "evaluator"])
@pytest.mark.parametrize("digest", ["bare", "wrong-bytes", "wrong-algorithm"])
def test_report_digest_representation_preserves_exact_source_check(
    native_case, role, digest
):
    observation, evidence, repository = native_case
    path = Path(
        evidence["executor_result" if role == "executor" else "evaluator_assessment"]
    )
    report = gate.read_json(path)
    value = report["target"]["greet_sha256"].removeprefix("sha256:")
    if digest == "wrong-bytes":
        value = "0" * 64
    elif digest == "wrong-algorithm":
        value = "sha512:" + value
    report["target"]["greet_sha256"] = value
    write_json(path, report)
    child = next(
        actor for actor in observation["descendants"] if actor["metadata"]["id"] == role
    )
    child["items"][-1]["text"] = json.dumps(report)
    if digest == "bare":
        assert gate.validate_native_case(observation, evidence, repository)
    else:
        with pytest.raises(gate.GateError) as caught:
            gate.validate_native_case(observation, evidence, repository)
        assert caught.value.outcome == "fail"


def test_final_success_assertion_without_native_children_is_incomplete(native_case):
    observation, evidence, repository = native_case
    observation["root"]["items"] = [
        {"type": "agentMessage", "text": "Executor and Evaluator succeeded"}
    ]
    with pytest.raises(gate.GateError) as caught:
        gate.validate_native_case(observation, evidence, repository)
    assert caught.value.outcome == "incomplete"


@pytest.mark.parametrize("role", ["executor", "evaluator"])
@pytest.mark.parametrize(
    "representation",
    [
        "bare",
        "prefixed",
        "wrong-bytes",
        "wrong-algorithm",
        "prefix",
        "suffix",
        "missing-path",
    ],
)
def test_native_report_path_delivery_checks_exact_digest(
    native_case, role, representation
):
    observation, evidence, repository = native_case
    path = Path(
        evidence["executor_result" if role == "executor" else "evaluator_assessment"]
    )
    digest = gate.sha256(path).removeprefix("sha256:")
    if representation == "prefixed":
        digest = "sha256:" + digest
    elif representation == "wrong-bytes":
        digest = "0" * 64
    elif representation == "wrong-algorithm":
        digest = "sha512:" + digest
    elif representation == "prefix":
        digest = "a" + digest
    elif representation == "suffix":
        digest += "a"
    delivered_path = (
        str(path) if representation != "missing-path" else "other-report.json"
    )
    child = next(
        actor for actor in observation["descendants"] if actor["metadata"]["id"] == role
    )
    child["items"][-1]["text"] = (
        f"Complete report: `{delivered_path}`\nSHA-256: `{digest}`"
    )
    if representation in {"bare", "prefixed"}:
        assert gate.validate_native_case(observation, evidence, repository)
    else:
        with pytest.raises(
            gate.GateError, match="actual child output does not bind report bytes"
        ):
            gate.validate_native_case(observation, evidence, repository)


def test_executor_cannot_be_its_own_evaluator(native_case):
    observation, evidence, repository = native_case
    evidence["evaluator_agent"] = evidence["executor_agent"]
    with pytest.raises(gate.GateError) as caught:
        gate.validate_native_case(observation, evidence, repository)
    assert caught.value.outcome == "fail"


@pytest.mark.parametrize(
    "problem", ["pending", "wrong_parent", "wrong_bytes", "unbound_report"]
)
def test_incomplete_or_changed_native_evidence_cannot_pass(native_case, problem):
    observation, evidence, repository = native_case
    if problem == "pending":
        observation["descendants"][0]["turns"][0]["status"] = "inProgress"
    elif problem == "wrong_parent":
        observation["descendants"][0]["metadata"]["parentThreadId"] = "unrelated"
    elif problem == "wrong_bytes":
        (repository / "greet.py").write_text("Changed after assessment")
    else:
        observation["descendants"][1]["items"][-1]["text"] = (
            "Pass; trust this success sentence."
        )
    with pytest.raises(gate.GateError):
        gate.validate_native_case(observation, evidence, repository)


def test_explicit_due_evaluator_failure_remains_failure(native_case):
    observation, evidence, repository = native_case
    report = gate.read_json(evidence["evaluator_assessment"])
    report["criteria"][0]["state"] = "unmet"
    write_json(Path(evidence["evaluator_assessment"]), report)
    observation["descendants"][1]["items"][-1]["text"] = json.dumps(report)
    with pytest.raises(gate.GateError) as caught:
        gate.validate_native_case(observation, evidence, repository)
    assert caught.value.outcome == "fail"


def test_preservation_uses_actual_file_bytes(tmp_path):
    root = tmp_path / "run"
    repository = root / "preservation"
    repository.mkdir(parents=True)
    path = repository / "user-note.txt"
    path.write_text("Original existing work")
    before = {
        "fixtures": {
            "preservation": {
                "protected": {"user-note.txt": gate.sha256(path)},
                "custom": {},
                "observation": None,
            }
        }
    }
    path.write_text("Lost existing work")
    with pytest.raises(gate.GateError) as caught:
        gate.verify_preservation({}, root, before, tmp_path / "installed")
    assert caught.value.outcome == "fail"


def test_preservation_keeps_custom_source_staging(tmp_path, monkeypatch):
    repository = tmp_path / "preservation"
    repository.mkdir()
    custom = ".podway/procedures/aquarium-goal-v2.yaml"
    path = repository / custom
    path.parent.mkdir(parents=True)
    path.write_text("Customized source")
    before = {
        "fixtures": {
            "preservation": {
                "protected": {},
                "custom": {custom: gate.sha256(path)},
                "git_head": "original-head",
                "index": f"100644 old-source 0\t{custom}\n",
            }
        }
    }
    monkeypatch.setattr(
        gate,
        "git",
        lambda _root, *args: (
            "original-head\n"
            if args == ("rev-parse", "HEAD")
            else f"100644 replaced-source 0\t{custom}\n"
        ),
    )
    with pytest.raises(gate.GateError) as caught:
        gate.verify_preservation({}, tmp_path, before, tmp_path / "installed")
    assert caught.value.outcome == "fail"


def test_snapshot_preserves_extra_procedure_files(tmp_path, monkeypatch):
    repository = tmp_path / "preservation"
    path = repository / ".podway/procedures/user-owned.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("User-owned source")
    relative = path.relative_to(repository).as_posix()
    monkeypatch.setattr(
        gate,
        "git",
        lambda _root, *args: relative + "\0" if args == ("ls-files", "-z") else "",
    )
    monkeypatch.setattr(gate, "observe", lambda *_args, **_kwargs: None)
    observed = gate.snapshot({}, repository, tmp_path / "plugin")
    assert observed["protected"] == {relative: gate.sha256(path)}


@pytest.fixture
def setup_case(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "tests/vm"))
    import native_observation

    repository = tmp_path / "task"
    for filename in gate.PROCEDURES:
        path = repository / ".podway/procedures" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Observed managed source")
    plugin = tmp_path / "released-cache"
    execution = {
        "type": "commandExecution",
        "id": "released-copy",
        "status": "completed",
        "exitCode": 0,
        "command": f'cp -n "{plugin}/assets/podway/procedures/aquarium-${{name}}-v2.yaml" ".podway/procedures/aquarium-${{name}}-v2.yaml"',
    }
    items = [
        {
            "type": "userMessage",
            "id": "setup-request",
            "text": "$aquarium:dev-setup scoped Podway",
        },
        execution,
        {
            "type": "agentMessage",
            "id": "setup-result",
            "phase": "final_answer",
            "text": "Actual setup result",
        },
    ]
    observation = {
        "root": {
            "metadata": {"id": "setup-thread", "cwd": str(repository)},
            "items": items,
            "turns": [
                {
                    "id": "released-turn",
                    "status": "completed",
                    "error": None,
                    "items": copy.deepcopy(items),
                }
            ],
        },
        "descendants": [],
    }
    monkeypatch.setattr(
        native_observation, "collect", lambda *_: copy.deepcopy(observation)
    )
    request = {"tools": {"codex": "/tools/codex"}}
    before = gate.verify_setup(request, tmp_path, "task", "setup-thread", plugin=plugin)
    return request, tmp_path, observation, before


def test_released_setup_handle_cannot_prove_candidate_update(setup_case):
    request, root, _, before = setup_case
    for filename in gate.PROCEDURES:
        (root / "task/.podway/procedures" / filename).write_text(
            "Manually copied candidate bytes"
        )
    with pytest.raises(gate.GateError) as caught:
        gate.verify_setup(
            request,
            root,
            "task",
            "setup-thread",
            plugin=root / "candidate-cache",
            before=before,
        )
    assert caught.value.outcome == "incomplete"


@pytest.mark.parametrize("route", ["copy-command", "file-change"])
def test_resumed_setup_binds_new_current_source_effects_and_preserves_capture(
    setup_case, route
):
    request, root, observation, before = setup_case
    original = Path(before["public_observation"]).read_bytes()
    plugin = root / "candidate-cache"
    items = [
        {
            "id": "candidate-setup-request",
            "type": "userMessage",
            "text": "$aquarium:dev-setup current candidate scoped Podway",
        },
        {
            "id": "read-current",
            "type": "commandExecution",
            "status": "completed",
            "exitCode": 0,
            "command": f'cat "{plugin}/skills/dev-setup/SKILL.md"',
        },
    ]
    if route == "copy-command":
        items.append(
            {
                "id": "copy-current",
                "type": "commandExecution",
                "status": "completed",
                "exitCode": 0,
                "cwd": str(root / "task"),
                "command": f'cp "{plugin}/assets/podway/procedures/aquarium-${{name}}-v2.yaml" ".podway/procedures/aquarium-${{name}}-v2.yaml"',
            }
        )
    else:
        items.append(
            {
                "id": "write-current",
                "type": "fileChange",
                "status": "completed",
                "changes": [
                    {
                        "path": str(
                            root / "task/.podway/procedures/aquarium-task-v2.yaml"
                        ),
                        "kind": {"type": "update"},
                    }
                ],
            }
        )
    observation["root"]["items"].extend(items)
    observation["root"]["turns"].append(
        {"id": "candidate-turn", "status": "completed", "error": None, "items": items}
    )
    result = gate.verify_setup(
        request, root, "task", "setup-thread", plugin=plugin, before=before
    )
    assert "candidate-turn" in result["completed_turn_ids"]
    assert result["public_observation"] != before["public_observation"]
    assert Path(before["public_observation"]).read_bytes() == original
    assert gate.sha256(result["public_observation"]) == result["observation_sha256"]


@pytest.mark.parametrize(
    "mismatch",
    ["old-source", "unrelated-command"],
)
def test_new_setup_turn_without_current_managed_effects_cannot_pass(
    setup_case, mismatch
):
    request, root, observation, before = setup_case
    plugin = root / "candidate-cache"
    command = f'cat "{plugin}/skills/dev-setup/SKILL.md"'
    if mismatch == "old-source":
        command = f'cp "{root}/released-cache/assets/podway/procedures/file.yaml" .podway/procedures/'
    elif mismatch == "unrelated-command":
        command = "git status --short"
    items = [
        {
            "id": "candidate-setup-request",
            "type": "userMessage",
            "text": "$aquarium:dev-setup candidate scoped Podway",
        },
        {
            "id": "new-command",
            "type": "commandExecution",
            "status": "completed",
            "exitCode": 0,
            "command": command,
        },
    ]
    observation["root"]["items"].extend(items)
    observation["root"]["turns"].append(
        {"id": "candidate-turn", "status": "completed", "error": None, "items": items}
    )
    with pytest.raises(gate.GateError) as caught:
        gate.verify_setup(
            request, root, "task", "setup-thread", plugin=plugin, before=before
        )
    assert caught.value.outcome == "incomplete"


def test_resumed_direct_copy_without_candidate_setup_invocation_is_incomplete(
    setup_case,
):
    request, root, observation, before = setup_case
    plugin = root / "candidate-cache"
    items = [
        {
            "id": "direct-copy-request",
            "type": "userMessage",
            "text": "Copy these files directly",
        },
        {
            "id": "direct-copy",
            "type": "commandExecution",
            "status": "completed",
            "exitCode": 0,
            "command": f'cp "{plugin}/assets/podway/procedures/aquarium-task-v2.yaml" .podway/procedures/',
        },
    ]
    observation["root"]["items"].extend(items)
    observation["root"]["turns"].append(
        {"id": "direct-copy-turn", "status": "completed", "error": None, "items": items}
    )
    with pytest.raises(gate.GateError) as caught:
        gate.verify_setup(
            request, root, "task", "setup-thread", plugin=plugin, before=before
        )
    assert caught.value.outcome == "incomplete"


@pytest.fixture
def update_case(setup_case, monkeypatch):
    request, root, observation, before = setup_case
    plugin = root / "candidate-cache"
    for filename in gate.PROCEDURES:
        path = plugin / "assets/podway/procedures" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Candidate " + filename)
    request["candidate"] = {"installed_plugin_root": str(plugin)}
    request["authority"] = {
        "observer": "Fixture operator",
        "reference": "Explicit VM test",
    }
    original = {"setup": {"task": before}, "fixtures": {"task": {"custom": {}}}}
    write_json(root / "baseline.json", original)
    binding = {
        "candidate": {"git_sha": "candidate"},
        "baseline_sha256": gate.sha256(root / "baseline.json"),
    }
    monkeypatch.setattr(gate, "update_binding", lambda *_: binding)
    monkeypatch.setattr(gate, "discover", lambda *_: {"data": []})
    operation = {"mode": "write", "calls": 0}

    def native(_request, _root, case, prompt, *, reply=None, resume_thread=None):
        number = operation["calls"]
        operation["calls"] += 1
        directory = root / "operations" / case
        prefix = directory / f"{number:03d}"
        if operation["mode"] in {"write", "partial"}:
            selected = (
                list(gate.PROCEDURES)[:2]
                if operation["mode"] == "partial"
                else gate.PROCEDURES
            )
            for filename in selected:
                if (
                    ".podway/procedures/" + filename
                    not in original["fixtures"]["task"]["custom"]
                ):
                    (root / "task/.podway/procedures" / filename).write_bytes(
                        (plugin / "assets/podway/procedures" / filename).read_bytes()
                    )
        argv = [
            sys.executable,
            "-B",
            "-c",
            f"from pathlib import Path; print(Path({str(plugin / 'assets/podway/procedures/aquarium-task-v2.yaml')!r}).read_text())",
        ]
        result = gate.command(argv)
        item = {
            "id": f"candidate-command-{number}",
            "type": "commandExecution",
            "status": "completed",
            "exitCode": result.returncode,
            "command": " ".join(argv),
        }
        if not operation.get("no_turn"):
            observation["root"]["items"].append(item)
            observation["root"]["items"].append(
                {
                    "id": f"candidate-input-{number}",
                    "type": "userMessage",
                    "text": prompt if reply is None else reply,
                }
            )
            status = operation.get("turn_status", "completed")
            observation["root"]["turns"].append(
                {
                    "id": f"candidate-turn-{number}",
                    "status": status,
                    "error": {"message": "Native failure"}
                    if status == "failed"
                    else None,
                    "items": [item],
                }
            )
        Path(str(prefix) + ".input").write_text(prompt if reply is None else reply)
        Path(str(prefix) + ".jsonl").write_text(
            '{"type":"thread.started","thread_id":"setup-thread"}\n'
        )
        write_json(
            Path(str(prefix) + ".invocation.json"),
            {
                "exit": operation.get("native_exit", 0),
                "thread_id": "setup-thread",
                "input_sha256": gate.sha256(str(prefix) + ".input"),
            },
        )
        if operation.get("native_exit", 0):
            raise gate.GateError("Native invocation failed")
        return "setup-thread"

    monkeypatch.setattr(gate, "invoke", native)
    return request, root, original, binding, operation


def test_candidate_update_captures_real_transition_and_resumed_partial_work(
    update_case,
):
    request, root, original, binding, operation = update_case
    operation["mode"] = "partial"
    with pytest.raises(gate.GateError) as caught:
        gate.setup_update(
            request, root, "task", resume_thread=original["setup"]["task"]["thread_id"]
        )
    assert caught.value.outcome == "incomplete"
    operation["mode"] = "write"
    result = gate.setup_update(
        request, root, "task", reply="Approve the remaining update"
    )
    assert result["outcome"] == "managed-update-observed"
    assert len(result["windows"]) == 2
    before = read_window(root, 0, "before")
    after = read_window(root, 0, "after")
    assert gate.image_hashes(before["managed_image"]) != gate.image_hashes(
        after["managed_image"]
    )
    assert operation["calls"] == 2
    assert (
        gate.verify_managed_update(request, root, "task", binding, original)[
            "thread_id"
        ]
        == "setup-thread"
    )


def read_window(root, number, phase):
    return gate.read_json(
        root / "operations/task-setup" / f"{number:03d}.setup-{phase}.json"
    )


@pytest.mark.parametrize("status", ["failed", "interrupted"])
def test_settled_failed_setup_preserves_failure_and_allows_explicit_reply(
    update_case, status
):
    request, root, original, binding, operation = update_case
    operation.update(mode="partial", native_exit=1, turn_status=status)
    with pytest.raises(gate.GateError) as caught:
        gate.setup_update(
            request, root, "task", resume_thread=original["setup"]["task"]["thread_id"]
        )
    assert caught.value.outcome == "incomplete"
    directory = root / "operations/task-setup"
    preserved = gate.files(directory)
    after = read_window(root, 0, "after")
    assert after["invocation_exit"] == 1
    assert "setup" not in after
    assert gate.image_hashes(after["managed_image"]) != gate.image_hashes(
        read_window(root, 0, "before")["managed_image"]
    )

    recovered = gate.reconcile_setup(request, root, "task", binding, original)
    assert recovered["settlement"]["native_status"] == status
    assert recovered["invocation_exit"] == 1
    assert operation["calls"] == 1
    with pytest.raises(gate.GateError) as caught:
        gate.verify_managed_update(request, root, "task", binding, original)
    assert caught.value.outcome == "incomplete"

    operation.update(mode="write", native_exit=0, turn_status="completed")
    result = gate.setup_update(request, root, "task", reply="Approve remaining work")
    assert result["outcome"] == "managed-update-observed"
    assert [window["invocation_exit"] for window in result["windows"]] == [1, 0]
    assert result["windows"][0]["settlement"]["native_status"] == status
    assert operation["calls"] == 2
    current = gate.files(directory)
    assert all(current[path] == digest for path, digest in preserved.items())


def test_transient_setup_observation_recovers_readonly_without_provider_replay(
    update_case, monkeypatch
):
    import native_observation

    request, root, original, binding, operation = update_case
    collect = native_observation.collect
    reads = 0

    def interrupted_read(*args):
        nonlocal reads
        reads += 1
        if reads == 1:
            raise native_observation.ObservationError("Read interrupted")
        return collect(*args)

    monkeypatch.setattr(native_observation, "collect", interrupted_read)
    with pytest.raises(gate.GateError) as caught:
        gate.setup_update(request, root, "task")
    assert caught.value.outcome == "incomplete"
    original_after = root / "operations/task-setup/000.setup-after.json"
    preserved = original_after.read_bytes()
    assert "setup" not in json.loads(preserved)
    recovered = gate.reconcile_setup(request, root, "task", binding, original)
    assert recovered["setup"]["thread_id"] == "setup-thread"
    result = gate.verify_managed_update(request, root, "task", binding, original)
    assert result["thread_id"] == "setup-thread"
    assert result["windows"][0]["invocation_exit"] == 0
    assert original_after.read_bytes() == preserved
    assert operation["calls"] == 1


def test_failed_no_turn_setup_cannot_be_relabelled_as_success(update_case):
    request, root, original, binding, operation = update_case
    operation.update(mode="compare", native_exit=1, no_turn=True)
    with pytest.raises(gate.GateError):
        gate.setup_update(
            request, root, "task", resume_thread=original["setup"]["task"]["thread_id"]
        )
    recovered = gate.reconcile_setup(request, root, "task", binding, original)
    assert recovered["settlement"]["native_status"] == "no-new-turn"
    assert "setup" not in recovered
    with pytest.raises(gate.GateError) as caught:
        gate.verify_managed_update(request, root, "task", binding, original)
    assert caught.value.outcome == "incomplete"
    assert operation["calls"] == 1


@pytest.mark.parametrize(
    "status,exit_code",
    [("no-new-turn", 0), ("no-new-turn", 1), ("failed", 1), ("interrupted", 1)],
)
def test_reply_without_new_completed_setup_preserves_continuity_and_can_recover(
    update_case, status, exit_code
):
    request, root, original, binding, operation = update_case
    operation["mode"] = "partial"
    with pytest.raises(gate.GateError):
        gate.setup_update(request, root, "task")
    operation.update(
        mode="compare",
        native_exit=exit_code,
        no_turn=status == "no-new-turn",
        turn_status=status,
    )
    with pytest.raises(gate.GateError):
        gate.setup_update(request, root, "task", reply="Approve remaining work")
    directory = root / "operations/task-setup"
    preserved = gate.files(directory)
    recovered = gate.reconcile_setup(request, root, "task", binding, original)
    assert "setup" not in recovered
    assert recovered["settlement"]["native_status"] == status
    assert recovered["invocation_exit"] == exit_code
    assert operation["calls"] == 2
    operation.update(
        mode="write", native_exit=0, no_turn=False, turn_status="completed"
    )
    result = gate.setup_update(request, root, "task", reply="Approve remaining work")
    assert result["outcome"] == "managed-update-observed"
    assert [window["invocation_exit"] for window in result["windows"]] == [
        0,
        exit_code,
        0,
    ]
    current = gate.files(directory)
    assert all(current[path] == digest for path, digest in preserved.items())
    assert operation["calls"] == 3


def test_nonzero_native_exit_with_completed_correct_update_still_cannot_pass(
    update_case,
):
    request, root, original, binding, operation = update_case
    operation.update(native_exit=1, turn_status="completed")
    with pytest.raises(gate.GateError):
        gate.setup_update(request, root, "task")
    recovered = gate.reconcile_setup(request, root, "task", binding, original)
    assert recovered["setup"]["thread_id"] == "setup-thread"
    assert recovered["settlement"]["native_status"] == "completed"
    assert recovered["invocation_exit"] == 1
    plugin = Path(request["candidate"]["installed_plugin_root"])
    assert gate.image_hashes(recovered["managed_image"]) == {
        filename: gate.sha256(plugin / "assets/podway/procedures" / filename)
        for filename in gate.PROCEDURES
    }
    with pytest.raises(gate.GateError) as caught:
        gate.verify_managed_update(request, root, "task", binding, original)
    assert caught.value.outcome == "incomplete"
    assert operation["calls"] == 1


def test_explicit_reply_after_no_turn_recovers_without_separate_reconcile(update_case):
    request, root, _, _, operation = update_case
    operation["mode"] = "partial"
    with pytest.raises(gate.GateError):
        gate.setup_update(request, root, "task")
    operation.update(mode="compare", no_turn=True)
    with pytest.raises(gate.GateError):
        gate.setup_update(request, root, "task", reply="Approve remaining work")
    directory = root / "operations/task-setup"
    preserved = gate.files(directory)
    operation.update(mode="write", no_turn=False)
    result = gate.setup_update(request, root, "task", reply="Approve remaining work")
    assert result["outcome"] == "managed-update-observed"
    assert [window["invocation_exit"] for window in result["windows"]] == [0, 0, 0]
    current = gate.files(directory)
    assert all(current[path] == digest for path, digest in preserved.items())
    assert operation["calls"] == 3


@pytest.mark.parametrize("problem", ["active-turn", "unobserved-change"])
def test_unsettled_setup_cannot_dispatch_reply_or_rewrite_captures(
    update_case, problem
):
    request, root, _, _, operation = update_case
    operation.update(mode="partial", native_exit=1, turn_status="inProgress")
    with pytest.raises(gate.GateError):
        gate.setup_update(request, root, "task")
    if problem == "unobserved-change":
        (root / "task/.podway/procedures/aquarium-task-v2.yaml").write_text(
            "Unobserved write after native return"
        )
    directory = root / "operations/task-setup"
    preserved = gate.files(directory)
    with pytest.raises(gate.GateError) as caught:
        gate.setup_update(request, root, "task", reply="Approve")
    assert caught.value.outcome == "incomplete"
    current = gate.files(directory)
    assert all(current[path] == digest for path, digest in preserved.items())
    assert not list(directory.glob("*.reconciled-*.json"))
    assert operation["calls"] == 1


def test_comparison_without_required_transition_cannot_pass(update_case):
    request, root, _, _, operation = update_case
    operation["mode"] = "compare"
    with pytest.raises(gate.GateError) as caught:
        gate.setup_update(request, root, "task")
    assert caught.value.outcome == "incomplete"
    assert gate.image_hashes(
        read_window(root, 0, "before")["managed_image"]
    ) == gate.image_hashes(read_window(root, 0, "after")["managed_image"])


@pytest.mark.parametrize("after_proposal", [False, True])
def test_manual_copy_before_native_operation_cannot_be_relabelled_as_upgrade(
    update_case, after_proposal
):
    request, root, _, _, operation = update_case
    if after_proposal:
        operation["mode"] = "compare"
        with pytest.raises(gate.GateError):
            gate.setup_update(request, root, "task")
    calls = operation["calls"]
    plugin = Path(request["candidate"]["installed_plugin_root"])
    for filename in gate.PROCEDURES:
        (root / "task/.podway/procedures" / filename).write_bytes(
            (plugin / "assets/podway/procedures" / filename).read_bytes()
        )
    with pytest.raises(gate.GateError) as caught:
        gate.setup_update(
            request, root, "task", reply="Approve" if after_proposal else None
        )
    assert caught.value.outcome == "incomplete"
    assert operation["calls"] == calls


def test_genuine_current_sources_allow_native_noop_and_preserve_custom_source(
    update_case,
):
    request, root, original, binding, operation = update_case
    plugin = Path(request["candidate"]["installed_plugin_root"])
    for filename in gate.PROCEDURES:
        (plugin / "assets/podway/procedures" / filename).write_bytes(
            (root / "task/.podway/procedures" / filename).read_bytes()
        )
    custom = ".podway/procedures/aquarium-goal-v2.yaml"
    original["fixtures"]["task"]["custom"][custom] = gate.sha256(root / "task" / custom)
    write_json(root / "baseline.json", original)
    binding["baseline_sha256"] = gate.sha256(root / "baseline.json")
    operation["mode"] = "compare"
    result = gate.setup_update(request, root, "task")
    assert result["outcome"] == "managed-update-observed"
    assert gate.image_hashes(
        read_window(root, 0, "before")["managed_image"]
    ) == gate.image_hashes(read_window(root, 0, "after")["managed_image"])
    assert (
        gate.sha256(root / "task" / custom)
        == original["fixtures"]["task"]["custom"][custom]
    )


def test_posthoc_handle_and_uncertain_window_do_not_dispatch_or_pass(update_case):
    request, root, original, binding, operation = update_case
    request["candidate"]["managed_updates"] = {"task": "setup-thread"}
    with pytest.raises(gate.GateError) as caught:
        gate.verify_managed_update(request, root, "task", binding, original)
    assert caught.value.outcome == "incomplete"
    write_json(
        root / "operations/task-setup/000.setup-before.json", {"unresolved": True}
    )
    with pytest.raises(gate.GateError) as caught:
        gate.setup_update(request, root, "task")
    assert caught.value.outcome == "incomplete"
    assert operation["calls"] == 0


def test_incomplete_epic_resume_preserves_task_case_artifacts(native_case, monkeypatch):
    observation, evidence, repository = native_case
    root = repository.parent
    task_root = root / "task-startup"
    write_json(task_root / "startup-evidence.json", evidence)
    preserved = gate.files(task_root)
    epic = root / "epic"
    epic.mkdir()
    shutil.copyfile(repository / "greet.py", epic / "greet.py")
    monkeypatch.syspath_prepend(str(ROOT / "tests/vm"))
    import native_observation

    monkeypatch.setattr(
        native_observation, "collect", lambda *_: copy.deepcopy(observation)
    )
    monkeypatch.setattr(
        gate, "invoke", lambda *_args, **_kwargs: "actual-existing-thread"
    )
    monkeypatch.setattr(gate, "oracle", lambda *_: [])
    monkeypatch.setattr(
        gate,
        "command",
        lambda *_args, **_kwargs: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    monkeypatch.setattr(
        gate,
        "observe",
        lambda _request, target: {
            "status": {
                "procedure": {
                    "id": "aquarium-task-v2"
                    if target == repository
                    else "aquarium-goal-v2"
                }
            },
            "guidance": {
                "node": {
                    "graph_node_id": "document"
                    if target == repository
                    else "record-evidence"
                }
            },
        },
    )
    request = {
        "tools": {"codex": "/tools/codex", "python": sys.executable},
        "authority": {"observer": "Operator", "reference": "VM request"},
    }
    assert gate.smoke(request, root, "task")["outcome"] == "pass"
    with pytest.raises(gate.GateError) as caught:
        gate.smoke(request, root, "epic")
    assert caught.value.outcome == "incomplete"
    epic_root = root / "epic-startup"
    epic_evidence = copy.deepcopy(evidence)
    for key in (
        "executor_assignment",
        "evaluator_assignment",
        "executor_result",
        "evaluator_assessment",
    ):
        original_path = Path(evidence[key])
        target = epic_root / original_path.name
        document = gate.read_json(original_path)
        if key.endswith("assignment"):
            document["work"]["repository"] = str(epic)
        write_json(target, document)
        epic_evidence[key] = str(target)
    write_json(epic_root / "startup-evidence.json", epic_evidence)
    assert gate.smoke(request, root, "epic")["outcome"] == "pass"
    assert gate.files(task_root) == preserved
    assert gate.smoke(request, root, "task")["outcome"] == "pass"
    wrong_case = copy.deepcopy(evidence)
    wrong_case["executor_assignment"] = epic_evidence["executor_assignment"]
    with pytest.raises(gate.GateError) as caught:
        gate.validate_native_case(observation, wrong_case, repository)
    assert caught.value.outcome == "incomplete"
    assert gate.files(task_root) == preserved


@pytest.mark.parametrize("malformed", ["null-target", "criteria-object"])
def test_malformed_report_refreshes_stale_pass_with_structured_incomplete(
    native_case, monkeypatch, capsys, malformed
):
    observation, evidence, repository = native_case
    path = Path(evidence["evaluator_assessment"])
    document = gate.read_json(path)
    if malformed == "null-target":
        document["target"] = None
    else:
        document["criteria"] = {row["id"]: row for row in document["criteria"]}
    write_json(path, document)
    observation["descendants"][1]["items"][-1]["text"] = json.dumps(document)
    root = repository.parent
    write_json(root / "result.json", {"outcome": "pass", "old": True})
    monkeypatch.setattr(gate, "load_request", lambda *_: ({}, root, {}))
    monkeypatch.setattr(
        gate,
        "run_gate",
        lambda *_: gate.validate_native_case(observation, evidence, repository),
    )
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "run", "--request", "request.json"])
    assert gate.main() == 2
    result = json.loads(capsys.readouterr().out)
    assert result["outcome"] == "incomplete"
    assert gate.read_json(root / "result.json") == result
    assert "old" not in result


@pytest.mark.parametrize(
    "name,procedure,node,passes",
    [
        ("task", "aquarium-task-v2", "document", True),
        ("epic", "aquarium-goal-v2", "record-evidence", True),
        ("task", "aquarium-goal-v2", "record-evidence", False),
        ("epic", "aquarium-task-v2", "document", False),
        ("task", "aquarium-task-v2", "record-evidence", False),
        ("epic", "aquarium-goal-v2", "document", False),
    ],
)
def test_each_startup_case_requires_its_correct_procedure_and_progression(
    name, procedure, node, passes
):
    current = {
        "status": {"procedure": {"id": procedure}},
        "guidance": {"node": {"graph_node_id": node}},
    }
    if passes:
        gate.verify_startup_state(name, current)
    else:
        with pytest.raises(gate.GateError):
            gate.verify_startup_state(name, current)


def test_recovery_reuses_same_invocation_without_dispatch(tmp_path, monkeypatch):
    directory = tmp_path / "operations/task-startup"
    write_json(
        directory / "000.invocation.json",
        {"exit": 0, "thread_id": "actual-existing-thread"},
    )
    (directory / "000.jsonl").write_text(
        '{"type":"thread.started","thread_id":"actual-existing-thread"}\n'
    )
    monkeypatch.setattr(
        gate.subprocess,
        "run",
        lambda *_args, **_kwargs: pytest.fail("replayed native work"),
    )
    assert (
        gate.invoke({}, tmp_path, "task-startup", "new prompt")
        == "actual-existing-thread"
    )


def test_initial_candidate_setup_can_resume_known_native_handle(tmp_path):
    (tmp_path / "task").mkdir()
    native = tmp_path / "codex"
    native.write_text(
        f"#!{sys.executable}\n"
        "import json,sys\n"
        "sys.stdin.read()\n"
        "print(json.dumps({'type':'thread.started','thread_id':sys.argv[-2]}))\n"
    )
    native.chmod(0o755)
    request = {"tools": {"codex": str(native)}, "authority": {"observer": "Operator"}}
    handle = "known-released-native-thread"
    assert (
        gate.invoke(
            request,
            tmp_path,
            "task-setup",
            "Invoke installed setup",
            resume_thread=handle,
        )
        == handle
    )
    receipt = gate.read_json(tmp_path / "operations/task-setup/000.invocation.json")
    assert receipt["argv"][-3:] == ["resume", handle, "-"]
    assert receipt["input_sha256"] == gate.sha256(
        tmp_path / "operations/task-setup/000.input"
    )


@pytest.mark.parametrize("handle", [None, "known-native-thread"])
def test_failed_native_invocation_retains_actual_exit_and_known_handle(
    tmp_path, handle
):
    (tmp_path / "task").mkdir()
    native = tmp_path / "codex"
    native.write_text(
        f"#!{sys.executable}\nimport sys\nsys.stdin.read()\nsys.exit(1)\n"
    )
    native.chmod(0o755)
    request = {"tools": {"codex": str(native)}, "authority": {"observer": "Operator"}}
    with pytest.raises(gate.GateError) as caught:
        gate.invoke(
            request, tmp_path, "task-setup", "Actual input", resume_thread=handle
        )
    assert caught.value.outcome == "incomplete"
    receipt = gate.read_json(tmp_path / "operations/task-setup/000.invocation.json")
    assert receipt["exit"] == 1
    assert receipt["thread_id"] == handle
    assert receipt["handle_source"] == ("known-resume" if handle else "unavailable")
    assert receipt["input_sha256"] == gate.sha256(
        tmp_path / "operations/task-setup/000.input"
    )


def test_unknown_previous_dispatch_is_not_replayed(tmp_path, monkeypatch):
    directory = tmp_path / "operations/task-startup"
    directory.mkdir(parents=True)
    (directory / "000.jsonl").write_text(
        '{"type":"thread.started","thread_id":"uncertain-thread"}\n'
    )
    monkeypatch.setattr(
        gate.subprocess,
        "run",
        lambda *_args, **_kwargs: pytest.fail("replayed uncertain work"),
    )
    with pytest.raises(gate.GateError) as caught:
        gate.invoke({}, tmp_path, "task-startup", "new prompt")
    assert caught.value.outcome == "incomplete"


def test_cleanup_rejects_pending_descendants(native_case):
    observation, _, _ = native_case
    observation["root"]["turns"] = [{"status": "completed"}]
    gate.verify_settlement(observation)
    observation["descendants"][1]["turns"][-1]["status"] = "inProgress"
    with pytest.raises(gate.GateError) as caught:
        gate.verify_settlement(observation)
    assert caught.value.outcome == "incomplete"


def test_terminal_recovery_history_does_not_require_every_old_turn_to_succeed(
    native_case,
):
    observation, evidence, repository = native_case
    observation["descendants"][0]["turns"].insert(
        0, {"status": "interrupted", "error": None}
    )
    assert (
        gate.validate_native_case(observation, evidence, repository)["executor_thread"]
        == "executor"
    )


def test_public_reader_uses_bounded_native_read_api_and_exits(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "tests/vm"))
    from native_observation import collect

    executable = tmp_path / "codex"
    log = tmp_path / "requests.jsonl"
    executable.write_text(
        f"#!{sys.executable}\n"
        "import json,sys\n"
        f"log={str(log)!r}\n"
        "for line in sys.stdin:\n"
        " q=json.loads(line)\n"
        " if 'id' not in q: continue\n"
        " with open(log,'a') as f: f.write(json.dumps(q)+'\\n')\n"
        " method=q['method']; params=q['params']; tid=params.get('threadId','root')\n"
        " if method=='initialize': result={}\n"
        " elif method=='thread/read': result={'thread':{'id':tid,'cwd':'.','parentThreadId':None if tid=='root' else 'root','path':'unneeded-private-path','status':{'type':'notLoaded'}}}\n"
        " elif method=='thread/list': result={'data':[{'id':'executor'}],'nextCursor':None}\n"
        " elif method=='thread/turns/list': result={'data':[{'id':'turn','status':'completed','error':None}],'nextCursor':None}\n"
        " elif method=='thread/items/list':\n"
        "  items=[{'type':'subAgentActivity','id':'spawn','kind':'started','agentPath':'/root/executor','agentThreadId':'executor'}] if tid=='root' else [{'type':'agentMessage','text':'Actual child result','phase':'final_answer'}]\n"
        "  items.append({'type':'reasoning','text':'unneeded'})\n"
        "  result={'data':[{'item':i} for i in items],'nextCursor':None}\n"
        " else: raise RuntimeError(method)\n"
        " print(json.dumps({'id':q['id'],'result':result}),flush=True)\n"
    )
    executable.chmod(0o755)
    observation = collect(str(executable), tmp_path, "root")
    assert observation["reader_exit"] is not None
    assert observation["descendants"][0]["metadata"]["parentThreadId"] == "root"
    assert "path" not in observation["root"]["metadata"]
    assert not any(item["type"] == "reasoning" for item in observation["root"]["items"])
    requests = [json.loads(line) for line in log.read_text().splitlines()]
    listed = next(
        item["params"] for item in requests if item["method"] == "thread/list"
    )
    assert listed["ancestorThreadId"] == "root"
    assert listed["useStateDbOnly"] is True
    assert all(
        item["params"]["itemsView"] == "full"
        for item in requests
        if item["method"] == "thread/turns/list"
    )
    assert not any(
        item["method"] in {"thread/start", "thread/resume", "turn/start"}
        for item in requests
    )


def test_changed_upgrade_candidate_cannot_reuse_old_success(
    tmp_path, candidate, monkeypatch
):
    monkeypatch.setattr(
        gate, "verify_candidate", lambda *_: {"git_sha": "new-candidate"}
    )
    monkeypatch.setattr(gate, "versions", lambda *_: {"aquarium": "candidate"})
    monkeypatch.setattr(gate, "installed_plugin", lambda *_: {"version": "candidate"})
    write_json(tmp_path / "baseline.json", {"schema": "aquarium.vm-baseline/v1"})
    write_json(
        tmp_path / "upgrade-observation.json",
        {
            "candidate": {"git_sha": "old-candidate"},
            "baseline_sha256": gate.sha256(tmp_path / "baseline.json"),
            "combination": {"aquarium": "candidate"},
        },
    )
    result = gate.run_gate({"candidate": candidate, "authority": {}}, tmp_path)
    assert result["outcome"] == "incomplete"
    assert result["cases"] == []
    assert result["candidate"] == {"git_sha": "new-candidate"}


def test_make_target_is_external_to_normal_aggregate():
    result = subprocess.run(
        ["make", "-n", "test"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    assert result.returncode == 0
    assert " -B tests/vm/run_acceptance.py run" not in result.stdout
    result = subprocess.run(
        ["make", "-n", "test-vm"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert " -B tests/vm/run_acceptance.py run" in result.stdout
