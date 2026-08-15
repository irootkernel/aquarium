# Tool Catalog

Use only the section for a selected tool. Repository instructions override this catalog.

## Shared version and safety policy

- Resolve the latest non-draft, non-prerelease stable release at execution time from the official repository, limited to a tool's supported release line when its section defines one. Display the exact tag and source before installation; never substitute `@latest` after approval.
- Preserve an already compatible installation unless the user approves an upgrade.
- Diagnose credentials by whether the owning CLI reports readiness. Never print, copy, or persist credential material.
- Keep configuration in each tool's native files. Never create `.root-kernel-dev-skills`, a selection manifest, or a shadow version registry.
- Treat every init, ignore edit, hook edit, global install, and network operation as a disclosed mutation requiring approval.

## Sanho

Official source: `https://github.com/irootkernel/sanho`

Supported release line: stable `v0.2.6` through `v0.2.x`. Resolve the newest non-draft, non-prerelease tag in that range. Use the same exact tag for the CLI and its optional `use-sanho` skill; do not pair the v0.2.6 skill contract with an older CLI or automatically cross into `v0.3+`.

Install an approved tag:

```bash
go install github.com/irootkernel/sanho/cmd/sanho@<tag>
```

The binary does not install the agent skill. Diagnose the CLI and workspace with `command -v sanho`, `sanho version --json`, `sanho status --json`, and `sanho doctor --json`; diagnose `use-sanho` independently in the Codex skill roots. Read JSON rather than inferring state from human tables or exit status alone. Doctor exits 0 when it reports warnings, so treat a positive `warnings` count as degraded even when the process succeeds.

For a new Codex user-scoped skill installation, fetch only these files from `https://raw.githubusercontent.com/irootkernel/sanho/<tag>/skills/use-sanho/` into a temporary directory under `~/.agents/skills`: `SKILL.md`, `references/lifecycle.md`, `references/authoring.md`, and `references/recovery.md`. Verify the complete file set, SHA-256 digests, and `name: use-sanho` frontmatter before atomically moving it to `~/.agents/skills/use-sanho`. Disclose every raw GitHub endpoint and the user-global target before approval.

If the target already exists, compare it with the approved source, show the complete diff, and obtain separate replacement approval; preserve a recoverable sibling backup and report its path. Never overwrite, merge, delete, or repair another discovered copy silently. After installation or replacement, tell the user to restart Codex so a new session loads the skill snapshot.

`sanho status` separates committed `HEAD` prediction from working-copy and local operation readiness. Consume `relation`, `publication`, `sync_preview`, `working_copy`, `local_readiness`, and `sync_in_progress` independently. Do not expose project URLs, actor email, workspace IDs, private paths, or doctor details in setup reports.

Use `sanho check --require-clean`, `--require-current`, and `--require-published` only when repository authority selects those policies. Exit 1 with `passed:false` is a policy mismatch; an `error` envelope means evaluation failed. `--require-current` contacts the canonical remote and requires network approval. `sanho diff`, `sanho diff --refresh`, and `sanho diff --local` are read-only inspection commands without JSON output; `--refresh` contacts the canonical remote.

Initialization always requires a user-confirmed project name. Inspect `sanho state --all --json` and normalize it without reporting private URLs or paths. A registered v2 project with a non-empty canonical URL may be reused without repeating the URL; an unregistered project still requires a user-confirmed documentation repository URL:

```bash
sanho init --project <project> --docs-repo-url <url>
sanho init --project <registered-project>
```

Before approval, disclose that init can create `.sanho.json` and `.sanho_base.json`, register a private clone, install managed Git hook lines, update ignore state, and conditionally stage documentation state. Inspect custom or Husky hooks and request any required management opt-in rather than forcing initialization. Never guess the project name or URL.

After initialization or upgrade, verify `sanho status --refresh --json`, `sanho doctor --json`, and `git status --short`. Do not run `sanho clean`, `sanho init --force`, `sanho sync --abort`, `sanho migrate`, or any sync/pull operation during setup.

For an explicitly requested repair, load and follow the installed `$use-sanho` lifecycle or recovery guidance when available. `sanho doctor --fix` requires its own repair approval and a fresh status and doctor check afterward. `sanho workspace forget <workspace-id>` requires selecting one exact row from `sanho state --all --json`, proving that its checkout path no longer exists, and separate removal approval. Do not map general setup, cancellation, or cleanup intent to either command.

## Mulgae

Official source: `https://github.com/irootkernel/mulgae`

Supported release line: stable `v0.1.13` through `v0.1.x`, native Apple Silicon macOS only. Resolve the newest non-draft, non-prerelease tag in that range. Use the same exact tag for the CLI and its optional `use-mulgae` skill; v0.1.12 does not provide the required split Config v2, skill, or MCP surfaces, and do not automatically cross into `v0.2+`. Installation requires Go `1.26.6` or newer.

Install an approved tag:

```bash
go install github.com/irootkernel/mulgae@<tag>
```

The binary does not install the agent skill. Diagnose the CLI, configuration, and provider readiness with `command -v mulgae`, `mulgae version --json`, `mulgae doctor --output json`, `mulgae config --mode effective --output json`, `mulgae config --mode provenance --output json`, and `mulgae providers --include-unverified --output json`.

Read stable fields and reason codes from complete JSON envelopes even when a readiness or configuration command exits non-zero. Treat missing shared project policy, missing machine-local configuration, and missing provider authentication separately, and never report native homes, executable paths, credentials, diagnostic messages, request IDs, or timestamps.

For a new Codex user-scoped skill installation, fetch only these files from `https://raw.githubusercontent.com/irootkernel/mulgae/<tag>/skills/use-mulgae/` into a temporary directory under `~/.agents/skills`: `SKILL.md`, `references/lifecycle.md`, `references/authoring.md`, and `references/recovery.md`. Verify the complete file set, SHA-256 digests, and `name: use-mulgae` frontmatter before atomically moving it to `~/.agents/skills/use-mulgae`.

If the target already exists, compare it with the approved source, show the complete diff, and obtain separate replacement approval; preserve a recoverable sibling backup and report its path. Never overwrite, merge, delete, or repair another discovered copy silently. After installation or replacement, tell the user to restart Codex so a new session loads the skill snapshot.

Mulgae Config v2 has two authorities. `.mulgae/config.yaml` is Git-shareable project policy; `.mulgae/local.yaml` is untracked mode-`0600` machine configuration. Ask which providers and roles to configure. Automatic provider selection requires authenticated ZCode and AGY; Kimi is opt-in, and bare initialization enables only the required `logic` role. Show discovered executable or launcher paths only in the exact private setup proposal, never in the diagnostic report.

For a new project, run `mulgae init --output json` with every intended provider and role only after approval; it creates both Config v2 files and does not edit Git ignore state. When a clone contains only shared `config.yaml`, plain `mulgae init --output json` bootstraps only `local.yaml` and rejects project-policy options.

When provider paths move or the shared provider set changes, propose `mulgae init --refresh-local --output json`, which preserves `config.yaml` and replaces only `local.yaml`. Keep new initialization, clone bootstrap, and refresh as distinct approvals. Config v1 is unsupported and has no automatic migration; show the exact legacy file, backup, and removal proposal and obtain separate destructive approval before initializing Config v2.

Propose these root-anchored Git ignore rules through an exact reviewed diff:

```gitignore
/.mulgae/*
!/.mulgae/config.yaml
```

Verify that only `.mulgae/config.yaml` is trackable and that `.mulgae/local.yaml` and all runtime state remain untracked and ignored. Propose `.mulgaeignore` entries from the repository's secrets, generated output, large artifacts, agent instructions, and non-reviewable paths. A `.mulgaeignore` intended as shared capture policy may be tracked only with explicit approval.

Treat MCP as an optional, separately approved project-local component. For a trusted project, merge this machine-specific entry into `.codex/config.toml` while preserving unrelated configuration:

```toml
[mcp_servers.mulgae]
command = "<absolute-selected-mulgae-path>"
args = ["mcp", "--project-root", "<absolute-git-root>"]
cwd = "<absolute-git-root>"
required = true
startup_timeout_sec = 30
tool_timeout_sec = 54000
```

Show the complete diff and whether `.codex/config.toml` is tracked before approval. Verify only the effective registration with `codex mcp get mulgae --json`: it must be enabled STDIO, resolve to the selected binary, bind its argument and cwd to the canonical repository, be required, and use startup and tool timeouts at least as large as the proposed defaults.

Never stage it during setup. Tell the user to restart Codex so a new session can expose `preflight_review`, `run_review`, `list_runs`, `get_run`, `list_findings`, and verified report and finding resources.

Verify configuration, provider readiness, skill files, and MCP registration only. Do not start the MCP server or run review, preflight, follow-up, delta, rerun, report, export, or any command that captures, transmits, or writes review source or artifacts during setup.

## Gaori

Official source: `https://github.com/irootkernel/gaori`

Supported release line: stable `v0.1.12` through `v0.1.x`. Resolve the newest non-draft, non-prerelease tag in that range. Use the same exact tag for the CLI and its optional `use-gaori` skill; v0.1.11 does not provide the required config-check, skill, portable-policy, or MCP surfaces, and do not automatically cross into `v0.2+`.

Install an approved tag:

```bash
go install github.com/irootkernel/gaori@<tag>
```

The binary does not install the agent skill. Diagnose the CLI and repository with `command -v gaori`, `gaori version --json`, and, when `.gaori/tester.yaml` exists, `gaori --json config check`. Diagnose `use-gaori` and project-local MCP registration independently. Config check validates schema-v2 config and all stored rules without resolving executables, running commands, or creating evidence.

For a new Codex user-scoped skill installation, fetch only these files from `https://raw.githubusercontent.com/irootkernel/gaori/<tag>/skills/use-gaori/` into a temporary directory under `~/.agents/skills`: `SKILL.md`, `references/lifecycle.md`, `references/authoring.md`, and `references/recovery.md`. Verify the complete file set, SHA-256 digests, and `name: use-gaori` frontmatter before atomically moving it to `~/.agents/skills/use-gaori`. Disclose every raw GitHub endpoint and the user-global target before approval.

If the target already exists, compare it with the approved source, show the complete diff, and obtain separate replacement approval; preserve a recoverable sibling backup and report its path. Never overwrite, merge, delete, or repair another discovered copy silently. After installation or replacement, tell the user to restart Codex if the skill does not appear in the active session.

Discover required checks from repository instructions, task runners, manifests, and CI before proposing `.gaori/tester.yaml` schema version 2. Map each configured command ID to an existing argv array, non-empty tags, explicit parser, and timeout. Do not add secrets, absolute paths, or machine-specific arguments to portable configuration.

Gaori is an optional execution and evidence-compression wrapper; it does not create a new test gate, change command authorization, override the child process exit status, or grant acceptance. Keep runtime state local while allowing Git to track portable config and reviewed active rules. Replace a blanket `.gaori/` ignore entry only through an approved exact diff:

```gitignore
.gaori/*
!.gaori/tester.yaml
!.gaori/tester/
.gaori/tester/*
!.gaori/tester/rules/
.gaori/tester/rules/*
!.gaori/tester/rules/*.yaml
```

This keeps `.gaori/toolchain.yaml`, `.gaori/rule-proposals/`, `.gaori/runs/`, and every other Gaori path local. Active rule YAML is executable extraction policy: do not create, update, stage, or commit it without the user's specific intent and review. Validate approved config or rule changes with `gaori --json config check`; do not run configured tests during setup.

Treat MCP as an optional, separately approved project-local component. For a trusted project, merge this machine-specific entry into `.codex/config.toml` while preserving unrelated configuration:

```toml
[mcp_servers.gaori]
command = "<absolute-selected-gaori-path>"
args = ["--repo", "<absolute-git-root>", "mcp"]
tool_timeout_sec = 60
```

Show the complete diff and whether `.codex/config.toml` is tracked before approval. Never stage it during setup. Verify only the effective registration with `codex mcp get gaori --json`; do not start the server or a test. Report disabled, non-STDIO, unresolvable-command, wrong-repository, and inactive or untrusted project entries as degraded. Tell the user to restart Codex so a new session can expose `start_configured_run`, `start_ad_hoc_run`, `get_run`, `wait_run`, `cancel_run`, and `get_excerpt`.

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

Supported release line: stable `v0.2.1` through `v0.2.x`, native Apple Silicon macOS only. Resolve the newest non-draft, non-prerelease tag in that range. Use the same exact tag for the CLI, daemon, and optional `use-podway` skill; v0.2.0 retains incompatible Procedure v1 and success-envelope surfaces, and do not automatically cross into `v0.3+`.

Resolve the exact release from GitHub Releases and download the Apple Silicon archive plus its published `.sha256` file. Disclose that release binaries are unsigned and not notarized. Verify with `shasum -a 256 -c` before installing both `podway` and `podwayd` at the approved user-local paths. Do not accept a prerelease, a version before v0.2.1, `v0.3+`, an unverified archive, mixed CLI and daemon versions, or unsupported platform.

The binaries do not install the agent skill. Diagnose `use-podway` independently in the Codex skill roots. For a new Codex user-scoped installation, fetch only `SKILL.md`, `references/lifecycle.md`, `references/authoring.md`, and `references/recovery.md` from `https://raw.githubusercontent.com/irootkernel/podway/<tag>/skills/use-podway/` into a temporary directory under `~/.agents/skills`. Verify the complete file set, SHA-256 digests, and `name: use-podway` frontmatter before atomically moving it to `~/.agents/skills/use-podway`. Disclose every raw GitHub endpoint and the user-global target before approval.

If the target exists, compare it with the approved source, show the complete diff, and obtain separate replacement approval; preserve a recoverable sibling backup and report its path. Never overwrite, merge, delete, or repair another discovered copy silently. After installation or replacement, tell the user to restart Codex so a new session loads the skill snapshot.

Install or refresh the per-user service only after separate approval:

```bash
podway daemon install --daemon-path <absolute-podwayd-path>
podway daemon status --json
```

The LaunchAgent runs after GUI login under the same OS user and is not a multi-user security boundary. Verify the compact `podway version --json` result, the `podway.output/v3` daemon envelope with `podway.daemon-status-result/v1`, daemon reachability and exact version match, and the `podway.output/v3` doctor envelope when the worktree is initialized. Runtime status and next must identify `podway.status-result/v2` and `podway.next-result/v2`; errors remain `podway.error/v1`.

Repository initialization and Root Kernel integration require another approval. `podway init` creates `.podway/config.yaml` and `.podway/.gitignore` for the repository to track, plus ignored `.podway/runtime/`; the opt-in gate itself checks Git tracking for the three procedures. Copy the three plugin-owned Procedure v2 sources to `.podway/procedures/` byte-for-byte and validate each with:

```bash
podway procedure check --warnings-as-errors <procedure-file>
```

The three required IDs are `root-kernel-task-v2`, `root-kernel-goal-v2`, and `root-kernel-validation-v2`. All absent means Root Kernel is not opted in. All present, tracked in Git, byte-identical, valid, and healthy means opted in. Partial, drifted, invalid, unsupported, or unhealthy state is degraded and must not silently fall back. The inspection script reports these as `integration_status` values `not_opted_in`, `opted_in`, or `degraded`. Updating a tracked copy requires showing and approving its exact diff; an active session retains its immutable snapshot.

`LEGACY_PROCEDURE_STATE_UNSUPPORTED` has a different meaning: the runtime contains Procedure v1 task state. Do not convert, edit, or delete that state automatically. Report the exact worktree and error, let the user make any desired backup, then require separate explicit approval before the supported `podway reset --all` recovery.
