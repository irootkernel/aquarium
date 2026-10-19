"""Current diagnostic evidence and approved documents; no product repair or QA execution."""

import copy

from adaptive_bundles import BundleError
from adaptive_design import application, object_value, quality

PHASES = {"baseline", "investigation", "proposal", "quality", "documentation"}
OPERATIONS = {
    "sha256:ca0eb2a9dca1d7d8f053736b051ff7d0210ba6fc47d717eaf646b40a16519ad5": "baseline",
    "sha256:5d8732f71031a0388c416d11454fc7e33d2536d0d23e54cb17e919fb0ec09177": "investigation",
    "sha256:9b06a322b31487a8cce1bf4cc2b6476013ade5506d6ca4d5a5c3be723c4db720": "proposal",
    "sha256:7f78ec7877ba135b591dcbb16b8b024daa00e81576e7524539f6ffdc01f70d85": "quality",
    "sha256:15d91150291a0cafba25f18d0fa074f4787d17208ca6e0782b711db94d1e7d30": "documentation",
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
    result = {
        "phase": phase,
        "product_implementation": False,
        "next_owner": "Coordinator",
    }
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
