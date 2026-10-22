# Haepari VM adoption for Aquarium

## Authority and implementation state

The sole consumer is `EPIC-019`, with `TASK-086` through `TASK-090`. The [canonical roadmap](../roadmap/README.md) owns identity, ordering, dependencies and lifecycle. This dossier owns the pilot's detailed scope and acceptance. Checklists describe planned evidence, not completed implementation.

Haepari [v0.1.0](https://github.com/irootkernel/haepari/releases/tag/v0.1.0) is published with release tag commit `800da97b7e2ca84a15d4ee5921702ec57bbc7d61`. Its release notes identify the validated archive build as `fc3b975f8a99cacb96aecc988d3adbc04dda7309`; the tag adds release metadata. It provides managed local/UTM Jobs and advisory named locks. Publication removes the old unreleased-product prerequisite; TASK-086 verified and accepted the exact archive, paired skill, capabilities and backend evidence, recorded in its checklist below. This dossier records no installation or later-task result.

Planning authorization covered documents only; execution follows the approved EPIC-019 workflow authorization and the host's installed release. It authorizes no producer edits, broker messages, host cleanup or publication; staging and local commits stay with the Coordinator under the repository commit gate; candidate installation and installation-dependent checks run only in the dedicated UTM VM.

## Goal and scope

Adopt published Haepari v0.1.0 as an Aquarium tool and qualify Aquarium's own managed VM path. Haepari owns admission, execution, manual occupancy, collection and owned Job cleanup; Aquarium recipes own installation assertions, guest fixtures and consumer cleanup. Use one shared per-user controller and one capacity-one persistent UTM resource. Haepari never starts, stops, clones or resets the VM.

Aquarium owns setup/catalog integration, fixed test profiles, Make/test adapters, installed-skill and migration scenarios, result transport and the qualified release-VM policy cutover. Public external leases and linked continuation remain excluded. Ordinary local tests retain their existing authority and dependencies. No second scheduler, compatibility registry, automatic publication or host candidate installation is introduced.

Shared legacy source and runtime stay available for remaining consumers. TASK-090 may detach only Aquarium-owned enrollment under its exact authority; final common removal belongs to EPIC-033. Preserve completed EPIC-002 history, native use-* skills, production state and unrelated hooks.

### Breaking-change record

Decided during Epic planning under the repository's breaking-change rule. EPIC-019 is breaking for Aquarium's own release operation: after TASK-090's accepted cutover, the release VM gate requires the shared Haepari release controller, the registered `UTM` resource and `make test-vm-host`, so maintainers complete that one-time transition before the next release containing the cutover. The exact installed cutover candidate must pass the TASK-090 pilot in the dedicated UTM VM before any release containing it; the current manual VM path stays authoritative until that acceptance. The release is not breaking for plugin users: Haepari setup stays optional and separately approved, and existing installations need no update or migration.

## Implementation contracts

### Native authorities and tool setup

Use the release-matched [use-haepari skill](https://github.com/irootkernel/haepari/blob/v0.1.0/skill/use-haepari/SKILL.md), [managed resource contract](https://github.com/irootkernel/haepari/blob/v0.1.0/docs/contracts/resource-and-runner.md), [lock contract](https://github.com/irootkernel/haepari/blob/v0.1.0/docs/contracts/locks.md) and [Mulgae integration contract](https://github.com/irootkernel/haepari/blob/v0.1.0/docs/integrations/mulgae-review.md). Check declared capabilities and qualified backend evidence independently of the version string. Deferred external-lease commands and automatic VM reset are not acceptance prerequisites.

Accept the official archive through its published checksum and sidecar, packaged `SHA256SUMS` and recorded build identity: version stamp, `source_revision`, `source_modified`, executable digest and complete skill-tree digest. Do not require the binary's build revision to equal the release tag or rebuild it to make them match. The frozen v0.1.0 capability arrays report `compiled_backends: ["local"]` and `qualified_backends: []`. Accept running-VM qualification from the separate digest-bound producer profile, then qualify Aquarium's combination in TASK-090; setup must not require a nonempty `qualified_backends` array.

TASK-087 adds the CLI and complete same-release `use-haepari` tree to global setup, native installation/freshness inspection and the tool catalog. Preserve the upstream `skill/use-haepari/` source layout. Repository setup checks the selected controller/resource and the capabilities needed by the operation. Installation, service activation and resource registration retain their native authority boundaries; setup does not submit Jobs or reviews.

Participating projects on one macOS arm64 machine and OS user select the same installed controller through its native installation configuration, including `HAEPARI_HOME`, and the same capacity-one VM resource. Register the VM once by its native identity; do not create per-project controllers or duplicate resources for that VM. Machine-local VM/SSH settings stay in Haepari/operator configuration. Add no `.aquarium`, shadow registry or second scheduler. Ordinary local checks and read-only review inspection require no VM occupancy.

### Project-owned entrypoints and immutable input

EPIC-024 owns Aquarium's manual guest-side `make test-vm` entrypoint and reusable `tests/vm/` scenarios without a Haepari dependency. TASK-088 and TASK-089 later reuse those outputs when adding Haepari host submission and result transport. They retain their roadmap lifecycle and producer dependencies; Haepari adoption does not block EPIC-024.

Aquarium adds a separate `make test-vm-host` wrapper with `HAEPARI=<absolute-cli> RESOURCE=<registered-id> MODE=auto|manual RUN_DIR=<private-physical-path>`. Release hands-on verification uses manual mode; automatic suites use auto mode. Select only consumer-declared suites through `SUITE`, with `release-acceptance` naming the release transaction. Preserve the guest-side `make test-vm` entrypoint and its current request contract. Other producers may expose an equivalent adapter.

Before assigning submission, the Coordinator allocates a private mode-0700 run directory and includes its path in the Executor assignment. Save the request key, exact spec, installation/resource identity and sealed candidate/test/profile/scenario bytes there before first submission. Agent-owned temporary runs use a unique physical directory under `/tmp`; retain it across pending or uncertain work. The wrapper reports the Job ID and blocks through native `wait`, without a status-polling loop. A timeout or uncertain reply reconnects to the same Job or replays the identical submission key and spec. It never generates a replacement key speculatively, controls VM power or installs the candidate on the host.

The guest entrypoint stays distinct from host submission and reuses EPIC-024's `make test-vm` for Aquarium. Haepari-managed execution verifies guest/lease identity before installation and never recursively submits a job. Development snapshots may include selected dirty-worktree bytes; their content digest is the candidate identity. Release evidence must satisfy the existing exact committed/distributed candidate policy. Queue waiting must not cause later worktree changes to alter the admitted candidate.

Use the frozen v0.1.0 Job schema and its supported `development` evidence class. Consumer provenance binds committed source and release/archive identities; it does not require a new controller-enforced evidence class. Choose phase budgets and applicable resource ceilings before admission, including enough manual time for the cases, evidence staging and consumer cleanup. Reconnection never extends a deadline.

One release-acceptance Job holds the VM continuously from the first baseline observation through candidate installation, automatic/manual scenarios, evidence collection and owned cleanup. Do not release between an upgrade and its assertions, or between preparation and hands-on work. Independent suites may use separate Jobs only when each checks and establishes its own starting state. `SUITE=all` retains every Job result and reports skipped or unobserved required work; it never turns a partial run into aggregate PASS.

### Managed VM execution

Adopted UTM verification uses native managed Jobs, including `awaiting_manual` occupancy and revision-bound manual completion. Return capacity through Haepari settlement after execution, required collection and owned cleanup. A wait timeout does not cancel or release a Job. Unknown execution follows native reconciliation and recovery; elapsed time or an empty process list cannot prove termination. EPIC-024's accepted historical manual results keep their original meaning.

### Delivery sequence and release ownership

The roadmap orders four complete Epics: EPIC-019 -> EPIC-031 -> EPIC-032 -> EPIC-033. EPIC-019 owns TASK-086 through TASK-090 and closes after the Aquarium pilot and canonical handoff. EPIC-031 then consumes the accepted adapter for release-role orchestration. EPIC-032 owns the nine producer returns, including Mulgae's native advisory integration. EPIC-033 owns whole-combination verification and shared legacy retirement. No later Epic resumes EPIC-019 or depends on this temporary dossier surviving its closeout.

Adoption means acceptance of TASK-090's exact cutover candidate after its installed pilot passes. TASK-089 prepares the adapter; TASK-090 updates `AGENTS.md` Release Policy, `TESTING.md`, `tests/vm/README.md` and affected release-handler references to select `make test-vm-host` and native managed-Job semantics before that candidate's verification and acceptance. The pilot uses its explicit VM-test authority. The current release path remains authoritative until the cutover is accepted. EPIC-019 does not require EPIC-031's future roles or EPIC-032's future Mulgae release to pass its pilot. Any later installed-source change requires affected observations again. Host activation and publication retain their separate authority.

After that cutover, Aquarium-owned installation-dependent checks targeting the same registered shared VM use the accepted managed adapter for occupancy, including development checks and any later EPIC-030 qualification. Acquire once at the outer host boundary; guest entrypoints and nested handler fixtures work inside the held Job without recursively acquiring its resource. Work targeting another environment follows its own authority. Native exclusion covers participating callers using the selected installation/resource; it does not police direct access that bypasses Haepari. Carry this occupancy requirement into the durable VM/testing guidance at TASK-090 closeout.

The adapter returns original candidate-bound results, evidence completeness, consumer cleanup and native disposition separately. Its canonical handoff identifies the selected controller/resource, saved request/spec/Job, native wait/recovery and cleanup responsibility. EPIC-031 maps those facts into its existing v3 roles and assessments without another scheduler or report schema.

### Baselines, profiles, and release combinations

Aquarium's native tool catalog continues to own support ranges and installation rules. A project-owned test profile selects exact binary, daemon, plugin, skill, rules, and effective configuration identities within those policies. It is immutable test input, not a second account-wide setup registry. Machine-local VM registration, package paths, SSH identity, and resource state belong to Haepari/operator configuration.

Normal development uses an explicitly accepted stable combination and overrides the selected product's entire declared candidate unit. A skill-only change can override its skill tree while retaining the binary. A next-release integration can select a named candidate combination. Resolve any default/latest alias before admission and retain its exact profile digest; never fetch latest while an admitted job executes.

Aquarium's final installed VM release gate applies the complete intended tool/skill combination, including unchanged pinned components. Candidate integration evidence and final official-distribution evidence remain distinct. If final binary or skill bytes change, prior evidence cannot silently qualify the new bytes.

### Complete skill and configuration identity

Compare complete incoming and installed skill trees, not only `SKILL.md` or an inspector's minimum file list. Include references, scripts, assets, executable bits, added/removed files, native source provenance, and effective connection settings. Binary and skill identities are separate; preserve independently pinned skills and same-release pairings according to the current native contract.

Honor the selected upstream installation scope, including shared `~/.agents/skills`, the active `<CODEX_HOME>/skills`, per-home rules, plugin-owned resources, and project discovery roots. Check duplicate/shadowing copies that the selected native client can load. Do not unify these roots or copy the host's active home into the VM.

Installation correctness, discovery in a fresh native process/session, observed skill behavior, and restoration are separate evidence classes. Pasting skill text into a prompt or executing a binary directly cannot qualify installed-skill discovery. Preserve missing manual observations as unverified; neither Haepari nor Aquarium invents a human pass.

### Migration and regression

A migration scenario begins with the exact prior supported installation combination and creates meaningful synthetic state through its old public interfaces. Verify the old behavior and record preservation invariants before applying the candidate. Keep the same data and configuration through update, then verify reads, new writes, restart, skill discovery, and required existing workflows.

Cover configuration and custom values, binary/service pairing, skill/rules replacement and obsolete-file removal, persistent data/identifiers, and the native busy-work policy. Prove either supported resume or safe refuse/drain before update; do not invent uninterrupted-upgrade support. Include a bounded interrupted migration and its documented recovery or safe failure. A retry must not duplicate logical work.

The immediate prior accepted version/profile is the default required path. Wider advertised upgrade paths require corresponding tests. A first release records the absence of a predecessor with evidence, not a fabricated migration pass. Product downgrade is a separate native promise; restoring the test VM does not prove it.

### Manual, live, and release-QA boundaries

Manual mode prepares the exact candidate environment and holds the same exclusive resource while the authorized fixture operator or Master performs the project checklist. Preparation-ready is not a test pass. While still `awaiting_manual`, perform the cases, stage their required evidence in the Job's declared output paths, then finish recipe cleanup and verify its inventory. Record cleanup and its evidence as required manual scenarios, preserving the staged case evidence. Only then submit `manual complete` with the actual observer, candidate/profile, observations and omissions. That command starts Haepari collection and owned cleanup; there is no later consumer-cleanup hook. Automatic workloads likewise finish recipe cleanup and stage its evidence before exiting. Missing human observations or failed/unobserved consumer cleanup prevent acceptance.

Offline fixtures are default. Live service/model use requires the exact approved guest endpoints, test identities, and cost/time scope. Never copy host account files or use real Sorage/production data as fixtures. VM restoration does not reverse external writes or charges.

The current `release-qa` is an offline disposable-scenario contract and must not silently gain global installation or live-provider authority. Add a separate installed VM verification step to the release workflow and bind its evidence to the same candidate and fixed environment. Existing automated VM tests do not replace the current release-delta assessment. Keep publication and host activation separate.

### Results, cleanup, and failure

Keep Haepari's workload outcome, required-evidence completeness, owned cleanup and final verdict separate from consumer installation/restoration assertions. A successful command with missing required observations or failed consumer cleanup cannot establish acceptance. A wrapper wait timeout reports PENDING; an unavailable observation reports UNKNOWN without inventing a terminal verdict. Reattach the original Job after connection loss.

Haepari cleans its own processes and Job paths; it does not undo arbitrary guest installation changes. Each recipe declares its starting-state checks, owned installation/fixture cleanup and reusable postcondition, preserving meaningful baseline state until assertions finish. Verify the resulting inventory before claiming consumer cleanup. An independent successor checks its own starting state and cannot assume a pristine VM. Native uncertain execution or protected Job evidence follows Haepari quarantine/recovery; a consumer restoration failure remains explicit and uses supported maintenance/recovery before affected reuse. Do not claim automatic rollback or quarantine for effects Haepari cannot observe.

Retain request/spec/result records for pending or uncertain work. Stage required evidence before removing consumer fixtures; native collection follows manual completion or automatic workload termination. Cancellation or deadline expiry preserves actual native outcomes and unfinished consumer cleanup, without claiming a clean guest or extending occupancy beyond native settlement. Raw runtime IDs, local paths, Sorage metadata and provider logs remain local evidence unless reviewed bounded promotion satisfies the existing evidence-residency contract.

## Task acceptance checklists

### TASK-086: Accept Haepari and freeze the consumer contract

Implement and document:

- [x] Verify the published v0.1.0 archive against its official checksum, complete package inventory and release-matched skill, source and executable identities. Read declared managed, durable-observation, advisory-lock, recovery, artifact and retention capabilities; distinguish compiled support from actually qualified backend evidence.
- [x] Freeze the project submission/result contract and read current Aquarium test, setup, tool-catalog, evidence, release, and Sorage authorities.
- [x] Accept persistent-VM automatic/manual execution, native wait/reconnect and owned cleanup evidence plus advisory queue/replay/renew/release semantics. Exclude deferred external leases, linked continuation and VM reset. Actual Mulgae integration belongs to EPIC-032 TASK-092 and is not required to close EPIC-019.
- [x] Define fixed consumer profiles as immutable test inputs and identify durable specification/architecture/ADR owners; profiles add no global registry or account-wide policy exception.

Do not:

- [x] Do not start consumer implementation on a design-only Haepari promise, assume a version implies capabilities, send producer requests, or install/update the host without its applicable authority.

Verify and complete:

- [x] Check valid/invalid managed and lock fixtures against the exact release, supported wait/reconnect and same-key replay. Verify stale grants cannot affect a successor and observation loss cannot create duplicate Jobs. Unobserved backend evidence stays a gap.
- [x] The handoff is sufficient without a circular dependency on Aquarium adoption; all missing prerequisite evidence keeps this task incomplete.

TASK-086 verification outcome (2026-10-23): the archive and sidecar digests match the official release (`6667cab3…a18`, `fb0a83ea…531`); the complete package inventory verifies against the packaged `SHA256SUMS`; the executable digest equals the archive binary and the producer qualification binding; the paired skill tree is byte-identical to the tagged source; and `version` reports the build basis `fc3b975f…` while the release tag `800da97…` adds metadata only. The frozen capability arrays are confirmed (compiled `local`, qualified empty). Managed Job and advisory-lock fixtures against the exact release binary in a disposable foreground controller verified native blocking wait and reconnect, caller timeout without cancellation, same-key replay with `CONFLICT` on changed input, observation loss without duplicate Jobs, lock queue/replay/renew/release with same-transaction successor grants, stale-grant isolation from a successor, and manual occupancy where an unobserved scenario prevents PASS while owned cleanup runs. The producer's digest-bound running-VM qualification was reconciled from its preserved records and accepted with its recorded limits; unobserved backend evidence on Aquarium's own registered VM remains a gap for TASK-088/090. The frozen consumer contract is reserved in the tool integrations specification and its consumer reference until those tasks ship it.

### TASK-087: Register Haepari and define fixed test profiles

Implement and document:

- [ ] Add Haepari CLI and complete same-release `use-haepari` registration, provenance/freshness checks and native setup routing to `dev-setup-global`, repository readiness, the tool catalog and affected status/bundle inventories where those enumerate supported components. Keep setup effects separately authorized and avoid requiring a live VM for ordinary local checks.
- [ ] Define common installation/resource selection and operation-specific capability checks. Preserve native private service/resource/SSH configuration, whole-tree skill comparison and the distinction between binary, controller and backend readiness.
- [ ] Add fixed candidate/test/profile inputs, native component/skill pins, candidate overrides and before/candidate/post-cleanup inventory contracts. Define product-absent and prior-version starting states and supported upgrade edges without a baseline-reset service.

Do not:

- [ ] Do not vendor upstream skills, commit credentials/local VM registrations, duplicate tool-catalog support authority, or resolve latest after admission.

Verify and complete:

- [ ] Validate missing/incompatible CLI or capability, mismatched installation/resource, duplicate skill locations, full-tree differences, independently pinned cases, settings drift and profile changes. Setup must not submit workloads or replace native configuration with a shadow registry.
- [ ] Profile definitions are reproducible test inputs and do not claim an actual VM was provisioned or a migration passed.

### TASK-088: Implement Aquarium's project-owned VM suites

Implement and document:

- [ ] Add the separate Haepari host wrapper, reusing EPIC-024's guest entrypoint and scenarios, with an immutable package/test bundle and truthful per-suite result mapping.
- [ ] Add actual candidate plugin installation, initial setup, previous-version synthetic state, upgrade, existing-behavior regression, restart and bounded migration failure/recovery scenarios.
- [ ] Keep managed UTM/SSH transport and owned Job collection/cleanup in Haepari. Recipes own guest installation/fixture changes and starting-state checks. Preserve ordinary local tests and EPIC-024's accepted historical evidence.

Do not:

- [ ] Do not install the candidate on the host, recursively enqueue from the guest, fabricate prior state with the new version, or erase migration state before assertions.

Verify and complete:

- [ ] Demonstrate one uninterrupted release-acceptance Job, manual hold, evidence staging and verified consumer cleanup before manual completion, automatic cleanup before workload exit, independent-suite starting states, queued-source immutability, missing-VM blockers, guest identity rejection and truthful result/cleanup failure propagation. Reconnect with the saved run directory after observation loss without a replacement Job.
- [ ] The actual plugin package, configuration and supported prior behavior are exercised; source-level tests alone do not complete this task.

### TASK-089: Integrate skills, hands-on and the VM release gate

Implement and document:

- [ ] Add complete skill/rules/configuration installation inspection and fresh native session discovery, representative workflow behavior and explicit manual observation records.
- [ ] Prepare the managed extension of EPIC-024's manual release step and candidate/profile-bound result transport for TASK-090's qualified policy cutover, preserving invocation authority, offline release-QA and publication authority.
- [ ] Define full intended release-combination and existing-stable-to-candidate upgrade scenarios, plus final distribution identity checks.
- [ ] Define controller/resource/Job identity, original observations and disposition responsibility for the existing release path. Promote that adapter contract before EPIC-019 closeout so EPIC-031 can consume it through existing assignments and handoffs; release-role implementation belongs to EPIC-031.

Do not:

- [ ] Do not substitute file hashes or pasted instructions for installed-skill behavior, auto-grade Master, contact providers by default, or broaden the existing release-qa invocation implicitly.

Verify and complete:

- [ ] Observe required actual installed-session and hands-on cases, including duplicate or stale skill failure, and verify cleanup restores the original discovery/configuration state.
- [ ] Missing human/live evidence remains incomplete and cannot be accepted through a successful Make exit alone.

### TASK-090: Qualify the Aquarium pilot and prepare Epic closeout

Implement and document:

- [ ] Run the Aquarium-only pilot with install/migration/regression/manual evidence, disconnect/cancel/collection/cleanup failures and a successor that verifies its own starting state. Use two disposable project callers against the same capacity-one VM resource and observe actual non-overlap and handoff.
- [ ] Prepare the canonical release-policy cutover in this Task's candidate and verify that exact installed candidate under explicit pilot authority before accepting adoption. Update `AGENTS.md`, `TESTING.md`, the VM guide and affected release-handler references together; preserve EPIC-024's historical manual results. Do not leave this operational policy change until TASK-102 or accept the cutover from wrapper availability alone.
- [ ] Promote the accepted setup, adapter, profile, skill/migration and recovery contracts with their actual verification limits. Supply the stable Haepari identity and reusable request/completion templates as canonical handoff inputs; EPIC-032 TASK-091 freezes producer packets after EPIC-031 closes.
- [ ] Inspect Aquarium's own legacy enrollment and, after explicit approval, detach its owned hook and development use while retaining shared infrastructure required by later producers.

Do not:

- [ ] Do not dispatch external projects before pilot acceptance, delete the shared manager, treat mock-only UTM evidence as sufficient, or label an acknowledgement as producer completion.

Verify and complete:

- [ ] Host stable Aquarium/tools/skills remain usable; runtime changes are confined to approved Haepari/test/own-detachment state.
- [ ] All pilot criteria and required manual observations are satisfied. Prepare independent whole-Epic validation, Master's overall acceptance, canonical outcomes and this dossier's deletion without waiting for producer returns or shared-channel retirement.

## Epic acceptance, handoff and dossier deletion

- [ ] TASK-086 through TASK-090 meet their criteria, the exact installed pilot passes, required actual manual observations exist and the accepted policy cutover matches the tested candidate.
- [ ] Independent whole-Epic validation covers setup, complete skill/profile identity, installed upgrade, shared-VM contention, manual occupancy, same-Job recovery and both native and consumer cleanup.
- [ ] Promote setup/adapter/profile and skill/migration contracts to [tool integrations](../specs/tool-integrations.md), the tool catalog, workflow specifications/architecture and affected native references; promote verification and operating requirements to `TESTING.md`, `tests/vm/` and operations. Include an accepted component/profile inventory and actual limitations usable by later Epics without raw runtime reports.
- [ ] EPIC-031 and EPIC-032 read EPIC-019's Canonical Outcomes and those durable owners. No producer return, Mulgae implementation, whole-combination pass or shared retirement is a completion criterion here.
- [ ] Obtain Master's actual overall acceptance; replace only EPIC-019's Detailed SOT with valid Canonical Outcomes. Replace every temporary navigation pointer, remove this dossier's TODO entry and delete this exact dossier under the approved closeout envelope. No other Epic declares it as an execution SOT; do not retain or archive it for later work.

Pilot acceptance, release publication and host activation remain separate states. Missing mandatory evidence keeps EPIC-019 incomplete; planned successor work does not.
