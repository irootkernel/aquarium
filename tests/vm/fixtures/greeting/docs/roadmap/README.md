# Roadmap

Lifecycle: `Planned` means not started; `In Progress` means authorized work is
active; `In Review` means delivery is awaiting required review or acceptance;
`Completed` means the original criteria and required acceptance are settled;
`Blocked` means a concrete prerequisite prevents progress; `Deferred` means
the operator has explicitly postponed the work. Start a dependent Task only
after its predecessor is completed.

## EPIC-001: Add greeting options

**Status:** `Planned`

Add uppercase and repeat options while preserving the original default and
named greetings. Deliver TASK-001 before TASK-002.

**Detailed SOT:** [Greeting options dossier](../todo/TODO-GREETING-OPTIONS.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-001 | Add uppercase greetings | Add --uppercase for default and named greetings without changing existing behavior. | Planned | None |
| TASK-002 | Add repeated greetings | Add --repeat with a positive integer count and support its combination with --uppercase. | Planned | TASK-001 |
