"""Non-installing retirement recipe decisions against disposable guest state."""

import copy
import hashlib
import importlib
import json
import os
import stat
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]


def preservation_facts(root):
    def file(path, content):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return {
            "path": str(path),
            "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content),
        }

    def metadata(path):
        info = path.lstat()
        return {
            "retained_path": str(path),
            "type": "directory" if path.is_dir() else "regular_file",
            "device": info.st_dev,
            "inode": info.st_ino,
            "mode": info.st_mode,
            "uid": info.st_uid,
            "gid": info.st_gid,
            "mtime_ns": info.st_mtime_ns,
        }

    qa = file(root / "qa/known.json", b"known QA")
    empty = root / "qa/empty"
    empty.mkdir()
    custody = file(root / "custody/bin/tool", b"known binary")
    legacy_launcher = root / "legacy/launcher"
    legacy_launcher.parent.mkdir()
    legacy_launcher.write_bytes(b"legacy content must remain unread")
    legacy_root = root / "legacy/runtime"
    legacy_root.mkdir()
    (legacy_root / "credential-sentinel").write_bytes(b"must not read")
    podway = [
        file(root / "podway/plist", b"safe plist"),
        file(root / "podway/service.json", b"safe state"),
    ]
    return {
        "original_handoff": {"sha256": "f" * 64},
        "qa": {
            "root": str(root / "qa"),
            "files": [qa],
            "directory_paths": [str(empty)],
            "not_captured": ["Whole-tree hash"],
        },
        "custody": {
            "root": str(root / "custody"),
            "files": [custody],
            "owner_sidecar": file(root / "custody.owner.json", b"custody owner"),
            "original_native_job": {
                "job_id": "original-custody-job",
                "lease_generation": 3,
            },
        },
        "legacy_preimage": {
            "root": str(root / "legacy"),
            "objects": [
                {**metadata(path), "content_read": False}
                for path in (legacy_launcher, legacy_root)
            ],
            "owner_sidecar": file(root / "legacy/owner.json", b"legacy owner"),
            "not_captured": ["Legacy contents were not read"],
        },
        "podway_preimage": {
            "root": str(root / "podway"),
            "files": [
                {
                    **metadata(Path(row["path"])),
                    "sha256": row["sha256"],
                    "bytes": row["bytes"],
                }
                for row in podway
            ],
            "owner_sidecar": file(root / "podway/owner.json", b"podway owner"),
        },
    }


@pytest.fixture
def smoke(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "tests/vm/recipes"))
    main = importlib.import_module("guest_main")
    combination = importlib.import_module("haepari_combination")
    protected = tmp_path / "retained-preimage"
    protected.write_bytes(b"original custody")
    originals = preservation_facts(tmp_path / "preservation")
    results = tmp_path / "results/retirement-smoke"
    results.mkdir(parents=True)
    profile = {
        "profile_id": "retained-c783",
        "components": [
            {
                "name": "aquarium-plugin",
                "version": "0.1.22-dev.c783a6dfbd0b",
                "sealed_artifact": {"tree_sha256": "c" * 64},
            },
            {"name": "podway", "version": "v0.2.17"},
        ],
    }
    tools = {"podway": {"path": str(tmp_path / "podway"), "binary_sha256": "a" * 64}}
    context = SimpleNamespace(
        root=tmp_path,
        home=tmp_path / "home",
        codex="fixture-codex",
        marketplace="fixture-market",
        job={"job_id": "original-job", "lease_generation": "1"},
        identity={"guest_uuid": "fixture-uuid"},
        inputs={
            "candidate": {"git_sha": "40f2-transport-only"},
            "host_harness_sha256": {"candidate_artifact.py": "current-source"},
            "retirement_smoke": {
                "profile_sha256": "b" * 64,
                "protected_paths": [str(protected)],
                "preservation": originals,
            },
        },
        profile=lambda _name: copy.deepcopy(profile),
        profile_digest=lambda _name: "b" * 64,
        marketplace_path=lambda _kind: tmp_path,
        snapshot=lambda *_args, **_kwargs: [],
    )
    monkeypatch.setattr(main.lib, "results_directory", lambda _suite: results)
    monkeypatch.setattr(
        main.lib, "verify_sealed_inputs", lambda _root: {"verified": True}
    )
    monkeypatch.setattr(
        main.lib,
        "installed_aquarium",
        lambda *_args: {
            "version": profile["components"][0]["version"],
            "enabled": True,
        },
    )
    monkeypatch.setattr(
        main.lib,
        "marketplace_registrations",
        lambda *_args: {"fixture-market": str(tmp_path)},
    )
    monkeypatch.setattr(main.lib, "tree_sha256_from_directory", lambda _path: "c" * 64)
    monkeypatch.setattr(main.lib, "context_value", lambda _key: tools["podway"]["path"])
    monkeypatch.setattr(
        combination, "observe_tools", lambda *_args: copy.deepcopy(tools)
    )
    calls = []
    output = {
        "schema": "podway.output/v4",
        "request_id": "00000000-0000-4000-8000-000000000001",
        "command": "version",
        "generated_at": "2026-11-13T00:00:00.000Z",
        "result": {
            "schema": "podway.version-result/v2",
            "product": "podway",
            "version": "v0.2.17",
            "target": "aarch64-apple-darwin",
            "build_identity": "sha256:" + "a" * 64,
            "source_commit": None,
            "contract_manifest_schema": "podway.contract-manifest/v2",
            "contract_manifest_digest": "sha256:" + "b" * 64,
        },
        "warnings": [],
    }

    def run(argv, **_kwargs):
        calls.append(argv)
        assert argv == [tools["podway"]["path"], "version", "--identity", "--json"]
        return subprocess.CompletedProcess(argv, 0, json.dumps(output), "")

    monkeypatch.setattr(main.lib, "run", run)

    # Any accidental recipe normalization or installation must fail this test.
    def forbidden(*_args, **_kwargs):
        pytest.fail("retirement recipe attempted an installation or normalization")

    for name in ("ensure_installed", "normalize_registration", "install_plugin"):
        if hasattr(main.lib, name):
            monkeypatch.setattr(main.lib, name, forbidden)
    monkeypatch.setattr(main, "run_baseline", forbidden)
    settled = {}

    def finish(suite, outcome, details, *, consumer_cleanup):
        settled.update(
            suite=suite,
            outcome=outcome,
            details=details,
            consumer_cleanup=consumer_cleanup,
        )
        return 0 if outcome == "pass" else 1

    monkeypatch.setattr(main.lib, "finish", finish)
    return SimpleNamespace(
        main=main,
        combination=combination,
        context=context,
        protected=protected,
        results=results,
        calls=calls,
        settled=settled,
        output=output,
        originals=originals,
    )


def test_retirement_observes_distinct_identities_and_preserves_custody(smoke):
    assert smoke.main.run_retirement_smoke(smoke.context) == 0
    assert smoke.settled["consumer_cleanup"] == "verified"
    identity = json.loads((smoke.results / "identity.json").read_text())
    assert identity["transported_payload"]["git_sha"] == "40f2-transport-only"
    assert identity["observed_guest_profile"] == "retained-c783"
    assert (
        identity["executing_host_harness"]["candidate_artifact.py"] == "current-source"
    )
    assert identity["job"]["job_id"] == "original-job"
    assert smoke.protected.read_bytes() == b"original custody"
    assert len(smoke.calls) == 1


@pytest.mark.parametrize("fault", ["summary", "schema", "command", "result_schema"])
def test_retirement_requires_podway_identity_envelope(smoke, fault):
    if fault == "summary":
        smoke.output.clear()
        smoke.output.update(name="podway", version="v0.2.17")
    elif fault == "result_schema":
        smoke.output["result"]["schema"] = "podway.version-result/v1"
    else:
        smoke.output[fault] = "wrong"
    with pytest.raises(smoke.main.lib.RecipeError):
        smoke.main.run_retirement_smoke(smoke.context)
    assert smoke.settled == {}
    assert not (smoke.results / "identity.json").exists()
    assert not (smoke.results / "consumer-cleanup.json").exists()
    assert smoke.protected.read_bytes() == b"original custody"


@pytest.mark.parametrize(
    "fault", ["profile", "plugin", "podway", "source", "source_bytes"]
)
def test_retirement_refuses_identity_mismatch_without_repair(smoke, monkeypatch, fault):
    if fault == "profile":
        smoke.context.profile_digest = lambda _name: "wrong"
    elif fault == "plugin":
        monkeypatch.setattr(
            smoke.main.lib,
            "installed_aquarium",
            lambda *_args: {"version": "wrong", "enabled": True},
        )
    elif fault == "podway":
        smoke.output["result"]["version"] = "v0.2.16"
    elif fault == "source":
        monkeypatch.setattr(
            smoke.main.lib, "marketplace_registrations", lambda *_args: {}
        )
    else:
        monkeypatch.setattr(
            smoke.main.lib, "tree_sha256_from_directory", lambda _path: "wrong"
        )
    with pytest.raises(smoke.main.lib.RecipeError):
        smoke.main.run_retirement_smoke(smoke.context)
    assert smoke.settled == {}
    assert smoke.protected.read_bytes() == b"original custody"


def test_retirement_protected_change_is_failed_cleanup(smoke, monkeypatch):
    def observe(*_args):
        if smoke.calls:
            Path(smoke.originals["qa"]["files"][0]["path"]).write_bytes(
                b"unexpected change"
            )
        return {"podway": {"path": str(smoke.protected.parent / "podway")}}

    monkeypatch.setattr(smoke.combination, "observe_tools", observe)
    assert smoke.main.run_retirement_smoke(smoke.context) == 1
    assert smoke.settled["consumer_cleanup"] == "failed"
    cleanup = json.loads((smoke.results / "consumer-cleanup.json").read_text())
    assert cleanup["protected_before"] != cleanup["protected_after"]
    assert cleanup["original_after_mismatches"]


def test_retirement_new_directory_metadata_drift_blocks_preservation(
    smoke, monkeypatch
):
    def observe(*_args):
        if smoke.calls:
            path = Path(smoke.originals["qa"]["directory_paths"][0])
            path.chmod(stat.S_IMODE(path.stat().st_mode) ^ stat.S_IXUSR)
        return {"podway": {"path": str(smoke.protected.parent / "podway")}}

    monkeypatch.setattr(smoke.combination, "observe_tools", observe)
    assert smoke.main.run_retirement_smoke(smoke.context) == 1
    cleanup = json.loads((smoke.results / "consumer-cleanup.json").read_text())
    assert (
        cleanup["original_before_mismatches"]
        == cleanup["original_after_mismatches"]
        == []
    )
    assert cleanup["protected_before"] != cleanup["protected_after"]


def test_retirement_malformed_identity_never_claims_cleanup(smoke, monkeypatch):
    monkeypatch.setattr(
        smoke.main.lib,
        "run",
        lambda *_args, **_kwargs: subprocess.CompletedProcess([], 0, "invalid", ""),
    )
    with pytest.raises(smoke.main.lib.RecipeError, match="not JSON"):
        smoke.main.run_retirement_smoke(smoke.context)
    assert smoke.settled == {}


def test_retirement_finite_observer_never_lists_or_reads_legacy_contents(
    smoke, monkeypatch
):
    original_open = os.open
    legacy = {
        Path(row["retained_path"]).name
        for row in smoke.originals["legacy_preimage"]["objects"]
    }
    opened_files = []

    def guarded_open(path, flags, *args, **kwargs):
        if not flags & os.O_DIRECTORY:
            assert Path(path).name not in legacy
            opened_files.append(Path(path).name)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", guarded_open)
    monkeypatch.setattr(
        os,
        "scandir",
        lambda *_args: pytest.fail("finite observer must not enumerate a directory"),
    )
    observed, violations = smoke.main.retirement_preservation(smoke.originals)
    assert violations == []
    assert observed
    assert "credential-sentinel" not in opened_files
    assert len(opened_files) == 7  # QA, binary, two Podway files and three sidecars.


def test_retirement_labels_current_type_policy_separately_from_recorded_type(smoke):
    observations, violations = smoke.main.retirement_preservation(smoke.originals)
    assert violations == []
    by_path = {row["path"]: row for row in observations}
    qa = smoke.originals["qa"]["files"][0]
    assert by_path[qa["path"]]["comparison_fields"] == {
        "original": ["bytes", "sha256"],
        "current_policy": ["type"],
    }
    legacy = smoke.originals["legacy_preimage"]["objects"][0]
    assert "type" in by_path[legacy["retained_path"]]["comparison_fields"]["original"]
    assert by_path[legacy["retained_path"]]["comparison_fields"]["current_policy"] == []
    path = Path(smoke.originals["qa"]["directory_paths"][0])
    path.rmdir()
    _observations, violations = smoke.main.retirement_preservation(smoke.originals)
    missing = next(row for row in violations if row["path"] == str(path))
    assert missing["original_mismatch_fields"] == []
    assert missing["current_policy_mismatch_fields"] == ["type"]


@pytest.mark.parametrize("fault", ["missing", "type", "metadata", "hash", "owner"])
def test_retirement_matches_originals_even_when_both_samples_agree(smoke, fault):
    originals = smoke.originals
    if fault in {"missing", "type"}:
        path = Path(originals["qa"]["directory_paths"][0])
        path.rmdir()
        if fault == "type":
            path.write_bytes(b"not a directory")
    elif fault == "metadata":
        path = Path(originals["legacy_preimage"]["objects"][0]["retained_path"])
        path.chmod(stat.S_IMODE(path.stat().st_mode) ^ stat.S_IXUSR)
    else:
        section = (
            originals["qa"]["files"][0]
            if fault == "hash"
            else originals["custody"]["owner_sidecar"]
        )
        Path(section["path"]).write_bytes(b"changed")
    before, violations = smoke.main.retirement_preservation(originals)
    after, after_violations = smoke.main.retirement_preservation(originals)
    assert before == after
    assert violations and after_violations
    assert smoke.main.run_retirement_smoke(smoke.context) == 1
    assert smoke.settled["consumer_cleanup"] == "failed"


@pytest.mark.parametrize(
    "fault", ["missing_original", "legacy_hash", "safe_file_symlink"]
)
def test_retirement_refuses_missing_or_out_of_scope_originals(smoke, fault):
    if fault == "missing_original":
        del smoke.originals["podway_preimage"]
    elif fault == "legacy_hash":
        smoke.originals["legacy_preimage"]["objects"][0]["sha256"] = "0" * 64
    else:
        row = smoke.originals["qa"]["files"][0]
        path = Path(row["path"])
        path.unlink()
        path.symlink_to(
            smoke.originals["legacy_preimage"]["objects"][0]["retained_path"]
        )
        _observed, violations = smoke.main.retirement_preservation(smoke.originals)
        assert violations
        return
    with pytest.raises(
        smoke.main.lib.RecipeError, match="original finite preservation"
    ):
        smoke.main.retirement_preservation(smoke.originals)
