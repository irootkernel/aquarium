"""Design-only evidence and approval boundaries; no provider or document execution."""

import copy
from pathlib import Path

from adaptive_bundles import BundleError, contained, directory, read_regular, sha256

LEAVES = {"interview", "pm", "seed", "qa"}
OPERATIONS = {
    "sha256:b891096f858bee3995ecc5588c8efbe0672abfd05d28042249484d6a05099be8": "context",
    "sha256:088fb738744c383c0a6bf628bbfa29ae4f53fab060ead5642e62afc1a4ddcc9a": "discovery",
    "sha256:96970035e3c2a943448c1602838bcc00ecde2c067a03cf8085fcfbae04515d8f": "draft",
    "sha256:51ea64185007a77ef7b4e5ba62cc0308bebcc0e2a71348276452439ef29ca5fd": "challenge",
    "sha256:564ebf6e69d47943d6d6c7caf1afb610443dce1dfd0f55ecd89e4710e5d67d96": "quality",
    "sha256:6f50b59fb6c2f641c8ae2cf8352df1119155346ede82700bf4ed1130a63918e6": "application",
}


def object_value(value, name):
    if not isinstance(value, dict):
        raise BundleError("invalid-input", name + " must be an object")
    return value


def quality(value):
    """Map actual QA delivery and local dispositions, never raw FAIL to invocation failure."""
    value = object_value(value, "design.quality")
    outcome = value.get("operation_outcome")
    if not isinstance(outcome, str) or outcome not in {"pass", "fail", "inconclusive"}:
        raise BundleError("invalid-input", "QA operation outcome is required")
    if outcome != "pass":
        return {
            "operation_outcome": outcome,
            "owner": "quality",
            "raw_verdict": value.get("raw_verdict"),
        }
    if (
        not isinstance(value.get("raw_verdict"), str)
        or value.get("raw_verdict") not in {"PASS", "REVISE", "FAIL"}
        or not value.get("draft_sha256")
    ):
        raise BundleError(
            "not-established", "Readable raw QA and exact draft identity are required"
        )
    findings = value.get("findings")
    if not isinstance(findings, list):
        raise BundleError("invalid-input", "QA findings must preserve every source row")
    counts = {"discovery": 0, "draft": 0}
    identifiers = set()
    for row in findings:
        row = object_value(row, "QA finding")
        identifier = row.get("id")
        if (
            not isinstance(identifier, str)
            or not identifier
            or identifier in identifiers
        ):
            raise BundleError("invalid-input", "QA findings need unique original IDs")
        identifiers.add(identifier)
        if (
            row.get("disposition") not in {"unresolved", "resolved", "rejected"}
            or not isinstance(row.get("basis"), str)
            or not row["basis"].strip()
        ):
            raise BundleError(
                "not-established",
                "Every QA finding needs its actual local disposition and basis",
            )
        if row["disposition"] == "unresolved":
            if not isinstance(row.get("owner"), str) or row.get("owner") not in counts:
                raise BundleError(
                    "incompatible", "Design QA findings belong to discovery or draft"
                )
            counts[row["owner"]] += 1
    return {
        "operation_outcome": "pass",
        "raw_verdict": value["raw_verdict"],
        "draft_sha256": value["draft_sha256"],
        "unresolved_discovery": counts["discovery"],
        "unresolved_draft": counts["draft"],
        "owner": "discovery"
        if counts["discovery"]
        else "draft"
        if counts["draft"]
        else "approval",
        "findings": copy.deepcopy(findings),
    }


def application(
    repository, proposal, approval, *, applied=False, approval_sources=("user",)
):
    """Re-read the exact approved targets before dispatch; the Worker rechecks before writes."""
    proposal = object_value(proposal, "design.proposal")
    targets = object_value(proposal.get("targets"), "design.proposal.targets")
    if not targets or not isinstance(proposal.get("diff"), str):
        raise BundleError(
            "invalid-input", "The complete proposed diff and targets are required"
        )
    if (
        not isinstance(approval, dict)
        or approval.get("source") not in approval_sources
        or approval.get("decision") != "approved"
    ):
        return {"status": "approval-required", "next_owner": "Primary"}
    if approval.get("proposal") != proposal:
        return {
            "status": "reapproval-required",
            "owner": "draft",
            "reason": "proposal-changed",
        }
    for name, snapshot in targets.items():
        snapshot = object_value(snapshot, "design target snapshot")
        if not {"before", "after"}.issubset(snapshot):
            raise BundleError(
                "invalid-input", "Targets need before and after byte identities"
            )
        for digest in (snapshot["before"], snapshot["after"]):
            if digest is not None and (
                not isinstance(digest, str)
                or len(digest) != 71
                or not digest.startswith("sha256:")
                or any(c not in "0123456789abcdef" for c in digest[7:])
            ):
                raise BundleError(
                    "invalid-input", "Target identities must be SHA-256 or absent"
                )
        if (
            not isinstance(name, str)
            or not name
            or Path(name).is_absolute()
            or ".." in Path(name).parts
        ):
            raise BundleError(
                "invalid-input",
                "Approved document targets must stay within the requested scope",
            )
        path = contained(Path(repository), Path(repository) / name)
        if path.exists() or path.is_symlink():
            actual = sha256(read_regular(Path(repository), path))
        else:
            with directory(Path(repository), path.parent, allow_missing=True):
                actual = None
        expected = snapshot["after" if applied else "before"]
        if actual != expected:
            return {
                "status": "reapproval-required",
                "owner": "draft",
                "reason": "target-changed",
                "path": name,
            }
    return {
        "status": "verified-applied" if applied else "approved-current",
        "targets": copy.deepcopy(targets),
    }


def context(repository, assignment, phase):
    """Consume optional ordinary design evidence; application itself always needs actual approval."""
    value = object_value(assignment["target"].get("design", {}), "target.design")
    result = {
        "phase": phase,
        "product_implementation": False,
        "delivery_commit": "separate-authority",
        "next_owner": "Primary",
    }
    if "quality" in value:
        result["quality"] = quality(value["quality"])
    if phase == "application":
        if "proposal" not in value:
            result["application"] = {
                "status": "approval-required",
                "next_owner": "Primary",
            }
        else:
            result["application"] = application(
                repository,
                value["proposal"],
                assignment["authority"].get("document_approval"),
                applied=value.get("applied") is True,
            )
    return result
