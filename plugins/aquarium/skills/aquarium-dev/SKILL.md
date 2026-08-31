---
name: aquarium-dev
description: "Diagnose, enroll, repair, rebuild, and expose the explicit Aquarium development channel for one supported canonical checkout. Use when the user explicitly invokes $aquarium:aquarium-dev or explicitly asks to manage Aquarium development-channel state; never invoke it implicitly."
---

# Aquarium Development Channel

Use unreleased local-main artifacts without changing production tool installations. This skill is explicit-only. Read [development-contract.md](references/development-contract.md) before any action.

## Diagnose before effects

1. Resolve this skill directory and run `python3 <skill-directory>/scripts/aquarium_dev.py diagnose --repository <git-root>`.
2. Read the complete JSON result or error. Diagnosis is read-only: do not create `~/.aquarium-dev/`, install a hook or launcher, build, authenticate, configure Codex, or repair anything.
3. Require Darwin on arm64, one regular non-symlink Git root, a supported producer identity, local `main`, both shared Make targets, and native repository-local hooks. Report dirty state separately; a build cannot consume it.
4. If an enrollment exists, compare the canonical checkout, hook ownership, current artifact, and executable command selector. Never discover or switch canonical checkouts implicitly.

## Keep approvals separate

Obtain separate explicit approvals for enrollment metadata, the Aquarium-owned native hook block, the initial or recovery build, and the user-local launcher. Re-enrollment additionally requires approval for the exact checkout transfer or same-checkout migration of one recorded legacy Aquarium block. No approval authorizes authentication, Codex configuration, production installation changes, a Git commit, or a producer-repository change.

Run enrollment only after both enrollment and hook approvals:

```text
python3 <skill-directory>/scripts/aquarium_dev.py enroll \
  --repository <git-root> --approve-enrollment --approve-hook
```

Add `--approve-reenrollment` only for an approved checkout transfer or same-checkout legacy-manager migration. Re-enrollment removes only the exact recorded Aquarium marker block. Missing, duplicate, changed, symbolic, external, or ambiguous hook state fails closed.

Install the explicit launcher only after approval:

```text
python3 <skill-directory>/scripts/aquarium_dev.py install-launcher \
  --approve-launcher
```

The only supported target is `~/.local/bin/aquarium-dev`. The launcher inherits the caller's complete environment, including any existing `CODEX_HOME`, and prepends only `~/.aquarium-dev/bin` to the child `PATH`.

For `podway`, `mulgae`, `gaori`, `sanho`, or `dolgorae`, it leases and executes the selected immutable development generation when one exists. Otherwise it resolves only that command from the caller's global `PATH`, excluding both Aquarium state roots. An enrolled but invalid development generation fails closed instead of hiding corruption behind a global fallback. It does not select, install, or configure a Codex plugin or MCP server.

## Build and expose development artifacts

Use `diagnose` again after every effect. Hook repair uses `repair-hook --approve-hook`; a build uses `rebuild --approve-build`. Never edit enrollment JSON, hook markers, `current` selectors, or stable `bin` indirections manually.

The native hook queues one exact completed local-main SHA. The manager builds that commit in an isolated exact checkout, seals the immutable generation, and atomically advances only `current/<project-id>`. Executable producers use one stable `bin/<project-id>` indirection through that selector, so readers cannot combine generations. Aquarium plugin artifacts remain available under `current/aquarium` for separately authorized consumers but are never installed into a Codex home by this workflow.

Run an enrolled executable explicitly:

```text
aquarium-dev <tool> [args...]
```

The development producer contract supports one Aquarium Codex plugin artifact plus `podway`, `mulgae`, `gaori`, `sanho`, and `dolgorae` executables at the exact respective paths `bin/<project-id>`. Each tool repository owns its producer implementation and enrolls its canonical checkout when its approved producer commit is created.

Until Dolgorae is enrolled, the launcher admits it through global fallback only. If neither development nor global Dolgorae exists, the invocation fails closed and requests `$aquarium:dev-setup`; there is no Dolgorae exception. Sanho alone is excluded from the required global-binary baseline.

## State boundary

All development-channel state lives under `~/.aquarium-dev`. Aquarium never writes development state beneath `~/.aquarium`, creates a dedicated Codex home, copies credentials, performs login, or changes plugin or MCP configuration. Development artifacts are local integration evidence only; they are not stable installations, release candidates, distribution artifacts, or release-QA substitutes.
