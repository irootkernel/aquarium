# Local Interfaces

Aquarium ships declarative skill contracts, Podway Procedure definitions, local structural inspectors, one commit hook, and verification helpers. JSON schema identifiers are compatibility surfaces for their owning workflows.

## Managed Podway Procedures

| Procedure ID | Version | Owner | Recorded lifecycle |
| --- | --- | --- | --- |
| `aquarium-task-v2` | `4` | `task-handler` | Plan, implementation, refinement, typed verification, phase-owned Mulgae review, goal assessment, approval, and closeout |
| `aquarium-goal-v2` | `5` | `epic-handler` | One member task, pre-validation remediation, or epic closeout goal with pre-decision hardening evidence |
| `aquarium-validation-v2` | `6` | `epic-handler` and `epic-validator` | Baseline, guarded audit, remediation, re-audit, bounded review decisions, disposition, assessment, and closeout |
| `aquarium-design-v2` | `2` | `new-project`, `new-feature`, `refactor`, and `design-qa` | Context, discovery, draft, challenge, guarded phase-owner quality, approval, application, assessment, and closeout |
| `aquarium-war-room-v2` | `2` | `war-room` | Baseline or reproduction, investigation, semantic cause and scope decisions, guarded proposal quality, approval, documentation, assessment, and closeout |

Procedure source bytes live under [`plugins/aquarium/assets/podway/procedures/`](../../plugins/aquarium/assets/podway/procedures/). The version belongs to the Procedure document, not the Aquarium plugin version, and an active session retains the immutable snapshot with which it started.

## Inspectors and Helpers

| Entrypoint | Input | Success schema | Behavior |
| --- | --- | --- | --- |
| `dev-setup/scripts/inspect_tools.py` | Absolute repository plus optional component flags | `aquarium-dev-setup-inspection.v10` | Read-only normalized Git, tool, skill, MCP, configuration, same-ID Podway-valid customization, and bounded readiness inspection |
| `docs-setup/scripts/inspect_docs.py` | Exact absolute Git root | `aquarium-docs-inspection/v2` | Minimal read-only discovery of documentation roles, explicit roadmap units and lifecycle links, exclusions, and unambiguous structural conflicts |
| `test-setup/scripts/inspect_testing.py` | Exact absolute Git root | `aquarium-test-setup-inspection.v1` | Static Make/Bun test-contract discovery without executing project code |
| `dev-setup-bundle/scripts/normalize_manifest.py` | External `aquarium.dev-setup-bundle/v1` YAML manifest | `aquarium-dev-setup-bundle-plan.v1` | Validates, canonicalizes, and deduplicates explicit repository setup selections |
| `independent-review/scripts/inspect_review_target.py` | Repository and one staged, HEAD, commit, or range selector | `aquarium-independent-review-target/v1` | Resolves exact Git objects, dirty boundaries, and target metadata without reviewing source |
| `orca-review/scripts/create_provider_terminal.py` | `aquarium-orca-provider-terminal-request/v1` JSON on standard input | `aquarium-orca-provider-terminal-result/v1` | Creates one provider terminal through the local Orca CLI after request validation |
| `release-handler/scripts/inspect_release_notes.py` | Repository, expected version, and release baseline | `aquarium-release-notes-inspection/v1` | Inventories cumulative release-note enrollment and candidate delta |
| `release-handler/scripts/inspect_publication_state.py` | `aquarium-release-publication-observation/v4` JSON on standard input | `aquarium-release-publication-state/v4` | Normalizes local, remote, tag, stable hosted Release, and exact or approved QA-neutral candidate binding supplied by the caller |
| `tests/verify_podway_compatibility.py` | `PODWAY_BIN` selected by the Make target | `aquarium-podway-compatibility.v2` | Executes the exact v0.2.6 CLI and sibling daemon against all managed Procedures, declaration-limit failures, and two fresh isolated runtime passes |

Every inspector also has a versioned error schema where applicable. Consumers use normalized fields and reason codes rather than parsing human stderr or exposing raw configuration and credential material.

## Roadmap Commit Hook

`plugins/aquarium/hooks/task_commit_gate.py` is a trusted local Codex PreToolUse guard for direct shell `git commit` commands. It resolves the Git root, inventories tracked roadmap candidates, and denies a direct commit when an active roadmap lifecycle requires the `AQUARIUM_COMMIT_GATE=task-commit-v1` marker.

The hook is advisory rather than a security boundary. Indirect commits may bypass it, and the marker does not prove task ownership, correct lifecycle transition, safe staging, or user authorization; `task-commit` remains responsible for those checks.

## Interface Change Rules

- Change a schema identifier when a consumer-visible JSON contract changes incompatibly; update every consumer and fixture in the same change.
- Preserve structured error envelopes and nonzero exits for invalid arguments, unsafe paths, unsupported versions, malformed external output, and unverifiable authority.
- Keep inspection read-only and bounded. Mutation belongs to the owning skill after an exact proposal and approval.
- Treat a green parser or schema validator as proof of only that structural contract; add scenario coverage for approval, lifecycle, ownership, and handoff behavior.
