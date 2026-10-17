"""Current diagnostic evidence and approved documents; no product repair or QA execution."""

import copy

from adaptive_bundles import BundleError
from adaptive_design import application, object_value, quality

PHASES = {"baseline", "investigation", "proposal", "quality", "documentation"}
OPERATIONS = {
    "sha256:cd1829ab2b0844c653d87281f2322a0e72912be287aa8f3983a7c0719a0683aa": "baseline",
    "sha256:eb8d5a130f9e853d46b32bfa93c700bc850cbbfc167aa41a16451640484aa616": "investigation",
    "sha256:e955f1171edb08a38b9fab4678e76b4df2117f35bc679510e5b70c76909dbb68": "proposal",
    "sha256:109d3a6614e046d232c017f274b629c418a479cfb319b421d8e6fabaabdd5524": "quality",
    "sha256:eae0700bcd738f27488e204d6490e978d0a6af8d0a59a72e7792498099a1173e": "documentation",
}


def diagnostic_quality(value):
    value = copy.deepcopy(object_value(value, "diagnosis.quality"))
    original_findings = copy.deepcopy(value.get("findings", []))
    findings = value.get("findings", [])
    if isinstance(findings, list):
        for row in findings:
            row = object_value(row, "QA finding")
            if row.get("disposition") == "unresolved":
                if not isinstance(row.get("owner"), str) or row.get("owner") not in {
                    "baseline",
                    "investigation",
                    "proposal",
                }:
                    raise BundleError(
                        "incompatible", "Unknown diagnostic correction owner"
                    )
                row["owner"] = "discovery" if row["owner"] == "baseline" else "draft"
    result = quality(value)
    if "unresolved_discovery" in result:
        result["unresolved_baseline"] = result.pop("unresolved_discovery")
        result["unresolved_proposal"] = result.pop("unresolved_draft")
        result["owner"] = {"discovery": "baseline", "draft": "investigation"}.get(
            result["owner"], result["owner"]
        )
        result["findings"] = original_findings
    return result


def conclusion(value):
    """Validate a declared recommendation, keeping its evidence and uncertainty visible."""
    value = object_value(value, "diagnosis.conclusion")
    cause, scope = value.get("cause"), value.get("scope")
    if (
        not isinstance(cause, str)
        or not isinstance(scope, str)
        or cause not in {"established", "no-work", "investigate-more", "blocked"}
        or scope not in {"task", "epic", "incomplete", "no-work"}
    ):
        raise BundleError(
            "invalid-input", "Diagnosis needs supported cause and scope values"
        )
    if (
        not isinstance(value.get("evidence"), list)
        or not value["evidence"]
        or any(not isinstance(row, str) or not row.strip() for row in value["evidence"])
    ):
        raise BundleError(
            "not-established", "Diagnostic conclusions need original evidence"
        )
    if cause == "no-work":
        if scope != "no-work" or value.get("expected_behavior_established") is not True:
            raise BundleError(
                "incompatible", "No-work requires evidence-backed expected behavior"
            )
    elif scope == "no-work":
        raise BundleError("incompatible", "An unexplained symptom is not no-work")
    if cause in {"blocked", "investigate-more"} and scope != "incomplete":
        raise BundleError("incompatible", "Unresolved diagnosis remains incomplete")
    if cause == "established" and value.get("causal_mechanism_established") is not True:
        raise BundleError(
            "not-established", "An established cause needs its causal evidence"
        )
    return copy.deepcopy(value)


def context(repository, assignment, phase):
    value = object_value(assignment["target"].get("diagnosis", {}), "target.diagnosis")
    result = {"phase": phase, "product_implementation": False, "next_owner": "Primary"}
    if "conclusion" in value:
        result["conclusion"] = conclusion(value["conclusion"])
    if "quality" in value:
        result["quality"] = diagnostic_quality(value["quality"])
    if phase == "documentation":
        proposal = value.get("proposal")
        approval = assignment["authority"].get("document_approval")
        if isinstance(proposal, dict) and proposal.get("no_change") is True:
            if (
                proposal.get("diff") != ""
                or proposal.get("targets") != {}
                or not (
                    isinstance(proposal.get("reason"), str)
                    and proposal["reason"].strip()
                )
            ):
                raise BundleError(
                    "invalid-input",
                    "No-change needs its explicit empty diff and reason",
                )
            status = "approval-required"
            if (
                isinstance(approval, dict)
                and approval.get("source") == "user"
                and approval.get("decision") == "approved"
            ):
                status = (
                    "approved-current"
                    if approval.get("proposal") == proposal
                    else "reapproval-required"
                )
                if status == "approved-current" and value.get("applied") is True:
                    status = "verified-applied"
            result["application"] = {"status": status, "no_change": True}
        elif proposal is None:
            result["application"] = {"status": "approval-required"}
        else:
            result["application"] = application(
                repository, proposal, approval, applied=value.get("applied") is True
            )
        if result["application"].get("status") == "reapproval-required":
            result["application"]["owner"] = "investigation"
    return result
