"""Prepare and apply specifically consented reusable definitions after closeout.

This source-only adapter never commits, advances sessions or assesses product work.
Use observations and grants are ordinary closeout evidence supplied by the Coordinator.
"""

import contextlib
import copy
import difflib
import os
import re
import sys
import uuid
from pathlib import Path

import yaml
from adaptive_bundles import (
    BundleError,
    _rename_exclusive,
    contained,
    directory,
    git,
    read_regular,
    sha256,
)
from adaptive_composition import compose, source_bytes
from adaptive_definitions import canonical_json, native_key, parse_definition
from adaptive_preparation import verify_directory, write_new


def obj(value, name):
    if not isinstance(value, dict):
        raise BundleError("invalid-input", name + " must be an object")
    return value


def reason(value, name):
    if not isinstance(value, str) or not value.strip():
        raise BundleError("not-established", name + " needs an actual basis")
    return value


def original(value):
    value = obj(value, "Originating workflow")
    for key in ("workflow", "epic", "task", "reference"):
        reason(value.get(key), key)
    return copy.deepcopy(value)


def native_checks(repository, client, path, binding, *, transformed):
    if Path(client.repository).resolve() != repository:
        raise BundleError("invalid-input", "Native client worktree differs")
    raw = read_regular(repository, path)
    if sha256(raw) != binding["procedure"]["source_sha256"]:
        raise BundleError("source-drift", "Source differs from its exact binding")
    observations = []
    if transformed:
        relative = str(path.relative_to(repository))
        for command, options in (
            ("format", ["--check"]),
            ("validate", []),
            ("vet", []),
            ("lint", ["--warnings-as-errors"]),
        ):
            observations.append(
                client.read(
                    ["procedure", command, *options, "--", relative],
                    "procedure." + command,
                    {
                        "podway.procedure-source-result/v1",
                        "podway.procedure-diagnostics-result/v1",
                    }
                    if command == "format"
                    else {"podway.procedure-diagnostics-result/v1"},
                )
            )
    preview = client.preview(path)
    actual = (
        preview["procedure_id"],
        preview["procedure_version"],
        preview["procedure_digest"],
    )
    if actual != native_key(binding) or read_regular(repository, path) != raw:
        raise BundleError("source-drift", "Native tuple or source changed")
    return observations + [preview]


def source_defaults(document):
    """Released Procedure v2 text_item.multiline defaults to true."""
    document = copy.deepcopy(document)
    for definition in document["node_definitions"].values():
        for item in definition.get("items", []):
            if item.get("type") == "text":
                item.setdefault("multiline", True)
    return document


def payload(repository, candidate, client):
    kind = candidate.get("kind")
    binding = parse_definition(source_bytes(repository, candidate["binding"]))
    if binding["schema"] != "aquarium.procedure-binding/v2":
        raise BundleError(
            "invalid-input", "A complete representative binding is required"
        )
    source_ref = (
        candidate["source"]
        if kind == "whole"
        else candidate["representative"]["source"]
    )
    source = source_bytes(repository, source_ref)
    source_path = contained(repository, source_ref["path"])
    transformed = candidate.get("transformed") is True or kind == "fragment"
    checked = native_checks(
        repository, client, source_path, binding, transformed=transformed
    )
    if kind == "whole":
        return {
            "procedure.yaml": source,
            "binding.json": canonical_json(binding),
        }, checked
    if kind != "fragment":
        raise BundleError(
            "invalid-input", "Preservation kind must be whole or fragment"
        )
    fragment = parse_definition(source_bytes(repository, candidate["source"]))
    if fragment["schema"] != "aquarium.procedure-fragment/v2":
        raise BundleError("invalid-input", "An exact fragment definition is required")
    representative = obj(candidate["representative"], "Fragment representative")
    draft = obj(representative.get("draft"), "Representative composition")
    composed = compose(repository, draft)
    components = draft["composition"]["components"]
    matches = [
        row
        for row in components
        if row.get("kind") == "fragment" and row.get("source") == candidate["source"]
    ]
    instance = copy.deepcopy(composed["document"])
    actual = yaml.safe_load(source)
    if isinstance(actual, dict):
        for key in ("id", "version"):
            instance[key] = actual.get(key)
    if len(matches) != 1 or source_defaults(actual) != source_defaults(instance):
        raise BundleError(
            "not-established", "Representative must flatten this exact fragment"
        )
    mapping = matches[0]["mapping"]
    for key, value in composed["mapping"].items():
        if key not in {"origins", "parameters"} and binding.get(key) != value:
            raise BundleError(
                "incompatible", "Representative binding differs from composition"
            )
    return {
        "fragment.json": canonical_json(fragment),
        "mapping.json": canonical_json(mapping),
        "representative.yaml": source,
        "representative.binding.json": canonical_json(binding),
    }, checked


def library_entries(repository, root):
    """Compare optional sources without making damaged history a prerequisite."""
    found, diagnostics = {}, []
    with directory(repository, root, allow_missing=True) as descriptor:
        if descriptor is None:
            return found, diagnostics
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if relative.parts[0].startswith(".promotion-"):
            if len(relative.parts) == 1:
                diagnostics.append(
                    {"path": str(relative), "status": "interrupted-staging"}
                )
            continue
        if path.is_dir() and not path.is_symlink():
            continue
        try:
            found[str(path.relative_to(root))] = sha256(read_regular(repository, path))
        except BundleError as error:
            diagnostics.append(
                {"path": str(path.relative_to(root)), "status": error.code}
            )
    return found, diagnostics


def offer(repository, request, client):
    """Return exact grouped content for consent; no repository writes."""
    repository = Path(repository).expanduser().resolve()
    request = obj(request, "Preservation request")
    origin = original(request.get("origin"))
    root = contained(repository, request["library_root"])
    existing, diagnostics = library_entries(repository, root)
    candidates = request.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise BundleError("invalid-input", "Preservation candidates are required")
    items, names = [], set()
    for candidate in candidates:
        candidate = obj(candidate, "Preservation candidate")
        name = candidate.get("name")
        if (
            not isinstance(name, str)
            or not name
            or Path(name).name != name
            or name in {".", ".."}
            or name in names
        ):
            raise BundleError(
                "invalid-input", "Candidates need distinct library entry names"
            )
        names.add(name)
        use = obj(candidate.get("use"), "Actual use")
        if use.get("outcome") != "successful":
            raise BundleError(
                "not-established", "Actual successful use is required for an offer"
            )
        reason(use.get("reference"), "Actual use reference")
        reason(use.get("evidence"), "Actual operation evidence")
        reason(candidate.get("future_use"), "Distinct future usefulness")
        reason(candidate.get("limits"), "Observed use and parameter limits")
        contents, checks = payload(repository, candidate, client)
        identity_files = (
            ("procedure.yaml", "binding.json")
            if candidate["kind"] == "whole"
            else ("fragment.json", "mapping.json")
        )
        entries = {path.rsplit("/", 1)[0] for path in existing if "/" in path}
        duplicates = sorted(
            entry
            for entry in entries
            if all(
                existing.get(entry + "/" + filename) == sha256(contents[filename])
                for filename in identity_files
            )
        )
        target = root / name
        with directory(repository, target, allow_missing=True) as descriptor:
            if descriptor is not None:
                raise BundleError(
                    "publication-conflict",
                    "Existing library entry is preserved; select a new entry or reuse it",
                    {"path": str(target)},
                )
        files = {
            str((target / filename).relative_to(repository)): raw.decode("utf-8")
            for filename, raw in contents.items()
        }
        diff = "".join(
            "".join(
                difflib.unified_diff(
                    [], raw.splitlines(keepends=True), fromfile="/dev/null", tofile=path
                )
            )
            for path, raw in sorted(files.items())
        )
        items.append(
            {
                "name": name,
                "kind": candidate["kind"],
                "future_use": candidate["future_use"],
                "use": copy.deepcopy(use),
                "limits": candidate["limits"],
                "files": files,
                "diff": diff,
                "duplicates": duplicates,
                "checks": checks,
                "runtime": "source-use-only; transformed candidate execution unobserved"
                if candidate.get("transformed") or candidate["kind"] == "fragment"
                else "prior use; fresh work retains current fit and due assessments",
                "adoption": "not-performed",
                "transformed": candidate.get("transformed") is True,
            }
        )
    result = {
        "origin": origin,
        "library_root": str(root.relative_to(repository)),
        "candidates": items,
        "diagnostics": diagnostics,
    }
    result["id"] = sha256(canonical_json(result))
    return {
        "status": "preservation-offer",
        "proposal": result,
        "next_owner": "Coordinator",
        "question": "Preserve which exact candidates after original finalization, and is a separate promotion commit authorized?",
    }


def finalized(repository, value):
    value = obj(value, "Original finalization")
    if value.get("accepted") is not True or not reason(
        value.get("reference"), "Original acceptance"
    ):
        raise BundleError("not-established", "Original acceptance is required")
    if value.get("commit"):
        commit = value["commit"]
        if not isinstance(commit, str) or not re.fullmatch(
            r"[0-9a-f]{40}|[0-9a-f]{64}", commit
        ):
            raise BundleError(
                "not-established", "Original commit must be an exact full object ID"
            )
        result = git(repository, "rev-parse", "--verify", commit + "^{commit}")
        if result.returncode or result.stdout.strip().decode() != commit:
            raise BundleError(
                "not-established", "Original accepted commit is unavailable"
            )
    elif value.get("no_commit") is not True:
        raise BundleError(
            "not-established",
            "Original commit or verified no-commit result is required",
        )
    native = obj(value.get("native"), "Native finalization")
    if native.get("required") is not False and (
        native.get("state") != "completed"
        or not native.get("reference")
        or not (
            native.get("disposition") in {"handed_off", "not_required"}
            or isinstance(native.get("undisposed_reason"), str)
            and native["undisposed_reason"].strip()
        )
    ):
        raise BundleError(
            "not-established",
            "Required original native finalization remains incomplete",
        )


def apply(repository, proposal, decision, finalization, client, *, commit_grant=None):
    """Apply exact consented new library entries; leave Git and original lifecycle alone."""
    repository = Path(repository).expanduser().resolve()
    proposal, decision = obj(proposal, "Proposal"), obj(decision, "Content consent")
    check = copy.deepcopy(proposal)
    identifier = check.pop("id")
    if sha256(canonical_json(check)) != identifier:
        raise BundleError("source-drift", "Preservation proposal changed")
    selected = decision.get("selected")
    if (
        decision.get("source") != "user"
        or decision.get("proposal_id") != identifier
        or not isinstance(selected, list)
        or any(not isinstance(name, str) for name in selected)
    ):
        raise BundleError(
            "approval-required", "Specific current content consent is required"
        )
    available = {row["name"]: row for row in proposal["candidates"]}
    if len(set(selected)) != len(selected) or set(selected) - available.keys():
        raise BundleError(
            "invalid-input", "Consent must name an exact candidate subset"
        )
    if not selected:
        return {
            "status": "preservation-declined",
            "effects": [],
            "original_work": "unchanged",
            "local_recovery": "retained",
        }
    finalized(repository, finalization)
    if Path(client.repository).resolve() != repository:
        raise BundleError("invalid-input", "Native client worktree differs")
    root = contained(repository, proposal["library_root"])
    existing_names = set()
    for name in selected:
        if available[name]["duplicates"]:
            raise BundleError(
                "duplicate",
                "Reuse an existing equivalent library entry",
                {"entries": available[name]["duplicates"]},
            )
        target = root / name
        with directory(repository, target, allow_missing=True) as descriptor:
            if descriptor is not None:
                for path, content in available[name]["files"].items():
                    location = contained(repository, path)
                    if location.parent != target or read_regular(
                        repository, location
                    ) != content.encode("utf-8"):
                        raise BundleError(
                            "publication-conflict",
                            "Existing promotion differs; preserve it",
                        )
                source_name = (
                    "procedure.yaml"
                    if available[name]["kind"] == "whole"
                    else "representative.yaml"
                )
                binding_name = (
                    "binding.json"
                    if available[name]["kind"] == "whole"
                    else "representative.binding.json"
                )
                binding = parse_definition(
                    read_regular(repository, target / binding_name)
                )
                native_checks(
                    repository,
                    client,
                    target / source_name,
                    binding,
                    transformed=available[name]["kind"] == "fragment"
                    or available[name]["transformed"],
                )
                existing_names.add(name)
        for path in available[name]["files"]:
            location = contained(repository, path)
            if (
                location.parent != target
                or git(repository, "check-ignore", "-q", "--", "./" + path).returncode
                == 0
            ):
                raise BundleError("unsafe", "Promotion target differs or is ignored")
    applied = [
        path
        for name in selected
        if name in existing_names
        for path in available[name]["files"]
    ]
    with directory(repository, root, create=True) as parent:
        for name in selected:
            if name in existing_names:
                continue
            temporary = ".promotion-" + uuid.uuid4().hex
            os.mkdir(temporary, 0o700, dir_fd=parent)
            stage = os.open(
                temporary, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent
            )
            try:
                for path, content in available[name]["files"].items():
                    write_new(stage, Path(path).name, content.encode("utf-8"))
                source_name = (
                    "procedure.yaml"
                    if available[name]["kind"] == "whole"
                    else "representative.yaml"
                )
                binding_name = (
                    "binding.json"
                    if available[name]["kind"] == "whole"
                    else "representative.binding.json"
                )
                binding = parse_definition(
                    available[name]["files"][
                        str((root / name / binding_name).relative_to(repository))
                    ]
                )
                native_checks(
                    repository,
                    client,
                    root / temporary / source_name,
                    binding,
                    transformed=available[name]["kind"] == "fragment"
                    or available[name]["transformed"],
                )
                verify_directory(repository, root / temporary, stage)
                for path, content in available[name]["files"].items():
                    if read_regular(
                        repository, root / temporary / Path(path).name
                    ) != content.encode("utf-8"):
                        raise BundleError(
                            "source-drift", "Staged promotion bytes changed"
                        )
                verify_directory(repository, root, parent)
                try:
                    _rename_exclusive(parent, temporary, name)
                except FileExistsError as error:
                    raise BundleError(
                        "publication-conflict", "Concurrent library entry was preserved"
                    ) from error
                os.fsync(parent)
                for path, content in available[name]["files"].items():
                    if read_regular(repository, path) != content.encode("utf-8"):
                        raise BundleError(
                            "source-drift", "Published library bytes changed"
                        )
                    applied.append(path)
            finally:
                original_error = sys.exc_info()[1]
                try:
                    try:
                        entry = os.stat(temporary, dir_fd=parent, follow_symlinks=False)
                    except FileNotFoundError:
                        entry = None
                    if entry is not None and (entry.st_dev, entry.st_ino) == (
                        os.fstat(stage).st_dev,
                        os.fstat(stage).st_ino,
                    ):
                        for filename in available[name]["files"]:
                            with contextlib.suppress(FileNotFoundError):
                                os.unlink(Path(filename).name, dir_fd=stage)
                        os.rmdir(temporary, dir_fd=parent)
                except OSError as error:
                    details = {
                        "path": str(root / temporary),
                        "cleanup_error": str(error),
                    }
                    if isinstance(original_error, BundleError):
                        details["original_failure"] = {
                            "status": original_error.code,
                            "message": str(original_error),
                            "details": original_error.details,
                        }
                    raise BundleError(
                        "cleanup-failed",
                        "Owned promotion staging cleanup failed",
                        details,
                    ) from original_error or error
                finally:
                    os.close(stage)
    handoff = None
    if commit_grant is not None:
        grant = obj(commit_grant, "Promotion commit grant")
        if (
            grant.get("purpose") != "procedure-library-promotion"
            or grant.get("proposal_id") != identifier
            or grant.get("selected") != selected
            or grant.get("consumed") is not False
            or not grant.get("reference")
        ):
            raise BundleError(
                "commit-authority-required",
                "Grant does not cover this exact promotion; content remains uncommitted",
                {"applied": applied},
            )
        handoff = {
            "origin": proposal["origin"],
            "paths": applied,
            "grant": copy.deepcopy(grant),
            "lifecycle_edits": [],
            "staging": "not-performed",
            "commit": "not-performed",
            "checks": [available[name]["checks"] for name in selected],
            "review_acceptance": "existing applicable source-diff policy remains due",
            "release_note": "resolve under originating workflow",
        }
    return {
        "status": "promotion-applied",
        "paths": applied,
        "original_work": "unchanged",
        "local_recovery": "retained",
        "commit": "not-performed",
        "task_commit_handoff": handoff,
    }
