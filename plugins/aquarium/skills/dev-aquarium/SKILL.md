---
name: dev-aquarium
description: "Diagnose, enroll, repair, rebuild, and launch the explicit Aquarium development channel for one supported canonical checkout. Use when the user explicitly invokes $aquarium:dev-aquarium or explicitly asks to manage Aquarium development-channel state; never invoke it implicitly."
---

# Aquarium Development Channel

Use the host-local development channel without changing stable global installations. This skill is explicit-only. Read [development-contract.md](references/development-contract.md) before any action.

## Diagnose before effects

1. Resolve this skill directory and run `python3 <skill-directory>/scripts/dev_aquarium.py diagnose --repository <git-root>`.
2. Read the complete JSON result or error. Diagnosis is read-only: do not create `~/.aquarium/`, install a hook, build, configure Codex, authenticate, or repair anything.
3. Require Darwin on arm64, one regular non-symlink Git root, a supported producer identity, local `main`, both shared Make targets, and native repository-local hooks. Report dirty state separately; a build cannot consume it.
4. If an enrollment exists, compare the canonical real checkout, hook ownership, current artifact, and isolated Codex state. Never discover or switch canonical checkouts implicitly.

## Keep approvals separate

Use the host's structured ask/answer tool when available. Obtain separate explicit approvals for each applicable effect:

- create or replace enrollment metadata;
- add, remove, or transfer the Aquarium-owned native hook block;
- perform the initial or recovery build;
- configure the isolated Codex home.

Changing to a different canonical checkout additionally requires explicit re-enrollment approval. Approval for one effect never authorizes another, authentication, stable-home mutation, publication, a Git commit, or a producer-repository change.

Run enrollment only after the enrollment and hook approvals are both current:

```text
python3 <skill-directory>/scripts/dev_aquarium.py enroll \
  --repository <git-root> --approve-enrollment --approve-hook
```

Add `--approve-reenrollment` only after the diagnosed project is already owned by another checkout and the user approves that exact transfer. Same-checkout enrollment is idempotent. Re-enrollment removes only the exact previously recorded Aquarium marker block; any missing, duplicate, changed, symbolic, external, or otherwise ambiguous hook fails closed.

## Repair and continue

Use `diagnose` again after every effect. Offer only the exact repair named by current output. Hook repair uses `repair-hook --approve-hook`; rebuild and Codex configuration retain their own approvals. Never edit enrollment JSON or hook markers manually, copy stable Codex credentials, or turn a broken enrollment into stable fallback.

The native hook queues an exact completed local-main SHA and starts asynchronous work. A request or worker failure may emit a bounded diagnostic but never rewrites or rolls back the completed Git commit.

## Launch

Use `launch --project-id <id> -- <command> [args...]` only after healthy diagnosis. It resolves and leases one immutable artifact before starting the child and holds that lease for the child's lifetime. If no enrollment exists, the command may use the named stable executable. If an enrollment exists but is broken, stop on the machine error and follow its repair action; never silently fall back.

The development Codex runtime uses only `~/.aquarium/codex`. Missing login is a user action reported as `CODEX_HOME=~/.aquarium/codex codex login`; this skill never authenticates or reads or copies the stable Codex home.
