# Tool Integration Matrix

Aquarium deliberately supports a defined toolchain. A healthy component never proves another component healthy, and approval for one tool or effect never authorizes another.

| Tool | Aquarium role | Supported identity | Platform or prerequisite | Important readiness boundary |
| --- | --- | --- | --- | --- |
| Codex | Primary agent runtime, plugin host, goals, MCP registrations, and hooks | Host-provided supported Codex | Repository and user configuration | Plugin availability, trusted hook state, goals, and MCP exposure remain distinct |
| Dolgorae | Immutable source capture and checked Independent Review lifecycle | Official stable `v0.1.2` through `v0.1.x`; dynamic release identity, machine envelope v2, and v0.1.2-compatible capabilities | Native Apple Silicon macOS; same-release `use-dolgorae` skill for delegated operations | Release metadata, archive, installed bytes, machine version, capability digest, paired-skill readiness, and guarded review admission remain distinct |
| Orca | Launches and supervises the requested static reviewer in a fresh session | No Aquarium release floor declared | Separately installed local Orca runtime | Run, Task, Dispatch, worker, Delivery, acknowledgement, and settlement must all be observed |
| Sanho | Commit inspection and optional documentation synchronization | Stable `v0.2.7` through `v0.2.x` | Matching optional `use-sanho` skill | CLI, skill, workspace enrollment, doctor state, and synchronization authority are independent |
| Mulgae | Multi-provider static review and structured finding projection | Stable `v0.1.21` through `v0.1.x` | Native Apple Silicon macOS; Go `1.26.6+` only for installation | CLI, Config v3, provider readiness, MCP scope, capture publication, findings query, and extraction quality are separate |
| Gaori | Runs existing checks and compresses their output | Stable `v0.1.16` through `v0.1.x` | Repository tester schema v2 when configured | Child exit status is pass/fail authority; parser and summary quality do not create a gate |
| Sorage | Brokers local document handoffs between registered projects | Stable `v0.1.1` through `v0.1.x` | Native Apple Silicon macOS; matching optional `use-sorage` skill | CLI, initialization, Vault health, Project binding, skill, ignore state, and Handoff authority remain distinct |
| Podway | Records Git-backed workflow goals, transitions, handoffs, and session lifecycle | Stable `v0.2.9` through `v0.2.x` | Native Apple Silicon macOS; matching CLI and daemon | CLI, daemon, workspace, managed Procedures, current session, and optional skill are separate readiness axes |
| Ouroboros | Supplies interview, PM, Seed, and QA leaves for explicit design workflows | `>=0.51.1,<0.54.0` | Existing `uv`; exact package version for installation | CLI, Codex rules and skills, MCP runtime, effective registration, and live exposure are independent |
| Lora / Lore | Supplies `lore-commits` and `lore-query` skills | Latest stable tag, or disclosed full `main` SHA when no stable tag exists | Detached exact checkout and user-global Codex installation | Complete source and target trees must match; `lore-setup` is intentionally not installed |
| Deslop | Supplies task refinement cleanup | No release line; disclosed full current upstream SHA | Detached Cursor Team Kit checkout, npm, and preserved MIT license | Only upstream `deslop` is installed; Aquarium does not vendor or customize it |
| Humanizer | Final prose pass for English human-authored documentation | Exact supported release `v2.11.1` | Exact detached checkout; `SKILL.md` and LICENSE at `~/.agents/skills/humanizer` | Installation and project guidance are separate; structural inspection alone cannot prove upstream freshness |
| im-not-ai | Final prose pass for Korean human-authored documentation | Exact supported release `v2.3.2` | Official Codex copy materialized in an isolated temporary `CODEX_HOME`, then installed in the active Codex skill root | `_workspace/` is removed after accepted text is applied; meaning and protected content must survive one fail-closed final pass |

## Installation and Freshness

Explicitly invoking `dev-setup-global` without a component list selects every supported user-global component and authorizes its bounded official metadata and raw-file freshness reads. A scoped continuation selects only its named components. Dolgorae uses official GitHub Release metadata; Dolgorae, Sanho, Mulgae, Gaori, Sorage, and Podway also compare their public upstream paired-skill files. Neither path authorizes installation, replacement, initialization, Project registration, another network endpoint, or any provider request.

Every installation proposal identifies the exact source ref, target, network endpoints, files, checksums or digests, backup choice, expected mutation, and post-action verification. Existing modified or duplicate skill copies are never overwritten or deleted silently.

Humanizer and im-not-ai are diagnosed and updated by `dev-setup-global`; installation actions remain separately approved. `dev-setup-bundle` prepares each selected user-global payload once, while target-level tool selection and `agents_guidance` decide whether English, Korean, both, or neither final-pass rule appears in a repository proposal.

## MCP Scope

Mulgae and Gaori may use global or isolated project-local MCP registrations. Aquarium inspects global, local, and effective registrations independently, prefers global for ordinary use, and preserves a local registration only when the user confirms that scope.

Ouroboros supports either a direct selected `ooo mcp serve` registration or the canonical isolated `uvx --isolated --python >=3.12 --from ouroboros-ai[mcp] ouroboros mcp serve` form with Codex selectors. A valid isolated registration is evaluated from its own launcher contract rather than the base CLI environment.

MCP registration correctness does not prove that the active Codex session has reloaded or exposes the expected tools. A restart may be required after skill or registration changes.

Sorage has no supported MCP surface. Its official CLI and `use-sorage` skill own discovery of requested documents and Handoff operations.

## Sorage Readiness

Sorage is optional and does not join Aquarium's production-binary baseline. Its setup is ready only when a supported Apple Silicon CLI is initialized, the complete ordered v0.1 `doctor --json` catalog has no blocking check, the exact Git root resolves to an active `git_repository` Project binding, the repository root `.gitignore` matches `.sorage/` with a non-negated rule and no tracked or symlinked content exists, and the canonical `~/.agents/skills/use-sorage` path exists. Exact-upstream and same-tag skill validity belong to `dev-setup-global`. Doctor warnings do not block the minimal local profile.

A healthy supported CLI remains `installed` while these readiness conditions are incomplete. An unhealthy runtime, invalid command contract, or blocking doctor result is `degraded`, except that the exact uninitialized all-blocking catalog remains `installed` with `readiness_status: initialization_required`. Only complete readiness is `configured`.

Only a successful unregistered result uses `registration_required`. A valid native Project resolution failure keeps the CLI `installed` with `readiness_status: resolution_error`; it cannot enter the Project creation or binding path.

Unless Project setup was explicitly requested, diagnosis reports `registration_required` and stops before Project listing or a registration proposal.

Global inventory checks the Sorage version and paired skill without opening repository state. Outside Plan Mode, `dev-setup-global` discloses the native open-and-migrate side effect before adding `--include-sorage-initialization` to run `sorage doctor`; this applies to both unscoped diagnosis and a scoped Sorage continuation. Repository `--include-sorage` diagnosis runs doctor and, when doctor has no blocking check, Project resolution only outside Plan Mode. These commands make no network request, but the native open-and-migrate path may update the local database or journal.

`dev-setup-global` uses `sorage init --non-interactive --json` as the separately approved default initialization. It does not enable the daemon, LaunchAgent, Vault Git repository, backup schedule, or remote push. `dev-setup` owns explicitly requested Project setup, including exact identity confirmation, Project creation or binding, and a fresh resolution check. It also owns separately approved root `.gitignore` preparation whenever Sorage readiness is diagnosed. An effective per-target `sorage` selection in an explicitly supplied `dev-setup-bundle` manifest counts as a Project setup request for that target, but Project listing and mutation still require their separate approvals. Aquarium never falls back to `--allow-unregistered` and never reads Handoff content during setup.

After readiness, Aquarium loads and invokes `use-sorage` only for an explicit broker operation. An inbox or outbox request checks only that list and does not authorize Handoff processing. Within requested sender processing, the same-release skill reads the current Review Note before revision and may read the bounded event timeline when needed. It owns every fetch, review, revision, acceptance, retention, deletion, backup, and Vault operation. The managed Vault and derived `.sorage/INBOX.md` remain native Sorage state, not repository authority or Aquarium workflow evidence.

## Podway Readiness

The CLI and daemon use the same supported release tag. The paired skill uses the independent full commit pinned by the [Podway catalog](../../plugins/aquarium/references/tool-catalog.md#podway), which owns the exact source, complete payload comparison, and replacement policy. A later runtime release does not automatically replace that skill pin.

Aquarium readiness requires a supported stable CLI and matching daemon, a healthy initialized workspace, tracked `.podway/config.yaml` and `.podway/.gitignore`, and all five managed Procedure paths as tracked regular non-symlink files with the expected filename and Procedure ID that pass `procedure check --warnings-as-errors`. Each file may contain canonical bytes or a Podway-valid same-ID local customization, but it must also expose the structural nodes, evidence items, and routes required by its current Aquarium handlers. Inspection reports native source validity and handler compatibility separately and never overwrites a customization.

Both inspectors use the catalog's fixed 120-second production-mode `daemon wait-ready` probe with at least five seconds of process-exit headroom. A healthy result requires a matching CLI and daemon version and a `podway.daemon-status-result/v3` payload with `mode=prod`, a supported Apple Silicon target, reachability, running status, readiness state and stage set to `ready`, null or bounded activity counts, and a closed recovery inventory whose completed count equals its total. A nonzero failed count may represent quarantined completed recovery and does not by itself degrade readiness. A prepared, running, incomplete, or undisposed terminal session is a lifecycle conflict owned by the matching workflow or `$use-podway`, not a setup repair.

The exact v0.2.5 compatibility transformation is migration evidence only. Any other source mismatch is divergence, and an active Procedure snapshot is never migrated in place.

Podway workspace removal is a separately authorized lifecycle operation owned by the `use-podway` skill pinned in the shared tool catalog. Aquarium setup and managed workflows never infer that authority from an opt-out, missing session, stale registry entry, or readiness problem. The first removal must identify `podway.workspace-removal-result/v1`, delete only the selected worktree's complete `.podway` tree, and preserve the Git worktree. The v0.2.9 compatibility gate requires an immediate identical replay to succeed with a null workspace UUID, both removal flags false, and `already_absent=true`. It independently verifies the absent registry entry and `.podway` tree; the former v0.2.8 error exception is rejected.

Moving an initialized workspace between Podway runtime modes requires separate authorization and belongs to the `use-podway` skill pinned in the shared tool catalog. Aquarium setup and managed workflows may diagnose a mode mismatch but never run `workspace mode plan` or `workspace mode apply`. The handoff must name the exact worktree and target mode. It must also disclose that apply rewrites tracked `.podway/config.yaml` and deletes all current and archived runtime history. Keep the fresh plan token private, require a separate approval immediately before apply, and re-observe the target-mode workspace after apply or exact replay. Report the tracked configuration change for a separate Git decision.

## Review and Check Adapters

Mulgae execution and exact recovery follow the [shared Mulgae review contract](../../plugins/aquarium/references/mulgae-review-contract.md) and the same-release `use-mulgae` skill. Setup consumes command-result v8 with Doctor v2 and performs no review, recovery, or cleanup writes.

Independent Review resolves `dolgorae` from the current PATH and requires an official global stable v0.1.x installation at or above v0.1.2. It verifies official release metadata once at review start, freezes the release and local candidate identity, then revalidates the path, file identity, executable bytes, machine version, and compatible capabilities before each source-bearing operation without another network lookup.

Profile selection is explicit and user-global; readiness uses offline diagnostics through the same-release `use-dolgorae` skill. Reusable Specialist requests follow that skill's External Specialist Engagement facade and the [Dolgorae consumer contract](../../plugins/aquarium/references/dolgorae-review-contract.md#reusable-specialist-requests). General Run and Brokered Hierarchy availability remains capability-dependent.

Dolgorae may separately publish an `aquarium-dev` generation for explicit development commands, but Aquarium creates no production runtime copy, Independent Review never consumes that generation, and Orca Review does not use Dolgorae.

Aquarium production-binary readiness requires supported global Podway, Mulgae, Gaori, and Dolgorae executables. A missing required executable fails closed and routes to the tool-scoped `$aquarium:dev-setup-global` workflow. Sanho is explicitly optional and does not fail this binary baseline. Development generations never satisfy production readiness.

Mulgae review is advisory. Aquarium requires complete capture coverage, passing CI decision, committed publication, a successful findings query, and zero locally verified unresolved findings before calling review clean.

Gaori is optional evidence compression around a repository-owned command. Its independent `use-gaori-status` skill explains native read-only statistics and estimates; a timing query preserves an existing await and does not create a recurring observation loop. The [Gaori integration contract](../../plugins/aquarium/references/gaori-integration.md) separates the authorized command result, Gaori execution and extraction status, and Aquarium acceptance. Extraction quality does not rewrite a child result, but an internal error or missing required evidence cannot establish successful verification.

Orca Review launches one fresh requested native reviewer through Orca in the current registered worktree. It accepts staged, HEAD, commit, and range targets; staged means the live `HEAD`-to-index change read through `git diff --cached`. Workspace and dirty targets still require Independent Review. Tests, authentication, unrequested reviewer changes, source or tracked and non-ignored worktree writes, commits, and publication are outside the static review authorization. All Orca reviewers may create or update review-related temporary files, native session state, tool output, and reports outside the worktree or in Git-ignored runtime paths within it, such as ignored files under `.omc/`. External locations include `/tmp`, `/private/tmp`, or provider-owned directories. They return the paths of retained report files used to deliver the result. Permitted external files and ignored runtime writes do not require warnings, extra checks, approval, or another review.

Ouroboros installs its CLI once per user and its rules, skills, and MCP registration separately in each Codex home. Global setup proposes all discovered homes, compares official release metadata, and reports current-home and all-home readiness separately. Shared Ouroboros skills are legacy migration candidates. Each configured home must bind its MCP launcher to itself and use the approved package version; live execution remains separate evidence.
