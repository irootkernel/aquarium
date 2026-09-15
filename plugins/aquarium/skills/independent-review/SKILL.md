---
name: independent-review
description: "Explain that Dolgorae-based Independent Review is temporarily unavailable, or dispatch exactly one explicitly preselected supported Orca or native Codex alternative under that route's own contract. Native Codex requires host fresh delegation. Use only when the user explicitly invokes $aquarium:independent-review."
---

# Independent Review

Independent Review is temporarily disabled. Stop before Dolgorae discovery, setup, Profile inspection, source capture, source transmission, provider contact, or any other Dolgorae review operation.

Explain that Aquarium does not currently offer its Dolgorae-backed Independent Review route. `workspace` and `dirty` targets have no Orca equivalent. Preserve the original target and review question and apply the routing matrix in [review-intent-contract.md](../../references/review-intent-contract.md#route-a-disabled-independent-review-request):

- With no preselected alternative, explain the available Orca and native Codex routes and launch nothing.
- With exactly one preselected Orca alternative, validate its supported target and requested reviewer, then invoke `$aquarium:orca-review` under that skill's prerequisites and authorization boundaries.
- With exactly one preselected native Codex alternative, proceed only when the host exposes fresh native delegation and follow [the native Codex route](../../references/review-intent-contract.md#use-a-native-codex-review-subagent). If delegation is unavailable, report that limitation and stop without fallback.
- With more than one preselected alternative, ask the user to choose exactly one and launch nothing.

A target unsupported by the selected route remains a reported limitation, not permission to translate or broaden it. Independent Review owns only the refusal and routing decision; the explicitly selected alternative owns its execution, source handling, lifecycle, evidence, and result.

Refusal alone authorizes no fallback review, setup action, source transmission, test, edit, staging, commit, or publication. Exactly one explicitly preselected supported alternative authorizes only that alternative under its own contract. Dolgorae remains available only through an explicitly requested `$aquarium:dev-setup-global` Dolgorae setup flow or an explicitly requested `$use-dolgorae` operation.
