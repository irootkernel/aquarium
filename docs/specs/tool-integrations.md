# Tool Integration Matrix

Aquarium deliberately supports a defined toolchain. A healthy component never proves another component healthy, and approval for one tool or effect never authorizes another.

| Tool | Aquarium role | Supported identity | Platform or prerequisite | Important readiness boundary |
| --- | --- | --- | --- | --- |
| Codex | Coordinator agent runtime, plugin host, goals, MCP registrations, and hooks | Host-provided supported Codex | Repository and user configuration | Plugin availability, trusted hook state, goals, and MCP exposure remain distinct |
| Dolgorae | Explicit setup and delegated operations; Subagent Review does not use Dolgorae | Stable `v0.1.2` through `v0.1.x` | Optional native Apple Silicon macOS CLI; same-release `use-dolgorae` skill for delegated operations | CLI, paired skill, platform, file safety, version, and capabilities remain distinct |
| Herdr | Supervises a fresh requested static reviewer in the current local session | `>=v0.9.3`, no upper bound | Separately installed upstream `herdr` skill; selected-route caller context | Native compatibility, client, server, skill and reviewer readiness are separate; complete output and submission/activity correlation are required |
| Sanho | Commit inspection and optional documentation synchronization | Stable `v0.2.10` through `v0.2.x` | Matching optional `use-sanho` skill | CLI, skill, workspace enrollment, doctor state, and synchronization authority are independent |
| Mulgae | Multi-provider static review and structured finding projection | Stable `>=v0.1.27` | Native Apple Silicon macOS; Go `1.27.1+` only for installation | CLI, native configuration, provider readiness, MCP scope, source evidence publication, findings query, and extraction quality are separate; live reviews also require the selected `HAEPARI_HOME` and native `mulgae-review` readiness |
| Gaori | Runs existing checks and compresses their output | Stable `v0.1.20` through `v0.1.x` | Repository tester schema v2 when configured | Child exit status is pass/fail authority; parser and summary quality do not create a gate |
| Sorage | Brokers local Handoffs, Project Memos and Channels | Stable `v0.1.4` through `v0.1.x` | Native Apple Silicon macOS; matching optional `use-sorage` skill | CLI, initialization, Vault health, Project binding, skill, ignore state, and broker authority remain distinct |
| Podway | Records Git-backed workflow goals, transitions, handoffs, and session lifecycle | Stable `>=v0.2.16`, no upper bound | Native Apple Silicon macOS; single Direct CLI | CLI identity, workspace, managed Procedures, current session, and optional skill are separate readiness axes |
| Ouroboros | Supplies interview, PM, Seed, and QA leaves for explicit design workflows | Stable `>=0.51.1` | Existing `uv`; exact package version for installation | CLI, Codex rules and skills, MCP runtime, effective registration, and live exposure are independent |
| Lora / Lore | Supplies `lore-commits` and `lore-query` skills | Latest stable tag, or disclosed full `main` SHA when no stable tag exists | Detached exact checkout and user-global Codex installation | Complete source and target trees must match; `lore-setup` is intentionally not installed |
| Deslop | Supplies task refinement cleanup | No release line; disclosed full current upstream SHA | Detached Cursor Team Kit checkout, npm, and preserved MIT license | Only upstream `deslop` is installed; Aquarium does not vendor or customize it |
| Humanizer | Final prose pass for English human-authored documentation | Stable `>=v2.11.1` | Exact detached checkout; upstream skill files at the documented default target, or `~/.agents/skills/humanizer` when no default is named | Installation and project guidance are separate; structural inspection alone cannot prove upstream freshness |
| im-not-ai | Final prose pass for Korean human-authored documentation | Stable `>=v2.3.2` | Exact selected Codex copy materialized in an isolated temporary `CODEX_HOME`, then installed in the active Codex skill root | `_workspace/` is removed after accepted text is applied; meaning and protected content must survive one fail-closed final pass |
| Haepari | Managed local/UTM Jobs and advisory locks for Aquarium's VM verification; optional setup, with the managed release-policy path qualified by TASK-090 | Stable `v0.1.0` through `v0.1.x`; every release passes the exact archive verification the [tool catalog](../../plugins/aquarium/references/tool-catalog.md#haepari) requires | Native Apple Silicon macOS; complete same-release `use-haepari` skill | Binary, controller, resource, skill, and backend qualification are separate; compiled support is not live readiness |

## Aquarium helper Python environment

The [shared Python runtime contract](../../plugins/aquarium/references/python-runtime.md)
owns `aquarium-python`, its pinned helper dependencies and the user-global
virtual environments under `~/.aquarium/python-runtime/`. Global setup owns
installation and repair; repository setup and adaptive workflows consume the
matching environment without project packages. Bundle setup prepares it before
manifest normalization. Existing users need one approved preparation after the
plugin update. This breaking transition requires installed UTM qualification;
source and fixture checks do not establish that result.

## Installation and Freshness

Explicitly invoking `dev-setup-global` without a component list selects every supported user-global component; scoped continuations select only their named components. Automatic diagnosis includes disclosed official release, tag, and commit metadata. For Dolgorae, Sanho, Mulgae, Gaori, Sorage, Podway, and Haepari, it also includes complete Git tree metadata and commit-pinned paired-skill files in ephemeral storage. Selected Lora or Deslop includes official npm metadata for the exact `skills` installer version. This lookup authority does not cover clone, archive download, upstream-code execution, installation, replacement, initialization, Project registration, unrelated endpoints, or provider requests. The shared tool catalog owns the exact sources and comparison procedure.

Every installation proposal identifies the exact source ref, target, network endpoints, files, checksums or digests, backup choice, expected mutation, and post-action verification. Existing modified or duplicate skill copies are never overwritten or deleted silently.

Humanizer and im-not-ai are diagnosed and updated by `dev-setup-global`; installation actions remain separately approved. `dev-setup-bundle` prepares each selected user-global payload once, while target-level tool selection and `agents_guidance` decide whether English, Korean, both, or neither final-pass rule appears in a repository proposal.

## MCP Scope

Mulgae, Gaori, and Sorage may use global or isolated project-local MCP registrations. Aquarium inspects global, local, and effective registrations independently and prefers global for ordinary use. A v2 bundle manifest may select either scope per target; local selection takes precedence over the default global list. Readiness requires the requested effective scope, so a valid registration shadowed by another scope is reported as a mismatch. A tool omitted from both lists has no requested MCP registration; any existing registration remains in place and may still expose tools. Registration removal or replacement retains its separate approval.

Ouroboros supports either a direct selected `ooo mcp serve` registration or the canonical isolated `uvx --isolated --python >=3.12 --from ouroboros-ai[mcp] ouroboros mcp serve` form with Codex selectors. A valid isolated registration is evaluated from its own launcher contract rather than the base CLI environment.

MCP registration correctness does not prove that the active Codex session has reloaded or exposes the expected tools. A restart may be required after skill or registration changes.

A v2 bundle target may also declare whether Mulgae's `artist` role is required. `true` requires artist alongside the six non-UI roles; `false` requires those six without artist. Setup compares the effective role selection with that intent and proposes a native configuration change under its existing approval boundary. The manifest does not select providers, models, credentials, or role assignments.

Sorage supports optional global or repository-local STDIO MCP registration using the selected `sorage mcp` executable. Bundle v2 accepts Sorage in both MCP scope lists. The native release-matched skill owns explicit Handoff, Memo and Channel operations, preferring exposed MCP with same-context CLI fallback. Registration does not prove active tool exposure or authorize broker work.

## Sanho operation guidance

The [Sanho catalog](../../plugins/aquarium/references/tool-catalog.md#sanho)
owns setup and response handling. The complete release-matched `use-sanho`
skill owns operation and recovery details. v0.2.10 removes the development
producer targets without adding product commands; existing host selections
still need separate Aquarium-owned retirement.

| Situation | Aquarium handoff |
| --- | --- |
| Authorized commit | Follow the paired skill's commit workflow: local status, actual Git outcome and post-hook HEAD; a freshness warning never justifies repeating a successful commit. |
| Authorized push | Refresh status and follow native recovery within the existing target and effects. Check application and canonical publication separately after a failure. |
| Publication prediction | Use optional `preview`; inspect `blocked` and `verdict` even at exit 0. A cached verdict does not predict a later fetch. |
| Active or uncertain sync | Load the skill's inspection reference for conditional `sync --inspect`. Stop on `inspection_unavailable`; do not strip the flag or change filters to bypass it. |
| Conflict recovery | Consume typed `reason`, lossless `paths` and `recovery_id`. Within the existing authorization, follow resolve, stage, commit and continue, omitting completed steps; exit 0 with conflicts is unfinished work. |
| Provenance or recovery candidate | Load inspection guidance for `log` and `show`; preserve cached/refreshed distinctions and `source: null` for external commits. |
| Readiness diagnosis | Accept doctor `info` as valid information; warnings still degrade readiness. Keep committed-tree preview separate from current worktree readiness. |

Do not add these diagnostics to routine editing or require every optional
command at every Git boundary. Keep initialization, destructive recovery,
host retirement and publication within their respective authorization.

## Sorage Readiness

Sorage remains optional and outside the production-binary baseline. The minimum is stable v0.1.4 within v0.1.x. The [Sorage catalog](../../plugins/aquarium/references/tool-catalog.md#sorage) owns release identity, native preflight, one-way storage upgrade, minimal initialization, Project setup and MCP scope rules.

Inventory is version-only. Selected diagnosis uses native zero-write preflight, preserving all six states and their exit codes. Only compatible storage admits operational doctor and Project resolution; these probes remain outside Plan Mode. Fresh storage requires approved initialization. A storage migration requires a verified backup and separate restore drill using the executable matching the storage's original writer before the approved new-binary backup-run migration. The installed v0.1.3 executable may not be that writer. Format-4 storage cannot be read by published v0.1.2. No Aquarium SQLite reader or init-based upgrade is used.

Readiness requires a supported Apple Silicon CLI, compatible storage, doctor with no blocking check, an active git_repository Project binding, the canonical skill path, and safe root .sorage/ ignore/tracking state. Global setup verifies the complete same-release skill tree. MCP readiness is assessed separately for the requested scope; absent MCP does not prohibit a permitted native CLI operation.

Project setup performs no broker discovery. Only successful unregistered_workspace permits a registration proposal; resolution errors preserve their native code. Creation, binding, rebind, unarchive and ignore changes require exact approved targets. Explicit setup permits bounded zero-write Project listing. Listing grants no mutation authority.

Requested Handoff, Memo and Channel communication remains available in Plan Mode without per-tool approval overrides. All 35 native tools publish communication context and readOnlyHint true; physical zero-write guarantees apply only to covered reads. Message contents retain their separate execution authority. Actual tool denials must not be bypassed.

Updating compatible v0.1.3 storage needs no new migration; update the matching CLI and complete skill, reconnect MCP, and verify server identity, instructions and tool annotations. Older storage follows the approved backup/restore and migration procedure.

Handoff reading, processing, feedback and document acceptance remain distinct; inline content can have null storageKey. Native Revision/Row Version fences and uncertain-request recovery belong to use-sorage. Memo or Channel content grants no work authority or roadmap completion. Aquarium does not add a broker, Channel scheduler or automatic Channel transport.

## Podway Readiness

The supported Podway version floor is stable `>=v0.2.16` without an upper bound, on native Apple Silicon macOS. The paired `use-podway` tree retains its independent full release-commit pin in the [Podway catalog](../../plugins/aquarium/references/tool-catalog.md#podway). Runtime upgrades leave that pin unchanged.

Global inspection validates the single CLI's compact version and Output v4/version-result v2 identity without opening a workspace. Repository readiness additionally requires a healthy writer-compatible workspace, tracked regular non-symlink configuration and all five managed Procedures with native validity and compatible handler structure. Preserve same-ID customizations, and report source provenance and handler compatibility separately.

Observation uses v6 under explicit contract generation 2; status retains v5 for direct and delegated Procedures. Native Error v2 codes determine recovery. Version eligibility does not prove these contracts or selected-route membership. Session conflicts and terminal disposition belong to the owning workflow or the pinned runtime skill.

The exact official v0.2.16 compatibility gate runs one CLI in disposable Git fixtures. It retains the full Procedure scenario inventory, validates successful outcome lookup and exact replay, and verifies fenced workspace-removal rejection and already-absent readback under workspace-removal-result v2. No daemon, runtime mode or account registry participates. Candidate installation and installed-skill functional verification remain separate UTM evidence.

Legacy and incompatible writer state remains unchanged on refusal. The [upgrade contract](../../plugins/aquarium/references/tool-catalog.md#upgrade-from-older-writers) owns the original-writer, separate service-retirement and explicit destructive-reset boundaries. Reset establishes fresh runtime history; it does not convert or preserve old sessions.

The `podway-upgrade` manual VM suite seals official v0.2.16 payload and complete skill files into a separate candidate profile, preserving the qualified v0.2.14 baseline. The [historical installed qualification](../../tests/vm/README.md#podway-v0215-adoption-suite) records EPIC-034's observed generation-2 upgrade and Task/Epic startup coverage. Preparation checks alone do not establish installed acceptance; each release retains its separate exact-candidate gate.

The [v0.2.16 direct SSH observations](../../tests/vm/README.md#podway-v0216-direct-ssh-observations) record scoped installed upgrade, initial Task/Epic progression and exact consumer restoration under Master's explicit Haepari exclusion. Separate one-Task fixtures also completed both flows through actual user acceptance, final repository results and native terminal disposition. Original startup evaluator gaps, failed attempts and the incomplete managed Job remain separate; these observations do not establish arbitrary workflow coverage or release acceptance.

Installed qualification for the v0.2.14 adoption covers explicit skill-path execution through authenticated Codex, fresh private Codex discovery and session-scoped Claude discovery. Authenticated private-plugin namespace dispatch, Claude provider execution and complete managed Worker/Judge runs remain unqualified for the combined v0.1.19 release.

## Review and Check Adapters

Mulgae execution and provider-free publication reconciliation follow the [shared Mulgae review contract](../../plugins/aquarium/references/mulgae-review-contract.md) and the same-release `use-mulgae` skill loaded by the agent that performs the operation. User-global setup admits the stable v0.1.27 release floor and supported platform without claiming repository contract verification. Repository setup additionally requires command-result v23 or later, Doctor v7 or later, and the release's native supported configuration. Review execution requires preflight v11 or later, independent project binding, `live_source: v1` and the expected project binding guard, and receipt-bound result reads through the paired skill. Setup performs no review, recovery, or cleanup writes.

Subagent Review uses three fresh base reviewers in the Coordinator's native harness plus one UI/UX specialist for UI-related work for one selected exact target and shared Review Brief. It can be invoked standalone or selected in Task, Epic, and validation workflows in place of Mulgae or Herdr. It requires fresh host delegation, retains every expected role report and host provenance, and carries no implied Dolgorae, Mulgae, or Herdr lifecycle guarantees.

Profile selection is explicit and user-global; readiness uses offline diagnostics through the same-release `use-dolgorae` skill. Reusable Specialist requests follow that skill's External Specialist Engagement facade and the [Dolgorae consumer contract](../../plugins/aquarium/references/dolgorae-review-contract.md#reusable-specialist-requests). General Run and Brokered Hierarchy availability remains capability-dependent.

Dolgorae may separately publish an `aquarium-dev` generation for explicit development commands, but Aquarium creates no production runtime copy and Herdr Review does not use Dolgorae.

Aquarium production-binary readiness requires supported global Podway, Mulgae, and Gaori executables. A missing required executable fails closed and routes to the tool-scoped `$aquarium:dev-setup-global` workflow. Dolgorae and Sanho are explicitly optional and do not fail this binary baseline. Development generations never satisfy production readiness.

Mulgae review is advisory. Embedded and standalone callers supply the shared purpose and Review Brief while the loaded `$use-mulgae` skill owns native source admission, execution, waiting, publication reconciliation, publication, and retention. Aquarium preserves one started operation and does not add a status-polling or liveness loop. It requires complete selected-role coverage, passing CI decision, committed publication, a successful findings query, zero locally verified unresolved findings, and no unmet or unverified completion criterion before approving completion.

Gaori is optional evidence compression around a repository-owned command. The agent performing the check loads `use-gaori`, which owns native execution and waiting. Its independent `use-gaori-status` skill explains native read-only statistics and estimates; a timing query preserves an existing await and does not create a recurring observation loop. The [Gaori integration contract](../../plugins/aquarium/references/gaori-integration.md) separates the authorized command result, Gaori execution and extraction status, and Aquarium acceptance. Extraction quality does not rewrite a child result, but an internal error or missing required evidence cannot establish successful verification.

Gaori v0.1.20 covers complete logs in runs, summarize, parser detection,
rule tests and redaction samples. Size alone does not degrade extraction;
record truncation and extraction failures still limit evidence. Analysis memory
grows with input size while summary and excerpt output stays bounded. Config and
rule YAML and legacy proposal selections retain their native size limits.
Status signature hashes match decoded summary signatures for malformed UTF-8,
allowing native proposal and insights consumers to verify current artifacts.
CLI and both paired skills use the same selected release; old artifacts retain
their original provenance and are not repaired by an upgrade. Existing users
must update from earlier versions before relying on this contract. Installed
skill functionality and UTM qualification remain separate from source checks
and the disposable native compatibility target in `TESTING.md`.

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

Mulgae requires native Config v5 at the supported minimum. Existing v4 migration changes both versions to 5 and removes `execution.workspace_access` under separate configuration authority. New reviews support workspace, stage, head, commit and diff; capture-bound selectors, request-digest guards and child/replay/compose creation are retired. Live source identities describe selection metadata, and callers maintain workspace/index consistency. Historical results remain readable.

Historical v0.1.25 scoped UTM qualification covers Config v4 rejection and deliberate v5 migration, historical v0.1.24 reads, all five target preflights, binding and source-safety failures, authenticated Codex review, terminal failure followed by an explicitly authorized fresh root, provider-free MCP publication and promoted-evidence v2 integrity at the Git boundary. Authenticated execution used the candidate skill's explicit path; native plugin replacement and fresh namespace discovery were verified separately in an isolated Codex home. Live-provider MCP execution, authenticated namespace dispatch and complete hardening-deferral and Task Commit workflows were not exercised. This scoped result does not qualify the combined release baseline, managed-Procedure upgrade or Master's functional checks required before release.

Historical v0.1.26 completion callers automatically prepared native requirements and consumed receipt-bound assessments under the shared review contract, using the temporary report-based override when extraction produced derived `answer_omitted` rows. Cursor and AGY remain native text-provider selections; artist eligibility and existing configuration stay native-owned. Scoped installed verification covered that report-based path, with final payload reconciliation allowing only the declared development-version stamp difference. Master's functional assessment and release acceptance remain separate.

Mulgae v0.1.27 or newer is the active supported floor (no upper version bound), keeping command v23, Doctor v7, preflight v11, and Config v5 floors. Live-provider reviews (`mulgae review`, `run_review`, and `start_review`) require an existing selected private `HAEPARI_HOME` with Haepari `advisory-lock/v1` and a capacity-one `mulgae-review` resource whose hold policy covers the admitted native review budget. The selected `HAEPARI_HOME` must reach the actual CLI or MCP process; a validated inherited `HAEPARI_LOCK_GRANT` is borrowed read-only within that installation. Local `--preflight`, receipt-bound inspection, and no-change reviews remain provider-free and lock-free. Mulgae alone owns acquisition, persisted-key replay, queued cancellation and raced-grant release, in-process renewal, borrower validation, and terminal release after protected work and verified local drain (`local_drain_state`); Aquarium and `$use-mulgae` add no outer lock wrapper. Advisory expiry can overlap surviving work and does not contain unknown execution, eliminate provider rate limits, or police uncoordinated callers. Partial-role failures preserve accepted role reports and release the lock after native termination before waiting for user decisions, without cross-run coverage or composition. Because v0.1.27 preserves native v3 requirement answers through extraction, the active report-based `answer_omitted` override is retired for new supported runs (leaving any new derived `answer_omitted` row `unverified` while preserving historical v0.1.26 rows and judgments). TASK-092 settled the remaining installed consumer qualification and the deferred workaround retirement after affected independent assessment and CO acceptance under the Epic delegation. The [TASK-092 direct UTM observations](../../tests/vm/README.md#task-092-direct-utm-caller-observations) retain the original MCP refusal, the successful CLI caller observations, the subset's native `invalid_assessment` result, and verified consumer restoration. One bounded MCP correction subsequently verified explicit environment forwarding and a native affected-only `provider/met` assessment without rewriting the original failure or repeating tests. Master's direct-SSH authorization replaces only the outer managed Job transport for this Task; it establishes no managed Job `PASS` or release acceptance.

## Haepari

This section freezes the accepted Haepari v0.1.0 artifact identity and the consumer contract boundary. Optional setup registration, fixed test profiles and the managed release-policy path are implemented: the [tool catalog](../../plugins/aquarium/references/tool-catalog.md#haepari) owns installation and readiness policy, and `tests/vm/profiles/` holds the immutable proposed profiles. TASK-088 through TASK-090 own the project-owned VM suites, the release-gate integration and the policy cutover. The exact installed TASK-090 pilot qualifies the managed path selected by Aquarium's release policy. Other repositories retain their own declared verification environment.

TASK-086 verified the official [Haepari v0.1.0](https://github.com/irootkernel/haepari/releases/tag/v0.1.0) release: archive SHA-256 `6667cab322f326eb390b8cab89fd292e22d7436312434e7facd66213fe1a8a18`, sidecar SHA-256 `fb0a83ea2f09694f3da61148a7dbc0e12de6cdc5963e796faa91f4d01ef1f531`, the complete packaged inventory, the executable digest, and a paired skill tree byte-identical to the `v0.1.0` tag. The binary's build basis `fc3b975f8a99cacb96aecc988d3adbc04dda7309` is the validated archive source; the release tag `800da97b7e2ca84a15d4ee5921702ec57bbc7d61` adds release metadata only, and acceptance never rebuilds to equalize them. The frozen capability output reports `managed-execution/v1`, `durable-observation/v1`, `advisory-lock/v1`, `managed-recovery/v1`, `artifact-delivery/v1` and `evidence-retention/v1`, with `compiled_backends: ["local"]` and an empty `qualified_backends`; compiled support is not live readiness, and setup must not require a nonempty qualified array. The producer's digest-bound running-VM qualification on its separate profile is accepted with its recorded limits; Aquarium's own installed combination on the registered shared VM remains TASK-088/090 evidence.

The frozen Aquarium submission and result contract lives in [haepari-integration.md](../../plugins/aquarium/references/haepari-integration.md), with operator procedures in [Haepari VM operations](../ops/haepari-vm-verification.md); release-matched upstream sources are authoritative, including the [CLI and job](https://github.com/irootkernel/haepari/blob/v0.1.0/docs/contracts/cli-and-jobs.md), [resource and runner](https://github.com/irootkernel/haepari/blob/v0.1.0/docs/contracts/resource-and-runner.md), [lock](https://github.com/irootkernel/haepari/blob/v0.1.0/docs/contracts/locks.md), [configuration](https://github.com/irootkernel/haepari/blob/v0.1.0/docs/contracts/configuration.md), [managed transition](https://github.com/irootkernel/haepari/blob/v0.1.0/docs/contracts/managed-transitions.md) and [artifact and profile](https://github.com/irootkernel/haepari/blob/v0.1.0/docs/contracts/artifact-and-profile.md) contracts, with [external leases](https://github.com/irootkernel/haepari/blob/v0.1.0/docs/contracts/external-leases.md) named as the deferred boundary. TASK-089 and TASK-090 added the release-transaction suite, the release-role and producer adapter handoff (separating pre-submission request/spec/profile records from returned `job_id`, `job_revision`, and verified export/cleanup records), the `PATH`/`.venv` interpreter selection rules for `make test-vm-host` and nested `make aquarium-dev-build`, the shared outer-boundary VM occupancy rule, and the final distribution identity checks to those references, so EPIC-031 through EPIC-033 consume them there without the adoption dossier. [ADR-0010](../architecture-decision-records/0010-haepari-vm-verification-and-advisory-locks.md) records two breaking transitions. Aquarium's release operation moves to the qualified managed path, while `release-handler` retains target-repository policy selection. Existing users of a managed aquarium-status runtime complete its routine approval-based managed update before the next terminal repository setup. Haepari setup itself stays optional. TASK-090's read-only legacy-enrollment audit confirmed Aquarium's own enrollment record points to another checkout, while the current checkout has no post-commit hook (`core.hooksPath` unset); live `~/.aquarium-dev` detachment and shared retirement remain deferred to EPIC-033 (`TASK-101`). The durable design lands in the [verification architecture](../architecture/verification.md) and the [component map](../architecture/components.md), with the adoption decision and qualification limits in ADR-0010 and the [VM guide](../../tests/vm/README.md#qualified-pilot-and-limits).

## Version inventory

[`aquarium:version`](../../plugins/aquarium/skills/version/SKILL.md) owns the
read-only inventory of the invoked plugin, supported CLIs and external skills.
Its helper returns `aquarium-version-report/v1` with an observation time and
component rows containing local evidence, official upstream metadata and a
comparison. Individual failures remain in the report; exit zero means report
completion, not universal probe success.

The helper uses native version commands without service, provider, workspace or
setup diagnosis. CLI paths identify the selected executable, not an attached
MCP server. Skill presence without explicit version metadata does not prove a
version. Only the active Codex home and shared skill root are inspected; other
homes remain independent. The plugin row comes from the package containing the
invoked skill, never the separate status reporter receipt.

Default lookup reads official GitHub latest stable Release metadata without
Aquarium support-range filtering. Lora follows its stable-tag/main-ref policy;
Deslop reports its main commit as a source reference. Offline mode makes no
network requests. The report creates no persistent registry and authorizes no
installation or upgrade.

Version report failures include safe reason codes and available exit or HTTP
status, without raw command stderr or exception payloads. A latest-Release 404
triggers a public release-list check; only a complete list without published
stable releases establishes absence. Local filesystem inspection failures stay
in their component row. Package origin is labeled from the invocation context,
with an explicit unknown label when installation or source origin is unproven.
