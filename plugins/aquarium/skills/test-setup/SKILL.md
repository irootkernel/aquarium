---
name: test-setup
description: "Audit, propose, and configure Aquarium's common Make or Bun testing contract for one repository, including evidence-backed legacy waivers. Use when the user explicitly invokes $aquarium:test-setup for test infrastructure or TESTING.md setup."
---

# Test Setup

Establish one repository's common test entrypoints and evidence without turning missing coverage into a passing facade. This standalone setup workflow may operate independently of roadmap tasks, but it never stages, commits, pushes, publishes, creates Aquarium state, or advances a Podway session.

Read [contract.md](references/contract.md), then read the applicable sections of [profiles.md](references/profiles.md) after detecting the repository languages and root orchestration authority.

## Establish the Repository

1. Resolve one Git root and read every applicable instruction file.
2. Inspect HEAD, branch, upstream, staged, unstaged, untracked, and conflicted state. Preserve unrelated work.
3. Read only regular non-symlink root Makefiles, package manifests and lockfiles, test configuration, CI, existing test suites, public usage documentation, non-secret environment setup, and root `TESTING.md` when present. Reject any symlinked authority or ancestor before reading it.
   Never read credential values or open `.env*`, authentication, key, token, secret, or credential files. Derive variable names only from non-secret documentation or templates proven to contain placeholders, or from redacted output of the owning tool; report a gap when values would be required.
4. Resolve this skill's directory and run `python3 <skill-directory>/scripts/inspect_testing.py --repository <git-root>`. Treat its JSON as conservative structural evidence only: it does not execute Make, Bun, tests, formatters, package hooks, or arbitrary project code and cannot prove test semantics or waiver equivalence.
5. If Python is unavailable or the inspection fails, report the gap and perform the same read-only inspection manually. Do not install a runtime or dependency as a fallback.

Classify the root as `make`, `typescript-bun`, or `polyglot-make`. A TypeScript subproject does not displace a polyglot repository's root Make authority. If multiple plausible product roots remain after inspection, ask the user to select the intended root before drafting changes.

## Audit the Contract

Build a rule-by-rule matrix using the stable `AQTEST-*` IDs in the contract reference. For each rule report `conforming`, `nonconforming`, `not applicable`, `waived`, or `unverifiable` with exact file and command evidence. For `AQTEST-009`, compare manifest and lockfile declarations, runner configuration, commands, imports, and representative tests with the canonical framework profile; a dependency name alone does not prove that the suite uses it.

Inspect the actual tests rather than trusting names. Unit scope is one isolated logical unit, not necessarily one source file. Integration scope may cross internal packages or components but must not depend on a separately managed database, container, network service, or live provider. End-to-end scope must drive a production-equivalent artifact only through public CLI, API, browser, or device interfaces.

Do not accept a successful empty target, unconditional skip, marker file, test count, directory name, or green CI badge as semantic coverage. A required target may report `not applicable` only when the layer has no possible subject in this product and `TESTING.md` records the evidence; absent coverage is not `not applicable`.

## Resolve Legacy Waivers

Waivers are available only for a pre-existing test arrangement whose relevant history predates the first `test-setup` proposal. They do not apply to a new project or new test design.

Before proposing one waiver:

1. Identify the exact waivable rule, existing implementation, evidence of equivalent or stronger behavior, migration risk, residual risk, and revalidation triggers.
2. Reject a waiver for common entrypoints, serial fail-fast execution, unit or integration isolation, silent E2E skipping, or production-environment safety.
3. Ask Master to approve that exact waiver. Approval of setup, another waiver, or the final file diff is not waiver approval.
4. Record only an approved waiver in `TESTING.md`; never make a Make or Bun handler read the document to bypass a test.

An existing npm, pnpm, or Yarn TypeScript project may retain its package manager only through an approved `AQTEST-008` waiver while preserving the four package scripts and Make adapters. An existing nonstandard but equivalent black-box E2E runner uses the same rule.

An existing noncanonical test framework uses `AQTEST-009`; its waiver may preserve that framework for subsequent tests in the same existing layer to prevent intra-project fragmentation, but never authorizes a newly introduced layer. Revalidate a waiver when any named trigger in the contract occurs.

## Align Optional Gaori Evidence

Gaori remains optional. Its absence is not a test-contract defect, and this skill does not install or update it. When `.gaori/tester.yaml` exists or Master explicitly includes Gaori mapping in the proposal, read the Gaori section of [profiles.md](references/profiles.md), inspect the exact command output family, and map only single-format commands to specialized parsers. Keep aggregate and mixed-output stages on `generic`.

If a Gaori binary is already available, `gaori parsers list` is a permitted read-only availability check. It does not prove support maturity or parser correctness. Do not run Gaori tests, change the Gaori repository, or claim cross-repository synchronization from Aquarium configuration alone.

## Propose the Complete Change

Reuse existing suites and commands before adding structure. Map extra gates into the nearest common stage instead of inserting peer stages into the aggregate. Do not duplicate a handler behind Make and Bun or replace meaningful existing coverage merely to normalize file layout.

When coverage is missing, design and include meaningful scenarios that prove the layer's boundary. Do not create placeholders or passing no-op tests. If complete coverage requires unresolved product behavior, credentials, production-like infrastructure, or a material test hook, resolve that decision before presenting an applicable proposal.

Prepare one complete diff for every affected Makefile, package manifest, lockfile, test, test-only environment definition, and root `TESTING.md`. State which commands can rewrite source, create processes, bind ports, create containers or volumes, contact a sandbox service, or incur cost. The proposal may include test-only setup and reset hooks, but they must be unavailable in production and may support setup, cleanup, or observation only; assertions still exercise public behavior.

Use structured ask/answer when available to request `Apply exactly this diff`, `Revise proposal`, or `Do not apply`. Snapshot every proposed target before asking. Re-read them immediately before mutation and discard approval if any target changed.

## Apply and Verify

Apply only the approved diff. Do not stage or modify unrelated files.

Run the inspector again first. Then run focused static checks for the changed test infrastructure. `test-prepare` intentionally applies meaning-preserving formatting; when unrelated dirty files fall within its formatter scope, do not run it in the original worktree. Use a faithful disposable copy when feasible or report the unresolved verification gap without touching that work.

Approval to apply files does not authorize a test that creates containers, databases, external sandbox resources, paid requests, or other persistent or network effects. Before such an E2E run, disclose exact endpoints, environment-identity checks, credential variable names without values, resources created and deleted, cleanup behavior, and cost boundary, then obtain separate approval. Fail before resource mutation when the target cannot be proven non-production. Missing prerequisites fail the complete gate; never convert them into a successful skip.

After authorized checks, compare the worktree with the pre-run snapshot. Classify formatter changes as test-owned only when they were disclosed and occurred before the behavioral stages. Any unexpected or unrelated mutation invalidates the run as completion evidence and must be reported without destructive rollback.

## Report

Return the repository and selected profile, structural inspection schema and status, rule matrix, exact handlers, applied files, approved waivers and triggers, test environment isolation, commands and exit codes, formatter changes, skipped or unauthorized checks, remaining evidence gaps, and separate staging, commit, and publication state.

Report `configured but unverified` when the files conform but a required complete gate was not authorized or could not run. Do not claim complete setup from structural inspection, documentation, or focused unit checks alone.
