---
name: release-qa
description: "Run one full scenario-based QA pass for an exact main release candidate, or one bounded confirmation pass after that full pass produces remediated findings. Use when the user explicitly invokes $aquarium:release-qa with an intended release version or asks it to propose and confirm one."
---

# Release QA

Assess one exact committed `main` candidate in either `full` or `confirmation` mode. A first pass is always `full` and uses two independent matrices: every active Design Gate and every material release-delta change. A later pass may use `confirmation` only under the bounded contract below.

Treat existing automated checks as already successful and mutate only disposable fixtures under `/tmp` during the QA pass. One invocation owns exactly one QA pass and, when a full pass has verified findings, at most one bounded remediation phase. It never starts a second QA pass by itself.

Explicit invocation authorizes read-only release discovery against the configured Git remote and hosting Releases, including use by those clients of already-configured ambient authentication without exposing credential material.

It also authorizes creation and mutation of bounded `/tmp` fixtures, fresh subagents for local QA, and the smallest local source, test, or documentation remediation directly required by verified findings after the QA pass completes. Run only focused checks needed to verify that remediation; the repository release policy remains authoritative for any later full gate.

It does not authorize staging, commits, pushes, tags, releases, networked or live product scenarios, credential inspection or changes, new authentication, global installation or configuration, persistent daemons, or a second QA pass. Preserve unrelated work. Stop before remediation when a finding needs a material product choice, authority expansion, or unrelated refactor, and report that decision instead.

## Establish the Release Contract

1. Resolve the Git root and read all applicable instructions and release policy. Inspect the worktree, conflicts, current branch, `HEAD`, local `main`, upstream, remote `main`, existing tags, and configured hosting Releases. Record the exact candidate SHA.
2. Require a clean worktree and one unambiguous committed candidate where `HEAD`, local `main`, upstream, and remote `main` agree. Treat read-only remote and hosting metadata lookup needed to establish those facts as explicitly authorized release discovery, not scenario authorization.
   - Permit the configured Git and hosting clients to use existing ambient authentication for private repositories, but never inspect, read, copy, print, persist, refresh, or reconfigure credential material and never initiate an authentication flow.
   - Return `INCOMPLETE` when access fails or the candidate, remote state, or published release authority cannot be established; never fetch, merge, switch branches, stash, or clean to repair it.
3. Accept an intended release version supplied by the user. Otherwise follow repository version policy; when none exists, propose the next patch after the latest stable release and obtain confirmation before QA. Treat the intended version as the prospective release identifier, not as a required value in candidate files. Do not edit version metadata.
   - Proceed whether committed version metadata still names the previous release or already names the intended version. Neither state is an `INCOMPLETE` condition or finding by itself.
   - When the candidate already contains the intended version, include that version change in the release delta and inspect its manifest, documentation, and pinned-validation consistency.
   - Do not run tag-time validators or require target-version metadata merely to establish the QA candidate. A dirty worktree still prevents an exact committed candidate under step 2, regardless of which files are dirty.
4. Resolve the previous release from the latest non-draft, non-prerelease published Release reachable from the candidate, or from an exact tag explicitly confirmed by the user. Stop on conflicting tags or Releases, an existing target-version tag or Release, or a baseline not contained in the candidate.
5. When no release tag exists, ask whether this is the first release and confirm its intended version. After confirmation, use the full reachable history and current public surface as new-release scope, with no regression baseline. Without confirmation return `INCOMPLETE`.
6. Define the delta solely from Git history as every commit after the previous release through the candidate, independent of the version currently recorded in candidate files. For example, with previous release `v0.2.3`, ten later candidate commits, and intended version `v0.2.4`, cover all ten commits whether the files still say `v0.2.3` or already say `v0.2.4`. When that range is empty, report that there is no release delta and return `INCOMPLETE` rather than `PASS`.

The previous release is assumed to work. Inspect its committed code, documentation, and tests only to reconstruct established behavior; do not check it out or execute it.

## Select Full or Confirmation Mode

Use `full` mode unless the enclosing release workflow supplies a confirmation manifest under `/tmp` that records all of the following exact facts:

- the intended version, previous release, current candidate SHA, and previous full-pass candidate SHA;
- the retained previous evidence root and the non-empty remediation commit range ending at the current candidate;
- the previous five-cluster matrix, every verified finding reproduction scenario, and every source surface changed by remediation;
- `confirmation_attempt: 1`, with evidence that no earlier confirmation pass was started for this full-pass candidate and remediation range.

Reject `confirmation` as `INCOMPLETE` if the manifest, retained evidence, exact Git objects, ancestry, remediation range, or one-attempt fact cannot be established. The confirmation candidate must still satisfy the clean and unambiguous committed-`main` rules above. A confirmation manifest is disposable workflow evidence, never repository authority; do not copy its date, intermediate candidate SHA, or evidence path into repository documentation.

In `full` mode, follow every section below and explore the complete Design Gate and release-delta matrices. In `confirmation` mode, do not rebuild or broaden those matrices. Dispatch fresh workers only for these five fixed clusters from the previous matrix:

1. commit-hook behavior, covering the previous matrix and the confirmed bypass and false-positive scenarios;
2. test-inspector environment, command, and framework scenarios;
3. dev-setup malformed output plus the previous MCP and manifest baseline matrix;
4. review-workflow validation graph and Delivery settlement;
5. shipped package, public documentation, and Procedure parity.

For each cluster, rerun every scenario recorded in its previous matrix, every confirmed finding reproduction, and every scenario whose exercised surface changed in the remediation range. Existing tests and validators remain prohibited as QA scenario evidence. Capture the same command, controlled environment, outcome, resulting files, worker identity, and source-repository status required for a full pass, but write all new evidence beneath a fresh confirmation evidence root.

Confirmation is a fixed verification pass, not a new edge-case search. Do not invent additional Bash syntax variants, fuzz parser inputs, or probe new generated-directory names. Do not turn a hook boundary that the candidate publicly documents as incomplete into a release blocker. A directly observed failure of a fixed scenario remains a finding; this restriction only forbids expanding the scenario inventory.

Confirmation may run exactly once after one full pass and its bounded remediation. It returns `PASS` only when every fixed scenario succeeds and no evidence gap remains. On `FINDINGS` or `INCOMPLETE`, stop the release without remediation, another confirmation, or another automatic full pass.

Route any same-family parser hardening to a separately authorized change, or require an explicit user risk-acceptance decision outside release QA. A confirmation `PASS` ends release QA for that candidate; do not run another release-qa pass before the already-authorized release gate.

## Establish Design Gate Enrollment

Read [design-gates.md](../../references/design-gates.md). Resolve the authoritative current and retired registry paths from repository authority, using `docs/gating-rules.md` and `docs/gating-rules-retired.md` only as defaults, and determine enrollment from candidate history, not only the current tree.

- If no Design Gate registry has ever existed in reachable history, run the release-delta matrix alone and report `Design Gate not enrolled`. This gradual opt-in is not a finding and does not block `PASS` when delta coverage is otherwise complete.
- If a registry existed in history but the candidate is missing its authoritative current path, record a contract finding. Never reinterpret deletion as opt-out.
- When the registry exists, parse every active gate and require its stable ID, concise title, invariant, scope, positive and failure scenario, local offline source-read-only procedure, declared disposable outputs, objective pass condition, revalidation triggers, sources, and owner. A malformed active entry is a contract finding; an unexecutable required gate or missing evidence makes the result `INCOMPLETE`.
- Exercise every active gate against the exact candidate, including gates unchanged in the release delta, under the disposable-project isolation regime below. Redirect its declared outputs and caches into the evidence root, compare source-repository status before and after each gate, and stop with `INCOMPLETE` on mutation. Keep its command, controlled environment, positive and failure outcomes, pass condition, and evidence path in an active Design Gate matrix. A verified active-gate failure is a finding.

Gate additions, changes, reactivations, retirements, current tombstones, and retired-registry changes also belong to the release-delta matrix. Confirm that every retirement leaves a current tombstone in the resolved current registry and preserves the full retired body and rationale in the resolved retired registry. Confirm that every reactivation restores the same ID as one active current body, removes its current tombstone, retains retired history, and appends a reactivation record.

Do not invoke providers or network services for a gate. A gate that requires either violates the Design Gate contract and cannot supply executable release evidence.

## Build the Release Delta Matrix

Read the commit list, complete diff, current public documentation, changed skills and instructions, runtime entrypoints, and relevant existing tests. Do not treat commit subjects as sufficient evidence.

Map every commit and material changed surface to one or more release-delta scenarios:

- an existing-behavior regression scenario derived from the previous release contract;
- a new-behavior success and failure scenario derived from the candidate contract;
- a changed-skill representative, boundary, or misuse prompt;
- a documentation, example, link, installation, or cross-file consistency inspection.

Give every user-visible or operationally risky change at least one executable scenario. Static inspection is sufficient only when the changed contract has no executable behavior. Record exclusions with exact evidence instead of silently sampling them away.

Do not run existing automated tests, `make test`, test runners, test scripts, linters, formatters, validators, generators, snapshot updates, CI commands, Gaori, Mulgae, or provider reviews as release-delta scenarios. Existing tests may be read as specifications, but their presence or prior success does not prove the release scenarios. The sole exception is an exact local offline procedure registered by an active Design Gate; execute it only in the Design Gate matrix and do not count the same run as release-delta scenario coverage.

## Exercise Disposable Projects

1. Create one evidence root with `mktemp -d /tmp/release-qa.XXXXXX` and a separate fixture directory for each scenario. Record the root and retain it for user inspection.
2. Use the current repository's candidate binaries, source entrypoints, scripts, skills, documentation, and other resources by exact path. Do not clone or execute the previous release. Keep the source repository read-only and confirm its Git status is unchanged after every scenario group.
3. Redirect `HOME`, XDG directories, temporary state, build outputs, and language or tool caches into the evidence root wherever applicable. Never write user-global state or rely on ambient credentials.
4. Prefer an existing candidate artifact. When execution requires a build, run only the smallest non-test build whose outputs and caches can be isolated under `/tmp`; do not permit network access or global installation. Record an evidence gap when a safe isolated build is impossible.
5. Keep scenarios offline and local by default. Do not contact live services, authenticate, start a persistent daemon, or send repository content externally. Record the blocked scenario as an evidence gap unless the user separately authorizes the exact external action.
6. Capture the command, working directory, controlled environment, exit status, output, and material resulting files. Stop local background processes before completing the scenario.

## Dispatch Fresh Scenario Agents

Use the available agent delegation surface to dispatch fresh subagents for independent risk clusters. Give each worker only the exact candidate paths, raw baseline contract and delta relevant to its cluster, assigned `/tmp` fixture, and scenario objective. Do not disclose suspected findings, expected defects, intended fixes, or another worker's output.

Require every worker to avoid existing test commands, source-repository writes, network access, credentials, global state, remediation, release-readiness decisions, and next-action recommendations. A worker may mutate only its assigned fixture and must return commands, observations, evidence paths, and source-repository status; the coordinator alone assigns final severity and status.

Do not replace an unavailable, failed, or timed-out fresh worker with coordinator execution or static review. Mark its required coverage as missing and return `INCOMPLETE`. Parallelize independent clusters when capacity allows without weakening isolation.

Adjudicate every worker report against the release contract and candidate. Reproduce a suspected defect in a clean sibling fixture or confirm it directly from deterministic evidence before accepting it. Put unreproduced, environment-dependent, or authority-dependent claims under evidence gaps, not findings.

## Report and Enforce the Convergence Boundary

Choose one overall result in this order across both matrices:

1. `INCOMPLETE` when any required release fact, active-gate execution or evidence, delta scenario, fresh-worker result, or safe execution prerequisite is missing, even when verified findings also exist.
2. `FINDINGS` when both applicable matrices are complete and at least one verified active-gate or release-delta defect remains.
3. `PASS` only when the active Design Gate matrix, when enrolled, and the release-delta matrix are both complete and no verified defect remains.

Return the intended version, previous release or confirmed first-release state, candidate SHA, commit range, Design Gate enrollment state, active-gate matrix, commit-to-scenario release-delta matrix, scenario commands and outcomes, source-repository status, retained `/tmp` evidence root, verified findings, and evidence gaps.

Classify verified findings as:

- **Critical**: security, privacy, data loss, or broadly destructive behavior;
- **High**: a core regression or promised new capability that is unusable;
- **Medium**: a bounded functional, skill, or documentation defect with material user impact;
- **Low**: a reproducible non-cosmetic inconsistency or minor usability defect.

For each finding give the violated baseline or candidate contract, reproduction steps, expected and actual behavior, impact, exact source and evidence locations, and confidence. Exclude style preferences, praise, speculative risks, duplicate symptoms, and claims the coordinator could not verify.

When the result is `PASS`, return the evidence and allow an already-authorized enclosing release workflow to continue its normal release procedure without another QA confirmation. `PASS` does not itself authorize staging, commits, pushes, tags, or publication.

When a full-mode result is `FINDINGS`, complete the current QA report first, then leave QA mode and implement only the smallest safe fixes for the verified findings. Add or adjust focused regression coverage when the finding is executable, run only the focused checks needed to verify the edits, and preserve unrelated work. Do not broaden remediation into general hardening, accept speculative edge cases as new scope, update evidence documents merely to bind an intermediate candidate SHA, stage, commit, push, or start another QA pass.

A confirmation-mode result never authorizes remediation; apply the stop and escalation rule in the confirmation contract instead.

After remediation, report the findings, why each required correction, the exact files changed, focused checks and outcomes, remaining uncertainty, and current Git state. Then stop and ask for explicit user confirmation before preparing a new committed candidate or running release QA again. The original release request, prior confirmation, silence, or a successful focused check is not confirmation for another QA pass.

When the result is `INCOMPLETE`, report the missing prerequisite or evidence and stop. Do not reinterpret incomplete coverage as a finding-remediation cycle and do not retry automatically.

After the user explicitly confirms the one bounded confirmation review, prepare a clean exact candidate only through the enclosing repository workflow and begin one new release-qa invocation with the required confirmation manifest. Do not substitute another full pass or a looser delta review. If confirmation does not pass, stop under its escalation rule; never enter an automatic review-remediation loop.

Version metadata may be committed before or after a passing QA run; its timing never narrows the original full-pass delta or substitutes for scenario evidence.
