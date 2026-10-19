"""Choose Design Podway applicability before importing native or source helpers."""

from pathlib import Path

ENTRYPOINTS = {"new-feature", "new-project", "refactor"}


class EntryPointError(ValueError):
    code = "invalid-arguments"


def branch(repository, entrypoint, *, opt_out=False):
    """Run before native imports, inspection, source rendering or initialization."""
    if not isinstance(entrypoint, str) or entrypoint not in ENTRYPOINTS:
        if opt_out:
            raise EntryPointError(
                "Podway opt-out on this helper requires a Design entrypoint"
            )
        return None
    scope = Path(repository).expanduser().resolve()
    git_backed = any((parent / ".git").exists() for parent in (scope, *scope.parents))
    if opt_out or (entrypoint == "new-project" and not git_backed):
        return {
            "status": "podway-inapplicable",
            "reason": "explicit-opt-out" if opt_out else "non-git-new-project",
            "entrypoint": entrypoint,
            "dispatch": None,
            "next_owner": "Coordinator",
            "requirements": [
                "Original entrypoint artifacts and independent grouped assessment",
                "Approved upstream leaves and separate PM clipboard authority",
                "Exact document diff approval and current target snapshots",
                "Separate delivery-input commit authority; no product implementation",
            ],
        }
    return None
