# Tool Catalog

Use only the section for a selected tool. Repository instructions override this catalog.

## Shared version and safety policy

- Resolve the latest non-draft, non-prerelease stable release at execution time from the official repository, limited to a tool's supported release line when its section defines one. Display the exact tag and source before installation; never substitute `@latest` after approval.
- Preserve an already compatible installation unless the user approves an upgrade.
- Diagnose credentials by whether the owning CLI reports readiness. Never print, copy, or persist credential material.
- Keep configuration in each tool's native files. Never create `.aquarium`, a selection manifest, or a shadow version registry.
- Selecting Sanho, Mulgae, Gaori, or Podway for setup or diagnosis authorizes one disclosed, bounded freshness comparison: resolve that tool's latest supported stable release from official GitHub Releases metadata and fetch its four paired-skill files from the documented `raw.githubusercontent.com` path into ephemeral storage. No separate approval is required for that comparison. Treat every init, ignore edit, hook edit, global install, provider contact, and network operation outside this exact exception as a disclosed mutation requiring approval.
- Apply the backup policy selected under `Choose a Backup Policy for Existing State` to every approved action that overwrites or removes an existing binary, skill, configuration, service, managed Procedure, or runtime state.

A backup choice requires exact backup and restoration commands plus verification before mutation. A no-backup choice requires the exact loss and recovery boundary in the proposal but no retained copy of the replaced state. It never waives source, checksum, frontmatter, diff, target, or post-install verification, and incoming payload staging is not a backup.

## Sanho

Official source: `https://github.com/irootkernel/sanho`

Supported release line: stable `v0.2.7` through `v0.2.x`. Resolve the newest non-draft, non-prerelease tag in that range. Use the same exact tag for the CLI and its optional `use-sanho` skill; v0.2.6 does not provide the required push-preview, canonical-history, commit-inspection, or normalized JSON argument-error surfaces, and do not automatically cross into `v0.3+`.

Install an approved tag:

```bash
go install github.com/irootkernel/sanho/cmd/sanho@<tag>
```

The binary does not install the agent skill. Diagnose the CLI and workspace with `command -v sanho`, `sanho version --json`, `sanho status --json`, and `sanho doctor --json`; diagnose `use-sanho` independently in the Codex skill roots. Read JSON rather than inferring state from human tables or exit status alone. Doctor exits 0 when it reports warnings, so treat a positive `warnings` count as degraded even when the process succeeds. Every malformed `--json` invocation must return the stable `invalid_arguments` error envelope; parse that envelope separately from the process exit and never reinterpret it as workspace state.

For a new Codex user-scoped skill installation, use only these files from the automatically fetched and verified `https://raw.githubusercontent.com/irootkernel/sanho/<tag>/skills/use-sanho/` payload: `SKILL.md`, `references/lifecycle.md`, `references/authoring.md`, and `references/recovery.md`. Verify the complete file set, SHA-256 digests, and `name: use-sanho` frontmatter before atomically moving it to `~/.agents/skills/use-sanho`. Repeat every raw GitHub endpoint and the user-global target in the installation proposal even though the comparison fetch itself needs no separate approval.

If the target already exists, compare it with the verified source, show the complete diff, follow the shared backup policy, and obtain separate replacement approval. Under the no-backup policy, remove only the exact approved target after the incoming file set is fully verified; disclose that local modifications will not be recoverable from the release ref. Never overwrite, merge, delete, or repair another discovered copy silently. After installation or replacement, tell the user to restart Codex so a new session loads the skill snapshot.

`sanho status` separates committed `HEAD` prediction from working-copy and local operation readiness. Consume `relation`, `publication`, `sync_preview`, `working_copy`, `local_readiness`, and `sync_in_progress` independently. Do not expose project URLs, actor email, workspace IDs, private paths, or doctor details in setup reports.

Use `sanho check --require-clean`, `--require-current`, and `--require-published` only when repository authority selects those policies. Exit 1 with `passed:false` is a policy mismatch; an `error` envelope means evaluation failed. `--require-current` contacts the canonical remote and requires network approval. `sanho diff`, `sanho diff --refresh`, and `sanho diff --local` are read-only inspection commands without JSON output; `--refresh` contacts the canonical remote.

At an authorized push boundary, leave `sanho preview --json` to the matching `use-sanho` skill. Preview writes nothing and reports a blocked push at exit 0, so branch on `blocked` and `verdict`, not the exit code; add `--refresh` only with network authorization when the verdict must match the canonical state the hook will fetch. A preview describes one snapshot and never grants push authority, while `sanho check` remains the explicit policy gate.

Leave canonical history and rewrite-recovery inspection to the matching `use-sanho` skill through read-only `sanho log` and `sanho show <commit>`. Both default to the cached canonical snapshot and `--refresh` requires network authorization. Source filters must use exact non-empty repository or workspace values from observed provenance; an `external` entry has `source: null` and matches no source filter. Use `show` before adopting an external recovery anchor, preserve binary content as classified with null content, and treat `too_large` as a bounded refusal rather than loading the document another way.

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

Supported release line: stable `v0.1.18` through `v0.1.x`, native Apple Silicon macOS only. Resolve the newest non-draft, non-prerelease tag in that range. Use the same exact tag for the CLI and its optional `use-mulgae` skill; v0.1.17 lacks the current provider certification floors and literal-packet AGY qualification authority required by Aquarium, and do not automatically cross into `v0.2+`. Installation requires Go `1.26.6` or newer.

Install an approved tag:

```bash
go install github.com/irootkernel/mulgae@<tag>
```

The binary does not install the agent skill. Default setup diagnosis uses only `command -v mulgae`, `mulgae version --json`, and `mulgae doctor --output json`, plus effective Codex MCP inspection when available. Require the `mulgae-command-result.v5` envelope and feature-detect `result.doctor.schema_version=mulgae-doctor-result.v2`. If Doctor v2 is absent, report the capability as unsupported; never fabricate failed dimensions or reconstruct them from `.mulgae/config.yaml` or `.mulgae/local.yaml`.

Project Doctor v2 reports `config_v3`, `local_configuration`, `provider_identity`, `configured_readiness`, and `role_route_readiness` independently. Preserve its `verified`, `failed`, `unverifiable`, and `not_applicable` states and each configured `provider_inventory[]` row's `binary_available` and `cli_compatible` fields. Use `cli_compatible.eligibility` as Mulgae's provider-version decision; `newer_than_verified` remains ready when eligibility is `eligible`. Treat setup as configured only when `configured_readiness.state=ready` and `exit_code=0`. Do not gate or report setup on static evidence, heartbeat, historical reviews, or `review_qualified`, and never report native homes, executable paths, credential-profile homes, credentials, diagnostic messages, request IDs, timestamps, or raw provider output.

Setup does not need `mulgae providers --output json`. If that command is explicitly inspected outside the default setup flow, keep `offline_ready_provider_count` and `static_evidence_ready_provider_count` distinct; missing static evidence is not a generic unavailable provider.

For a new Codex user-scoped skill installation, use only these files from the automatically fetched and verified `https://raw.githubusercontent.com/irootkernel/mulgae/<tag>/skills/use-mulgae/` payload: `SKILL.md`, `references/lifecycle.md`, `references/authoring.md`, and `references/recovery.md`. Verify the complete file set, SHA-256 digests, and `name: use-mulgae` frontmatter before atomically moving it to `~/.agents/skills/use-mulgae`. Repeat every raw GitHub endpoint and the user-global target in the installation proposal even though the comparison fetch itself needs no separate approval.

If the target already exists, compare it with the verified source, show the complete diff, follow the shared backup policy, and obtain separate replacement approval. Under the no-backup policy, remove only the exact approved target after the incoming file set is fully verified; disclose that local modifications will not be recoverable from the release ref. Never overwrite, merge, delete, or repair another discovered copy silently. After installation or replacement, tell the user to restart Codex so a new session loads the skill snapshot.

Mulgae Config v3 has two authorities. `.mulgae/config.yaml` is Git-shareable project policy; `.mulgae/local.yaml` is untracked mode-`0600` machine configuration. Keep `execution.workspace_access: none`. Ask which providers and roles to configure. Automatic provider selection still requires authenticated ZCode and AGY; Kimi and Codex are explicit opt-ins, and bare initialization enables only the required `logic` role. Show discovered executable, launcher, data-home, and credential-home paths only in the exact private setup proposal, never in the diagnostic report.

For a new project, run `mulgae init --output json` with every intended provider and role only after approval; it creates both Config v3 files, writes `validation.extraction.enabled: true` for prose-first structured finding extraction, and does not edit Git ignore state. When a clone contains only shared `config.yaml`, plain `mulgae init --output json` bootstraps only `local.yaml` and rejects project-policy options.

An older Config v3 that omits `validation.extraction.enabled` remains valid and treats extraction as disabled/defaulted. Do not add the field during diagnosis, clone bootstrap, refresh, or an unrelated repair. Enabling it in an existing project changes shared project policy and requires an exact diff plus separate approval. Once the field is written, every collaborator and automation reading the config must use Mulgae v0.1.16 or newer because v0.1.15 rejects the unknown field; never claim backward compatibility or silently remove the policy.

When provider paths move or the shared provider set changes, propose `mulgae init --refresh-local --output json`, which preserves `config.yaml` and replaces only `local.yaml`; apply the shared backup policy to the replaced local file. Keep new initialization, clone bootstrap, and refresh as distinct approvals.

Config v1 and v2 are unsupported and have no automatic migration. Show the exact legacy files without reading or printing their contents and apply the shared backup policy before removal.

Under the backup policy, separately propose a user-chosen mode-`0700` backup directory outside the repository, preserve both files and their modes with `cp -p`, privately verify file names, modes, and SHA-256 digests, and disclose the exact `cp -p` restoration commands.

Under the no-backup policy, disclose that legacy project policy, private paths, modes, and other local-only values will not be recoverable unless the user independently versioned them. Obtain separate approval for the exact destructive legacy-file removal under either policy.

If Config v3 initialization fails, preserve the failure and do not partially edit either authority. Offer the disclosed restoration only when a verified backup exists; otherwise report that no rollback copy is available. Never reinterpret legacy provider policy or private paths automatically.

When the user selects Codex, require a real Codex CLI `0.149.0` or newer and let Mulgae diagnose its authenticated readiness; never sign in, read `auth.json`, or accept an API-key environment variable on the user's behalf. A single-profile configuration uses the selected native Codex login with `mulgae init --providers codex --roles <roles> --output json`. Optional model and reasoning-effort values are shared project policy; omission preserves Codex CLI defaults.

For several Codex identities, keep the two authorities separate using this Config v3 shape; it is sufficient for the active setup session even when a newly replaced `$use-mulgae` skill will not load until Codex restarts:

```yaml
# .mulgae/config.yaml project policy (relevant fields)
providers:
  codex:
    default_credential_profile: "personal"
roles:
  logic: {enabled: true, primary_provider: "codex"}
  security: {enabled: true, primary_provider: "codex", credential_profile: "work"}
```

```yaml
# .mulgae/local.yaml private machine mapping (relevant fields)
providers:
  codex:
    executable: "/absolute/path/to/the/common/codex"
    credential_homes:
      - profile: "personal"
        home: "/absolute/private/CODEX_HOME"
      - profile: "work"
        home: "/absolute/private/work-CODEX_HOME"
```

Use operator-chosen lowercase kebab-case aliases, map exactly the default and role override aliases in lexical order, and use one common real Codex executable. Obtain separate approval for the shared policy and private local mapping, show the exact proposed YAML privately, and preserve unrelated Config v3 fields. Mulgae may project only the selected home's `auth.json` into a disposable runtime; do not expose profile paths or credential material. After writing, require Doctor v2 to verify provider identity, report the intended role-to-profile aliases through redacted role references, and mark Codex binary and CLI compatibility ready without returning any home or executable path.

Mulgae v0.1.16 preserves the accepted Markdown report byte-for-byte, then may use the internal `002-extract` artifact to derive structured finding candidates. Retry, repair, and extraction share the single second provider-invocation slot, so extraction does not increase the existing invocation budget; never run `002-extract` manually or add an agent-side retry. Keep reports, extraction artifacts, complete provider stdout, and complete provider stderr in private Mulgae runtime state. Consume only bounded structured status, finding, and readiness fields in Aquarium workflows, and verify every extracted finding as an advisory hypothesis against current authority and implementation.

Track `structured_extraction_status` as an evidence axis independent of review completion: `structured` means structured candidates were derived, `mixed` means only some accepted reports produced them, and `reports_only` means accepted reports remain authoritative without structured candidates. `reports_only` is not itself a failure and never replaces or relaxes capture coverage, CI decision, publication, findings-query, or unresolved-valid-finding requirements.

Setup verification remains limited to version, Doctor v2, and effective MCP registration. The command envelope is `mulgae-command-result.v5`, Doctor remains `mulgae-doctor-result.v2`, and preflight remains `mulgae-review-preflight.v3`; do not infer new setup probes from extraction or lifecycle support. Doctor's adapter-owned local version command is offline: it uses no credential projection, project working directory, provider API, or network request. Do not inspect config contents or runs, and do not invoke heartbeat, qualification, preflight, review, source transmission, or MCP startup to validate setup.

Heartbeat is outside setup. Only after a separate explicit user request acknowledging possible authentication, network access, cost, and remote logging may an agent propose `mulgae heartbeat --provider <family> --authorize-live-request --output json`, adding `--credential-profile <profile>` only for an explicitly selected named Codex configuration. Never add `--authorize-live-request` automatically. Require `mulgae-provider-heartbeat-result.v1` and preserve its typed `succeeded`, `provider_failure`, `timeout`, `authentication_failure`, `malformed_response`, or `execution_failure` status without retry. Do not promote success into offline readiness or review qualification. Without authorization, preserve Mulgae's `attempted=false` and `live_authorization_required` result.

Propose these root-anchored Git ignore rules through an exact reviewed diff:

```gitignore
/.mulgae/*
!/.mulgae/config.yaml
```

Verify that only `.mulgae/config.yaml` is trackable and that `.mulgae/local.yaml` and all runtime state remain untracked and ignored. Propose `.mulgaeignore` entries from the repository's secrets, generated output, large artifacts, agent instructions, and non-reviewable paths. A `.mulgaeignore` intended as shared capture policy may be tracked only with explicit approval.

Treat MCP as an optional, separately approved component and prefer one user-global registration in the active Codex home (`$CODEX_HOME/config.toml`, default `~/.codex/config.toml`). A global registration inherits the active Codex session's working directory, so do not pin a repository path or `cwd`:

```toml
[mcp_servers.mulgae]
command = "<absolute-selected-mulgae-path>"
args = ["mcp"]
required = true
startup_timeout_sec = 30
tool_timeout_sec = 7501
```

When the user explicitly chooses repository-local scope, merge this machine-specific alternative into `<absolute-git-root>/.codex/config.toml` while preserving unrelated configuration:

```toml
[mcp_servers.mulgae]
command = "<absolute-selected-mulgae-path>"
args = ["mcp", "--project-root", "<absolute-git-root>"]
cwd = "<absolute-git-root>"
required = true
startup_timeout_sec = 30
tool_timeout_sec = 7501
```

Show the complete diff and target scope before approval; for a local target also show whether `.codex/config.toml` is tracked. Verify three views independently without starting the server: query the global registration from a neutral filesystem-root cwd with the active Codex home, query the local registration from the same neutral cwd with `CODEX_HOME=<absolute-git-root>/.codex`, and query the effective registration from the repository with the active Codex home. Treat a named server as absent only when its entire stderr is Codex's exact named-server-not-found diagnostic. Timeout, mixed diagnostics, malformed output, and every other nonzero result are degraded or unverifiable, never proof of absence.

The effective entry must be enabled STDIO, resolve to the selected binary, be required, and use startup and tool timeouts at least as large as the proposed defaults. Global scope requires exact `args = ["mcp"]` and no fixed `cwd`; local scope requires exact `mcp --project-root <canonical-root>` arguments and repository-bound `cwd`. The 7501-second tool timeout covers the admitted two-hour review deadline plus retry and finalization margin; preserve any larger existing value. Record the Codex version and output capability separately. An observable `required: true` is verified, observable `false` is a registration mismatch, and an absent field is `required_unverifiable`; absence alone is not a mismatch because supported Codex output may omit the configured property.

Whenever an isolated local Mulgae registration exists, ask whether that scope is intentional. If confirmed, preserve it even when global is preferred. If not, show and separately approve removal of only the local `mulgae` table, using `CODEX_HOME=<absolute-git-root>/.codex codex mcp remove mulgae` or an equivalent exact TOML edit. Reinspect the file afterward. Delete `.codex/config.toml` only when parsed TOML has no remaining semantic content, and delete `.codex/` only when the directory is then empty; preserve comments with retained settings, every unrelated table, and every nonempty directory. Apply the shared backup policy before removal, never remove the global registration as part of local cleanup, and never stage the file during setup. Repository configuration paths must be regular non-symlink paths before `mulgae doctor` or any owning Codex CLI probe may read them.

Never stage it during setup. Tell the user to restart Codex so a new session can expose `preflight_review`, `start_review`, `await_review`, `cancel_review`, the foreground-compatible `run_review`, `list_runs`, `get_run`, `list_findings`, and verified report and finding resources. The v0.1.17 lifecycle starts exactly once and awaits the same process-local invocation without transferring observer cancellation to provider execution; use the foreground path atomically when any lifecycle tool is absent. The attached MCP surface remains versioned independently; CLI fallback preflight must identify `mulgae-review-preflight.v3`.

Verify configuration, provider readiness, skill files, and MCP registration only. Do not start the MCP server or run heartbeat, review, qualification, preflight, follow-up, delta, rerun, report, export, or any command that captures, transmits, or writes review source or artifacts during setup. Mulgae owns its bounded same-provider retry; never add a downstream review, qualification, or heartbeat retry for a final typed failure.

## Gaori

Official source: `https://github.com/irootkernel/gaori`

Supported release line: stable `v0.1.14` through `v0.1.x`. Resolve the newest non-draft, non-prerelease tag in that range. Use the same exact tag for the CLI and its optional `use-gaori` skill; v0.1.13 lacks the terminal-only `await_run` surface required by Aquarium, and do not automatically cross into `v0.2+`.

Install an approved tag:

```bash
go install github.com/irootkernel/gaori@<tag>
```

The binary does not install the agent skill. Diagnose the CLI and repository with `command -v gaori`, `gaori version --json`, and, when `.gaori/tester.yaml` exists, `gaori --json config check`. Diagnose `use-gaori` and global, local, and effective MCP registration independently. Config check validates schema-v2 config and all stored rules without resolving executables, running commands, or creating evidence.

For a new Codex user-scoped skill installation, use only these files from the automatically fetched and verified `https://raw.githubusercontent.com/irootkernel/gaori/<tag>/skills/use-gaori/` payload: `SKILL.md`, `references/lifecycle.md`, `references/authoring.md`, and `references/recovery.md`. Verify the complete file set, SHA-256 digests, and `name: use-gaori` frontmatter before atomically moving it to `~/.agents/skills/use-gaori`. Repeat every raw GitHub endpoint and the user-global target in the installation proposal even though the comparison fetch itself needs no separate approval.

If the target already exists, compare it with the verified source, show the complete diff, follow the shared backup policy, and obtain separate replacement approval. Under the no-backup policy, remove only the exact approved target after the incoming file set is fully verified; disclose that local modifications will not be recoverable from the release ref. Never overwrite, merge, delete, or repair another discovered copy silently. After installation or replacement, tell the user to restart Codex if the skill does not appear in the active session.

Discover required checks from repository instructions, task runners, manifests, and CI before proposing `.gaori/tester.yaml` schema version 2. Map each configured command ID to an existing argv array, non-empty tags, explicit parser, and timeout. Use `gaori --json parsers list` as the authoritative live registry before selecting a parser. The v0.1.14 registry has fifteen labels; `dotnet-test` and `gradle-test` are Experimental and their bounded summaries may require manual confirmation. Use `gaori --json parsers detect <raw-log>` only to diagnose an explicitly selected existing log: it reports candidates without selecting a parser, loading configuration, creating evidence, or changing the command result. Do not add secrets, absolute paths, or machine-specific arguments to portable configuration.

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

This keeps `.gaori/toolchain.yaml`, `.gaori/rule-proposals/`, `.gaori/runs/`, and every other Gaori path local. Active rule YAML is executable extraction policy: do not create, update, stage, or commit it without the user's specific intent and review. Validate approved config or rule changes with `gaori --json config check`. When approved redaction patterns change and the user has explicitly selected an existing raw log no larger than 256 KiB, use `gaori --json config check --sample <raw-log>` to report ordered match and replaced-byte counts without emitting matched text or pattern definitions. Do not run configured tests during setup.

Leave completed evidence and proposal reconciliation to the matching `use-gaori` skill. Its `gaori --json runs list`, `gaori --json rules proposals`, and `gaori rules show --proposal <name>` paths are read-only discovery, not repair, activation, command reruns, or durable job recovery. Never inspect prior run contents or raw logs automatically during setup.

Treat MCP as an optional, separately approved component and prefer one user-global registration in the active Codex home (`$CODEX_HOME/config.toml`, default `~/.codex/config.toml`). A global registration inherits the active Codex session's working directory, so do not pin a repository path or `cwd`:

```toml
[mcp_servers.gaori]
command = "<absolute-selected-gaori-path>"
args = ["mcp"]
tool_timeout_sec = 3601
```

When the user explicitly chooses repository-local scope, merge this machine-specific alternative into `<absolute-git-root>/.codex/config.toml` while preserving unrelated configuration:

```toml
[mcp_servers.gaori]
command = "<absolute-selected-gaori-path>"
args = ["--repo", "<absolute-git-root>", "mcp"]
tool_timeout_sec = 3601
```

Show the complete diff and target scope before approval; for a local target also show whether `.codex/config.toml` is tracked. Never stage it during setup. Verify global, isolated local, and effective registrations with the same three-view procedure used for Mulgae. Global scope requires exact `args = ["mcp"]` and no fixed `cwd`; local scope requires exact `--repo <canonical-root> mcp` arguments and no fixed `cwd`. Do not start the server or a test. Require a numeric, non-boolean `tool_timeout_sec` of at least 3601 seconds so the host deadline exceeds a one-hour command and evidence finalization, while preserving any larger existing value. Report missing or inadequate timeout, disabled, non-STDIO, unresolvable-command, wrong-repository, and inactive or untrusted entries as degraded. Treat only Codex's exact named-server-not-found diagnostic as absence.

Whenever an isolated local Gaori registration exists, ask whether that scope is intentional. If not, show and separately approve removal of only the local `gaori` table, using `CODEX_HOME=<absolute-git-root>/.codex codex mcp remove gaori` or an equivalent exact TOML edit. Apply the same backup, semantic-empty-file, empty-directory, unrelated-setting preservation, and no-staging rules as Mulgae local cleanup. Never remove the global registration as part of local cleanup.

Tell the user to restart Codex so a new session can expose `start_configured_run`, `start_ad_hoc_run`, `get_run`, `wait_run`, terminal-only `await_run`, `cancel_run`, `get_excerpt`, and the read-only `list_runs` completed-evidence inventory. `await_run` observes one process-local invocation without cancelling execution when that observer ends; use `get_run` or bounded `wait_run` when the host deadline cannot safely cover terminal completion. `list_runs` is stateless and cannot recover an invocation ID or reattach a disconnected run. Every present repository configuration path that Gaori may inspect, including `.gaori/tester.yaml`, every descendant of `.gaori/tester/rules/`, and `.gaori/toolchain.yaml`, must have regular non-symlink lexical ancestry before any owning CLI probe may read it; an absent primary path stops that probe rather than consulting ambient state.

## Lora / Lore

Official source: `https://github.com/tmdgusya/lora`

Lora distributes agent skills rather than a runtime service. Configure it for Codex user-global scope. Resolve the latest stable tag when one exists; otherwise resolve the full current `main` commit SHA and disclose that fallback before approval. Because `npx skills add <repository>#<full-sha>` treats the SHA as a branch name, prepare a temporary detached checkout at the approved commit and install from that local source instead.

Install only the two compatible skills from the approved ref:

```bash
git clone --filter=blob:none --no-checkout https://github.com/tmdgusya/lora <temporary-source-root>/lora
git -C <temporary-source-root>/lora fetch --depth=1 origin <approved-tag-or-full-sha>
git -C <temporary-source-root>/lora checkout --detach FETCH_HEAD
git -C <temporary-source-root>/lora rev-parse HEAD
npx skills add <temporary-source-root>/lora \
  --skill lore-commits \
  --skill lore-query \
  --global \
  --agent codex \
  --copy \
  --yes
```

The clone and fetch contact GitHub, and `npx` contacts npm and writes under the Codex user-global skill directory. Require the detached `HEAD` to equal the approved ref before installation. Do not install or invoke Lora's `lore-setup`; it copies the full Lore protocol into AGENTS.md and conflicts with the reference-and-override policy. If `lore-setup` is already installed, report it without removing or rewriting it.

Before updating an existing `lore-commits` or `lore-query`, compare its complete installed file set with the approved source, show the target and diff, and apply the shared backup policy before the approved `npx skills add` action. Under the no-backup policy, disclose that local modifications will not be recoverable from the source ref. After installation, enumerate both complete source and target trees, reject missing and extra paths, and compare every regular file byte-for-byte; any symlink or digest mismatch fails verification. The bundled inspector reports only structural presence and frontmatter as `unverifiable`, never complete-source currency. Do not report configured until this post-action complete-tree comparison passes. Do not treat installation as commit authority.

## Cursor Team Kit / Deslop

Official source: `https://github.com/cursor/plugins`

Deslop is a separately installed upstream prerequisite, not an Aquarium skill. This integration has no supported skill-specific release line, so resolve and disclose the full current `main` commit SHA through official GitHub commit metadata, then prepare a temporary detached checkout at that exact commit. Never install from a moving `main` or use a full SHA as an `npx skills` URL fragment.

Install only the upstream Deslop skill from the approved checkout and preserve its parent plugin's MIT notice:

```bash
git clone --filter=blob:none --no-checkout https://github.com/cursor/plugins <temporary-source-root>/cursor-plugins
git -C <temporary-source-root>/cursor-plugins fetch --depth=1 origin <approved-full-sha>
git -C <temporary-source-root>/cursor-plugins checkout --detach FETCH_HEAD
git -C <temporary-source-root>/cursor-plugins rev-parse HEAD
npx skills add <temporary-source-root>/cursor-plugins/cursor-team-kit \
  --skill deslop \
  --global \
  --agent codex \
  --copy \
  --yes
install -m 0644 <temporary-source-root>/cursor-plugins/cursor-team-kit/LICENSE ~/.agents/skills/deslop/LICENSE
```

The clone and fetch contact GitHub, and `npx` contacts npm and writes `~/.agents/skills/deslop`. Show every endpoint, command, approved SHA, target, source digest, and expected file before installation approval. Verify that the installed `SKILL.md` and LICENSE are byte-identical to the detached checkout, the frontmatter is exactly `name: deslop`, the target contains no extra files, and no duplicate or symlink installation exists in another Codex skill root.

If the target exists, compare its complete tree with the approved source plus LICENSE, show the complete diff, apply the shared backup policy, and obtain separate replacement approval. Never merge an Aquarium variant or local customization into the upstream payload. After installation or replacement, clean up the ephemeral checkout when possible and tell the user to restart Codex before resuming the requesting Aquarium workflow.

## Podway

Official source: `https://github.com/irootkernel/podway`

Supported release line: stable `v0.2.6` through `v0.2.x`, native Apple Silicon macOS only. Resolve the newest non-draft, non-prerelease tag in that range. Use the same exact tag for the CLI, daemon, and optional `use-podway` skill. Podway v0.2.5 has migrated reset-receipt read-back, degraded-store reset recovery, and bounded correlated daemon-log guarantees, but lacks the Procedure declaration-limit compatibility required by Aquarium. Do not automatically cross into `v0.3+`.

Resolve the exact release from GitHub Releases and download the Apple Silicon archive plus its published `.sha256` file. Disclose that release binaries are unsigned and not notarized. Verify with `shasum -a 256 -c` before installing both `podway` and `podwayd` at the approved user-local paths. Do not accept a prerelease, a version before v0.2.6, `v0.3+`, an unverified archive, mixed CLI and daemon versions, or unsupported platform.

The binaries do not install the agent skill. Diagnose `use-podway` independently in the Codex skill roots. For a new Codex user-scoped installation, use only `SKILL.md`, `references/lifecycle.md`, `references/authoring.md`, and `references/recovery.md` from the automatically fetched and verified `https://raw.githubusercontent.com/irootkernel/podway/<tag>/skills/use-podway/` payload. Verify the complete file set, SHA-256 digests, and `name: use-podway` frontmatter before atomically moving it to `~/.agents/skills/use-podway`. Repeat every raw GitHub endpoint and the user-global target in the installation proposal even though the comparison fetch itself needs no separate approval.

If the target exists, compare it with the verified source, show the complete diff, follow the shared backup policy, and obtain separate replacement approval. Under the no-backup policy, remove only the exact approved target after the incoming file set is fully verified; disclose that local modifications will not be recoverable from the release ref. Never overwrite, merge, delete, or repair another discovered copy silently. After installation or replacement, tell the user to restart Codex so a new session loads the skill snapshot.

Install or refresh the per-user service only after separate approval:

```bash
podway daemon install --daemon-path <absolute-podwayd-path>
podway daemon status --json
```

If that install is interrupted after authenticated service metadata is prepared, rerun the same approved command with the same absolute daemon path and no `--socket` override. Podway v0.2.5 reconciles the prepared receipt and waits for the prior launchd label to unload before replacement bootstrap. Never edit service metadata, sockets, receipts, or LaunchAgent files to recover the installation.

Podway v0.2.5 writes daemon events as bounded fixed-schema `podway.daemon-log/v1` JSONL with opaque request, workspace, session, job, and diagnostic correlation. It keeps at most ten 1-MiB daemon-log files and a separate daemon-owned five-file bootstrap stream while LaunchAgent standard output and error go to `/dev/null`. Treat these logs as bounded diagnostics, not lifecycle authority, and never expose raw log contents in setup reports.

The LaunchAgent runs after GUI login under the same OS user and is not a multi-user security boundary. Verify the compact `podway version --json` result, the `podway.output/v3` daemon envelope with `podway.daemon-status-result/v1` or `podway.daemon-status-result/v2`, daemon reachability and exact version match, and the `podway.output/v3` doctor envelope when the worktree is initialized. Daemon status v1 remains compatible. For v2, require `readiness_state=ready`, `readiness_stage=ready`, and closed `worktree_recovery` with every worktree completed and none failed before treating the daemon as healthy. Do not invoke a reserved readiness-wait command during setup. The read-only readiness inspector may inventory a session through `podway.status-result/v3` or `podway.compact-status-result/v3`; managed workflow automation must use `podway observe --json --wait-for-idle` and require `podway.observation-result/v2`. Prepared lifecycle mutations use `podway.session-start-result/v3`, `podway.session-begin-result/v1`, `podway.terminal-disposition-result/v1`, and `podway.session-reset-result/v1`; prepared-aware lifecycle jobs use `podway.job-result/v4` and `podway.job-lookup-result/v4`. Errors remain `podway.error/v1`.

`start` creates a prepared revision-0 session without a cursor, attempt, or goal. The owning handler must re-observe it and use the fresh fenced `session.begin` mutation template to create attempt 1 and any initial goal before recording evidence. A prepared session permits only begin, eligible reset, or eligible replacement. Terminal sessions expose a disposition template until the exact current revision records `handed_off` or `not_required`; only then may an approved normal reset or `start --replace-eligible` proceed. Never substitute force reset or force replacement for missing handoff authority.

Treat that bounded inventory as readiness evidence only. Never use dev-setup to observe, cancel, discard, or reset a routine supported Procedure v2 current session; return an exact standalone `$use-podway` lifecycle request instead. Keep `LEGACY_PROCEDURE_STATE_UNSUPPORTED` and its separately approved workspace-wide `podway reset --all` recovery as the only session-state reset exception in this catalog.

Repository initialization and Aquarium readiness configuration require another approval. `podway init` creates `.podway/config.yaml` and `.podway/.gitignore` for the repository to track, plus ignored `.podway/runtime/`. Copy the five plugin-owned Procedure v2 sources to `.podway/procedures/` byte-for-byte and validate each with:

```bash
podway procedure check --warnings-as-errors <procedure-file>
```

The five required IDs are `aquarium-task-v2`, `aquarium-goal-v2`, `aquarium-validation-v2`, `aquarium-design-v2`, and `aquarium-war-room-v2`. Their presence describes readiness, never workflow activation. Require regular non-symlink files and non-symlink path components before hashing or invoking `procedure check`; a symlinked managed path is degraded and must never be read or executed. Check each safe present file independently even when it differs from the plugin source. All absent means `readiness_status=not_configured`; all present, tracked in Git, byte-identical, valid, and healthy means `readiness_status=ready`; partial, drifted, invalid, unsupported, or unhealthy state means `readiness_status=degraded`. The v8 inspection omits Podway unless invoked with `--include-podway`.

Updating a tracked copy requires showing and approving its exact diff and applying the shared backup policy; an active session retains its immutable snapshot.

The renamed inspector reports `migration_required=true` when any tracked or untracked `root-kernel-task-v2.yaml`, `root-kernel-goal-v2.yaml`, or `root-kernel-validation-v2.yaml` remains in `.podway/procedures/`. This is a product-rename migration and forces degraded readiness until the old files are separately removed and the `aquarium-*` files are installed. Finish or explicitly dispose of any active old session first; never convert or delete its runtime history as part of managed-file replacement.

The v8 inspector reports `migration_kinds.product_rename` and `migration_kinds.podway_v0.2.5_workaround` separately. The latter is true only for the exact deterministic v0.2.5 compatibility bytes derived from the current canonical source: the goal Procedure omits its one `max_total_length: 1000000`, while task and validation replace their one adjacent `max_item_length: 1200` plus `max_total_length: 1000000` pair with `max_item_length: 1000`. It classifies every other mismatch as `diverged`. Never keep or install a second workaround source. Show the exact diff and separately approve replacement with the canonical plugin bytes; the workaround remains degraded until then.

`LEGACY_PROCEDURE_STATE_UNSUPPORTED` has a different meaning: the runtime contains Procedure v1 task state. Do not convert, edit, or delete that state automatically. Report the exact worktree and error and apply the shared backup policy before separately proposing the supported `podway reset --all` recovery. Under the no-backup policy, disclose that the reset permanently deletes the legacy runtime history and that Git cannot restore it, then require separate explicit approval.

Podway v0.2.5 also preserves explicit confirmed `podway reset --all` recovery when the workspace binding is readable but disposable full-store openability or internal-codec inspection fails. Treat that condition as degraded, preserve the exact stable error evidence, apply the shared backup policy, and require a separate reset proposal and explicit approval; recoverability never grants deletion authority.

## Ouroboros

Official source: `https://github.com/Q00/ouroboros`

Python package: `ouroboros-ai`. Support only `>=0.51.1,<0.52.0`; do not automatically cross into `0.52+`. Installation requires an existing `uv` and one resolved exact package version. Show the Python package index request, exact version, package target, and `uv tool install ouroboros-ai==<exact-version>` or exact approved upgrade command before separate approval. Never install `uv` as a side effect and never install an unpinned range.

Diagnose four independent components with the v7 inspector's explicit `--include-ouroboros` flag: the CLI through `ooo --version`, Codex rules and skills through `ooo codex doctor`, and the effective registration through `codex mcp get ouroboros --json`, plus runtime configuration through the matching launcher contract. Run `ooo mcp doctor --json` only for a direct selected-`ooo` registration because it inspects that package environment. For the canonical `uvx --isolated` launcher, derive runtime configuration from the exact isolated command instead; do not misclassify an intentional MCP 1.x base profile as the MCP 2 server environment. These probes are local and read-only: they do not contact a provider, initiate authentication, make a network request, or start an MCP server, though the direct MCP doctor may inspect bounded local authentication-readiness metadata without exposing credential material. A healthy CLI does not prove that packaged Codex rules and skills are installed, that the MCP runtime is configured, or that Codex has an enabled registration.

The inspector checks Codex registration even when `ooo` is absent. Registration is `configured` only when the entry is named `ouroboros`, enabled, uses STDIO, and matches either the selected `ooo` executable with exactly `args = ["mcp", "serve"]` or Ouroboros's canonical isolated Codex launcher. The isolated form resolves to the PATH-selected `uvx`, uses exactly one ordered `--isolated --python >=3.12 --from ouroboros-ai[mcp]` prefix with an optional supported exact release pin, ends in `ouroboros mcp serve`, and selects Codex through the required environment or exact command suffix. The environment form requires `OUROBOROS_AGENT_RUNTIME=codex` and `OUROBOROS_LLM_BACKEND=codex`; optional `OUROBOROS_RUNTIME`, when present, must also equal `codex`. The suffix form is exactly `--runtime codex --llm-backend codex`. Reject unsupported pins, inherited nested-runtime sentinels, conflicting selectors, missing extras, extra arguments, and registration environment keys outside those three selectors. A canonical isolated registration establishes configured runtime state without running the base-environment MCP doctor, including when the base `ooo` executable is absent; a registration that matches neither supported launcher leaves runtime configuration unverifiable without probing an unrelated package environment, and live tool exposure remains separate host evidence. Registration is `missing` only for Codex's definite named-server-not-found response, `degraded` for disabled, mismatched, incomplete, malformed, timed-out, or failed probes, and `unverifiable` when Codex itself is absent. Report only the normalized status and reason code; never expose raw registration stderr or configuration secrets.

Package installation or upgrade and the selected configuration action are separate persistent mutations with separate approvals. For full configuration, run only `ooo setup --runtime codex --non-interactive --mcp-mode auto`: it installs and prunes packaged Codex rules and upstream Ouroboros skills while it may also change Codex MCP configuration and Ouroboros runtime state. Do not run `ooo codex refresh` before full setup. Offer refresh only as a separately approved rules-and-skills repair alternative when full setup is not selected. Re-read exact targets before each approved mutation and stop if they changed.

No setup action authorizes a provider call, authentication, repository-source transmission, `auto`, `run`, `ralph`, `evolve`, Seed creation, or an Aquarium design workflow. Verify only version, Codex integration doctor, MCP doctor, effective registration, and, when safely observable in the active host, live MCP tool exposure. A Codex restart may be required after skill or MCP changes.
