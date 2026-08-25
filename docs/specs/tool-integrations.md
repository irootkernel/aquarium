# Tool Integration Matrix

Aquarium deliberately supports a defined toolchain. A healthy component never proves another component healthy, and approval for one tool or effect never authorizes another.

| Tool | Aquarium role | Supported identity | Platform or prerequisite | Important readiness boundary |
| --- | --- | --- | --- | --- |
| Codex | Primary agent runtime, plugin host, goals, MCP registrations, and hooks | Host-provided supported Codex | Repository and user configuration | Plugin availability, trusted hook state, goals, and MCP exposure remain distinct |
| Orca | Supervises selected non-Codex static reviewers | No Aquarium release floor declared | Separately installed local Orca runtime | Run, Task, terminal, provider process, and report settlement must all be observed |
| Sanho | Commit inspection and optional documentation synchronization | Stable `v0.2.7` through `v0.2.x` | Matching optional `use-sanho` skill | CLI, skill, workspace enrollment, doctor state, and synchronization authority are independent |
| Mulgae | Multi-provider static review and structured finding projection | Stable `v0.1.18` through `v0.1.x` | Native Apple Silicon macOS; Go `1.26.6+` only for installation | CLI, Config v3, provider readiness, MCP scope, capture publication, findings query, and extraction quality are separate |
| Gaori | Runs existing checks and compresses their output | Stable `v0.1.14` through `v0.1.x` | Repository tester schema v2 when configured | Child exit status is pass/fail authority; parser and summary quality do not create a gate |
| Podway | Records Git-backed workflow goals, transitions, handoffs, and session lifecycle | Stable `v0.2.6` through `v0.2.x` | Native Apple Silicon macOS; matching CLI and daemon | CLI, daemon, workspace, managed Procedures, current session, and optional skill are separate readiness axes |
| Ouroboros | Supplies interview, PM, Seed, and QA leaves for explicit design workflows | `>=0.51.1,<0.52.0` | Existing `uv`; exact package version for installation | CLI, Codex rules and skills, MCP runtime, effective registration, and live exposure are independent |
| Lora / Lore | Supplies `lore-commits` and `lore-query` skills | Latest stable tag, or disclosed full `main` SHA when no stable tag exists | Detached exact checkout and user-global Codex installation | Complete source and target trees must match; `lore-setup` is intentionally not installed |
| Deslop | Supplies task refinement cleanup | No release line; disclosed full current upstream SHA | Detached Cursor Team Kit checkout, npm, and preserved MIT license | Only upstream `deslop` is installed; Aquarium does not vendor or customize it |

## Installation and Freshness

For Sanho, Mulgae, Gaori, and Podway, selecting the tool in `dev-setup` authorizes a bounded freshness comparison against official GitHub Releases metadata and four public upstream skill files. It does not authorize installation, replacement, another network endpoint, or any provider request.

Every installation proposal identifies the exact source ref, target, network endpoints, files, checksums or digests, backup choice, expected mutation, and post-action verification. Existing modified or duplicate skill copies are never overwritten or deleted silently.

## MCP Scope

Mulgae and Gaori may use global or isolated project-local MCP registrations. Aquarium inspects global, local, and effective registrations independently, prefers global for ordinary use, and preserves a local registration only when the user confirms that scope.

Ouroboros supports either a direct selected `ooo mcp serve` registration or the canonical isolated `uvx --isolated --python >=3.12 --from ouroboros-ai[mcp] ouroboros mcp serve` form with Codex selectors. A valid isolated registration is evaluated from its own launcher contract rather than the base CLI environment.

MCP registration correctness does not prove that the active Codex session has reloaded or exposes the expected tools. A restart may be required after skill or registration changes.

## Podway Readiness

Aquarium readiness requires a supported stable CLI and matching daemon, a healthy initialized workspace, tracked `.podway/config.yaml` and `.podway/.gitignore`, and all five managed Procedure files as regular non-symlink byte-identical copies that pass `procedure check --warnings-as-errors`.

Daemon status v2 is healthy only when readiness state and stage are `ready` and worktree recovery is closed with no failures. A prepared, running, incomplete, or undisposed terminal session is a lifecycle conflict owned by the matching workflow or `$use-podway`, not a setup repair.

The exact v0.2.5 compatibility transformation is migration evidence only. Any other source mismatch is divergence, and an active Procedure snapshot is never migrated in place.

## Review and Check Adapters

Mulgae review is advisory. Aquarium requires complete capture coverage, passing CI decision, committed publication, a successful findings query, and zero locally verified unresolved findings before calling review clean.

Gaori is optional evidence compression around a repository-owned command. The original command, its authorization, and its exit status remain authoritative; parser detection or summary extraction never changes the result.

Orca reviewers receive one exact target and relevant authority. Dirty content, tests, authentication, provider changes, edits, commits, and publication are outside the static review authorization.
