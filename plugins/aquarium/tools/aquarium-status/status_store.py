"""Safe local ledger storage for aquarium-status."""

from __future__ import annotations

import contextlib
import fcntl
import os
import stat
import tempfile
import unicodedata
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import yaml
from status_contract import (
    COMPONENT_OUTCOMES,
    LEDGER_SCHEMA,
    OUTCOMES,
    SHA256_RE,
    ContractError,
    parse_time,
    validate_scope,
    validate_uuid4,
    validate_version,
)
from yaml.events import AliasEvent
from yaml.nodes import MappingNode


class LedgerLoader(yaml.SafeLoader):
    """Safe loader that rejects aliases and duplicate mapping keys."""

    def compose_node(self, parent: Any, index: Any) -> Any:
        if self.check_event(AliasEvent):
            raise yaml.constructor.ConstructorError(None, None, "aliases are forbidden")
        return super().compose_node(parent, index)


def _construct_mapping(
    loader: LedgerLoader, node: MappingNode, deep: bool = False
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise yaml.constructor.ConstructorError(None, None, "duplicate key")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


LedgerLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


def state_root() -> Path:
    return Path.home() / ".aquarium"


def ledger_path() -> Path:
    return state_root() / "status.yaml"


def _ensure_directory(path: Path) -> None:
    if path.exists() or path.is_symlink():
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise ContractError("state_unsafe", f"unsafe owned directory: {path}", 1)
        if stat.S_IMODE(info.st_mode) != 0o700:
            raise ContractError(
                "state_unsafe", f"owned directory has unsafe mode: {path}", 1
            )
        return
    path.mkdir(mode=0o700)


def _regular_owned(path: Path, *, allow_absent: bool = True) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        if allow_absent:
            return False
        raise
    if (
        stat.S_ISLNK(info.st_mode)
        or not stat.S_ISREG(info.st_mode)
        or stat.S_IMODE(info.st_mode) != 0o600
    ):
        raise ContractError("state_unsafe", f"unsafe owned file: {path}", 1)
    return True


@contextlib.contextmanager
def locked(exclusive: bool) -> Iterator[None]:
    try:
        root = state_root()
        if not exclusive:
            try:
                info = root.lstat()
            except FileNotFoundError:
                yield
                return
            if (
                stat.S_ISLNK(info.st_mode)
                or not stat.S_ISDIR(info.st_mode)
                or stat.S_IMODE(info.st_mode) != 0o700
            ):
                raise ContractError(
                    "state_unsafe", f"unsafe owned directory: {root}", 1
                )
        else:
            _ensure_directory(root)
        path = state_root() / "status.lock"
        if path.exists() or path.is_symlink():
            _regular_owned(path)
        elif not exclusive:
            if ledger_path().exists() or ledger_path().is_symlink():
                raise ContractError(
                    "state_unsafe", "status ledger exists without its lock", 1
                )
            yield
            return
        flags = os.O_RDWR | os.O_NOFOLLOW
        if exclusive:
            flags |= os.O_CREAT
        descriptor = os.open(path, flags, 0o600)
        if exclusive:
            os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "r+b") as stream:
            fcntl.flock(stream, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
            yield
    except ContractError:
        raise
    except OSError as error:
        raise ContractError("lock_failed", "status ledger lock failed", 1) from error


def empty_ledger() -> dict[str, Any]:
    return {"schema": LEDGER_SCHEMA, "file_revision": 0, "repositories": []}


def _exact(
    value: Any, required: set[str], optional: set[str] | None = None
) -> dict[str, Any]:
    optional = optional or set()
    if (
        not isinstance(value, dict)
        or not set(value).issubset(required | optional)
        or not required.issubset(value)
    ):
        raise ValueError("invalid closed object")
    return value


def _attempt(value: Any, file_revision: int, row_revision: int) -> dict[str, Any]:
    item = _exact(
        value,
        {
            "attempt_id",
            "input_sha256",
            "expected_row_revision",
            "aquarium_version",
            "started_at",
            "completed_at",
            "outcome",
            "scope",
            "recorded_file_revision",
            "recorded_row_revision",
        },
    )
    validate_uuid4(item["attempt_id"])
    if (
        not isinstance(item["input_sha256"], str)
        or SHA256_RE.fullmatch(item["input_sha256"]) is None
    ):
        raise ValueError("invalid attempt digest")
    if (
        type(item["expected_row_revision"]) is not int
        or item["expected_row_revision"] < 0
    ):
        raise ValueError("invalid expected revision")
    validate_version(item["aquarium_version"])
    started = parse_time(item["started_at"], "started_at")
    completed = parse_time(item["completed_at"], "completed_at")
    if (
        completed < started
        or not isinstance(item["outcome"], str)
        or item["outcome"] not in OUTCOMES
    ):
        raise ValueError("invalid attempt outcome")
    validate_scope(item["scope"])
    for name, maximum in (
        ("recorded_file_revision", file_revision),
        ("recorded_row_revision", row_revision),
    ):
        if type(item[name]) is not int or item[name] < 1 or item[name] > maximum:
            raise ValueError("invalid recorded revision")
    if item["recorded_file_revision"] < item["recorded_row_revision"]:
        raise ValueError("invalid cross-revision relationship")
    if item["recorded_row_revision"] != item["expected_row_revision"] + 1:
        raise ValueError("invalid row revision transition")
    return item


def _canonical_absolute_path(value: Any) -> bool:
    if not isinstance(value, str) or not Path(value).is_absolute():
        return False
    normalized = unicodedata.normalize("NFC", value)
    return (
        normalized == value
        and os.path.normpath(value) == value
        and not any(part in {".", ".."} for part in value.split(os.sep))
    )


def _validate_ledger(value: Any) -> dict[str, Any]:
    ledger = _exact(value, {"schema", "file_revision", "repositories"})
    if (
        ledger["schema"] != LEDGER_SCHEMA
        or type(ledger["file_revision"]) is not int
        or ledger["file_revision"] < 1
        or not isinstance(ledger["repositories"], list)
    ):
        raise ValueError("invalid ledger")
    roots: list[str] = []
    attempt_roots: dict[str, str] = {}
    attempt_requests: dict[str, tuple[str, str]] = {}
    for row_value in ledger["repositories"]:
        row = _exact(
            row_value,
            {
                "git_root",
                "git_common_dir",
                "project",
                "row_revision",
                "last_attempt",
                "components",
            },
            {"last_full_ready"},
        )
        if (
            not _canonical_absolute_path(row["git_root"])
            or not _canonical_absolute_path(row["git_common_dir"])
            or not isinstance(row["project"], str)
            or not row["project"]
            or row["project"] != unicodedata.normalize("NFC", row["project"])
            or type(row["row_revision"]) is not int
            or row["row_revision"] < 1
            or row["row_revision"] > ledger["file_revision"]
            or not isinstance(row["components"], dict)
            or any(name not in {"sanho", "aquarium_dev"} for name in row["components"])
        ):
            raise ValueError("invalid row")
        latest = _attempt(
            row["last_attempt"], ledger["file_revision"], row["row_revision"]
        )
        attempt_id = latest["attempt_id"]
        request_identity = (row["git_root"], latest["input_sha256"])
        if (
            attempt_id in attempt_requests
            and attempt_requests[attempt_id] != request_identity
        ):
            raise ValueError("attempt identifier has conflicting requests")
        attempt_requests[attempt_id] = request_identity
        if attempt_id in attempt_roots and attempt_roots[attempt_id] != row["git_root"]:
            raise ValueError("attempt identifier crosses roots")
        attempt_roots[attempt_id] = row["git_root"]
        if (
            latest["recorded_row_revision"] != row["row_revision"]
            or latest["expected_row_revision"] != row["row_revision"] - 1
        ):
            raise ValueError("invalid latest attempt revision")
        if "last_full_ready" in row:
            full = _attempt(
                row["last_full_ready"], ledger["file_revision"], row["row_revision"]
            )
            attempt_id = full["attempt_id"]
            request_identity = (row["git_root"], full["input_sha256"])
            if (
                attempt_id in attempt_requests
                and attempt_requests[attempt_id] != request_identity
            ):
                raise ValueError("attempt identifier has conflicting requests")
            attempt_requests[attempt_id] = request_identity
            if (
                attempt_id in attempt_roots
                and attempt_roots[attempt_id] != row["git_root"]
            ):
                raise ValueError("attempt identifier crosses roots")
            attempt_roots[attempt_id] = row["git_root"]
            if full["outcome"] != "ready" or full["scope"] != {"kind": "full"}:
                raise ValueError("invalid full-ready attempt")
        for observation in row["components"].values():
            component = _exact(observation, {"attempt_id", "outcome", "version"})
            validate_uuid4(component["attempt_id"])
            if (
                component["attempt_id"] in attempt_roots
                and attempt_roots[component["attempt_id"]] != row["git_root"]
            ):
                raise ValueError("attempt identifier crosses roots")
            attempt_roots[component["attempt_id"]] = row["git_root"]
            if (
                not isinstance(component["outcome"], str)
                or component["outcome"] not in COMPONENT_OUTCOMES
            ):
                raise ValueError("invalid component outcome")
            validate_version(component["version"])
        roots.append(row["git_root"])
    if roots != sorted(roots, key=lambda item: item.encode("utf-8")) or len(
        roots
    ) != len(set(roots)):
        raise ValueError("invalid row order")
    return ledger


def read_ledger() -> tuple[dict[str, Any], bytes | None]:
    path = ledger_path()
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        return empty_ledger(), None
    except OSError as error:
        raise ContractError(
            "state_corrupt", "status ledger is unreadable or invalid", 1
        ) from error
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600:
            raise ValueError("unsafe ledger file")
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = -1
            raw = stream.read()
        text = raw.decode("utf-8")
        value = yaml.load(text, Loader=LedgerLoader)
        value = _validate_ledger(value)
        if yaml_bytes(value) != raw:
            raise ValueError("ledger is not canonical YAML")
    except (
        OSError,
        UnicodeError,
        ValueError,
        TypeError,
        yaml.YAMLError,
        ContractError,
    ) as error:
        raise ContractError(
            "state_corrupt", "status ledger is unreadable or invalid", 1
        ) from error
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    return value, raw


def yaml_bytes(value: dict[str, Any]) -> bytes:
    return yaml.safe_dump(
        value,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=True,
    ).encode("utf-8")


def _write_once(target: Path, content: bytes) -> None:
    descriptor, name = tempfile.mkstemp(prefix=".status.", dir=target.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, target)
        directory = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        temporary.unlink(missing_ok=True)


def write_ledger(value: dict[str, Any], previous: bytes | None) -> None:
    target = ledger_path()
    content = yaml_bytes(value)
    try:
        _write_once(target, content)
    except OSError as error:
        try:
            if previous is None:
                target.unlink(missing_ok=True)
                directory = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
            else:
                _write_once(target, previous)
        except OSError as rollback_error:
            raise ContractError(
                "durability_failed", "ledger write and rollback failed", 1
            ) from rollback_error
        raise ContractError(
            "state_write_failed", "ledger write failed and was rolled back", 1
        ) from error
