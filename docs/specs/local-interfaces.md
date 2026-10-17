# Local Interfaces

Aquarium ships declarative skill contracts, Podway Procedure definitions, local structural inspectors, one commit hook, and verification helpers. JSON schema identifiers are compatibility surfaces for their owning workflows.

## Production Status Interfaces

`TASK-048` froze and `TASK-049` shipped the original production setup-status interfaces.
The ledger now uses
`aquarium-production-status/v2`; the record input and receipt use
`aquarium-production-status-record/v1` and
`aquarium-production-status-record-receipt/v2`; JSON show output uses
`aquarium-production-status-report/v2`; language refresh uses
`aquarium-production-status-language-refresh-receipt/v1`; exact deletion uses
`aquarium-production-status-forget-receipt/v1`; and failures use
`aquarium-production-status-error/v1`. Setup handoff and recording results use
`aquarium-production-status-attempt/v1` and
`aquarium-production-status-recording-result/v1`. Installation and diagnosis use
`aquarium-status-runtime/v1`, `aquarium-status-runtime-inspection/v1`, and
`aquarium-status-runtime-error/v1`.

The CLI is `aquarium-status show --format text|json [--refresh]
[--source-root <absolute-path>]`, closed-JSON `record` on standard input,
`refresh-languages [--git-root <recorded-absolute-path>]`, and
`forget --git-root <absolute-path> [--if-file-revision <revision>
--if-row-revision <revision> --if-row-sha256 <digest>]`. Exit 0 is a
successful result, exit 1 is owned-state failure, exit 2 is invalid caller input,
and exit 3 is a revision or attempt conflict. The exact fields, write timing,
locking, runtime installation, and retention rules are owned by the
[production-status specification](production-status.md).

## Managed Podway Procedures

| Procedure ID | Version | Owner | Recorded lifecycle |
| --- | --- | --- | --- |
| `aquarium-task-v2` | `31` | `task-handler` | Selected plan input, implementation, refinement, typed verification, route-specific entry, operation, evidence, provenance, backend, recovery, completion, finding, owner, Low-settlement, goal-assessment, approval, and closeout decisions |
| `aquarium-goal-v2` | `34` | `epic-handler` | One member task, pre-validation remediation, or final closeout goal with route-specific operation and evidence decisions, separate delegated and waived finding confirmation, lifecycle-safe recovery, completion, hardening deferral, Low settlement, and path-bound assessment and closeout |
| `aquarium-validation-v2` | `33` | `epic-handler` and `epic-validator` | Baseline, severity-aware audit, namespaced obligation composition, and serial route binding, assessment, provenance, backend applicability, recovery, finding confirmation, completion, required-evidence, blocker, Low-settlement, and path-bound assessment decisions |
| `aquarium-design-v2` | `11` | `new-project`, `new-feature`, and `refactor` | Context, discovery, draft, challenge, guarded phase-owner quality, approval, application, assessment, and closeout with action guidance |
| `aquarium-war-room-v2` | `11` | `war-room` | Baseline or reproduction, investigation, semantic cause and scope decisions including evidence-backed no-work, guarded proposal quality, approval, documentation, assessment, and closeout with action guidance |

Procedure source bytes live under [`plugins/aquarium/assets/podway/procedures/`](../../plugins/aquarium/assets/podway/procedures/). The version belongs to the Procedure document, not the Aquarium plugin version, and an active session retains the immutable snapshot with which it started.

## Inspectors and Helpers

| Entrypoint | Input | Success schema | Behavior |
| --- | --- | --- | --- |
| `dev-setup-global/scripts/inspect_global_tools.py` | Optional existing working directory, repeatable component scope and Codex homes, command timeout, Ouroboros release verification, and Sorage initialization diagnosis | `aquarium-dev-setup-global-inspection.v6` | Selected user-global CLI, paired-skill, service, global MCP, writing-skill, Lore, Ouroboros, and `aquarium-status` inspection without requiring or reading repository configuration |
| `dev-setup-global/scripts/inspect_skill_inventory.py` | Official recursive tree JSON on stdin, resolved `--tree-sha`, and `--skill-path` | `aquarium-skill-inventory/v1` | Selects every regular file in the complete skill subtree; rejects invalid metadata or selection with `error.code=invalid_inventory` and exit 2. Commit provenance, fetch and payload digest verification remain caller-owned. |
| `dev-setup/scripts/inspect_tools.py` | Repository plus optional component/MCP flags, or explicit selected Podway source/resume flags described below | `aquarium-dev-setup-inspection.v23` | Default repository/tool inventory or selected-only Podway admission, with separate native runtime, managed-library and selected-definition results. Gaori timeout readiness is structural: positive finite or absent values do not prove a command fits the host deadline. |
| `docs-setup/scripts/inspect_docs.py` | Exact absolute Git root | `aquarium-docs-inspection/v2` | Minimal read-only discovery of documentation roles, explicit roadmap units and lifecycle links, exclusions, and unambiguous structural conflicts |
| `test-setup/scripts/inspect_testing.py` | Exact absolute Git root | `aquarium-test-setup-inspection.v1` | Static Make/Bun test-contract discovery without executing project code |
| `dev-setup-bundle/scripts/normalize_manifest.py` | External `aquarium.dev-setup-bundle/v2` YAML manifest | `aquarium-dev-setup-bundle-plan.v2` | Validates target MCP scopes, Sorage slug and Mulgae artist intent, then emits ordered targets and the needed global MCP union |
| `independent-review/scripts/inspect_review_target.py` | Repository and one workspace, staged, dirty, HEAD, commit, or range selector | `aquarium-independent-review-target/v1` | Read-only target identity and state inspector used before and after all expected host reviewer reports; its fingerprint is not an immutable capture |
| `release-handler/scripts/inspect_release_notes.py` | Repository, expected version, and release baseline | `aquarium-release-notes-inspection/v1` | Inventories cumulative release-note enrollment and candidate delta |
| `release-qa/scripts/manage_release_qa.py` | Versioned full-pass, preparation, admission, or finish JSON | `aquarium-release-qa-confirmation-record/v3`, `aquarium-release-qa-confirmation-manifest/v3`, `aquarium-release-qa-confirmation-claim/v2`, `aquarium-release-qa-confirmation-settlement-admission/v1`, or `aquarium-release-qa-confirmation-result/v2` | Creates immutable QA matrices, binds exact remediation and finding-to-scenario coverage, admits one digest-bound settlement per claim, and persists one immutable terminal result |
| `release-handler/scripts/inspect_publication_state.py` | `aquarium-release-publication-observation/v5` JSON on standard input | `aquarium-release-publication-state/v5` | Checks the repository-resolved expected title, local main, both remote ancestry relations, tag, stable hosted Release, and exact or approved QA-neutral binding; a proven remote descendant can finish publication at the original release SHA |
| `tests/verify_podway_compatibility.py` | Exact official v0.2.14 `PODWAY_BIN` selected by Make | `aquarium-podway-compatibility.v9` | Runs the single Direct CLI in at most four disposable Git fixtures, binds source/manifest/CLI and Aquarium identities, preserves the full five-Procedure correction and lifecycle scenario inventory, and verifies declaration rejection, workspace/session outcome lookup and replay, legacy/writer refusal and reset, and fenced workspace removal with already-absent readback |

The v9 compatibility result includes `outcome_recovery` and `upgrade_scenarios` beside the retained lifecycle, correction-matrix and workspace-removal results. These are native disposable-fixture assertions, not installed skill acceptance.

Every inspector also has a versioned error schema where applicable. Consumers use normalized fields and reason codes rather than parsing human stderr or exposing raw configuration and credential material.

The v1 test inspector exposes `make.output_unverifiable` for output uncertainty when Make reads the file, and `make.targets.<target>.definitions[].execution_unverifiable` for target execution uncertainty. Parser recommendations are computed per stage; formatting and unrelated declarations do not invalidate a known command. Semantic correctness and waiver equivalence remain `not_evaluated`.

The global Gaori entry exposes `status_skill` for the optional `use-gaori-status` installation, using the same inspection shape as `paired_skill`. Its health does not change `cli`, `paired_skill`, or `global_mcp`. Repository inspection checks only its canonical path in `trusted_global_skills`.

The global v6 payload separates shared components from home-scoped Ouroboros integration. Sanho, Mulgae, Gaori, Sorage, Podway, and Dolgorae are wrapped objects with a normalized `cli` member and any applicable `paired_skill`, `global_mcp`, `installation_prerequisites`, `identity`, `identity_probe`, `initialization_status`, or `initialization_probe` members. A paired skill is `configured` only when its single valid installation is the canonical `~/.agents/skills/<name>` target; an installation found only in another known Codex skill root or duplicated across roots is `degraded` so global setup can propose canonical migration or cleanup. Lora, Deslop, Humanizer, and im-not-ai remain flat component objects with a top-level `status` and component-specific `skills`, `agent_skill`, `probes`, MCP, or runtime fields. Lora requires its single valid `lore-commits` and `lore-query` installations at `~/.agents/skills/lore-commits` and `~/.agents/skills/lore-query`, and Deslop requires its single valid installation at `~/.agents/skills/deslop`; an alternate-root or duplicate installation degrades the component. im-not-ai uses the active Codex home's `skills/humanize-korean` target. A copy in another Codex home is independent, while a copy in `~/.agents/skills` is a duplicate.

Humanizer exposes `supported_range: ">=2.11.1"` and accepts a stable frontmatter version at or above that floor. im-not-ai exposes `supported_range: ">=2.3.2"`; its generated Codex skill has no version field, so offline `version` and `version_supported` remain null and exact-tree freshness belongs to global setup's selected-release comparison. Both structural inspections permit additional regular skill files because the selected upstream release owns the exact file set; setup compares the full selected source and target trees. A sole active-home Humanizer copy is a valid structural candidate, and a sole shared copy remains the fallback. The inspector cannot establish which target the selected Humanizer release documents. A Humanizer copy at both targets is a duplicate; copies in inactive Codex homes are independent. Ouroboros reports `legacy_shared_skills` for shared copies matching a selected package skill name and separate same-name `shared_skill_conflicts`; either degrades home readiness.

Dolgorae also exposes local file-safety, identity-stability, and capability fields beside `cli`, plus `paired_skill` for `use-dolgorae`. It does not expose release verification or official-executable fields. Its CLI and skill statuses are independent. Local skill structure and hashes do not establish same-release freshness; global setup compares the complete `skills/use-dolgorae/` subtree at the selected release commit under the tool catalog's inventory contract. Dolgorae version JSON has exactly `name` and `version`; capabilities use machine envelope v2 while advertising machine protocol v1.

Ouroboros exposes `cli`, `freshness`, `current_home`, `current_home_readiness`, `all_discovered_homes_readiness`, `homes`, `legacy_shared_skills`, and `shared_skill_conflicts`. Its top-level `status` is the current home's configuration readiness. Each home reports independent `rules`, `skills`, `codex_integration`, `mcp_registration`, `mcp_runtime`, `runtime_package`, `home_binding`, and `live_runtime` results. Completed artifact comparisons include relative missing, extra, and changed file paths; `unverifiable` and `unsafe` results may contain only a status and reason. The live result remains `not_observed`; configuration checks do not verify a running process. A recognized unpinned launcher has an unverifiable package version and cannot establish complete home readiness.

Repeatable `--codex-home` adds locations to active, default, and discovered homes; aliases are merged. Blank home arguments return `invalid_arguments` before probes; nonblank paths retain their spaces. Explicit homes that are regular files return `invalid_codex_home`. An automatically selected active home that is a regular file instead produces a `degraded` row with reason `home_not_a_directory`; its component results are `unverifiable`, its doctor and MCP probes are skipped, and other homes and components remain in the payload.

Automatic home resolution failures retain the original path spelling with `home_resolution_failed` and skip home probes. Discovery failures and otherwise unhandled path errors during home inspection produce `home_inspection_failed` for the affected home; artifact read failures use `artifact_read_failed` on the affected component. Healthy homes and other components remain available. Shared skill discovery skips an unresolvable active root, and im-not-ai reports `unverifiable` with a null `expected_target` when that root cannot be resolved. Only invalid explicit home arguments become `invalid_codex_home`.

`--verify-ouroboros-release` opts into official PyPI stable-release comparison, with installed, latest stable, and latest supported versions kept distinct. The supported floor is `0.51.1` with no upper bound; `latest_supported` is null when stable releases exist but none meets it. The obsolete `compatibility_review_required` field is absent. Both options require Ouroboros to be selected. Freshness without the flag is `not_checked`; lookup failure, including an HTTP protocol error, is `freshness_unverifiable` without discarding other results. An installed CLI whose version probe fails or cannot be parsed produces `freshness_unverifiable` with reason `cli_version_unverifiable`, while any successfully fetched release metadata remains available. Only an absent CLI is `missing` after a successful lookup.

The native package resolver runs once through the uv-tool interpreter beside the selected CLI, with isolated Python imports; unresolved or mismatched package assets cannot establish rules/skills health. Rules and skills are compared separately from the aggregate Codex doctor.

The global inspector's repeatable `--component` option selects only the named components and returns only those `tools` entries in catalog order; omitting it selects all supported global components. A Sorage initialization diagnosis is invalid unless its component is selected. The `--repository` option validates only an existing compatibility directory; every selected global CLI, Codex, Podway, Sorage, Go, Dolgorae, and Ouroboros probe runs from a neutral filesystem root so repository-local configuration cannot affect its result. `--timeout-seconds` bounds ordinary commands. The Podway `identity` member contains the validated Direct CLI version-result v2 identity, and `identity_probe` contains its normalized probe result. CLI readiness requires the supported stable version, Apple Silicon target and native identity contract; global diagnosis opens no workspace and probes no service.

`dev-setup-global` starts with version-only Sorage inspection. Outside Plan Mode, after disclosing native database and journal effects, `--include-sorage-initialization` checks the selected installation state before `sorage doctor`. For a pre-Memo database, it checks the configuration against the Vault marker and recorded database identities, then runs native configuration validation. A valid matching installation yields `upgrade_preflight_required`, then `upgrade_migration_required` after `--sorage-upgrade-preflight-complete`; doctor remains deferred until separately approved native migration succeeds. A missing database in a nonempty home or an incomplete or mismatched configuration yields `installation_recovery_required`. An unverifiable state yields `upgrade_state_unverifiable`. Neither recovery nor unverifiable state runs doctor.

The repository inspector's v23 Podway entry exposes `identity`, `probes.identity` and an always-present `migration_kinds.runtime_contract` boolean. The latter identifies native legacy-Store or writer-manifest refusal; other configuration errors retain their native reason and remain degraded. Its default inventory payload exposes exactly twelve `trusted_global_skills` entries: `use-sanho`, `use-dolgorae`, `use-mulgae`, `use-gaori`, `use-gaori-status`, `use-sorage`, `use-podway`, `lore-commits`, `lore-query`, `deslop`, `humanizer`, and `humanize-korean`. Each entry contains only `canonical_path`, `present`, and `verification_scope: "presence_only"`. The `humanize-korean` path belongs to the active Codex home. Humanizer uses a sole active-home copy when present and otherwise the shared target; the other entries use `~/.agents/skills`. The same presence-only object replaces `tools.<name>.agent_skill` for Sanho, Mulgae, Gaori, Sorage, and optional Podway. Its `tools` object excludes Dolgorae, Lora, Deslop, Humanizer, im-not-ai, and Ouroboros because those components belong to the global inspector.

Each `tools.podway.managed_procedures` entry reports immutable file provenance
through `source_state` and `update_explanation`, while
`handler_contract_status` (`compatible`, `unqualified`, `incompatible`, or
`not_checked`) and stable `handler_contract_reasons` describe whether the
installed graph exposes the structural nodes, items, and routes consumed by
current Aquarium handlers. A Podway-valid same-ID customization remains
`valid_customization`; an unrecognized semantic graph or incompatible handler
contract independently keeps readiness degraded and is never overwritten by
inspection.

Task, Goal, and Validation entries also report `review_route_readiness` for each
current route as `ready`, `unavailable`, or `unverified`; Design and War Room
entries report an empty map. The inspector qualifies the snapshot's declared
routes only after native checks and overall readiness pass. A prior-canonical
snapshot may remain generally compatible while a newer route is unavailable.
This setup inspector requires PyYAML and readable declarations to qualify routes. Routine managed-session admission checks the selected route against the exact installed Procedure snapshot after its native and handler-contract checks, without running global setup diagnosis.

When a repository component depends on a missing or degraded user-global MCP registration, the inspector reports the recommendation `continue_with_dev_setup_global`. Repository workflows use the same continuation for unavailable or unready user-global services and do not repair either class locally.

The additive `tools.sorage` member reports the common tool fields plus `version_supported`, `platform`, `agent_skill`, `initialization_status`, `project_registration`, and `readiness_status`. It also reports whether the repository root `.gitignore` matches `.sorage/` with a non-negated rule, tracking and symlink state, and normalized `version`, `doctor`, and `project_resolve` probes. A local or global exclude rule alone does not satisfy the reported ignore policy. The `ignored` field reports root-rule coverage independently of index state, so a tracked `.sorage/` path may have both `ignored` and `tracked` set to `true`; tracking still blocks readiness. The version probe validates the bare v0.1 name/version object. Doctor and Project probes validate Sorage envelopes, and doctor state is accepted only for the complete ordered 20-check v0.1 catalog.

The inspector exposes only doctor severity counts and the resolved Project slug, status, and binding kind. It excludes Installation IDs, Workspace keys, request IDs, display names, Vault and binding paths, check messages, Handoff metadata, and Artifact content.

`status` describes supported CLI health and becomes `configured` only at complete readiness. `readiness_status` describes initialization, registration, and repository preparation. Default inventory leaves a supported Sorage CLI's readiness `not_inspected`; an unsupported version or platform is `degraded` without running a readiness probe.

A successful unregistered result is `registration_required`. A valid native resolution failure is `resolution_error` and cannot authorize Project creation or binding. `--include-sorage` runs doctor after selection and runs Project resolution only when doctor has no blocking check. The repository inspector owns `tools.sorage` repository readiness; the global inspector owns user-global installation and update evidence.

`plugins/aquarium/tools/aquarium-dev/aquarium_dev.py` owns diagnose, enrollment, hook repair, build request, rebuild, worker, cleanup, launcher installation, and managed-service planning and application. Managed-service producers emit `aquarium-dev-producer-description/v2` and `aquarium-dev-artifact-manifest/v2`; their controllers emit `aquarium-dev-service-status/v1`, `aquarium-dev-service-plan/v1`, and `aquarium-dev-service-result/v1`. It has no Codex-configuration or production-tool setup operation. The installed `aquarium-dev` CLI exposes the manager commands; its tool-invocation form accepts a supported tool and arguments, falls back only an absent foreground tool to the caller's global `PATH` outside both Aquarium roots, and requires a matching ready managed service without production fallback while leaving the caller's environment unchanged.

The release-QA evidence lifecycle accepts `aquarium-release-qa-cluster-result/v1` worker results and the `aquarium-release-qa-full-pass/v2`, `aquarium-release-qa-confirmation-prepare/v2`, `aquarium-release-qa-confirmation-begin/v2`, and `aquarium-release-qa-confirmation-finish/v2` command inputs. Full-pass v2 and record/manifest v3 explicitly bind a previous-release or first-release baseline; the latter retains every reachable commit and current tree path with null previous-release identity. They freeze the active Design Gate inventory and positive/failure scenario matrix separately from delta coverage. Confirmation preserves those exact fields, and claim, admission, and result schemas remain unchanged. These inputs and artifacts use closed shapes, create-once outputs with physically normalized parents and byte-bounded basenames, canonical bytes, and exact digests. Before a settlement admission exists, repeating an identical begin verifies the existing artifact and returns the same successful claim receipt without replacing it; begin cannot authorize another worker dispatch after admission. Finish creates one claim-keyed settlement admission that binds the canonical request, submitted evidence bytes, and terminal output path, matches scenario identities independently of array order, and computes its verdict from the same cluster bytes verified against the admission before converging on one terminal `PASS`, `FINDINGS`, `INCOMPLETE`, or `REJECTED` result. A canonical admission with a malformed snapshot shape settles as `REJECTED`. A changed request or output path reports `settlement_pending` before a terminal exists and `settlement_replay` afterward; neither can replace an artifact. Unexpected transient settlement failures remain recoverable by the exact admitted request and output path. Contract failures return `aquarium-release-qa-error/v1` with a nonzero exit.

## Adaptive definition interfaces

The [shared adaptive contract](../../plugins/aquarium/references/adaptive-procedures.md)
owns `aquarium.procedure-binding/v1`, `aquarium.procedure-fragment/v1`, their
closed JSON schemas and necessary native declaration signatures. The shared
Python helper parses definitions, calculates canonical UTF-8 JSON identities,
extracts native recovery tuples and checks declaration slices with typed aliases.
It preserves native operation IDs/digests and accepts explicit verified signature
extensions. These checks establish neither whole-graph qualification nor actual
agent execution. The shared `adaptive_admission.py` and `adaptive_bundles.py`
helpers admit exact known sources and implement atomic locally ignored
retention and exact native `(id, version, digest)` recovery across all approved
searched roots. Their retained complete source/binding does not depend on mutable
origin libraries. Fit selection and source-only preparation now use ordinary
Worker assignment/plan data and retain ignored `.candidates` bundles without
adoption. `adaptive_composition.py` expands explicit whole/fragment inputs and
typed ports through that same preparation CLI. It retains operation identities,
resolves native references and dependencies, and rejects unresolved/private
rework or unavailable required evidence. The explicit helpers below implement
guarded whole-graph qualification and exact suitability/bootstrap. Task, Goal, Validation, Design and Diagnosis activation is implemented.

The [preparation CLI](../../plugins/aquarium/shared/prepare_adaptive_procedure.py)
takes `--repository`, `--assignment <file-or->`, optional Design `--podway-opt-out`, and, for approved native preparation,
`--podway <exact-binary>`. The ordinary assignment's `target.procedure_plan.mode`
selects read-only `plan-only` or approved source-only `prepare`. Its full input,
coverage identities, output and exit contract are in the
[shared adaptive contract](../../plugins/aquarium/references/adaptive-procedures.md#selection-and-source-only-preparation).
Exit 0 returns JSON `planned`, `prepared` or Design `podway-inapplicable`. That status skips source selection/rendering and native imports for explicit `--podway-opt-out` or non-Git `new-project`; no binary or runtime dependency is needed. The Design-only flag rejects unsupported or absent entrypoints as `invalid-arguments` JSON with exit 2 before native/source work. The API uses `opt_out=True` with the same boundary. Other failures exit 2 with a distinct status. A prepared target names exact source and binding paths, native tuple,
source SHA, coverage plan and outstanding qualification. This interface performs
no session operation or generated-source adoption and changes no handler default.

The [adaptive launcher](../../plugins/aquarium/shared/manage_adaptive_procedure.py)
accepts `inspect`, `retain`, `resume`, `context`, `transition-plan`, `transition` or `transition-recover` with the owning repository and invoking entrypoint. The native path requires every approved root and applicable selected review route. Design `--podway-opt-out` and non-Git `new-project` return `podway-inapplicable` before native imports or discovery, without roots, source, qualification, binary or session. Inspect/retain take a source;
retention also takes an approved write root. It emits JSON with source/binding,
retention disposition and actual session context, or a distinct failure status.
An optional bootstrap reference is a cross-check. It uses native check/preview for
the actual canonical digest, separately verifies source-file SHA-256, and requires
the supported frozen known-source/reference contract. Changed/new qualification
uses exact binding and ordinary suitability context. Task, Goal, Validation, Design and Diagnosis use the activated mapped consumer. Inspect/retain/resume/context perform no session mutation. Explicit transition actions follow the consented atomic contract below; no action installs tools. On the native path, YAML and `jsonschema` must be available in its reported interpreter. Missing dependencies return `missing-prerequisite`.
The setup inspector's explicit selected mode lazily imports these helpers,
preserves full managed-library diagnostics and exposes selected/runtime readiness
separately. Selected-provider readiness stays with its existing review-route owner.

The shared [atomic transition interface](../../plugins/aquarium/references/adaptive-execution.md#consented-atomic-supersede) uses `--transition-input <json>`, `--qualification <ordinary-context.json>` and, for execution/recovery, `--consent <json>`, with the same repository, roots, entrypoint and Podway executable. Planning returns exit 0 `replacement-consent-required` and an exact checkpoint/disclosure without native mutation. Actual approved `transition` performs only native preserve-start; `transition-recover` looks up that original key and reconciles lineage/current state before optional identical replay with `--replay`. Success returns exit 0 `superseded-prepared-resolved`, no dispatch and separately authorized begin pending. A lookup miss with unchanged predecessor readback and no `--replay` returns exit 0 `same-request-replay-available`, the retained `checkpoint` and no dispatch or mutation; it is not a completed transition. Explicit `--replay` is required to submit the original request. Failures exit 2 with typed status, including absent consent, stale consent, native conflicts and `outcome-unknown`. Checkpoint/request data stays in ordinary local orchestration records; no central database, universal report or new authority is created.

## Selected Podway CLI contract

The repository inspector enters selected mode only with one of
`--selected-podway-source <path>` or `--resume-selected-podway`. Supply
`--repository <path-inside-worktree>`, repeated `--podway-root <root>` for every
approved searched root, and `--podway-entrypoint <handler>`. The seven entrypoint
values are `task-handler`, `epic-handler`, `epic-validator`, `new-feature`,
`new-project`, `refactor` and `war-room`. Task, Goal and Validation also require
`--podway-review-route` with `mulgae`, `herdr`, `independent-review` or `waived`.
`--podway-bootstrap <binding-path>` optionally cross-checks native-tuple recovery;
`--podway-customization-basis <existing-envelope-disposition>` carries the current
adopted-customization decision. `--timeout-seconds` retains the inspector's
documented command timeout. Selected mode does not require `--include-podway` and
does not probe other providers. Supplying selected-only options without a selected
mode, or omitting roots/entrypoint, is an argument error.

Selected mode returns `schema_version: aquarium-dev-setup-inspection.v23`,
`inspection_scope: selected-podway`, Git `repository` inventory,
`tools.podway` and `selected_procedure`. It has no `trusted_global_skills`
inventory. Missing adaptive dependencies instead return the schema version,
`selected_procedure` with dependency/interpreter and empty `tools`, before native
work. `tools.podway.runtime_readiness` always has `state`, `session_procedure`,
`session_lifecycle` and `session_contract_supported`. State is `ready`, `degraded`
or `unavailable`; unobserved session fields are null and an unchecked session
contract is null, without claiming incompatibility. A checked no-session response
can establish the session contract while retaining null identity/lifecycle.

Successful selected results expose source, binding, interpreter, invocation mode,
customization disposition and selected-provider ownership. `retention_status` and
`retention.status` report lookup disposition; `retention.diagnostics` contains
historical failures and their key-association limits, and `retention.aliases`
contains equivalent retained locations. `session` exposes the actual current
tuple/lifecycle, definition conflict and remaining work-identity reconciliation.
Failure results contain `status`, `message`, interpreter and `details`. Runtime
failure details retain normalized version/identity/doctor/session probes, native
error codes, timeout/exit evidence, runtime readiness and migration diagnosis.
Selected-key damage retains resolver diagnostics and stops; `missing` means no
associated retained candidate was found, while associated missing files or an
empty exact candidate location are `corrupt`.

The inspector exits 0 for selected `ready`, 2 for selected conflicts or failed
admission. Typed repository/inspection errors use the existing v23 `error.code`
and `error.message` shape and their declared exit status (2 for invalid arguments
or repository selection, 1 for failed Git-status inspection). These results never
authorize repair, replacement or session mutation.

The adaptive launcher takes positional `inspect`, `retain`, `resume`, `context`, `transition-plan`, `transition` or `transition-recover`, required `--repository` and `--entrypoint`, plus applicable `--review-route`. Repeated `--root` is required only on the native path. Optional `--podway-opt-out` is Design-only; an unsupported or absent entrypoint with this flag returns `invalid-arguments` JSON and exit 2 before native imports, discovery or source work. Valid Design opt-out and non-Git `new-project` return `podway-inapplicable` and exit 0 without native dependencies or session requirements. Inspect/retain require `--source`; retain also requires
`--write-root`. Optional `--bootstrap` and `--customization-basis` have the meanings
above. `--podway <executable>` overrides PATH discovery. Repository paths resolve
through `expanduser().resolve()` before applicability checks; native repository paths then resolve to their owning Git root. The launcher emits source/binding, byte size/hash for
source bytes, lookup diagnostics and actual session context. `retain` returns
`retained` and may prepare material while disclosing an existing session conflict;
it does not resolve that conflict. Native inspection and resume success return `ready`; `context` returns the mapped statuses below, and the non-native Design branch returns `podway-inapplicable`. Transition actions use `--transition-input`, `--qualification`, actual `--consent` for execution/recovery, and optional explicit `--replay`, as specified above; their exit-0 statuses are `replacement-consent-required`, `same-request-replay-available` and `superseded-prepared-resolved`. Conflicts and
failures return status/message/interpreter/details JSON and exit 2; success exits
0. Native runtime diagnostics appear in `details.probes`, and conflicting tuple
and lifecycle in `details.session`. Argument-parser usage errors exit 2 with
stderr usage text; `--help` exits 0 with help text. Missing adaptive dependencies
instead return status, dependency and interpreter before native work. An
unresolved resume returns its lookup failure status, including `missing`.

Admission statuses distinguish `missing-prerequisite`, `missing-session`,
`runtime-unavailable`, `unsupported-runtime`, `runtime-failure`, `native-invalid`,
`incompatible`, `not-established`, `route-unavailable` and `session-conflict`.
Storage failures include `corrupt`, `ambiguous`, `unsupported`, `unsafe`,
`tracked-conflict`, `ignore-conflict`, `publication-conflict` and `git-error`.
Direct native failures retain their Error v2 code. No status establishes actual
agent execution or installed behavior. These explicit selected interfaces do not
change ordinary handlers' all-five managed-library readiness rule.

## Commit attribution trailers

The [live-source identity helper](../../plugins/aquarium/skills/task-commit/scripts/source_identity_digest.py) reads one UTF-8 native identity JSON object from stdin and prints its `sha256:<64-hex>` metadata digest. It uses Mulgae's field order and Go JSON escaping, independently of input formatting, key order or stdin text encoding. Invalid JSON, missing or extra fields, incorrect field types and invalid UTF-8 encoding return exit 2 without a digest. Schema validation and equality with retained preflight and receipt-bound run evidence remain caller responsibilities under the [evidence contract](../../plugins/aquarium/references/evidence-residency.md#promote-live-source-evidence-v2). It reads no native runtime files and writes no state.

The [commit attribution contract](../../plugins/aquarium/references/commit-attribution.md) requires each of the Git trailers `Aquarium-Workflow`, `Aquarium-Epic`, and `Aquarium-Task` to occur once. It defines verified `none` values, native ID preservation, and the change-origin handoff. `task-commit` parses both the prepared and post-hook message with Git. These fields describe workflow ownership; they do not replace native evidence or prove authorization.

## Roadmap Commit Hook

`plugins/aquarium/hooks/task_commit_gate.py` is a trusted local Codex PreToolUse guard for direct shell `git commit` commands. It resolves the Git root, inventories tracked roadmap candidates, and denies a direct commit when an active roadmap lifecycle requires the `AQUARIUM_COMMIT_GATE=task-commit-v1` marker. A marked commit also requires non-empty effective `user.name` and `user.email` values from Git local or worktree configuration; system, global, and command-scope values are not repository identity.

The hook is advisory rather than a security boundary. Indirect commits may bypass it, and the marker does not prove task ownership, correct lifecycle transition, safe staging, user authorization, or the final commit identity; `task-commit` remains responsible for pinning and verifying both author and committer.

## Interface Change Rules

- Change a schema identifier when a consumer-visible JSON contract changes incompatibly; update every consumer and fixture in the same change.
- Preserve structured error envelopes and nonzero exits for invalid arguments, unsafe paths, unsupported versions, malformed external output, and unverifiable authority.
- Keep inspection read-only and bounded. Mutation belongs to the owning skill after an exact proposal and approval.
- Treat a green parser or schema validator as proof of only that structural contract; add scenario coverage for approval, lifecycle, ownership, and handoff behavior.

The bundled `.mcp.json` starts the installed `aquarium-dev` stdio server. Its six `aquarium_dev_*` tools map to diagnose, enroll, repair-hook, rebuild, service-plan, and service-apply and return the same JSON envelopes as the CLI, with MCP `isError` set for failures. The bundled `tools/aquarium-dev/install.py` provides read-only runtime diagnosis and an explicitly approved install/update operation; runtime identity and setup failures use `aquarium-dev-runtime/v1`, `aquarium-dev-runtime-inspection/v1`, and `aquarium-dev-runtime-error/v1`.

The v23 repository inspector removes `.mulgaeignore` from the Mulgae configuration inventory. It admits stable Mulgae v0.1.25 or newer and command-result v19 or newer, while retaining the Doctor v5 member name `config_v3` for native Config v5 diagnostics.

The [qualification CLI](../../plugins/aquarium/shared/qualify_adaptive_procedure.py)
accepts `--repository`, `--assignment <file-or->`, `--podway <exact-binary>`,
optional `--assessment <ordinary-report-file>`, `--combined-task-plan` and
`--retain`. The preparation CLI's optional `--bootstrap` adds recording topology
for changed/new sources without modifying known reuse or plan-only behavior.
Qualification returns exact target and ordinary Judge assignment when assessment
is due (exit 3), `qualified` or `qualified-known` on current passage (exit 0), and
a distinct JSON failure (exit 2). The shared adaptive contract defines scoped
phase/global criteria, bootstrap artifact representation, current retention
authority and in-session reassessment. No helper starts a session or activates a
handler. Closed optional binding semantic/capability maps retain static custom
operation definitions inside the existing two-file/hash boundary.

Adequate unchanged adaptive reuse uses a candidate's actual `prior_suitability`
ordinary report together with its exact retained binding/source, current native
and structural proof and original-source fit. It returns `qualified-known`
without a new Judge assignment. Bootstrap timing is `established-reuse`; its
artifact evidence is an ordinary selection checkpoint carrying prior definition
evidence and current applicability, never an old report relabeled as current.
Plan-only cannot run the retained native proof and reports not-established
without writing or generating an alternative. A material in-session basis change
uses the existing reassessment route. Live review ordinals, remaining grants and
native retrieval handles alone do not invalidate an unchanged definition.

## Activated adaptive execution consumer

`manage_adaptive_procedure.py` also accepts positional `context`, `--qualification`
(ordinary assignment plus actual due assessment JSON), `--binding` for selected
inspection/retention, and optional exact `--session` for continuation. The setup
inspector forwards corresponding `--podway-binding` and
`--podway-qualification` values only in selected mode. Resume resolves its
binding path from the retained native tuple before qualification; it does not
require a bootstrap item to be selected.

On the native path, `context` needs an existing session and the exact ordinary invocation context. It returns `prepared-resolved`, `dispatch-ready`, `primary-owned`, `attachment-required`, `stop-before-work`, `terminal-resolved`, or Design/Diagnosis `approval-required` / `reapproval-required`, with native
status/templates, active items, selected evidence, current role/capabilities,
due phase skills, original authority and an ordinary v2 dispatch when applicable.
The Design/Diagnosis approval statuses return no dispatch; they preserve the actual exact-diff approval and changed-target reapproval boundary. Successful read-only resolution exits 0, including those approval stops and a requested handoff stop. The early `podway-inapplicable` exit-0 branch needs no session;
errors retain status/message/details and exit 2. Terminal state does not imply
achievement. Missing topology preserves the running session; `context` does not replace it. The separate explicitly consented transition actions own that mutation. This context adapter launches no agent and performs no native mutation.
Before start, qualification keeps exact raw requirement-source pins. On
in-session re-entry, it compares the complete extracted criterion/part basis
with the approved coverage basis while retaining original provenance and report
targets. Non-affecting edits outside that basis do not force another assessment;
real requirement, authority, plan, review or execution-definition changes retain
their stop or reassessment route. A handoff boundary uses native selected
artifact evidence when declared, and otherwise the previously verified ordinary
checkpoint metadata with current session/attempt and exact-byte checks.

The [execution contract](../../plugins/aquarium/references/adaptive-execution.md)
owns invocation mappings, actual independent assessment/bootstrap import, due
Task leaf loading, plan artifact verification, same-operation retrieval and
commit-success/finalization recovery. Original source coverage and applicable
review/acceptance/grants remain ordinary workflow responsibilities.

## Reusable Procedure preservation

`shared/promote_adaptive_procedure.py offer|apply --repository <worktree>
--input <closeout-json-or-dash> --podway <explicit-binary>` uses the
[ordinary closeout input and exact content consent](../../plugins/aquarium/references/procedure-promotion.md).
`offer` is read-only and returns grouped `preservation-offer` source/binding or
fragment/mapping/representative payloads, proposed diffs and native checks.
`apply` returns `preservation-declined` for an empty accepted subset, or
`promotion-applied` for exact consented content after original accepted commit or
verified no-commit and required native finalization. Optional matching promotion
commit authority produces a task-commit handoff; the helper never stages or
commits. Success returns exit 0; typed input, consent, finalization, path,
prerequisite and native failures return JSON status/message/details and exit 2.
A supplied mismatching/consumed promotion grant returns exit 2
`commit-authority-required` with `details.applied`: consented files already exist
uncommitted, and no commit handoff is produced. Same-proposal recovery preserves
those files and can accept a matching grant. Local recovery material and original
lifecycle remain unchanged.

The guest-only driver adds `seed-development` and `development` for the
[seven-entrypoint case inventory](../../tests/vm/fixtures/adaptive/cases.json).
Its fixed canonical release regressions remain separate. Exact candidate/tools,
public native role/result and selected evidence, original criteria, application
approval and case oracles must pass; helper tests do not establish installed
behavior. See [VM usage](../../tests/vm/README.md).
