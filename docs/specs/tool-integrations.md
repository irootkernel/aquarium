# Tool Integration Matrix

Aquarium deliberately supports a defined toolchain. A healthy component never proves another component healthy, and approval for one tool or effect never authorizes another.

| Tool | Aquarium role | Supported identity | Platform or prerequisite | Important readiness boundary |
| --- | --- | --- | --- | --- |
| Codex | Primary agent runtime, plugin host, goals, MCP registrations, and hooks | Host-provided supported Codex | Repository and user configuration | Plugin availability, trusted hook state, goals, and MCP exposure remain distinct |
| Dolgorae | Explicit setup and delegated operations; Independent Review does not use Dolgorae | Stable `v0.1.2` through `v0.1.x` | Optional native Apple Silicon macOS CLI; same-release `use-dolgorae` skill for delegated operations | CLI, paired skill, platform, file safety, version, and capabilities remain distinct |
| Herdr | Supervises a fresh requested static reviewer in the current local session | `>=v0.9.3`, no upper bound | Separately installed upstream `herdr` skill; selected-route caller context | Native compatibility, client, server, skill and reviewer readiness are separate; complete output and submission/activity correlation are required |
| Sanho | Commit inspection and optional documentation synchronization | Stable `v0.2.9` through `v0.2.x` | Matching optional `use-sanho` skill | CLI, skill, workspace enrollment, doctor state, and synchronization authority are independent |
| Mulgae | Multi-provider static review and structured finding projection | Stable `>=v0.1.24` | Native Apple Silicon macOS; Go `1.27.1+` only for installation | CLI, native configuration, provider readiness, MCP scope, capture publication, findings query, and extraction quality are separate |
| Gaori | Runs existing checks and compresses their output | Stable `v0.1.18` through `v0.1.x` | Repository tester schema v2 when configured | Child exit status is pass/fail authority; parser and summary quality do not create a gate |
| Sorage | Brokers local Handoffs and Project Memos | Stable `v0.1.2` through `v0.1.x` | Native Apple Silicon macOS; matching optional `use-sorage` skill | CLI, initialization, Vault health, Project binding, skill, ignore state, and broker authority remain distinct |
| Podway | Records Git-backed workflow goals, transitions, handoffs, and session lifecycle | Stable `>=v0.2.14`, no upper bound | Native Apple Silicon macOS; single Direct CLI | CLI identity, workspace, managed Procedures, current session, and optional skill are separate readiness axes |
| Ouroboros | Supplies interview, PM, Seed, and QA leaves for explicit design workflows | Stable `>=0.51.1` | Existing `uv`; exact package version for installation | CLI, Codex rules and skills, MCP runtime, effective registration, and live exposure are independent |
| Lora / Lore | Supplies `lore-commits` and `lore-query` skills | Latest stable tag, or disclosed full `main` SHA when no stable tag exists | Detached exact checkout and user-global Codex installation | Complete source and target trees must match; `lore-setup` is intentionally not installed |
| Deslop | Supplies task refinement cleanup | No release line; disclosed full current upstream SHA | Detached Cursor Team Kit checkout, npm, and preserved MIT license | Only upstream `deslop` is installed; Aquarium does not vendor or customize it |
| Humanizer | Final prose pass for English human-authored documentation | Stable `>=v2.11.1` | Exact detached checkout; upstream skill files at the documented default target, or `~/.agents/skills/humanizer` when no default is named | Installation and project guidance are separate; structural inspection alone cannot prove upstream freshness |
| im-not-ai | Final prose pass for Korean human-authored documentation | Stable `>=v2.3.2` | Exact selected Codex copy materialized in an isolated temporary `CODEX_HOME`, then installed in the active Codex skill root | `_workspace/` is removed after accepted text is applied; meaning and protected content must survive one fail-closed final pass |

## Installation and Freshness

Explicitly invoking `dev-setup-global` without a component list selects every supported user-global component; scoped continuations select only their named components. Automatic diagnosis includes disclosed official release, tag, and commit metadata. For Dolgorae, Sanho, Mulgae, Gaori, Sorage, and Podway, it also includes complete Git tree metadata and commit-pinned paired-skill files in ephemeral storage. Selected Lora or Deslop includes official npm metadata for the exact `skills` installer version. This lookup authority does not cover clone, archive download, upstream-code execution, installation, replacement, initialization, Project registration, unrelated endpoints, or provider requests. The shared tool catalog owns the exact sources and comparison procedure.

Every installation proposal identifies the exact source ref, target, network endpoints, files, checksums or digests, backup choice, expected mutation, and post-action verification. Existing modified or duplicate skill copies are never overwritten or deleted silently.

Humanizer and im-not-ai are diagnosed and updated by `dev-setup-global`; installation actions remain separately approved. `dev-setup-bundle` prepares each selected user-global payload once, while target-level tool selection and `agents_guidance` decide whether English, Korean, both, or neither final-pass rule appears in a repository proposal.

## MCP Scope

Mulgae and Gaori may use global or isolated project-local MCP registrations. Aquarium inspects global, local, and effective registrations independently and prefers global for ordinary use. A v2 bundle manifest may select either scope per target; local selection takes precedence over the default global list. Readiness requires the requested effective scope, so a valid registration shadowed by another scope is reported as a mismatch. A tool omitted from both lists has no requested MCP registration; any existing registration remains in place and may still expose tools. Registration removal or replacement retains its separate approval.

Ouroboros supports either a direct selected `ooo mcp serve` registration or the canonical isolated `uvx --isolated --python >=3.12 --from ouroboros-ai[mcp] ouroboros mcp serve` form with Codex selectors. A valid isolated registration is evaluated from its own launcher contract rather than the base CLI environment.

MCP registration correctness does not prove that the active Codex session has reloaded or exposes the expected tools. A restart may be required after skill or registration changes.

A v2 bundle target may also declare whether Mulgae's `artist` role is required. `true` requires artist alongside the six non-UI roles; `false` requires those six without artist. Setup compares the effective role selection with that intent and proposes a native configuration change under its existing approval boundary. The manifest does not select providers, models, credentials, or role assignments.

Sorage has no supported MCP surface. Its official CLI and `use-sorage` skill own requested Handoff and Project Memo operations.

## Sorage Readiness

Sorage is optional and does not join Aquarium's production-binary baseline. Its setup is ready only when a supported Apple Silicon CLI is initialized, the complete ordered v0.1 `doctor --json` catalog has no blocking check, the exact Git root resolves to an active `git_repository` Project binding, the repository root `.gitignore` matches `.sorage/` with a non-negated rule and no tracked or symlinked content exists, and the canonical `~/.agents/skills/use-sorage` path exists. Exact-upstream and same-tag skill validity belong to `dev-setup-global`. Doctor warnings do not block the minimal local profile.

A healthy supported CLI remains `installed` while these readiness conditions are incomplete. An unhealthy runtime, invalid command contract, or blocking doctor result is `degraded`, except that the exact uninitialized all-blocking catalog remains `installed` with `readiness_status: initialization_required`. Only complete readiness is `configured`.

Only a successful unregistered result uses `registration_required`. A valid native Project resolution failure keeps the CLI `installed` with `readiness_status: resolution_error`; it cannot enter the Project creation or binding path.

Unless Project setup was explicitly requested, diagnosis reports `registration_required` and stops before Project listing or a registration proposal.

Global inventory first checks the Sorage version and paired skill without opening repository state. Before v0.1.2 opens an existing pre-Memo installation, follow the upstream upgrade procedure: stop old writers, verify and retain a format-1 backup, and prove its restore in a separate empty installation. A v0.1.2 executable alone does not establish that preparation or migration occurred.

Outside Plan Mode, disclose native database and journal effects before requesting `--include-sorage-initialization` or repository `--include-sorage` diagnosis. Each inspector checks the selected database schema first. It runs doctor for a missing or empty home or an already migrated database. For a pre-Memo database, it checks the configuration ID against the Vault marker and recorded database IDs, then calls native `config validate`. A valid matching installation returns `upgrade_preflight_required`; after the owner confirms the preflight, `--sorage-upgrade-preflight-complete` returns `upgrade_migration_required` without running doctor. Recheck the exact installation identity immediately before the separately approved native `sorage init --reconfigure --non-interactive --json`, then rerun diagnosis after migration.

A missing database in a nonempty home or an incomplete or mismatched configuration returns `installation_recovery_required`. An unverifiable database returns `upgrade_state_unverifiable`; neither state opens doctor. Repository diagnosis resolves the Project only when doctor has no blocking check. These commands make no network request, but native commands may update the local database or journal.

`dev-setup-global` uses `sorage init --non-interactive --json` as the separately approved default initialization. It does not enable the daemon, LaunchAgent, Vault Git repository, backup schedule, or remote push. `dev-setup` owns explicitly requested Project setup, including exact identity confirmation, Project creation, binding or rebind, and a fresh resolution check. Archive and unarchive use the implicit User actor in v0.1.2. It also owns separately approved root `.gitignore` preparation whenever Sorage readiness is diagnosed. An effective per-target `sorage` selection in an explicitly supplied `dev-setup-bundle` manifest counts as a Project setup request for that target. An optional target slug identifies the intended Project and is compared with native resolution; a different existing binding is a mismatch, while listing and mutation still require their separate approvals. Aquarium never falls back to `--allow-unregistered` and never reads Handoff or Memo content during setup.

For an explicit broker operation, Aquarium loads the release-matched `use-sorage` skill and supported CLI without requiring current repository setup readiness. An inbox or outbox request checks only that list and does not authorize Handoff processing or Memo discovery. Explicit Memo requests use the same-release skill; an explicit `--project` or Memo ID does not require a current-directory Project binding. Memo add or list without an explicit Project or all-project scope still uses native current-directory resolution. Memo text grants no execution authority, and closing one does not complete a roadmap task or another tool's lifecycle. Within requested sender processing, that skill reads the current Review Note before revision and may read the bounded event timeline when needed. It owns every fetch, review, revision, acceptance, retention, deletion, backup, and Vault operation. The managed Vault and derived `.sorage/INBOX.md` remain native Sorage state, not repository authority or Aquarium workflow evidence.

## Podway Readiness

The supported Podway version floor is stable `>=v0.2.14` without an upper bound, on native Apple Silicon macOS. The paired `use-podway` tree retains its independent full release-commit pin in the [Podway catalog](../../plugins/aquarium/references/tool-catalog.md#podway). Runtime upgrades leave that pin unchanged.

Global inspection validates the single CLI's compact version and Output v4/version-result v2 identity without opening a workspace. Repository readiness additionally requires a healthy writer-compatible workspace, tracked regular non-symlink configuration and all five managed Procedures with native validity and compatible handler structure. Preserve same-ID customizations, and report source provenance and handler compatibility separately.

Observation and status use v5 for direct and delegated Procedures. Native Error v2 codes determine recovery. Version eligibility does not prove these contracts or selected-route membership. Session conflicts and terminal disposition belong to the owning workflow or the pinned runtime skill.

The exact official v0.2.14 compatibility gate runs one CLI in disposable Git fixtures. It retains the full Procedure scenario inventory, validates successful outcome lookup and exact replay, and verifies fenced workspace-removal rejection and already-absent readback under workspace-removal-result v2. No daemon, runtime mode or account registry participates. Candidate installation and installed-skill functional verification remain separate UTM evidence.

Legacy and incompatible writer state remains unchanged on refusal. The [upgrade contract](../../plugins/aquarium/references/tool-catalog.md#upgrade-from-older-writers) owns the original-writer, separate service-retirement and explicit destructive-reset boundaries. Reset establishes fresh runtime history; it does not convert or preserve old sessions.

Installed qualification for the v0.2.14 adoption covers explicit skill-path execution through authenticated Codex, fresh private Codex discovery and session-scoped Claude discovery. Authenticated private-plugin namespace dispatch, Claude provider execution and complete managed Worker/Judge runs remain unqualified for the combined v0.1.19 release.

## Review and Check Adapters

Mulgae execution and exact recovery follow the [shared Mulgae review contract](../../plugins/aquarium/references/mulgae-review-contract.md) and the same-release `use-mulgae` skill loaded by the agent that performs the operation. User-global setup admits the stable v0.1.24 release floor and supported platform without claiming repository contract verification. Repository setup additionally requires command-result v18 or later, Doctor v5 or later, and the release's native supported configuration. Review execution requires preflight v7 or later, independent project binding, paired execution guards, and receipt-bound result reads through the paired skill. Setup performs no review, recovery, or cleanup writes.

Independent Review uses three fresh host-native Codex subagents for one selected exact target and shared Review Brief. It can be invoked standalone or selected in Task, Epic, and validation workflows in place of Mulgae or Herdr. It requires fresh host delegation, retains all three role reports and host provenance, and carries no implied Dolgorae, Mulgae, or Herdr lifecycle guarantees.

Profile selection is explicit and user-global; readiness uses offline diagnostics through the same-release `use-dolgorae` skill. Reusable Specialist requests follow that skill's External Specialist Engagement facade and the [Dolgorae consumer contract](../../plugins/aquarium/references/dolgorae-review-contract.md#reusable-specialist-requests). General Run and Brokered Hierarchy availability remains capability-dependent.

Dolgorae may separately publish an `aquarium-dev` generation for explicit development commands, but Aquarium creates no production runtime copy and Herdr Review does not use Dolgorae.

Aquarium production-binary readiness requires supported global Podway, Mulgae, and Gaori executables. A missing required executable fails closed and routes to the tool-scoped `$aquarium:dev-setup-global` workflow. Dolgorae and Sanho are explicitly optional and do not fail this binary baseline. Development generations never satisfy production readiness.

Mulgae review is advisory. Embedded and standalone callers supply the shared purpose and Review Brief while the loaded `$use-mulgae` skill owns native capture, execution, waiting, recovery, publication, and retention. Aquarium preserves one started operation and does not add a status-polling or liveness loop. It requires complete capture coverage, passing CI decision, committed publication, a successful findings query, zero locally verified unresolved findings, and no unmet or unverified completion criterion before approving completion.

Gaori is optional evidence compression around a repository-owned command. The agent performing the check loads `use-gaori`, which owns native execution and waiting. Its independent `use-gaori-status` skill explains native read-only statistics and estimates; a timing query preserves an existing await and does not create a recurring observation loop. The [Gaori integration contract](../../plugins/aquarium/references/gaori-integration.md) separates the authorized command result, Gaori execution and extraction status, and Aquarium acceptance. Extraction quality does not rewrite a child result, but an internal error or missing required evidence cannot establish successful verification.

Herdr Review uses one fresh explicitly requested native reviewer in the current local Herdr session. It accepts staged, HEAD, commit and range targets through the shared static contract; workspace and dirty remain unsupported. The upstream skill owns pane and agent operations, prompt submission, waiting, output and recovery. Admission requires actual reviewer identity, submission/activity correlation, applicable target and Brief, and a complete purpose-specific report. Timeout, stalled submission or unknown state preserves that operation; never blindly resend or replace it. Close only the pane this review created after successful admission and evidence recording. Reports keep findings, criterion assessment, verification gaps, operational deviations and native operation status separate, with `backend-check-result=not-provided`. Source and Git state remain read-only; permitted external or Git-ignored review output is a review aid. The migration contract owns selected-route setup and preserved legacy state; structural validation does not establish observed native/manual qualification.

The [Herdr migration runbook](../ops/herdr-migration.md) connects selected-route
readiness with preserved legacy sources, customizations and immutable snapshots.
Repository updates require an exact approved diff; active or uncertain legacy
workers require authoritative settlement before another review. Current source
identity, native validity, handler compatibility and route readiness remain
separate checks. Observed native/manual qualification follows the
[implementation guide](../implementation-tips/qualifying-herdr-review.md) and
the separate functional verification contract in [`TESTING.md`](../../TESTING.md).

Ouroboros installs its CLI once per user and its rules, skills, and MCP registration separately in each Codex home. Global setup proposes all discovered homes, compares official release metadata, and reports current-home and all-home readiness separately. Shared Ouroboros skills are legacy migration candidates. Each configured home must bind its MCP launcher to itself and use the approved package version; live execution remains separate evidence.
