import http.client
import importlib.util
import io
import json
import sys
import unicodedata
import urllib.error
import urllib.response
import uuid
from email.message import Message
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
STATUS_TOOLS = ROOT / "plugins/aquarium/tools/aquarium-status"


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, STATUS_TOOLS / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def status_modules(monkeypatch):
    """Load status modules without adding their generic names to sys.path."""
    contract = _load_module("aquarium_status_contract_unit", "status_contract.py")
    monkeypatch.setitem(sys.modules, "status_contract", contract)
    store = _load_module("aquarium_status_store_unit", "status_store.py")
    report = _load_module("aquarium_status_report_unit", "status_report.py")
    monkeypatch.setitem(sys.modules, "status_store", store)
    monkeypatch.setitem(sys.modules, "status_report", report)
    cli = _load_module("aquarium_status_cli_unit", "aquarium_status.py")
    return SimpleNamespace(contract=contract, store=store, report=report, cli=cli)


def _version(value="v1.2.3", source="recorded_attempt", status="observed"):
    return {"value": value, "source": source, "status": status}


def _record(root: Path, *, attempt_id=None, revision=0, scope=None, components=None):
    return {
        "schema": "aquarium-production-status-record/v1",
        "attempt_id": attempt_id or str(uuid.uuid4()),
        "expected_row_revision": revision,
        "git_root": str(root),
        "project": "Aquarium",
        "started_at": "2026-09-18T00:00:00Z",
        "completed_at": "2026-09-18T00:01:00Z",
        "outcome": "ready",
        "scope": scope or {"kind": "full"},
        "components": components or {},
    }


def _write_record(cli, monkeypatch, value):
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(value)))
    return cli.record()


def test_canonical_json_normalizes_nested_strings_and_has_stable_bytes(status_modules):
    contract = status_modules.contract
    decomposed = "Cafe\N{COMBINING ACUTE ACCENT}"
    normalized = unicodedata.normalize("NFC", decomposed)
    value = {"z": [decomposed], decomposed: {"b": 2, "a": 1}}

    encoded = contract.canonical_json(value)

    assert (
        encoded
        == (f'{{"{normalized}":{{"a":1,"b":2}},"z":["{normalized}"]}}\n').encode()
    )
    assert contract.digest(value) == contract.digest(contract.normalize_strings(value))


def test_record_validation_normalizes_project_and_closes_nested_shapes(
    status_modules, tmp_path
):
    contract = status_modules.contract
    value = _record(
        tmp_path,
        scope={"kind": "scoped", "components": ["aquarium-dev", "sanho"]},
        components={"sanho": {"outcome": "ready", "version": _version()}},
    )
    value["project"] = "Cafe\N{COMBINING ACUTE ACCENT}"

    validated = contract.validate_record(value, str(tmp_path))

    assert validated["project"] == "Caf\N{LATIN SMALL LETTER E WITH ACUTE}"
    assert validated["scope"] == {
        "kind": "scoped",
        "components": ["aquarium-dev", "sanho"],
    }


@pytest.mark.parametrize(
    "timestamp",
    [
        "20260918T000000Z",
        "2026-W38-5T00:00:00Z",
        "2026-09-18 00:00:00Z",
        "2026-09-18T00:00Z",
        "2026-09-18T00:00:00+00:00",
    ],
)
def test_record_validation_rejects_non_rfc3339_utc_timestamps(
    status_modules, tmp_path, timestamp
):
    value = _record(tmp_path)
    value["started_at"] = timestamp

    with pytest.raises(status_modules.contract.ContractError, match="RFC 3339"):
        status_modules.contract.validate_record(value, str(tmp_path))


def test_record_validation_preserves_arbitrary_fractional_second_order(
    status_modules, tmp_path
):
    value = _record(tmp_path)
    value["started_at"] = "2026-09-18T00:00:00.1234569Z"
    value["completed_at"] = "2026-09-18T00:00:00.1234561Z"

    with pytest.raises(status_modules.contract.ContractError, match="completion time"):
        status_modules.contract.validate_record(value, str(tmp_path))


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.update(extra=True),
        lambda value: value.update(expected_row_revision=True),
        lambda value: value.update(
            scope={"kind": "scoped", "components": ["sanho", "sanho"]}
        ),
        lambda value: value.update(
            scope={"kind": "scoped", "components": ["sanho"]},
            components={"aquarium_dev": {"outcome": "ready", "version": _version()}},
        ),
        lambda value: value.update(
            components={
                "sanho": {
                    "outcome": "ready",
                    "version": _version(),
                    "extra": True,
                }
            }
        ),
        lambda value: value.update(
            components={
                "sanho": {
                    "outcome": "ready",
                    "version": _version(value="1.2.3"),
                }
            }
        ),
    ],
)
def test_record_validation_rejects_nonclosed_or_inconsistent_input(
    status_modules, tmp_path, mutate
):
    value = _record(tmp_path)
    mutate(value)

    with pytest.raises(status_modules.contract.ContractError) as raised:
        status_modules.contract.validate_record(value, str(tmp_path))

    assert raised.value.code == "invalid_input"


def test_absent_ledger_is_read_only_and_returns_the_empty_state(
    status_modules, tmp_path, monkeypatch
):
    store = status_modules.store
    state = tmp_path / ".aquarium"
    monkeypatch.setattr(store, "state_root", lambda: state)

    with store.locked(False):
        ledger, previous = store.read_ledger()

    assert ledger == store.empty_ledger()
    assert previous is None
    assert not state.exists()


def test_canonical_yaml_round_trips_and_noncanonical_yaml_fails_closed(
    status_modules, tmp_path, monkeypatch
):
    store = status_modules.store
    state = tmp_path / ".aquarium"
    state.mkdir(mode=0o700)
    monkeypatch.setattr(store, "state_root", lambda: state)
    path = state / "status.yaml"
    ledger = {
        "schema": "aquarium-production-status/v1",
        "file_revision": 1,
        "repositories": [],
    }
    canonical = store.yaml_bytes(ledger)
    path.write_bytes(canonical)
    path.chmod(0o600)

    assert store.read_ledger() == (ledger, canonical)

    path.write_bytes(canonical + b"# semantically inert but noncanonical\n")
    with pytest.raises(status_modules.contract.ContractError) as raised:
        store.read_ledger()
    assert raised.value.code == "state_corrupt"


@pytest.mark.parametrize(
    "content",
    [
        (
            b"schema: aquarium-production-status/v1\n"
            b"file_revision: 1\nfile_revision: 2\nrepositories: []\n"
        ),
        (
            b"schema: aquarium-production-status/v1\n"
            b"file_revision: 1\nrepositories: &rows []\nextra: *rows\n"
        ),
        b"not: [valid",
    ],
)
def test_corrupt_yaml_constructs_are_rejected(
    status_modules, tmp_path, monkeypatch, content
):
    store = status_modules.store
    state = tmp_path / ".aquarium"
    state.mkdir(mode=0o700)
    monkeypatch.setattr(store, "state_root", lambda: state)
    path = state / "status.yaml"
    path.write_bytes(content)
    path.chmod(0o600)

    with pytest.raises(status_modules.contract.ContractError) as raised:
        store.read_ledger()

    assert raised.value.code == "state_corrupt"
    assert raised.value.exit_code == 1


def test_unsafe_state_directory_and_ledger_mode_fail_closed(
    status_modules, tmp_path, monkeypatch
):
    store = status_modules.store
    state = tmp_path / ".aquarium"
    state.mkdir(mode=0o755)
    monkeypatch.setattr(store, "state_root", lambda: state)

    with (
        pytest.raises(status_modules.contract.ContractError) as raised,
        store.locked(False),
    ):
        pass
    assert raised.value.code == "state_unsafe"

    state.chmod(0o700)
    path = state / "status.yaml"
    path.write_bytes(
        store.yaml_bytes(
            {
                "schema": "aquarium-production-status/v1",
                "file_revision": 1,
                "repositories": [],
            }
        )
    )
    path.chmod(0o644)
    with pytest.raises(status_modules.contract.ContractError) as raised:
        store.read_ledger()
    assert raised.value.code == "state_corrupt"


def test_full_then_scoped_record_preserves_full_ready_and_omitted_component(
    status_modules, tmp_path, monkeypatch
):
    store = status_modules.store
    cli = status_modules.cli
    state = tmp_path / ".aquarium"
    repository = tmp_path / "repository"
    common = tmp_path / "common.git"
    monkeypatch.setattr(store, "state_root", lambda: state)
    monkeypatch.setattr(cli, "git_identity", lambda raw: (str(repository), str(common)))
    monkeypatch.setattr(cli, "VERSION_OVERRIDE", ("v1.2.3", "bundled_plugin_manifest"))
    first_id = str(uuid.uuid4())
    second_id = str(uuid.uuid4())
    first = _record(
        repository,
        attempt_id=first_id,
        components={
            "sanho": {"outcome": "ready", "version": _version("v1.0.0")},
            "aquarium_dev": {"outcome": "ready", "version": _version("v1.1.0")},
        },
    )
    second = _record(
        repository,
        attempt_id=second_id,
        revision=1,
        scope={"kind": "scoped", "components": ["aquarium-dev"]},
        components={
            "aquarium_dev": {
                "outcome": "failed",
                "version": _version(None, "unavailable", "unknown"),
            }
        },
    )
    second["outcome"] = "failed"

    assert _write_record(cli, monkeypatch, first)["row_revision"] == 1
    assert _write_record(cli, monkeypatch, second)["row_revision"] == 2
    with store.locked(False):
        ledger, _ = store.read_ledger()
    row = ledger["repositories"][0]

    assert ledger["file_revision"] == 2
    assert row["last_attempt"]["attempt_id"] == second_id
    assert row["last_attempt"]["scope"] == {
        "kind": "scoped",
        "components": ["aquarium-dev"],
    }
    assert row["last_full_ready"]["attempt_id"] == first_id
    assert row["components"]["sanho"]["attempt_id"] == first_id
    assert row["components"]["aquarium_dev"]["attempt_id"] == second_id
    assert row["components"]["aquarium_dev"]["outcome"] == "failed"


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        (_version("v1.2.3"), _version("v1.2.3"), "current"),
        (_version("v1.2.2"), _version("v1.2.3"), "behind"),
        (_version("v1.3.0"), _version("v1.2.3"), "ahead"),
        (_version(None, "unavailable", "unknown"), _version("v1.2.3"), "unknown"),
        (
            _version(None, "not_requested", "not_checked"),
            _version("v1.2.3"),
            "not_checked",
        ),
    ],
)
def test_freshness_is_derived_independently(status_modules, left, right, expected):
    assert status_modules.report.freshness(left, right) == expected


def test_release_observation_is_offline_by_default(status_modules, monkeypatch):
    report = status_modules.report
    monkeypatch.setattr(
        report,
        "_open_release_request",
        lambda *args, **kwargs: pytest.fail("offline reporting contacted the network"),
    )

    value, warning = report.release_version(False)

    assert value == {"value": None, "source": "not_requested", "status": "not_checked"}
    assert warning is None


def test_release_refresh_accepts_only_a_stable_official_tag(
    status_modules, monkeypatch
):
    report = status_modules.report
    observed = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, limit):
            observed["limit"] = limit
            return b'{"tag_name":"v2.3.4"}'

    def open_request(request, timeout):
        observed.update(url=request.full_url, timeout=timeout)
        return Response()

    monkeypatch.setattr(report, "_open_release_request", open_request)

    value, warning = report.release_version(True)

    assert value == {
        "value": "v2.3.4",
        "source": "official_github_release",
        "status": "observed",
    }
    assert warning is None
    assert observed == {
        "url": report.LATEST_RELEASE_URL,
        "timeout": 10,
        "limit": report.MAX_EXTERNAL_BYTES + 1,
    }


def test_failed_release_refresh_is_partial_data_not_an_exception(
    status_modules, monkeypatch
):
    report = status_modules.report

    def unavailable(*args, **kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(report, "_open_release_request", unavailable)

    value, warning = report.release_version(True)

    assert value == {"value": None, "source": "unavailable", "status": "unknown"}
    assert warning == "release_refresh_failed"


def test_malformed_http_release_response_is_partial_data(status_modules, monkeypatch):
    report = status_modules.report

    def malformed(*args, **kwargs):
        raise http.client.BadStatusLine("malformed response")

    monkeypatch.setattr(report, "_open_release_request", malformed)

    value, warning = report.release_version(True)

    assert value == {"value": None, "source": "unavailable", "status": "unknown"}
    assert warning == "release_refresh_failed"


def test_release_refresh_rejects_redirects(status_modules, monkeypatch):
    report = status_modules.report
    observed = []
    real_build_opener = report.urllib.request.build_opener

    class RedirectFixture(report.urllib.request.BaseHandler):
        def default_open(self, request):
            observed.append(request.full_url)
            headers = Message()
            headers["Location"] = "https://example.invalid/release"
            response = urllib.response.addinfourl(
                io.BytesIO(b""),
                headers,
                request.full_url,
                code=302,
            )
            response.msg = "Found"
            return response

    def build_opener(handler):
        return real_build_opener(handler, RedirectFixture())

    monkeypatch.setattr(report.urllib.request, "build_opener", build_opener)

    value, warning = report.release_version(True)

    assert value == {"value": None, "source": "unavailable", "status": "unknown"}
    assert warning == "release_refresh_failed"
    assert observed == [report.LATEST_RELEASE_URL]


def _source_tree(root: Path, *, changelog="## v1.3.0 - Unreleased\n"):
    manifest = root / "plugins/aquarium/.codex-plugin/plugin.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text('{"name":"aquarium","version":"1.2.3"}\n', encoding="utf-8")
    (root / "CHANGELOG.md").write_text(changelog, encoding="utf-8")


def test_source_versions_require_and_preserve_the_exact_source_root(
    status_modules, tmp_path, monkeypatch
):
    report = status_modules.report
    source = tmp_path / "source"
    source.mkdir()
    _source_tree(source)
    monkeypatch.setattr(
        report, "_git_identity", lambda root: (str(source), str(source / ".git"))
    )

    plugin, unreleased, warning = report.source_versions(str(source))

    assert plugin == {
        "value": "v1.2.3",
        "source": "source_root_manifest",
        "status": "observed",
    }
    assert unreleased == {
        "value": "v1.3.0",
        "source": "source_root_changelog",
        "status": "observed",
    }
    assert warning is None

    alias = tmp_path / "source-link"
    alias.symlink_to(source, target_is_directory=True)
    with pytest.raises(status_modules.contract.ContractError) as raised:
        report.source_versions(str(alias))
    assert raised.value.code == "invalid_source_root"


def test_source_observation_without_one_open_version_is_independently_unknown(
    status_modules, tmp_path, monkeypatch
):
    report = status_modules.report
    source = tmp_path / "source"
    source.mkdir()
    _source_tree(source, changelog="# Changelog\n")
    monkeypatch.setattr(
        report, "_git_identity", lambda root: (str(source), str(source / ".git"))
    )

    plugin, unreleased, warning = report.source_versions(str(source))

    assert plugin["status"] == "observed"
    assert unreleased == {"value": None, "source": "unavailable", "status": "unknown"}
    assert warning == "source_observation_unavailable"


def _set_report_home(report, monkeypatch, home: Path):
    monkeypatch.setattr(report.Path, "home", classmethod(lambda cls: home))


def test_enrollment_reports_absent_without_creating_home_state(
    status_modules, tmp_path, monkeypatch
):
    report = status_modules.report
    _set_report_home(report, monkeypatch, tmp_path)

    value, warning = report.enrollment({"git_root": "/checkout"})

    assert value == {"state": "absent", "project_id": None}
    assert warning is None
    assert not (tmp_path / ".aquarium-dev").exists()


def test_enrollment_distinguishes_enrolled_invalid_and_unreadable(
    status_modules, tmp_path, monkeypatch
):
    report = status_modules.report
    _set_report_home(report, monkeypatch, tmp_path)
    enrollments = tmp_path / ".aquarium-dev/enrollments"
    enrollments.mkdir(parents=True)
    path = enrollments / "aquarium.json"
    document = {
        "schema": "aquarium-dev-enrollment/v1",
        "project_id": "aquarium",
        "checkout": "/checkout",
        "hook_path": "/checkout/.git/hooks/post-commit",
        "hook_block": "managed",
        "enrolled_at": "2026-09-18T00:00:00+00:00",
    }
    path.write_text(json.dumps(document), encoding="utf-8")

    assert report.enrollment({"git_root": "/checkout"}) == (
        {"state": "enrolled", "project_id": "aquarium"},
        None,
    )

    document["extra"] = True
    path.write_text(json.dumps(document), encoding="utf-8")
    assert report.enrollment({"git_root": "/checkout"}) == (
        {"state": "invalid", "project_id": None},
        "enrollment_invalid",
    )

    path.unlink()
    enrollments.rmdir()
    enrollments.symlink_to(tmp_path, target_is_directory=True)
    assert report.enrollment({"git_root": "/checkout"}) == (
        {"state": "unreadable", "project_id": None},
        "enrollment_unreadable",
    )
