# Reference-Based AGENTS.md Guidance

Use this reference only after the user approves preparation of an AGENTS.md proposal.

## Minimal reference section

Adapt names only when the installed skill namespace differs:

```markdown
## Development skill references

- Use `$root-kernel:task-handler` for one named roadmap task.
- Use `$root-kernel:epic-handler` to implement one roadmap epic as sequential task goals.
- Use `$root-kernel:epic-validator` to cold-validate and remediate one completed roadmap epic.
- Use `$root-kernel:dev-setup` to diagnose or configure development tooling.
- Use `$use-sanho` at an authorized commit or push boundary in a Sanho-managed repository, or for an explicitly requested Sanho operation.
- Use `$use-mulgae` for an authorized Mulgae review, run inspection, finding follow-up, configuration diagnosis, cleanup plan, or recovery.
- Use `$use-gaori` when a selected long or noisy check is routed through Gaori or existing Gaori evidence must be inspected.
- Use `$use-podway` for Podway Procedure v2 session operation, authoring, lifecycle, diagnosis, or recovery; Root Kernel workflow skills retain their stricter roadmap, ownership, and approval rules.
- In repositories opted into Root Kernel Podway procedures, treat the roadmap as lifecycle authority, Podway as active execution and evidence state, and the Codex goal as a temporary projection of actionable work.
- Use `$lore-commits` for non-trivial commit messages and `$lore-query` to inspect recorded decision context.
- Repository-specific rules below override defaults from the referenced skills.

### Repository overrides

<only rules that actually differ from the referenced skills>
```

Omit a reference to a skill that is not selected or installed. In particular, omit `$use-sanho`, `$use-mulgae`, `$use-gaori`, or `$use-podway` when only the corresponding CLI is installed. Omit the override heading when there are no overrides.

## Classify existing guidance

Move or retain as an override only information that materially differs from the referenced skills, including:

- authoritative roadmap paths, lifecycle states, and task-ID normalization;
- exact test commands, permission limits, and Gaori command IDs, version pins, or repository-specific MCP requirements;
- Sanho documentation ownership, selected `sanho check` policies, project identity, conflict policy, or repository-specific exceptions;
- Mulgae role sets, provider routing, target selection, timeouts, artist inputs, or stricter authorization;
- Podway enablement, procedure overrides, lifecycle ownership, version constraints, or stricter session-reset policy;
- commit subject prefixes and task-ID formats that override Lore's generic summary line;
- project-specific sensitive paths, generated sources, fallback behavior, and unavailable gates.

Replace duplicated common workflow, generic Sanho commit/push safety prose, generic Mulgae target, MCP/CLI, status, finding, cancellation, cleanup, and recovery prose, generic Gaori execution, artifact-inspection, cancellation, cleanup, and recovery prose, generic Podway Procedure v2 operation, authoring, lifecycle, and recovery prose, Lore trailer vocabulary, and generic command examples with references. Preserve stricter Root Kernel session ownership and approval rules. Preserve ambiguous text and call it out in the proposal rather than guessing that it is duplicate.

When a repository says Mulgae requires an explicit request, clarify whether explicit `$root-kernel:task-handler` invocation is the authorized task-scoped request; do not silently weaken the repository rule.

## Produce and apply the proposal

1. Record the exact target path and current file bytes or object hash.
2. Show a complete diff that labels retained overrides through their final placement.
3. Explain any ambiguous text left unchanged.
4. Request a second ask/answer decision for that exact diff.
5. Re-read the target before writing. Any change invalidates approval.
6. Apply only the displayed patch and show the resulting diff.

Do not insert generated markers around unrelated content, rewrite the entire file for formatting, or modify nested AGENTS.md or other agent instruction files by default.
