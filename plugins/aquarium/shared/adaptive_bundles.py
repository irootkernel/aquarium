"""Ignored, self-contained Procedure bundles and exact native-key lookup."""

import contextlib
import ctypes
import errno
import fcntl
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import uuid
from pathlib import Path

from adaptive_definitions import (
    DefinitionError,
    canonical_json,
    definition_id,
    native_key,
    parse_definition,
)


class BundleError(ValueError):
    def __init__(self, code, message, details=None):
        super().__init__(message)
        self.code = code
        self.details = {} if details is None else details


def sha256(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def contained(repository, path):
    repository = Path(repository).resolve()
    path = Path(os.path.abspath(repository / path))
    try:
        relative = path.relative_to(repository)
    except ValueError as exc:
        raise BundleError("unsafe", "Definition path leaves the worktree") from exc
    if relative.parts and relative.parts[0] == ".git":
        raise BundleError("unsafe", "Definition path is not a source location")
    return path


@contextlib.contextmanager
def directory(repository, path, *, create=False, allow_missing=False):
    repository = Path(repository).resolve()
    path = contained(repository, path)
    descriptors = []
    missing = False
    try:
        try:
            descriptor = os.open(
                repository, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            )
            descriptors.append(descriptor)
            for part in path.relative_to(repository).parts:
                if create:
                    try:
                        os.mkdir(part, dir_fd=descriptor)
                    except FileExistsError:
                        pass
                try:
                    descriptor = os.open(
                        part,
                        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                        dir_fd=descriptor,
                    )
                except FileNotFoundError:
                    if not allow_missing:
                        raise
                    missing = True
                    break
                descriptors.append(descriptor)
        except OSError as exc:
            raise BundleError(
                "missing" if exc.errno == errno.ENOENT else "unsafe",
                f"Unsafe or unavailable definition directory: {path}",
            ) from exc
        yield None if missing else descriptor
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def read_regular(repository, path):
    path = contained(repository, path)
    with directory(repository, path.parent) as parent:
        try:
            descriptor = os.open(
                path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent
            )
        except OSError as exc:
            raise BundleError(
                "missing" if exc.errno == errno.ENOENT else "unsafe",
                f"Cannot read definition: {path}",
            ) from exc
        with os.fdopen(descriptor, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise BundleError("unsafe", f"Definition is not a regular file: {path}")
            return stream.read()


def git(repository, *arguments):
    result = subprocess.run(
        [
            "git",
            *(["--literal-pathspecs"] if arguments[0] == "ls-files" else []),
            "-C",
            str(repository),
            *arguments,
        ],
        capture_output=True,
        check=False,
    )
    if result.returncode not in {0, 1}:
        raise BundleError("git-error", result.stderr.decode(errors="replace").strip())
    return result


def roots_for(repository, roots):
    result = sorted({contained(repository, Path(root)) for root in roots})
    if not result:
        raise BundleError("unsupported", "The approved searched roots are required")
    for root in result:
        with directory(repository, root, allow_missing=True):
            pass
    return result


def verified_bundle(repository, path):
    binding_bytes = read_regular(repository, path / "binding.json")
    try:
        binding = parse_definition(binding_bytes)
    except DefinitionError as exc:
        code = (
            "unsupported"
            if exc.code in {"unsupported-schema", "unsupported-compatibility"}
            else "corrupt"
        )
        raise BundleError(code, str(exc)) from exc
    if binding["schema"] not in {
        "aquarium.procedure-binding/v1",
        "aquarium.procedure-binding/v2",
    }:
        raise BundleError("unsupported", "Retained definition is not a binding")
    if binding_bytes != canonical_json(binding) or path.name != definition_id(binding):
        raise BundleError(
            "corrupt", "Retained binding canonical bytes or bundle ID differ"
        )
    source = read_regular(repository, path / "procedure.yaml")
    if sha256(source) != binding["procedure"]["source_sha256"]:
        raise BundleError("corrupt", "Retained source bytes differ from the binding")
    return {
        "path": str(path),
        "binding": binding,
        "bundle_id": path.name,
        "source": source,
    }


def local_status(repository, path):
    paths = [
        str((path / name).relative_to(repository))
        for name in ("procedure.yaml", "binding.json")
    ]
    if git(repository, "ls-files", "-z", "--", *paths).stdout:
        raise BundleError(
            "tracked-conflict", "Selected retained definitions are tracked"
        )
    for relative in paths:
        if git(repository, "check-ignore", "-q", "--", "./" + relative).returncode:
            raise BundleError(
                "ignore-conflict", "Selected retained definitions are not ignored"
            )


def _key_hints(repository, path, native_identity):
    keys = set()
    try:
        value = json.loads(read_regular(repository, path / "binding.json"))
        procedure = value.get("procedure") if isinstance(value, dict) else None
        if isinstance(procedure, dict):
            key = tuple(procedure.get(field) for field in ("id", "version", "digest"))
            if all(isinstance(part, str) for part in key):
                keys.add(key)
    except (BundleError, ValueError):
        pass
    if native_identity is not None:
        try:
            read_regular(repository, path / "procedure.yaml")
            key = tuple(native_identity(path / "procedure.yaml"))
            if len(key) == 3 and all(isinstance(part, str) for part in key):
                keys.add(key)
        except (BundleError, ValueError):
            pass
    return keys


def resolve_bundle(
    repository, roots, key, *, native_identity=None, bootstrap=None, bundle_id=None
):
    """Resolve valid adopted content; unrelated invalid entries remain diagnostics."""
    repository = Path(repository).resolve()
    roots = roots_for(repository, roots)
    key = tuple(key)
    matches, failures, diagnostics = [], [], []
    for root in roots:
        local = root / ".local"
        with directory(repository, local, allow_missing=True) as descriptor:
            if descriptor is None:
                continue
            names = sorted(os.listdir(descriptor))
        for name in names:
            if not re.fullmatch(r"[0-9a-f]{64}", name):
                continue
            path = local / name
            try:
                bundle = verified_bundle(repository, path)
                if native_identity is None:
                    if native_key(bundle["binding"]) == key:
                        failures.append(
                            {
                                "path": str(path),
                                "code": "not-established",
                                "key_established": True,
                            }
                        )
                    continue
                if tuple(native_identity(path / "procedure.yaml")) != native_key(
                    bundle["binding"]
                ):
                    raise BundleError(
                        "corrupt",
                        "Retained binding tuple differs from native source identity",
                    )
                if native_key(bundle["binding"]) == key:
                    local_status(repository, path)
                    matches.append(bundle)
            except BundleError as exc:
                hints = _key_hints(repository, path, native_identity)
                selected = key in hints or name == bundle_id
                diagnostic = {
                    "path": str(path),
                    "code": "corrupt"
                    if selected and exc.code == "missing"
                    else exc.code,
                    "key_established": bool(hints) or name == bundle_id,
                }
                diagnostics.append(diagnostic)
                if selected:
                    failures.append(diagnostic)
    if failures:
        return {
            "status": failures[0]["code"],
            "diagnostics": diagnostics,
            "aliases": [],
        }
    if not matches:
        return {"status": "missing", "diagnostics": diagnostics, "aliases": []}
    if len({bundle["bundle_id"] for bundle in matches}) != 1:
        return {
            "status": "ambiguous",
            "diagnostics": diagnostics,
            "aliases": [b["path"] for b in matches],
        }
    bundle = matches[0]
    aliases = [match["path"] for match in matches]
    selected_damage = [
        entry
        for entry in diagnostics
        if Path(entry["path"]).name == bundle["bundle_id"]
    ]
    if selected_damage:
        for entry in selected_damage:
            entry["key_established"] = True
            if entry["code"] == "missing":
                entry["code"] = "corrupt"
        return {
            "status": selected_damage[0]["code"],
            "diagnostics": diagnostics,
            "aliases": aliases,
        }
    if bootstrap is not None:
        selected = contained(repository, Path(bootstrap))
        if selected.name == "binding.json":
            selected = selected.parent
        try:
            crosscheck = verified_bundle(repository, selected)
        except BundleError as exc:
            return {"status": exc.code, "diagnostics": diagnostics, "aliases": aliases}
        if (
            crosscheck["bundle_id"] != bundle["bundle_id"]
            or str(selected) not in aliases
        ):
            return {
                "status": "ambiguous",
                "diagnostics": diagnostics,
                "aliases": aliases,
            }
    return {
        "status": "resolved",
        **bundle,
        "aliases": aliases,
        "diagnostics": diagnostics,
    }


@contextlib.contextmanager
def publication_lock(repository):
    """An empty worktree Git-metadata lock, without session/bundle state."""
    result = git(repository, "rev-parse", "--git-path", "aquarium-adapt.lock")
    if result.returncode:
        raise BundleError("git-error", "Cannot locate worktree publication lock")
    path = Path(os.fsdecode(result.stdout).strip())
    if not path.is_absolute():
        path = Path(repository) / path
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise BundleError("unsafe", "Publication lock is not a regular file")
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        os.close(descriptor)


def _ignored_local(repository, root, bundle_id, local_name=".local"):
    local = root / local_name
    relative = str(local.relative_to(repository))
    target = local / bundle_id
    paths = [
        str((target / name).relative_to(repository))
        for name in ("procedure.yaml", "binding.json")
    ]
    if git(repository, "ls-files", "-z", "--", *paths).stdout:
        raise BundleError(
            "tracked-conflict", "Selected retention target contains tracked definitions"
        )
    with directory(repository, local, create=True) as descriptor:
        if any(
            git(repository, "check-ignore", "-q", "--", "./" + path).returncode
            for path in paths
        ):
            if git(repository, "ls-files", "-z", "--", relative + "/.gitignore").stdout:
                raise BundleError(
                    "ignore-conflict",
                    "Tracked ignore policy needs its own authorized update",
                )
            try:
                ignore = os.open(
                    ".gitignore",
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=descriptor,
                )
            except FileExistsError as exc:
                raise BundleError(
                    "ignore-conflict",
                    "Existing ignore policy does not cover retained bundles",
                ) from exc
            with os.fdopen(ignore, "wb") as stream:
                stream.write(b"*\n")
                stream.flush()
                os.fsync(stream.fileno())
        local_status(repository, target)
    return local


def _rename_exclusive(descriptor, source, destination):
    library = ctypes.CDLL(None, use_errno=True)
    name, flag = ("renameatx_np", 4) if sys.platform == "darwin" else ("renameat2", 1)
    function = getattr(library, name, None)
    if function is None:
        raise BundleError(
            "unsupported", "Atomic non-replacing directory publication is unavailable"
        )
    function.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    function.restype = ctypes.c_int
    if function(
        descriptor, os.fsencode(source), descriptor, os.fsencode(destination), flag
    ):
        number = ctypes.get_errno()
        raise OSError(number, os.strerror(number))


def publish_bundle(
    repository, roots, write_root, source, binding, *, qualify, native_identity=None
):
    """Publish only an exact qualified candidate, atomically and without replacement."""
    if not callable(native_identity):
        raise BundleError(
            "not-established", "Publication needs native identity verification"
        )
    repository = Path(repository).resolve()
    roots = roots_for(repository, roots)
    write_root = contained(repository, Path(write_root))
    if write_root not in roots:
        raise BundleError(
            "unsupported", "Write root is outside the approved searched roots"
        )
    if sha256(source) != binding["procedure"]["source_sha256"]:
        raise BundleError("corrupt", "Candidate source bytes differ from the binding")
    key = native_key(binding)
    bundle_id = definition_id(binding)
    qualify(source, binding)
    preflight = resolve_bundle(
        repository, roots, key, native_identity=native_identity, bundle_id=bundle_id
    )
    if preflight["status"] not in {"resolved", "missing"}:
        raise BundleError(
            preflight["status"],
            "Existing exact-key content requires recovery",
            preflight,
        )
    with publication_lock(repository):
        resolved = resolve_bundle(
            repository, roots, key, native_identity=native_identity, bundle_id=bundle_id
        )
        if resolved["status"] == "resolved":
            qualify(resolved["source"], resolved["binding"])
            original = json.loads(canonical_json(resolved["binding"]))
            candidate = json.loads(canonical_json(binding))
            original["procedure"].pop("source_sha256")
            candidate["procedure"].pop("source_sha256")
            if original != candidate:
                raise BundleError(
                    "ambiguous", "A changed mapping requires a distinct native revision"
                )
            return resolved
        if resolved["status"] != "missing":
            raise BundleError(
                resolved["status"], "Existing exact-key content requires recovery"
            )
        local = _ignored_local(repository, write_root, bundle_id)
        with directory(repository, local) as descriptor:
            try:
                existing = os.stat(bundle_id, dir_fd=descriptor, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                raise BundleError(
                    "unsafe" if stat.S_ISLNK(existing.st_mode) else "corrupt",
                    "Candidate bundle path already exists and needs recovery",
                )
            owned_name = ".prepare-" + uuid.uuid4().hex
            os.mkdir(owned_name, dir_fd=descriptor)
            stage = os.open(
                owned_name,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=descriptor,
            )
            published = False
            try:
                for name, content in [
                    ("procedure.yaml", source),
                    ("binding.json", canonical_json(binding)),
                ]:
                    output = os.open(
                        name,
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                        0o600,
                        dir_fd=stage,
                    )
                    with os.fdopen(output, "wb") as stream:
                        stream.write(content)
                        stream.flush()
                        os.fsync(stream.fileno())
                os.fsync(stage)
                with directory(repository, local) as current:
                    if (os.fstat(current).st_dev, os.fstat(current).st_ino) != (
                        os.fstat(descriptor).st_dev,
                        os.fstat(descriptor).st_ino,
                    ):
                        raise BundleError(
                            "unsafe", "Retention directory changed during publication"
                        )
                qualify(source, binding)
                if tuple(native_identity(local / owned_name / "procedure.yaml")) != key:
                    raise BundleError(
                        "corrupt", "Staged native tuple differs from the binding"
                    )
                try:
                    _rename_exclusive(descriptor, owned_name, bundle_id)
                except FileExistsError as exc:
                    raise BundleError(
                        "publication-conflict", "A competing target was preserved"
                    ) from exc
                published = True
                os.fsync(descriptor)
            finally:
                try:
                    stage_info = os.stat(
                        owned_name, dir_fd=descriptor, follow_symlinks=False
                    )
                    owned_at_stage = (stage_info.st_dev, stage_info.st_ino) == (
                        os.fstat(stage).st_dev,
                        os.fstat(stage).st_ino,
                    )
                except FileNotFoundError:
                    owned_at_stage = False
                if not published and owned_at_stage:
                    for name in ("procedure.yaml", "binding.json"):
                        with contextlib.suppress(FileNotFoundError):
                            os.unlink(name, dir_fd=stage)
                    with contextlib.suppress(OSError):
                        os.rmdir(owned_name, dir_fd=descriptor)
                os.close(stage)
        result = resolve_bundle(repository, roots, key, native_identity=native_identity)
        if result["status"] != "resolved":
            raise BundleError(
                result["status"], "Published bundle could not be verified"
            )
        return result
