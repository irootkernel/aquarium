"""Design-only evidence and approval boundaries; no provider or document execution."""

import copy
from pathlib import Path

from adaptive_bundles import BundleError, contained, directory, read_regular, sha256

LEAVES = {"interview", "pm", "seed", "qa"}
OPERATIONS = {
    "sha256:3279982bbafdfd77f1ea7529e52e7f8f75d27ed67db1cbcad58d111e86ce3738": "context",
    "sha256:baa70e7d4134003ea497218429495c25281cbe54c9d271a1ed6dcb16f3c37a48": "discovery",
    "sha256:81ebe0a24739a44ce487d32b41158cc4b909ab0d8f2575093db271b25e1c2053": "draft",
    "sha256:0ec2cd15b2a122b217eb0a28f88c04c60867414ec7e107fb3b182ae79ac359f9": "challenge",
    "sha256:41f30306cb9903b5e0c76e2819d5ec8e64bc39cd1cb842fe22c16da545ec1d6d": "quality",
    "sha256:7e593f53fbeb186570313947c7b7740c3538da3d897142a3f0638c1127b41367": "application",
    "sha256:42e73ba6814be2ec1abbe316b51e1f63399575bc792bad75b32bf5daa5a7d18c": "application",
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


def approved_targets(proposal, approval, *, approval_sources=("user",)):
    """Validate an actual approval and its exact target identities."""
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
        return {"status": "approval-required", "next_owner": "Coordinator"}
    if approval.get("proposal") != proposal:
        return {
            "status": "reapproval-required",
            "owner": "draft",
            "reason": "proposal-changed",
        }
    return target_images(targets)


def target_images(targets):
    """Validate byte identities independently of the authority granting a write."""
    targets = object_value(targets, "document targets")
    if not targets:
        raise BundleError("invalid-input", "Document targets are required")
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
    return {"status": "approved", "targets": copy.deepcopy(targets)}


def current_targets(repository, targets, *, applied=False):
    """Compare validated targets with the current safe file images."""
    for name, snapshot in targets.items():
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


def application(
    repository, proposal, approval, *, applied=False, approval_sources=("user",)
):
    """Re-read the exact approved targets before dispatch; the Executor rechecks before writes."""
    approved = approved_targets(proposal, approval, approval_sources=approval_sources)
    if approved["status"] != "approved":
        return approved
    return current_targets(repository, approved["targets"], applied=applied)


def scoped_history(work, changes):
    """Validate historical grants and continuous images without authorizing new writes."""
    if not isinstance(changes, list):
        raise BundleError("invalid-input", "Document changes must be an ordered list")
    history = {}
    for change in changes:
        change = object_value(change, "Document change")
        if "document_write" in change:
            checked = _scoped_targets(
                work, change.get("targets"), change["document_write"], history
            )
        else:
            checked = approved_targets(change.get("proposal"), change.get("approval"))
        if checked["status"] != "approved":
            raise BundleError(
                checked["status"], "Historical document authority is missing"
            )
        for name, images in checked["targets"].items():
            if name in history and images["before"] != history[name]["after"]:
                raise BundleError(
                    "not-established", "Document changes are not continuous"
                )
            history[name] = {
                "before": history.get(name, images)["before"],
                "after": images["after"],
            }
    return history


def scoped_targets(work, targets, grant, *, changes=None):
    """Check current scope; create includes revisions proven by continuous history."""
    history = scoped_history(work, [] if changes is None else changes)
    checked = _scoped_targets(work, targets, grant, history)
    if checked["status"] == "approved":
        for name, images in checked["targets"].items():
            if name in history and images["before"] != history[name]["after"]:
                raise BundleError(
                    "not-established", "Document changes are not continuous"
                )
    return checked


def _scoped_targets(work, targets, grant, history):
    """A historical grant proves past effects only; each new effect needs its own grant."""
    if (
        not isinstance(grant, dict)
        or grant.get("source") != "user"
        or grant.get("decision") != "approved"
        or not isinstance(grant.get("reference"), str)
        or not grant["reference"].strip()
    ):
        return {"status": "approval-required", "next_owner": "Coordinator"}
    checked = target_images(targets)
    identity = {key: work.get(key) for key in ("repository", "roadmap", "epic")}
    if grant.get("work") != identity:
        raise BundleError("incompatible", "Document scope belongs to another work unit")
    paths = object_value(grant.get("paths"), "document_write.paths")
    for operations in paths.values():
        if (
            not isinstance(operations, list)
            or not operations
            or any(
                not isinstance(op, str) or op not in {"create", "update", "delete"}
                for op in operations
            )
        ):
            raise BundleError(
                "invalid-input", "Document operations must be explicit lists"
            )
    for name, images in checked["targets"].items():
        operation = (
            "delete"
            if images["after"] is None
            else "create"
            if images["before"] is None
            else "update"
        )
        operations = paths.get(name, [])
        created_revision = (
            operation == "update"
            and "create" in operations
            and name in history
            and history[name]["before"] is None
            and history[name]["after"] == images["before"]
        )
        if not name.endswith(".md") or (
            operation not in operations and not created_revision
        ):
            raise BundleError(
                "incompatible", "Document write exceeds the granted scope"
            )
    return checked


def requires_content_acceptance(document, binding, node):
    """Bypass acceptance only when every goal boundary excludes positive outcomes."""
    placements = {row["id"]: row for row in document["graph"]["nodes"]}
    definitions = document.get("node_definitions", {})
    predecessors, incoming = {}, {}
    for placement in placements.values():
        options = {
            option["id"]: option
            for option in definitions.get(placement.get("use"), {}).get("options", [])
        }
        for option, route in placement.get("routes", {}).items():
            predecessors.setdefault(route["to"], set()).add(placement["id"])
            incoming.setdefault(route["to"], []).append(
                (placement, options.get(option, {}).get("guards", []))
            )
        if placement.get("next"):
            successor = placement["next"]
            predecessors.setdefault(successor, set()).add(placement["id"])
            incoming.setdefault(successor, []).append((placement, []))

    def selected(placement, guard):
        reference = guard.get("evidence", {})
        return bool(reference.get("node") and reference.get("item")) and any(
            row.get("node") == reference["node"]
            and row.get("required") is True
            and reference["item"] in row.get("items", [])
            for row in placement.get("evidence_from", [])
        )

    def conflicts(left, right):
        if left.get("evidence") != right.get("evidence"):
            return False
        for equal, other in ((left, right), (right, left)):
            if "equals" not in equal:
                continue
            value = equal["equals"]
            if (
                "not_equals" in other
                and type(value) is type(other["not_equals"])
                and value == other["not_equals"]
            ):
                return True
            if (
                "equals" in other
                and type(value) is type(other["equals"])
                and value != other["equals"]
            ):
                return True
        return False

    goals = {}
    for boundary in binding["goal_assessments"]:
        current = boundary["node"]
        outcomes = set(boundary["outcomes"].values())
        placement = placements.get(current, {})
        options = {
            option["id"]: option
            for option in definitions.get(placement.get("use"), {}).get("options", [])
        }
        positive = [
            options.get(option, {}).get("guards", [])
            for option, outcome in boundary["outcomes"].items()
            if outcome == "achieved"
        ]
        direct_entry = current == document["graph"].get("entry") or current in (
            document.get("manual_rework", {}).get("allowed_targets", [])
        )
        # A qualified native assessment declares all three outcomes. Its positive
        # option may still be excluded by every incoming decision's fresh guards.
        if (
            positive
            and not direct_entry
            and incoming.get(current)
            and all(
                any(
                    selected(source, entry)
                    and selected(placement, guard)
                    and conflicts(entry, guard)
                    for entry in entry_guards
                    for guard in positive_guards
                )
                for source, entry_guards in incoming[current]
                for positive_guards in positive
            )
        ):
            outcomes.discard("achieved")
        goals[current] = outcomes
    pending, seen, outcomes = [node], set(), set()
    while pending:
        current = pending.pop()
        if current in seen:
            continue
        seen.add(current)
        if current in goals:
            outcomes.update(goals[current])
        elif current in predecessors:
            pending.extend(predecessors[current])
        else:
            return True
    return not outcomes or not outcomes.issubset({"not_achieved", "superseded"})


def document_acceptance(targets, acceptance):
    """Final content acceptance binds the current applied images, not a proposed diff."""
    images = {name: row["after"] for name, row in targets.items()}
    return (
        isinstance(acceptance, dict)
        and acceptance.get("source") == "user"
        and acceptance.get("decision") == "accepted"
        and isinstance(acceptance.get("reference"), str)
        and bool(acceptance["reference"].strip())
        and acceptance.get("files") == images
    )


def context(repository, assignment, phase, *, scoped=False):
    """Consume optional ordinary design evidence; application itself always needs actual approval."""
    value = object_value(assignment["target"].get("design", {}), "target.design")
    result = {
        "phase": phase,
        "product_implementation": False,
        "delivery_commit": "separate-authority",
        "next_owner": "Coordinator",
    }
    if "quality" in value:
        result["quality"] = quality(value["quality"])
    feature = assignment["target"]["procedure_plan"]["entrypoint"] == "new-feature"
    if scoped and not feature and "document_write" in assignment["authority"]:
        raise BundleError("incompatible", "Scoped document writes require new-feature")
    use_scope = scoped and feature
    if use_scope:
        result["write_mode"] = "scoped-worktree"
    if use_scope and (phase == "application" or value.get("applied") is True):
        targets = value.get("targets", {})
        checked = scoped_targets(
            assignment["work"],
            targets,
            assignment["authority"].get("document_write"),
            changes=value.get("changes"),
        )
        result["application"] = checked
        if checked["status"] == "approved":
            history = scoped_history(assignment["work"], value.get("changes", []))
            all_targets = {**history, **checked["targets"]}
            unchanged = {
                name: images
                for name, images in history.items()
                if name not in checked["targets"]
            }
            result["application"] = current_targets(repository, unchanged, applied=True)
            if result["application"]["status"] == "verified-applied":
                applied = value.get("applied") is True
                result["application"] = current_targets(
                    repository,
                    all_targets if applied else checked["targets"],
                    applied=applied,
                )
            if result["application"]["status"] == "reapproval-required":
                result["application"]["status"] = "reconciliation-required"
            result["accepted"] = document_acceptance(
                all_targets, assignment["authority"].get("document_acceptance")
            )
    if phase == "application" and not use_scope:
        if "proposal" not in value:
            result["application"] = {
                "status": "approval-required",
                "next_owner": "Coordinator",
            }
        else:
            result["application"] = application(
                repository,
                value["proposal"],
                assignment["authority"].get("document_approval"),
                applied=value.get("applied") is True,
            )
    if "caller" in value:
        from adaptive_squad import design_return

        if assignment["target"]["procedure_plan"]["entrypoint"] != "new-feature":
            raise BundleError(
                "incompatible", "A collaboration caller returns through new-feature"
            )
        result["collaboration_return"] = design_return(
            assignment, value, result.get("application", {})
        )
    return result
