"""Synthetic driver records and isolated filesystem controls, not qualification."""

import json
import os
import signal
import subprocess
import sys
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tests/vm/recipes"))
sys.path.insert(0, str(ROOT / "tests/vm"))
import release_fixture as fixture
import release_orchestration as release


def test_registry_has_fixed_case_outputs_and_original_coverage():
    suites = json.loads((ROOT / "tests/vm/host_suites.json").read_text())["suites"]
    inventory = release.cases(SimpleNamespace(checkout=ROOT))
    suite = suites[release.SUITE]
    assert set(suite["manual"]["required_scenarios"]) == set(inventory)
    assert len(inventory) == 13
    native_rows = [
        row
        for case in inventory.values()
        for row in case["variants"]
        if row.get("original_native_row")
    ]
    assert len(native_rows) == 7
    assert all(row["native_required"] is True for row in native_rows)
    assert len(set(suite["required_outputs"])) == 34
    for case in inventory:
        for suffix in ("tar", "manifest.json"):
            assert (
                f"results/{release.SUITE}/evidence/{case}.{suffix}"
                in suite["required_outputs"]
            )
    assert (
        "release-startup"
        in suites["release-acceptance"]["manual"]["required_scenarios"]
    )
    assert "release-startup" not in suites["epic-squad"]["manual"]["required_scenarios"]


@pytest.fixture
def context(tmp_path, monkeypatch):
    results = tmp_path.resolve() / "results/release-orchestration"
    results.mkdir(parents=True)
    context = SimpleNamespace(
        root=tmp_path.resolve(),
        checkout=ROOT,
        home=tmp_path / "home",
        codex="unused",
        inputs={"candidate": {"git_sha": "a" * 40}},
        job={"job_id": "synthetic"},
    )
    monkeypatch.setattr(release.lib, "guard", lambda _: {})
    monkeypatch.setattr(release.lib, "job_identity", lambda: context.job)
    monkeypatch.setattr(release.lib, "verify_sealed_inputs", lambda _: {})
    monkeypatch.setattr(release.lib, "results_directory", lambda _: results)
    monkeypatch.setattr(release.lib, "RECORDED_INVENTORIES", {})
    return context, results


def test_wrong_guest_identity_precedes_all_writes(tmp_path, monkeypatch):
    root = tmp_path / "absent"
    monkeypatch.setattr(
        release.lib,
        "guard",
        lambda _: (_ for _ in ()).throw(release.lib.IdentityError("wrong guest")),
    )
    with pytest.raises(release.lib.IdentityError):
        release.run(SimpleNamespace(root=root), "prepare")
    assert not root.exists()


def test_native_start_and_resume_receive_verified_environment(context, monkeypatch):
    context, results = context
    world = context.root / "world"
    fixture.seed(world, order="before", baseline="previous", mode="full")
    for name in ("GH_TOKEN", "GITHUB_TOKEN", "GIT_DIR", "GIT_WORK_TREE"):
        monkeypatch.setenv(name, "synthetic-production-value")
    fake = context.root / "synthetic-codex"
    fake.write_text(
        f"#!{sys.executable}\n"
        "import json,os,sys\n"
        "print(json.dumps({'type':'thread.started','thread_id':'synthetic-thread'}))\n"
        "print(json.dumps({'type':'turn.completed'}))\n"
        "with open(os.path.join(os.environ['AQUARIUM_RELEASE_FIXTURE_ROOT'],'selected-env.json'),'w') as f:\n"
        " json.dump({'argv':sys.argv[1:],'cwd':os.getcwd(),'input':sys.stdin.read(),'env':dict(os.environ)},f)\n"
    )
    fake.chmod(0o700)
    context.codex = str(fake)
    directory = results / "synthetic-case"
    directory.mkdir()
    policy = ["exec", "--json", "--sandbox", "workspace-write"]
    for path in (
        directory,
        world / "repo/.git",
        world / "origin.git",
        world / "hosting",
    ):
        policy += ["--add-dir", str(path)]

    def check_launch(number, value, suffix):
        selected = json.loads((world / "selected-env.json").read_text())
        assert selected["argv"] == policy + [
            "--output-last-message",
            str(directory / f"operations/{number:03d}.last"),
            *suffix,
        ]
        assert selected["cwd"] == str(world / "repo")
        assert selected["input"] == value
        env = selected["env"]
        assert env["HOME"] == str(context.home)
        assert env["XDG_CONFIG_HOME"] == os.environ.get(
            "XDG_CONFIG_HOME", str(context.home / ".config")
        )
        assert env["PATH"].split(os.pathsep)[0] == str(world / "bin")
        assert env["GIT_CONFIG_GLOBAL"] == os.devnull
        assert env["GIT_CONFIG_NOSYSTEM"] == "1"
        assert env["GIT_CONFIG_COUNT"] == "1"
        assert env["GIT_CONFIG_KEY_0"] == "core.hooksPath"
        assert env["GIT_CONFIG_VALUE_0"] == str(world / "hooks")
        assert all(
            name not in env
            for name in ("GH_TOKEN", "GITHUB_TOKEN", "GIT_DIR", "GIT_WORK_TREE")
        )

    assert (
        release.invoke(context, world, directory, "synthetic prompt", None)["thread_id"]
        == "synthetic-thread"
    )
    check_launch(0, "synthetic prompt", ["-C", str(world / "repo"), "-"])
    originals = {p: p.read_bytes() for p in (directory / "operations").iterdir()}
    with pytest.raises(release.lib.RecipeError, match="existing native"):
        release.invoke(context, world, directory, "duplicate", None)
    assert (
        release.invoke(context, world, directory, "", "actual synthetic reply")[
            "thread_id"
        ]
        == "synthetic-thread"
    )
    check_launch(1, "actual synthetic reply", ["resume", "synthetic-thread", "-"])
    assert all(p.read_bytes() == value for p, value in originals.items())
    (world / "bin/gh").write_text("changed")
    with pytest.raises(fixture.FixtureError):
        release.invoke(context, world, directory, "", "next reply")
    assert len(list((directory / "operations").glob("*.invocation.json"))) == 2


@pytest.mark.parametrize("resume", [False, True])
@pytest.mark.parametrize("fault", ["missing", "file", "symlink", "foreign-owner"])
@pytest.mark.parametrize(
    "root", ["world", "repo", "repo/.git", "origin.git", "hosting", "evidence"]
)
def test_unsafe_native_writable_roots_precede_effects(
    context, monkeypatch, root, fault, resume
):
    ctx, results = context
    world = ctx.root / "world"
    fixture.seed(world, order="before", baseline="previous", mode="full")
    directory = results / "case"
    directory.mkdir()
    if resume:
        native_window(directory, 0)
    path = (
        directory if root == "evidence" else world if root == "world" else world / root
    )
    if fault == "foreign-owner":
        stat = Path.stat

        def foreign_owner(value, *args, **kwargs):
            actual = stat(value, *args, **kwargs)
            if value == path:
                fields = list(actual)
                fields[4] = os.getuid() + 1
                return os.stat_result(fields)
            return actual

        monkeypatch.setattr(Path, "stat", foreign_owner)
    else:
        saved = path.with_name(path.name + ".saved")
        path.rename(saved)
        if fault == "file":
            path.write_text("not a directory")
        elif fault == "symlink":
            path.symlink_to(saved, target_is_directory=True)
    before = {p for p in ctx.root.rglob("*")}
    originals = {
        p: p.read_bytes() for p in before if p.is_file() and not p.is_symlink()
    }
    # Even fixture Git validation must follow the root guard.
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *a, **kw: pytest.fail("unsafe root launched a process"),
    )
    with pytest.raises(fixture.FixtureError):
        release.invoke(ctx, world, directory, "prompt", "reply" if resume else None)
    assert {p for p in ctx.root.rglob("*")} == before
    assert all(p.read_bytes() == value for p, value in originals.items())


@pytest.mark.parametrize("resume", [False, True])
@pytest.mark.parametrize(
    "fault",
    [
        "outside-world",
        "outside-evidence",
        "evidence-is-world",
        "evidence-contains-world",
    ],
)
def test_native_grants_stay_inside_job_and_separate_from_world(
    context, monkeypatch, fault, resume
):
    ctx, results = context
    owned = ctx.root
    ctx.root = owned / "job"
    ctx.root.mkdir()
    world = (owned if fault == "outside-world" else ctx.root) / "world"
    fixture.seed(world, order="before", baseline="previous", mode="full")
    directory = {
        "outside-world": ctx.root / "evidence",
        "outside-evidence": results / "case",
        "evidence-is-world": world,
        "evidence-contains-world": ctx.root,
    }[fault]
    directory.mkdir(exist_ok=True)
    if resume:
        native_window(directory, 0)
    before = {p for p in owned.rglob("*")}
    originals = {p: p.read_bytes() for p in before if p.is_file()}
    monkeypatch.setattr(
        subprocess,
        "Popen",
        lambda *a, **kw: pytest.fail("unsafe boundary launched a process"),
    )
    with pytest.raises(fixture.FixtureError):
        release.invoke(ctx, world, directory, "prompt", "reply" if resume else None)
    assert {p for p in owned.rglob("*")} == before
    assert all(p.read_bytes() == value for p, value in originals.items())


@pytest.mark.parametrize("resume", [False, True])
@pytest.mark.parametrize(
    "fault", ["missing", "symlink", "nonexecutable", "changed", "foreign-origin"]
)
def test_native_launch_revalidates_hosting_and_origin_before_writes(
    context, monkeypatch, fault, resume
):
    ctx, results = context
    world = ctx.root / "world"
    fixture.seed(world, order="before", baseline="previous", mode="full")
    directory = results / "case"
    directory.mkdir()
    if resume:
        native_window(directory, 0)
    gh = world / "bin/gh"
    if fault == "missing":
        gh.unlink()
    elif fault == "symlink":
        saved = gh.with_name("gh.saved")
        gh.rename(saved)
        gh.symlink_to(saved)
    elif fault == "nonexecutable":
        gh.chmod(0o600)
    elif fault == "changed":
        gh.write_text("changed executable bytes")
    else:
        fixture.git(world, "remote", "set-url", "origin", str(ctx.root / "foreign.git"))
    before = {p: p.read_bytes() for p in directory.rglob("*") if p.is_file()}
    popen = subprocess.Popen

    def validated_process(argv, *args, **kwargs):
        assert argv[0] == "git", "fixture validation must precede native launch"
        return popen(argv, *args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", validated_process)
    with pytest.raises(fixture.FixtureError):
        release.invoke(ctx, world, directory, "prompt", "reply" if resume else None)
    assert {p: p.read_bytes() for p in directory.rglob("*") if p.is_file()} == before


def test_uncertain_native_window_cannot_be_redispatched(context):
    context, results = context
    world = context.root / "world"
    fixture.seed(world, order="before", baseline="previous", mode="full")
    directory = results / "case"
    (directory / "operations").mkdir(parents=True)
    (directory / "operations/000.jsonl").write_text("partial")
    with pytest.raises(release.lib.RecipeError, match="uncertain"):
        release.invoke(context, world, directory, "prompt", None)


def populated(context):
    context, results = context
    index = {"candidate_sha": "a" * 40, "cases": {}}
    for name in release.cases(context):
        directory = results / "originals" / name
        directory.mkdir(parents=True)
        (directory / "original.json").write_bytes(b'{"explicitly":"synthetic"}\n')
        index["cases"][name] = {"required": ["original.json"], "observations": []}
    records = {
        "case-evidence.json": index,
        "prepared.json": {"candidate_sha": "a" * 40},
        "candidate.json": {"candidate_sha": "a" * 40},
        "consumer-cleanup.json": {
            "consumer_cleanup": "verified",
            "candidate_sha": "a" * 40,
        },
        "consumer-result.json": {
            "candidate": {"git_sha": "a" * 40},
            "consumer_cleanup": "verified",
        },
        "inventories.json": {
            "schema": "aquarium.vm-suite-inventories/v1",
            "inventories": {},
        },
    }
    for name, value in records.items():
        release.lib.write_document(results / name, value)
    return context, results, index


def test_staging_preserves_original_bytes_and_restoration_receipt(context):
    ctx, results, _ = populated(context)
    before = (results / "consumer-result.json").read_bytes()
    assert release.stage(ctx, results) == 0
    with tarfile.open(results / "evidence/consumer-restoration.tar") as archive:
        assert archive.extractfile("consumer-result.json").read() == before
        assert (
            archive.extractfile("originals/consumer-restoration/original.json").read()
            == b'{"explicitly":"synthetic"}\n'
        )
    assert (results / "consumer-result.json").read_bytes() == before
    assert (
        json.loads((results / "result.json").read_text())["functional_cases"]
        == "not assessed"
    )


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "symlink",
        "traversal",
        "candidate",
        "empty-required",
        "malformed-inventory",
    ],
)
def test_staging_missing_or_unsafe_evidence_never_passes(context, fault):
    ctx, results, index = populated(context)
    case = next(iter(index["cases"]))
    original = results / "originals" / case / "original.json"
    if fault == "missing":
        original.unlink()
    elif fault == "symlink":
        original.unlink()
        original.symlink_to(results / "candidate.json")
    elif fault == "traversal":
        index["cases"][case]["required"] = ["../candidate.json"]
    elif fault == "candidate":
        index["candidate_sha"] = "b" * 40
    elif fault == "empty-required":
        index["cases"][case]["required"] = []
    else:
        (results / "inventories.json").write_bytes(b"{broken")
    release.lib.write_document(results / "case-evidence.json", index)
    assert release.stage(ctx, results) == 2
    assert len(list((results / "evidence").glob("*.tar"))) == 13
    if fault == "malformed-inventory":
        assert (results / "inventories.json").read_bytes() == b"{broken"
    if fault == "empty-required":
        with tarfile.open(results / f"evidence/{case}.tar") as archive:
            assert archive.extractfile(f"originals/{case}/original.json").read()


def test_interrupted_archive_preserves_previous_complete_evidence(context, monkeypatch):
    ctx, results, _ = populated(context)
    assert release.stage(ctx, results) == 0
    path = results / "evidence/released-baseline.tar"
    before = path.read_bytes()

    def interrupted(*_):
        raise OSError("injected staging failure")

    monkeypatch.setattr(release.lib, "stage_evidence_archive", interrupted)
    assert release.stage(ctx, results) == 2
    assert path.read_bytes() == before
    assert (
        len(json.loads((results / "stage-evidence.json").read_text())["attempts"]) == 2
    )


def test_manifest_commit_failure_preserves_last_complete_pair(context, monkeypatch):
    ctx, results, index = populated(context)
    assert release.stage(ctx, results) == 0
    archive = results / "evidence/released-baseline.tar"
    manifest = archive.with_suffix(".manifest.json")
    prior = (archive.read_bytes(), manifest.read_bytes())
    added = results / "originals/released-baseline/new.json"
    added.write_bytes(b'{"new":"immutable original"}\n')
    index["cases"]["released-baseline"]["required"].append("new.json")
    release.lib.write_document(results / "case-evidence.json", index)
    replace = Path.replace

    def fail_manifest(path, target):
        if path.name == "released-baseline.manifest.json.partial":
            raise OSError("injected second replacement failure")
        return replace(path, target)

    with monkeypatch.context() as fault:
        fault.setattr(Path, "replace", fail_manifest)
        assert release.stage(ctx, results) == 2
    assert (archive.read_bytes(), manifest.read_bytes()) == prior
    assert added.read_bytes() == b'{"new":"immutable original"}\n'
    failed = json.loads((results / "stage-evidence.json").read_text())
    assert len(failed["attempts"]) == 2
    assert failed["ok"] is False
    assert release.stage(ctx, results) == 0
    assert archive.read_bytes() != prior[0]
    assert release.archive_pair_valid(archive, manifest)
    with tarfile.open(archive) as content:
        assert (
            content.extractfile("originals/released-baseline/new.json").read()
            == added.read_bytes()
        )


def test_first_manifest_failure_transports_available_payload_and_retries(
    context, monkeypatch
):
    ctx, results, _index = populated(context)
    original = results / "originals/released-baseline/original.json"
    original_bytes = original.read_bytes()
    archive = results / "evidence/released-baseline.tar"
    manifest = archive.with_suffix(".manifest.json")
    replace = Path.replace

    def fail_manifest(path, target):
        if path.name == "released-baseline.manifest.json.partial":
            raise OSError("synthetic first manifest commit failure")
        return replace(path, target)

    with monkeypatch.context() as fault:
        fault.setattr(Path, "replace", fail_manifest)
        assert release.stage(ctx, results) == 2
    with tarfile.open(archive) as content:
        assert (
            content.extractfile("originals/released-baseline/original.json").read()
            == original_bytes
        )
        assert (
            content.extractfile("prepared.json").read()
            == (results / "prepared.json").read_bytes()
        )
    document = json.loads(manifest.read_text())
    assert document["sha256"] == fixture.digest(archive)
    assert "originals/released-baseline/original.json" in {
        row["path"] for row in document["members"]
    }
    first = json.loads((results / "stage-evidence.json").read_text())
    assert first["ok"] is False
    assert len(first["attempts"]) == 1
    assert len(list((results / "evidence").glob("*.tar"))) == 13
    assert len(list((results / "evidence").glob("*.manifest.json"))) == 13
    assert original.read_bytes() == original_bytes
    assert release.stage(ctx, results) == 0
    history = json.loads((results / "stage-evidence.json").read_text())
    assert len(history["attempts"]) == 2
    assert history["attempts"][0]["ok"] is False
    assert history["ok"] is True
    with tarfile.open(archive) as content:
        assert (
            content.extractfile("originals/released-baseline/original.json").read()
            == original_bytes
        )


def test_process_exit_between_pair_replacements_recovers_original_pair(
    context, monkeypatch
):
    ctx, results, index = populated(context)
    assert release.stage(ctx, results) == 0
    archive = results / "evidence/released-baseline.tar"
    manifest = archive.with_suffix(".manifest.json")
    prior = (archive.read_bytes(), manifest.read_bytes())
    added = results / "originals/released-baseline/new.json"
    added.write_bytes(b'{"new":"original after interruption"}\n')
    index["cases"]["released-baseline"]["required"].append("new.json")
    release.lib.write_document(results / "case-evidence.json", index)
    script = """
import os,sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path(sys.argv[1]) / 'tests/vm/recipes'))
import release_orchestration as release
results = Path(sys.argv[2])
context = SimpleNamespace(checkout=Path(sys.argv[1]), inputs={'candidate':{'git_sha':'a'*40}})
original = Path.replace
def replace(path, target):
    if path.name == 'released-baseline.manifest.json.partial':
        os._exit(91)
    return original(path, target)
Path.replace = replace
release.stage(context, results)
"""
    interrupted = subprocess.run(
        [sys.executable, "-B", "-c", script, str(ROOT), str(results)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert interrupted.returncode == 91, interrupted.stdout + interrupted.stderr
    assert archive.with_name(archive.name + ".previous").read_bytes() == prior[0]
    assert manifest.with_name(manifest.name + ".previous").read_bytes() == prior[1]
    assert (
        json.loads((results / "stage-evidence.json").read_text())["state"]
        == "in-progress"
    )
    with monkeypatch.context() as fault:
        fault.setattr(
            release.lib,
            "stage_evidence_archive",
            lambda *_: (_ for _ in ()).throw(OSError("stop after recovery")),
        )
        assert release.stage(ctx, results) == 2
    assert (archive.read_bytes(), manifest.read_bytes()) == prior
    assert release.stage(ctx, results) == 0
    assert release.archive_pair_valid(archive, manifest)
    assert (
        len(json.loads((results / "stage-evidence.json").read_text())["attempts"]) == 4
    )
    assert added.read_bytes() == b'{"new":"original after interruption"}\n'


def test_native_required_variants_cannot_be_filled_with_helper_passes(context):
    ctx, results, index = populated(context)
    ctx.profile = lambda _: {"profile_id": "synthetic-profile"}
    ctx.profile_digest = lambda _: "d" * 64
    for name, case in release.cases(ctx).items():
        index["cases"][name]["observations"] = [
            {
                "variant": row["id"],
                "status": "pass",
                "evidence_class": "fixture-helper",
                "decision_reference": "synthetic operator record",
            }
            for row in case["variants"]
        ]
    release.lib.write_document(results / "case-evidence.json", index)
    release.lib.write_document(
        results / "stage-evidence.json",
        {
            "ok": True,
            "case_index_sha256": fixture.digest(results / "case-evidence.json"),
        },
    )
    assert release.run(ctx, "complete-template") == 0
    rows = json.loads((results / "manual-complete-template.json").read_text())[
        "scenarios"
    ]
    assert (
        next(row for row in rows if row["id"] == "full-gate-before-commit")["status"]
        == "unobserved"
    )


def test_cleanup_refuses_invalid_inventory_before_new_snapshot(context, monkeypatch):
    ctx, results, _ = populated(context)
    (results / "inventories.json").write_bytes(b"{broken")
    monkeypatch.setattr(
        release,
        "observation",
        lambda *args: pytest.fail("must not snapshot over invalid history"),
    )
    with pytest.raises(release.lib.RecipeError, match="invalid"):
        release.run(ctx, "consumer-cleanup")
    assert (results / "inventories.json").read_bytes() == b"{broken"


def native_window(directory, number, *, exit=0, handle="synthetic-root"):
    windows = directory / "operations"
    windows.mkdir(parents=True, exist_ok=True)
    prefix = windows / f"{number:03d}"
    Path(str(prefix) + ".input").write_text("explicitly synthetic input")
    Path(str(prefix) + ".stderr").write_text("")
    Path(str(prefix) + ".jsonl").write_text(
        json.dumps({"type": "thread.started", "thread_id": handle}) + "\n"
        if handle
        else ""
    )
    fixture.write_once(
        Path(str(prefix) + ".request.json"),
        {
            "argv": ["synthetic", str(number)],
            "input_sha256": fixture.digest(Path(str(prefix) + ".input")),
        },
    )
    fixture.write_once(
        Path(str(prefix) + ".invocation.json"),
        {
            "argv": ["synthetic", str(number)],
            "exit": exit,
            "thread_id": handle,
        },
    )


@pytest.fixture
def native_records(context, monkeypatch):
    import native_observation

    ctx, results = context
    world = ctx.root / "release-worlds/release-startup"
    world.parent.mkdir()
    fixture.seed(world, order="before", baseline="previous", mode="full")
    directory = results / "originals/release-startup/release-startup"
    (directory / "operations").mkdir(parents=True)
    native_window(directory, 0)
    observed = {
        "root": {
            "metadata": {"id": "synthetic-root", "cwd": str(world / "repo")},
            "turns": [{"status": "completed"}],
            "items": [],
        },
        "descendants": [],
    }
    evidence = {}
    reports = {}
    for role, schema, result_key in [
        ("executor", "aquarium.executor-handoff/v3", "executor_result"),
        ("evaluator", "aquarium.evaluator-assessment/v3", "evaluator_assessment"),
    ]:
        report = {
            "schema": schema,
            "target": {
                "files": {"manifest.json": fixture.digest(world / "repo/manifest.json")}
            },
            "checkpoint_result": "pass",
            "verdict": "evidence-needed",
            "criteria": [
                {
                    "id": name,
                    "state": "met",
                    "source": "original fixture criteria",
                    "evidence": ["synthetic source record"],
                }
                for name in release.STARTUP_CRITERIA
            ]
            + [{"id": "future-publication", "state": "unverified"}],
        }
        reports[role] = report
        path = directory / (role + "-result.json")
        fixture.write_once(path, report)
        evidence[result_key] = str(path)
        assignment = directory / (role + "-assignment.json")
        fixture.write_once(
            assignment,
            {
                "schema": "aquarium.assignment/v3",
                "role": role,
                "work": {"repository": str(world / "repo")},
            },
        )
        evidence[role + "_assignment"] = str(assignment)
        evidence[role + "_agent"] = role
        observed["root"]["items"].extend(
            {
                "type": "subAgentActivity",
                "kind": kind,
                "agentThreadId": role,
                "agentPath": "/root/" + role,
            }
            for kind in ("started", "completed")
        )
        observed["descendants"].append(
            {
                "metadata": {"id": role, "parentThreadId": "synthetic-root"},
                "turns": [{"status": "completed", "error": None}],
                "items": [
                    {
                        "type": "agentMessage",
                        "phase": "final_answer",
                        "text": json.dumps(report),
                    }
                ],
            }
        )
    fixture.write_once(directory / "startup-evidence.json", evidence)
    monkeypatch.setattr(native_observation, "collect", lambda *args: observed)
    return ctx, results, directory, reports, observed, world


def test_startup_capture_preserves_future_gaps_and_original_public_results(
    native_records,
):
    ctx, results, directory, reports, observed, _world = native_records
    result = release.capture(ctx, results, "release-startup", startup=True)
    assert result["state"] == "recorded"
    assert reports["executor"]["target"]["files"]
    assert result["native_capture"] == "native-000.json"
    assert json.loads((directory / result["native_capture"]).read_text()) == observed
    assert result["actors"] == {"executor": "executor", "evaluator": "evaluator"}
    assert (
        json.loads((directory / "evaluator-result.json").read_text())["verdict"]
        == "evidence-needed"
    )


@pytest.mark.parametrize(
    "fault",
    ["negative", "missing-criterion", "unbound-report", "byte-drift", "pending-child"],
)
def test_startup_capture_rejects_original_evidence_gaps(native_records, fault):
    import run_acceptance

    ctx, results, directory, reports, observed, world = native_records
    if fault == "negative":
        reports["evaluator"]["checkpoint_result"] = "fail"
    elif fault == "missing-criterion":
        reports["evaluator"]["criteria"].pop(0)
    elif fault == "byte-drift":
        (world / "repo/manifest.json").write_text("changed")
    elif fault == "pending-child":
        observed["descendants"][1]["turns"][0]["status"] = "inProgress"
    else:
        observed["descendants"][1]["items"][0]["text"] = (
            "a summary cannot bind original bytes"
        )
    if fault in {"negative", "missing-criterion"}:
        (directory / "evaluator-result.json").write_text(
            json.dumps(reports["evaluator"])
        )
        observed["descendants"][1]["items"][0]["text"] = json.dumps(
            reports["evaluator"]
        )
    with pytest.raises((release.lib.RecipeError, run_acceptance.GateError)):
        release.capture(ctx, results, "release-startup", startup=True)
    assert not list(directory.glob("capture-*.json"))


def restored_consumers(ctx, results, monkeypatch):
    baseline = {
        "candidate_sha": "a" * 40,
        "inventory": [],
        "state": {"effective": "original"},
        "tools": {"binary_sha256": {}, "skill_tree_sha256": {}},
    }
    release.lib.write_document(results / "prepared.json", baseline)
    release.lib.write_document(results / "candidate.json", {"candidate_sha": "a" * 40})
    release.lib.write_document(
        results / "inventories.json",
        {
            "schema": "aquarium.vm-suite-inventories/v1",
            "inventories": {},
        },
    )
    ctx.marketplace = "synthetic-marketplace"
    calls = []
    monkeypatch.setattr(
        release, "observation", lambda *args, **kwargs: calls.append(args) or baseline
    )
    return calls


@pytest.mark.parametrize("later", ["uncaptured", "pending-child", "reader-failure"])
def test_cleanup_requires_latest_settlement_after_successful_capture(
    native_records, monkeypatch, later
):
    import native_observation
    import run_acceptance

    ctx, results, directory, _reports, observed, world = native_records
    release.capture(ctx, results, "release-startup", startup=True)
    old = (directory / "capture-000.json").read_bytes()
    calls = restored_consumers(ctx, results, monkeypatch)
    native_window(directory, 1)
    if later == "pending-child":
        observed["descendants"][0]["turns"][0]["status"] = "inProgress"
        with pytest.raises(run_acceptance.GateError):
            release.capture(ctx, results, "release-startup", startup=True)
    elif later == "reader-failure":
        with monkeypatch.context() as failure:
            failure.setattr(
                native_observation,
                "collect",
                lambda *args: (_ for _ in ()).throw(
                    RuntimeError("synthetic reader failure")
                ),
            )
            with pytest.raises(RuntimeError):
                release.reconcile(ctx, directory, world)
    with pytest.raises(release.lib.RecipeError, match="missing or stale"):
        release.run(ctx, "consumer-cleanup")
    assert not calls
    assert not (results / "consumer-result.json").exists()
    assert (directory / "capture-000.json").read_bytes() == old
    observed["descendants"][0]["turns"][0]["status"] = "completed"
    release.reconcile(ctx, directory, world)
    assert release.run(ctx, "consumer-cleanup") == 0
    assert calls


@pytest.mark.parametrize("changed", ["receipt", "request", "input", "log", "native"])
def test_cleanup_rejects_changed_settlement_inputs(
    native_records, monkeypatch, changed
):
    ctx, results, directory, _reports, _observed, _world = native_records
    release.capture(ctx, results, "release-startup", startup=True)
    calls = restored_consumers(ctx, results, monkeypatch)
    path = (
        directory
        / {
            "receipt": "operations/000.invocation.json",
            "request": "operations/000.request.json",
            "input": "operations/000.input",
            "log": "operations/000.jsonl",
            "native": "native-000.json",
        }[changed]
    )
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(release.lib.RecipeError):
        release.run(ctx, "consumer-cleanup")
    assert not calls


@pytest.mark.parametrize(
    "failure",
    ["failed-parent", "interrupted-child", "missing-reports", "negative-assessment"],
)
def test_terminal_failure_restoration_is_independent_of_case_result(
    native_records, monkeypatch, failure
):
    import run_acceptance

    ctx, results, directory, reports, observed, _world = native_records
    calls = restored_consumers(ctx, results, monkeypatch)
    if failure == "failed-parent":
        observed["root"]["turns"][0]["status"] = "failed"
    elif failure == "interrupted-child":
        observed["descendants"][0]["turns"][0]["status"] = "interrupted"
    elif failure == "missing-reports":
        (directory / "startup-evidence.json").unlink()
    else:
        reports["evaluator"]["checkpoint_result"] = "fail"
        (directory / "evaluator-result.json").write_text(
            json.dumps(reports["evaluator"])
        )
        observed["descendants"][1]["items"][0]["text"] = json.dumps(
            reports["evaluator"]
        )
    before = {p: p.read_bytes() for p in directory.rglob("*") if p.is_file()}
    with pytest.raises(
        (release.lib.RecipeError, run_acceptance.GateError, FileNotFoundError)
    ):
        release.capture(ctx, results, "release-startup", startup=True)
    assert not list(directory.glob("capture-*.json"))
    settlement = json.loads((directory / "settlement-000.json").read_text())
    assert settlement["workload_result"] == (
        "failed" if failure in {"failed-parent", "interrupted-child"} else "unassessed"
    )
    assert release.run(ctx, "consumer-cleanup") == 0
    assert calls
    assert (
        json.loads((results / "consumer-cleanup.json").read_text())["consumer_cleanup"]
        == "verified"
    )
    assert all(path.read_bytes() == content for path, content in before.items())
    assert not list(directory.glob("capture-*.json"))


@pytest.mark.parametrize(
    "fault",
    [
        "active-parent",
        "active-child",
        "uncollected-child",
        "pending-write",
        "pending-command",
        "metadata-active",
        "missing-receipt",
        "unknown-exit",
    ],
)
def test_reconcile_never_settles_uncertain_actors_or_process(
    native_records, monkeypatch, fault
):
    import run_acceptance

    ctx, results, directory, _reports, observed, world = native_records
    calls = restored_consumers(ctx, results, monkeypatch)
    if fault == "active-parent":
        observed["root"]["turns"][0]["status"] = "inProgress"
    elif fault == "active-child":
        observed["descendants"][0]["turns"][0]["status"] = "inProgress"
    elif fault == "uncollected-child":
        observed["descendants"].pop()
    elif fault in {"pending-write", "pending-command"}:
        observed["root"]["items"].append(
            {
                "type": "fileChange"
                if fault == "pending-write"
                else "commandExecution",
                "status": "inProgress",
            }
        )
    elif fault == "metadata-active":
        observed["root"]["metadata"]["status"] = {"type": "active"}
    elif fault == "missing-receipt":
        (directory / "operations/000.invocation.json").unlink()
    else:
        path = directory / "operations/000.invocation.json"
        document = json.loads(path.read_text())
        document["exit"] = None
        path.write_text(json.dumps(document))
    with pytest.raises((release.lib.RecipeError, run_acceptance.GateError)):
        release.reconcile(ctx, directory, world)
    with pytest.raises(release.lib.RecipeError):
        release.run(ctx, "consumer-cleanup")
    assert not calls
    assert not (results / "consumer-result.json").exists()


def test_interrupted_exited_window_reconciles_original_log_without_dispatch(
    native_records, monkeypatch
):
    ctx, results, directory, _reports, observed, world = native_records
    calls = restored_consumers(ctx, results, monkeypatch)
    receipt = directory / "operations/000.invocation.json"
    original = json.loads(receipt.read_text())
    original.update(exit=-2, thread_id=None)
    receipt.write_text(json.dumps(original))
    observed["root"]["turns"][0]["status"] = "interrupted"
    before = {p: p.read_bytes() for p in (directory / "operations").iterdir()}
    monkeypatch.setattr(
        release, "invoke", lambda *args: pytest.fail("reconciliation must not dispatch")
    )
    result, _ = release.reconcile(ctx, directory, world)
    assert result["thread_id"] == "synthetic-root"
    assert result["workload_result"] == "failed"
    assert release.run(ctx, "consumer-cleanup") == 0
    assert calls
    assert all(p.read_bytes() == content for p, content in before.items())


def test_reconcile_retains_original_handle_when_later_receipt_omits_it(native_records):
    ctx, _results, directory, _reports, _observed, world = native_records
    native_window(directory, 1, exit=-2, handle=None)
    result, _ = release.reconcile(ctx, directory, world)
    assert result["thread_id"] == "synthetic-root"
    assert result["workload_result"] == "failed"


def test_interrupted_invoker_retains_actual_waited_process_exit(context, monkeypatch):
    ctx, results = context
    world = ctx.root / "world"
    fixture.seed(world, order="before", baseline="previous", mode="full")
    fake = ctx.root / "synthetic-interrupted-invoker"
    fake.write_text(
        f"#!{sys.executable}\nimport json,sys\nprint(json.dumps({{'type':'thread.started','thread_id':'synthetic-root'}}))\nsys.exit(7)\n"
    )
    fake.chmod(0o700)
    ctx.codex = str(fake)
    communicate = subprocess.Popen.communicate

    def interrupted(process, *args, **kwargs):
        result = communicate(process, *args, **kwargs)
        if process.args[0] == str(fake):
            raise KeyboardInterrupt("synthetic interruption after actual process wait")
        return result

    monkeypatch.setattr(subprocess.Popen, "communicate", interrupted)
    directory = results / "originals/synthetic/variant"
    directory.mkdir(parents=True)
    with pytest.raises(KeyboardInterrupt):
        release.invoke(ctx, world, directory, "synthetic input", None)
    receipt = json.loads((directory / "operations/000.invocation.json").read_text())
    assert receipt["exit"] == 7
    assert receipt["thread_id"] == "synthetic-root"
    assert len(list((directory / "operations").glob("*.request.json"))) == 1


def test_reconcile_refuses_window_changed_during_public_collection(
    native_records, monkeypatch
):
    import native_observation

    ctx, results, directory, _reports, observed, world = native_records
    calls = restored_consumers(ctx, results, monkeypatch)

    def changed(*args):
        native_window(directory, 1)
        return observed

    monkeypatch.setattr(native_observation, "collect", changed)
    with pytest.raises(release.lib.RecipeError, match="changed during observation"):
        release.reconcile(ctx, directory, world)
    with pytest.raises(release.lib.RecipeError):
        release.run(ctx, "consumer-cleanup")
    assert not calls
    assert (directory / "native-000.json").is_file()
    assert not (directory / "settlement-000.json").exists()


def test_genuine_launch_failure_permits_restoration_without_success(
    context, monkeypatch
):
    import native_observation

    ctx, results = context
    world = ctx.root / "world"
    fixture.seed(world, order="before", baseline="previous", mode="full")
    fake = ctx.root / "synthetic-no-thread"
    ctx.codex = str(fake)
    directory = results / "originals/synthetic/variant"
    directory.mkdir(parents=True)
    with pytest.raises(release.lib.RecipeError):
        release.invoke(ctx, world, directory, "synthetic failed start", None)
    receipt = json.loads((directory / "operations/000.invocation.json").read_text())
    assert receipt["launch_error"]
    assert receipt["exit"] is None
    assert receipt["thread_id"] is None
    calls = restored_consumers(ctx, results, monkeypatch)
    monkeypatch.setattr(
        native_observation,
        "collect",
        lambda *args: pytest.fail("no native thread was launched"),
    )
    result, observed = release.reconcile(ctx, directory, world)
    assert observed is None
    assert result["workload_result"] == "failed"
    assert release.run(ctx, "consumer-cleanup") == 0
    assert calls
    with pytest.raises(release.lib.RecipeError):
        release.invoke(ctx, world, directory, "duplicate", None)
    assert len(list((directory / "operations").glob("*.request.json"))) == 1


@pytest.mark.parametrize("exit_code", [7, -signal.SIGTERM])
def test_launched_no_handle_exit_cannot_prove_native_settlement(
    context, monkeypatch, exit_code
):
    import native_observation

    ctx, results = context
    world = ctx.root / "world"
    fixture.seed(world, order="before", baseline="previous", mode="full")
    fake = ctx.root / "synthetic-launched-no-handle"
    fake.write_text(
        f"#!{sys.executable}\nimport os,signal,sys\nfrom pathlib import Path\n"
        "Path(os.environ['AQUARIUM_RELEASE_FIXTURE_ROOT'],'launched').write_text('synthetic process ran')\n"
        + (
            "sys.exit(7)\n"
            if exit_code == 7
            else "os.kill(os.getpid(),signal.SIGTERM)\n"
        )
    )
    fake.chmod(0o700)
    ctx.codex = str(fake)
    directory = results / "originals/synthetic/variant"
    directory.mkdir(parents=True)
    with pytest.raises(release.lib.RecipeError):
        release.invoke(ctx, world, directory, "synthetic uncertain start", None)
    assert (world / "launched").read_text() == "synthetic process ran"
    receipt = json.loads((directory / "operations/000.invocation.json").read_text())
    assert receipt["exit"] == exit_code
    assert receipt["thread_id"] is None
    assert "launch_error" not in receipt
    originals = {p: p.read_bytes() for p in (directory / "operations").iterdir()}
    calls = restored_consumers(ctx, results, monkeypatch)
    monkeypatch.setattr(
        native_observation,
        "collect",
        lambda *args: pytest.fail("no original handle is available for collection"),
    )
    with pytest.raises(release.lib.RecipeError) as error:
        release.reconcile(ctx, directory, world)
    assert error.value.outcome == "incomplete"
    assert not list(directory.glob("settlement-*.json"))
    with pytest.raises(release.lib.RecipeError):
        release.run(ctx, "consumer-cleanup")
    assert not calls
    assert not (results / "consumer-result.json").exists()

    # A cached settlement without native proof must not bypass the cleanup guard.
    binding = json.loads((directory / "native-000.request.json").read_text())
    fixture.write_once(
        directory / "settlement-000.json",
        {
            "candidate_sha": ctx.inputs["candidate"]["git_sha"],
            "invocation": binding,
            "request": "native-000.request.json",
            "settled": True,
            "workload_result": "failed",
        },
    )
    with pytest.raises(release.lib.RecipeError):
        release.run(ctx, "consumer-cleanup")
    assert not calls
    assert not (results / "consumer-result.json").exists()
    assert all(p.read_bytes() == content for p, content in originals.items())
    with pytest.raises(release.lib.RecipeError):
        release.invoke(ctx, world, directory, "duplicate", None)
    assert len(list((directory / "operations").glob("*.request.json"))) == 1


def test_latest_failed_cleanup_cannot_use_an_earlier_passing_receipt(context):
    ctx, results, _index = populated(context)
    release.lib.write_document(
        results / "consumer-cleanup.json",
        {"consumer_cleanup": "failed", "candidate_sha": "a" * 40},
    )
    assert release.stage(ctx, results) == 2


def test_failed_native_window_with_known_handle_resumes_same_handle(context):
    ctx, results = context
    world = ctx.root / "world"
    fixture.seed(world, order="before", baseline="previous", mode="full")
    fake = ctx.root / "synthetic-codex"
    fake.write_text(
        f"#!{sys.executable}\nimport json,sys\nprint(json.dumps({{'type':'thread.started','thread_id':'original-handle'}}))\nsys.exit(0 if 'resume' in sys.argv else 1)\n"
    )
    fake.chmod(0o700)
    ctx.codex = str(fake)
    directory = results / "case"
    directory.mkdir(parents=True)
    with pytest.raises(release.lib.RecipeError, match="incomplete"):
        release.invoke(ctx, world, directory, "synthetic start", None)
    receipt = release.invoke(ctx, world, directory, "", "synthetic recovery")
    assert receipt["argv"][-3:] == ["resume", "original-handle", "-"]
    assert len(list((directory / "operations").glob("*.request.json"))) == 2


@pytest.mark.parametrize(
    "stage,phase", [("prior", "before"), ("candidate", "candidate")]
)
def test_observation_uses_existing_inventory_phases(context, monkeypatch, stage, phase):
    import guest_main
    import podway_upgrade

    ctx, _ = context
    calls = []
    ctx.snapshot = lambda *args, **kwargs: calls.append((args, kwargs)) or {}
    monkeypatch.setattr(
        guest_main,
        "skill_identity_document",
        lambda *args, **kwargs: {"comparisons": {"all_passed": True}},
    )
    monkeypatch.setattr(podway_upgrade, "observe_tools", lambda *args: {})
    monkeypatch.setattr(podway_upgrade, "restoration_state", lambda *args: {})
    release.observation(ctx, stage, release.SUITE)
    assert calls == [
        (
            (release.SUITE, phase),
            {"profile": "stable" if stage == "prior" else "podway-candidate"},
        )
    ]


def test_cleanup_preserves_failed_observation_and_requires_actual_restoration(
    context, monkeypatch
):
    ctx, results, _ = populated(context)
    baseline = {
        "candidate_sha": "a" * 40,
        "inventory": [],
        "state": {"effective": "original"},
        "tools": {"binary_sha256": {}, "skill_tree_sha256": {}},
    }
    release.lib.write_document(results / "prepared.json", baseline)
    ctx.marketplace = "fixture-marketplace"
    current = {**baseline, "state": {"effective": "drifted"}}
    monkeypatch.setattr(release, "observation", lambda *args, **kwargs: current)
    assert release.run(ctx, "consumer-cleanup") == 1
    history = json.loads((results / "inventories.json").read_text())
    assert history["failed_cleanup_observations"][0]["state"] == {
        "effective": "drifted"
    }
    current["state"] = baseline["state"]
    assert release.run(ctx, "consumer-cleanup") == 0
    assert (
        json.loads((results / "consumer-cleanup.json").read_text())["consumer_cleanup"]
        == "verified"
    )
    assert (
        json.loads((results / "inventories.json").read_text())[
            "failed_cleanup_observations"
        ]
        == history["failed_cleanup_observations"]
    )
