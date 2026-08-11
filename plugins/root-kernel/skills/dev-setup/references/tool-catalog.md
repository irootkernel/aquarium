# Tool Catalog

Use only the section for a selected tool. Repository instructions override this catalog.

## Shared version and safety policy

- Resolve the latest non-draft, non-prerelease stable release at execution time from the official repository. Display the exact tag and source before installation; never substitute `@latest` after approval.
- Preserve an already compatible installation unless the user approves an upgrade.
- Diagnose credentials by whether the owning CLI reports readiness. Never print, copy, or persist credential material.
- Keep configuration in each tool's native files. Never create `.root-kernel-dev-skills`, a selection manifest, or a shadow version registry.
- Treat every init, ignore edit, hook edit, global install, and network operation as a disclosed mutation requiring approval.

## Sanho

Official source: `https://github.com/irootkernel/sanho`

Install an approved tag:

```bash
go install github.com/irootkernel/sanho/cmd/sanho@<tag>
```

Diagnose with `command -v sanho`, `sanho version --json`, `sanho status --json`, and `sanho doctor --json`. Read JSON rather than inferring state from human tables or exit status alone.

Initialization requires a user-confirmed project name and documentation repository URL:

```bash
sanho init --project <project> --docs-repo-url <url>
```

Before approval, disclose that init can create `.sanho.json` and `.sanho_base.json`, register a private clone, install managed Git hook lines, update ignore state, and conditionally stage documentation state. Inspect custom or Husky hooks and request any required management opt-in rather than forcing initialization. Never guess the project name or URL.

After initialization or upgrade, verify `sanho status --refresh --json`, `sanho doctor --json`, and `git status --short`. Do not run `sanho clean`, `sanho init --force`, `sanho sync --abort`, `sanho migrate`, or any sync/pull operation during setup.

## Mulgae

Official source: `https://github.com/irootkernel/mulgae`

Install an approved tag:

```bash
go install github.com/irootkernel/mulgae@<tag>
```

Diagnose with `command -v mulgae`, `mulgae version --json`, `mulgae config --mode effective --output json`, and `mulgae providers --include-unverified`. Treat missing project configuration separately from missing provider authentication.

Ask which providers to configure. The current default topology uses authenticated ZCode and AGY; Kimi is opt-in. Show any discovered executable or launcher paths before initialization. Run `mulgae init` only after approval. It creates `.mulgae/config.yaml` and refuses to overwrite an existing configuration; never remove an existing config to bypass that protection.

Propose `.mulgaeignore` entries from the repository's secrets, generated output, large artifacts, agent instructions, and non-reviewable paths. Keep `.mulgae/` local and ignored. A `.mulgaeignore` intended as a shared capture policy may be tracked only with explicit approval.

Verify config and provider readiness only. Do not run review, preflight, follow-up, rerun, or any command that captures or transmits source during setup.

## Gaori

Official source: `https://github.com/irootkernel/gaori`

Install an approved tag:

```bash
go install github.com/irootkernel/gaori@<tag>
```

Diagnose with `command -v gaori` and `gaori version --json`. Discover required checks from repository instructions, task runners, manifests, and CI before proposing `.gaori/tester.yaml` schema version 2.

Map each configured command ID to an existing argv array, tags, explicit parser, and timeout. Gaori is an optional execution and evidence-compression wrapper; it does not create a new test gate, change command authorization, or override the child process exit status. Keep the entire `.gaori/` directory local and ignored.

Validate configuration with a non-executing command such as `gaori rules list` when supported by the installed version. Do not run the configured tests during setup unless the user separately authorizes them.

## Lora / Lore

Official source: `https://github.com/tmdgusya/lora`

Lora distributes agent skills rather than a runtime service. Configure it for Codex user-global scope. Resolve the latest stable tag when one exists; otherwise resolve the full current `main` commit SHA and disclose that fallback before approval.

Install only the two compatible skills from the approved ref:

```bash
npx skills add https://github.com/tmdgusya/lora#<tag-or-full-sha> \
  --skill lore-commits \
  --skill lore-query \
  --global \
  --agent codex \
  --copy \
  --yes
```

This command contacts npm and GitHub and writes under the Codex user-global skill directory. Do not install or invoke Lora's `lore-setup`; it copies the full Lore protocol into AGENTS.md and conflicts with the reference-and-override policy. If `lore-setup` is already installed, report it without removing or rewriting it.

Verify that `lore-commits/SKILL.md` and `lore-query/SKILL.md` exist, have valid frontmatter, and match the approved source ref. Do not treat installation as commit authority.

## Podway

Official source: `https://github.com/irootkernel/podway`

Status: planned.

Show Podway in the inventory as unavailable for setup. Do not download release binaries, install a LaunchAgent, initialize state, start `podwayd`, or add task-handler integration.
