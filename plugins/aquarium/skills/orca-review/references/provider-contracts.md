# Provider Contracts

Read only the section for the selected tool:model. The version-matched Orca guides remain authoritative for command grammar, terminal readiness, Dispatch injection, waiting, transcript reads, recovery, and release.

In the examples, `<ORCA>` means the single platform-native executable already resolved from `$orca-cli`, and `<PROVIDER>` means the selected provider CLI's consent-bound canonical absolute native-executable path. A shebang script, text launcher, shim, or wrapper is not eligible because its recorded file can remain unchanged while delegated code changes. Replace both paths directly rather than creating a shell variable, resolving a bare command again, or running a placeholder literally. Create the Run and Task before the terminal, wait for that exact terminal to become TUI-idle, then inject the Task as one supervised Dispatch.

## Shared Launch Boundary

Use a fresh terminal in the verified immutable `/tmp` snapshot through the consent-bound local Orca runtime; never launch in or identify the original checkout to a participant. Never pass or inherit an Orca environment or pairing selector. Start it through `<ORCA> terminal create --worktree path:<absoluteSnapshotPath> --command <command> --json` using `<PROVIDER>` as the command's executable, preserve its returned handle, wait with an explicit timeout, and use the live guide's `orchestration dispatch --inject` path. Confirm the local runtime identity, snapshot path, canonical provider executable, terminal command, and model from the launch output or transcript before accepting findings.

If the CLI exits, requests authentication, rejects the model or read-only mode, cannot receive the Dispatch, or cannot send lifecycle messages, report the exact operational failure. Do not remove read-only flags, weaken permissions, switch models, reuse a terminal, or start another provider.

The lead owns final synthesis. Subagents return evidence to the lead and never report directly to the Aquarium coordinator. The lead must inspect cited code and authority itself before accepting a subagent claim.

## `claude:fable with opus/sonnet`

Launch command:

```text
<PROVIDER> --model fable --permission-mode plan
```

Fable is the master reviewer. It concentrates on decomposition, orchestration, evidence review, validation, requirement-goal assessment, decisions, deduplication, and final reporting rather than performing every first-pass investigation itself.

For every nonempty review, Fable delegates at least one bounded investigation or analysis task to a Claude subagent with an explicit per-invocation `opus` or `sonnet` model. Use Opus for deep requirement, architecture, concurrency, or correctness reasoning and Sonnet for broad code, caller, test, and documentation tracing; use both when the target materially benefits from independent coverage. Project defaults or inherited aliases must not silently replace the explicit subagent model.

For every subagent, Fable records the requested model and verifies the effective model from native Agent task or session metadata or an explicit runtime model identity reported by that subagent. A missing, ambiguous, or mismatched effective model makes the topology unverifiable and prevents a clean verdict.

Fable accepts only claims it can trace to exact repository evidence. Its topology record lists the Opus and Sonnet work actually used, their roles, and whether each result was accepted, rejected, or still needs confirmation.

## `claude:opus`

Launch command:

```text
<PROVIDER> --model opus --permission-mode plan
```

The Opus lead delegates at least two independent review slices to Claude subagents using `model: inherit` or an explicit `opus` override. Assign non-overlapping concerns derived from the target, such as requirement traceability, runtime and persistence behavior, or regression-test coverage. The lead verifies and deduplicates their conclusions before reporting.

For every subagent, the Opus lead records the requested model and verifies the effective model from native Agent task or session metadata or an explicit runtime model identity reported by that subagent. A missing, ambiguous, or mismatched effective model makes the topology unverifiable and prevents a clean verdict.

## `codex:gpt-5.6-sol`

Launch command:

```text
<PROVIDER> --model gpt-5.6-sol --sandbox read-only --ask-for-approval never
```

The Codex lead delegates at least two independent review slices through its native subagent tools. Do not set a model override on a subagent; every subagent must inherit `gpt-5.6-sol`. The lead verifies the effective model from available session or tool metadata, reviews the evidence, and deduplicates the results before reporting.

## `cursor:grok-4.6`

Launch command:

```text
<PROVIDER> --model grok-4.6 --mode plan
```

The Cursor lead delegates at least two independent review slices to native subagents configured with `model: inherit`. Do not use project or user subagents that force another model. The lead verifies available task metadata, reviews cited evidence, and deduplicates the results before reporting.

## `kimi:k3`

Launch command:

```text
<PROVIDER> --model k3 --plan
```

The Kimi lead delegates at least two independent review slices through `Agent` or `AgentSwarm` with the primary model explicitly selected. Do not accept a configured secondary model or an agent profile that overrides K3. If the installed Kimi version cannot request or verify the primary model for subagents, report topology as unverifiable and do not return a clean verdict.

Prefer read-only `explore` or equivalent custom review agents. The lead verifies their evidence and deduplicates the results before reporting.
