# Provider Contracts

Read only the selected provider section after loading the shared review and Orca supervision contracts. The version-matched Orca guides remain authoritative for terminal creation, readiness, Dispatch injection, lifecycle messages, settlement, and recovery.

`<PROVIDER>` is the consent-bound absolute provider entrypoint. The provider sections below define logical argument vectors, not shell command fragments. Resolve this skill directory and use `scripts/create_provider_terminal.py` for the only provider-terminal creation path. Send its `aquarium-orca-provider-terminal-request/v1` JSON through non-expanding stdin; never put provider paths or arguments in a shell command, heredoc with expansion, environment assignment, or string concatenation.

The helper revalidates the consent-bound Orca and provider canonical targets and digests, serializes the provider argv once, and invokes Orca through a native subprocess argument vector. If non-expanding stdin is unavailable, stop before terminal creation.

Launch one fresh terminal in the current worktree and keep it in the provider's read-only or plan mode. Authentication prompts, model rejection, premature exit, missing Dispatch support, helper rejection, or any request to weaken permissions stop the review.

The lead owns the final verdict. Optional native subagents gather bounded evidence for the lead; they do not report directly to Aquarium. Record their requested and effective identities when the provider exposes that information. Never claim a model identity that the provider does not expose.

## Claude Fable

Provider arguments:

```text
<PROVIDER> --model fable --permission-mode plan
```

Fable manages decomposition, evidence review, requirement-goal assessment, decisions, deduplication, and final synthesis. It may create Opus or Sonnet subagents when the target benefits from deeper or broader investigation. Use Opus for difficult architecture, concurrency, or correctness reasoning and Sonnet for broad caller, test, or documentation tracing. A small review may remain Fable-only.

Record which Opus or Sonnet work was actually used and whether Fable accepted, rejected, or qualified each result. Optional subagent absence is not an error.

## Kimi K3

Provider arguments:

```text
<PROVIDER> --model k3 --plan
```

Kimi may use its native review or exploration agents when useful. Do not select a configured secondary model silently. Record the effective lead or subagent identity when exposed; otherwise report it as unknown without turning that absence alone into a failed review.

## Agy

Default provider arguments:

```text
<PROVIDER> --mode plan --sandbox
```

Use the installed Agy defaults unless the user supplied an exact override. Append only the supplied values as native arguments:

```text
--agent <agent> --model <model> --effort <effort>
```

Do not run `agy agent`, `agy models`, or another discovery command. Record the effective agent and model if the launched session exposes them; otherwise report the identity as unknown. Unknown default identity is disclosed evidence, not permission to probe a provider service.

## Cursor Agent Grok 4.6

Provider arguments:

```text
<PROVIDER> --model grok-4.6 --mode plan
```

Cursor Agent may use native inherited-model subagents when useful. Do not use a project or user agent definition that forces another model. Record available task and model metadata and let the lead verify and deduplicate all subagent evidence.
