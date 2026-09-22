# Development Tool Catalog

This catalog is shared by `dev-setup-global` and `dev-setup`. The global skill owns user-global installation, upgrades, paired skills, services, and global MCP state. The repository skill owns only repository configuration and readiness. Read only the sections needed for the selected components.

Use only the section for a selected tool. Repository instructions override this catalog.

## Aquarium Development Manager

Source: the exact installed Aquarium plugin, under `tools/aquarium-dev/`. This optional local tool uses Aquarium's release version and has hash-pinned MCP Python SDK dependencies. It has no paired skill. Its MCP registration comes from the plugin; do not add a duplicate global registration.

Run `inspect_global_tools.py --component aquarium-dev` to compare the installed runtime with the bundled source and check its launcher without changing either. This component requires Apple Silicon macOS and Python 3.11 or newer. It is not a production-binary prerequisite.

For a scoped install or update request, resolve the current skill's plugin root, inspect its payload, and show the exact bundled version, source digest, manager root, launcher target, and existing state. After runtime and launcher approval, run:

```text
python3 <plugin-root>/tools/aquarium-dev/install.py install --approve-install --approve-launcher
```

The same command installs or updates. It creates an isolated Python environment under `~/.aquarium-dev/manager/versions/` and installs exact, hash-verified wheels from `https://pypi.org/simple` and its `files.pythonhosted.org` download host. Disclose that network access before execution. It validates the package and SDK before switching `manager/current`, installs the regular-file `~/.local/bin/aquarium-dev` entry, and preserves the prior runtime and launcher if preparation or selection fails. Prior runtime generations remain available to admitted workers and open MCP sessions. No source is uploaded.

Re-run diagnosis and `~/.local/bin/aquarium-dev version`. Start a new Codex session for the plugin's MCP server. A plugin update does not update the runtime automatically; an identity mismatch requires this explicit update before the bundled MCP server can start. The existing CLI remains on its installed version. The installer does not change Git hooks, enroll checkouts, build producers, activate services, configure Codex, or change authentication. Legacy hook migration is a later, separately approved `aquarium-dev enroll` operation described in the [development contract](development-contract.md).

## Aquarium Production Status

Source: the exact installed Aquarium plugin under `tools/aquarium-status/`. Run
`inspect_global_tools.py --component aquarium-status` for read-only diagnosis.
The component is selected by default for unscoped global setup and once as
infrastructure for a setup bundle, but it is not a production-binary prerequisite
or a bundle manifest v1 tool.

Installation requires Apple Silicon macOS and Python 3.11 or newer. Before an
approved install, update, or repair, disclose `https://pypi.org/simple` and
`https://files.pythonhosted.org`, the exact `~/.aquarium/status-runtime/` and
`~/.local/bin/aquarium-status` targets, and whether either target already exists.
Never replace an unknown regular launcher. After approval run:

```text
python3 <plugin-root>/tools/aquarium-status/install.py install --approve-install --approve-launcher
```

The installer admits only hash-pinned PyYAML 6.0.3 binary wheels, verifies the
payload, interpreter, and every dependency file before activation, and restores
the prior selector and launcher if activation fails. It uploads no source or
ledger data. Re-run the scoped inspector and `aquarium-status show --format
json`; the latter reports history and freshness but does not establish live tool
health. Plugin updates never update this runtime automatically.

## Shared version and safety policy

- Resolve the latest non-draft, non-prerelease stable release at execution time from the official repository, limited to a tool's supported release line when its section defines one. Display the exact tag and source before installation; never substitute `@latest` after approval.
- Use the selected upstream release's documented default skill location. When it names `$CODEX_HOME`, use the active Codex home's `skills` directory (`~/.codex/skills` when unset). When it gives no default location, use `~/.agents/skills`. Check locations loaded by the same Codex home before installing so setup does not create a duplicate.
- Preserve an already compatible installation unless the user approves an upgrade.
- Diagnose credentials by whether the owning CLI reports readiness. Never print, copy, or persist credential material.
- Keep configuration in each tool's native files. Never create `.aquarium`, a selection manifest, or a shadow version registry.
- A direct unscoped `$aquarium:dev-setup-global` invocation authorizes bounded official Release metadata lookup for every supported global component. A scoped continuation authorizes the same lookup only for its named components. Dolgorae, Sanho, Mulgae, Gaori, Sorage, and Podway also allow one disclosed bounded freshness comparison against the paired-skill files from the documented `raw.githubusercontent.com` path in ephemeral storage. Sorage has one file; Dolgorae, Mulgae, and Podway each have four; Sanho has five. Gaori has seven files for `use-gaori` and one for `use-gaori-status`. No separate approval is required for those exact lookups. Treat archive downloads, init, Project registration, ignore edits, hook edits, global installs, provider contact, and every network operation outside these exceptions as separately approved effects.
- Apply the backup policy selected under `Choose a Backup Policy for Existing State` to every approved action that overwrites or removes an existing binary, skill, configuration, service, managed Procedure, or runtime state.

A backup choice requires exact backup and restoration commands plus verification before mutation. A no-backup choice requires the exact loss and recovery boundary in the proposal but no retained copy of the replaced state. It never waives source, checksum, frontmatter, diff, target, or post-install verification, and incoming payload staging is not a backup.

## Choose a Backup Policy for Existing State

When an approved setup plan will first overwrite or remove existing tool, skill, configuration, service, managed Procedure, or runtime state, establish one backup policy for the current setup request. If the user already explicitly requested backups or no backups, adopt that choice without asking again. Otherwise offer `Create and verify backups` and `Proceed without backups`, recommending the backup choice. Do not ask about backups for diagnosis or a new installation that replaces nothing.

Keep the selected policy for later overwrite and removal proposals in the same setup request unless the user changes it. The policy does not authorize any mutation: show and approve every exact replacement or removal. One Ouroboros proposal may cover the listed CLI, home integration, MCP, and migration actions; do not request approval again for an action already covered. Never persist the choice in repository or user-global configuration.

For the backup policy, show the exact backup path, commands, verification, and restoration procedure before approval, and stop before mutation if the selected backup cannot be verified. For the no-backup policy, state the exact existing paths or state that will be lost and the available recovery boundary.

A published Git ref may allow a distributed skill or binary to be installed again, but it does not recover local modifications. Treat tracked state as recoverable only when it already exists in Git history, and disclose that private configuration, untracked files, and runtime history may be permanently lost.

Preparing and validating an incoming payload in a temporary location is not a backup and remains required.

## Sanho

Official source: `https://github.com/irootkernel/sanho`

Supported release line: stable `v0.2.8` through `v0.2.x`. Resolve the newest non-draft, non-prerelease tag in that range. Use the same exact tag for the CLI and its optional `use-sanho` skill; v0.2.7 lacks the dedicated inspection reference, revised authorization and recovery guidance, and conflicted-sync content-retention fix required by Aquarium. Do not automatically cross into `v0.3+`.

Install an approved tag:

```bash
go install github.com/irootkernel/sanho/cmd/sanho@<tag>
```

The binary does not install the agent skill. Diagnose the CLI and workspace with `command -v sanho`, `sanho version --json`, `sanho status --json`, and `sanho doctor --json`; diagnose `use-sanho` independently in the Codex skill roots. Read JSON rather than inferring state from human tables or exit status alone. Doctor exits 0 when it reports warnings, so treat a positive `warnings` count as degraded even when the process succeeds. Every malformed `--json` invocation must return the stable `invalid_arguments` error envelope; parse that envelope separately from the process exit and never reinterpret it as workspace state.

For a new Codex user-scoped skill installation, use only these files from the automatically fetched and verified `https://raw.githubusercontent.com/irootkernel/sanho/<tag>/skills/use-sanho/` payload: `SKILL.md`, `references/authoring.md`, `references/inspection.md`, `references/lifecycle.md`, and `references/recovery.md`. Verify the complete file set, SHA-256 digests, and `name: use-sanho` frontmatter before atomically moving it to `~/.agents/skills/use-sanho`. Repeat every raw GitHub endpoint and the user-global target in the installation proposal even though the comparison fetch itself needs no separate approval.

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

## Dolgorae

Official source: `https://github.com/irootkernel/dolgorae`

Supported release line: official stable `v0.1.2` through `v0.1.x` for native Apple Silicon macOS. Resolve the newest non-draft, non-prerelease tag in that range. Reject v0.1.0, v0.1.1, v0.2 or later, source builds, and development generations.

For an approved installation or update, download the selected tag's official Apple Silicon archive and published `.sha256` file. Verify the checksum before extraction. Extract into ephemeral storage, reject absolute or parent-traversing entries, symlinks, hard links, devices, and unexpected files, and propose one absolute user-owned target, normally `~/.local/bin/dolgorae`. Apply the active backup policy before replacement and never use `sudo` or write a system location.

The v0.1.x distributions are ad-hoc linker-signed, not Developer ID signed or notarized. Disclose that Gatekeeper may require the user to approve the checksum-verified binary locally. Verify the installed target as an executable regular non-symlink arm64 Mach-O file outside Aquarium state roots, and require the exact `{name, version}` JSON from `dolgorae version --json` and a successful closed machine envelope v2 from `dolgorae runtime capabilities`. Capabilities must preserve the v0.1.2 consumer requirements, including machine envelope v2 and advertised machine protocol v1, `home/.dolgorae/controller-carriers`, read-only shared-lane behavior, credential safety, bounded artifacts and interactions, and the required review features. Do not migrate or fall back to v0.1.0 Application Support state.

Dolgorae distributes the optional `use-dolgorae` skill separately from the binary. Diagnose it independently at `~/.agents/skills/use-dolgorae`. The local inspector reports structural readiness and per-file hashes; `configured` alone is not same-release freshness evidence. Compare the complete tree under `skills/use-dolgorae/` from the installed supported tag, or the selected latest supported tag when preparing an installation. It contains four files: `SKILL.md`, `references/configuration.md`, `references/lifecycle.md`, and `references/recovery.md`. Read the files from `https://raw.githubusercontent.com/irootkernel/dolgorae/<selected-tag>/skills/use-dolgorae/` in ephemeral storage. These public raw-file reads are part of the selected Dolgorae freshness diagnosis. Require matching bytes, valid frontmatter, regular files, and no missing or extra files; report duplicate and symlink states independently. Never compare against a moving branch or vendor the skill into Aquarium.

After skill installation or replacement approval and the shared backup decision, copy that verified complete tree to the canonical target and compare it again. Preserve local modifications and alternate installations until their exact replacement or migration is approved. Binary readiness and paired-skill readiness remain separate. Repository `dev-setup` checks only canonical skill presence. The `dolgorae` bundle component includes the CLI and paired skill without changing the bundle manifest schema.

Use `$use-dolgorae` for explicitly requested workspace, global Profile, review, engagement, and recovery operations. Global Profile list/show and offline doctor take no workspace scope. A Profile supplies account and launch configuration; doctor compatibility is separate from envelope success. Report `LEGACY_STATE_UNSUPPORTED` through the upstream recovery contract, without automatic migration or initialization. Setup does not create a workspace or Profile, authenticate, start a runtime server, transmit source, or run a review. Dolgorae requires no global MCP registration. A checked attached tool is usable only when the host actually exposes it; do not invoke its hidden adapter from the shell.

For an explicit reusable Specialist request, follow `$use-dolgorae` and the [Dolgorae consumer contract](dolgorae-review-contract.md#reusable-specialist-requests). General Run and Brokered Hierarchy operations still require their own advertised availability; the supported External Specialist facade retains its separate milestone contract.

## Mulgae

Official source: `https://github.com/irootkernel/mulgae`

Supported releases: stable `v0.1.23` or newer, native Apple Silicon macOS only. Resolve the newest non-draft, non-prerelease release at or above that minimum. SemVer build metadata does not make an otherwise stable release ineligible. Use the same exact tag for the CLI and its optional `use-mulgae` skill. Do not impose an upper version bound or reject a later stable `v0.1.x`, `v0.2+`, or major release solely because its version is newer. Installation requires Go `1.26.6` or newer.

Install an approved tag:

```bash
go install github.com/irootkernel/mulgae@<tag>
```

The binary does not install the agent skill. Repository setup diagnosis uses only `command -v mulgae`, `mulgae version --json`, and `mulgae doctor --output json`, plus effective Codex MCP inspection when available. Apply these minimum response contracts to the observed supported version:

| Mulgae | Command envelope | Doctor | Configuration | Provider inventory |
| --- | --- | --- | --- | --- |
| Stable `>=v0.1.23` | `mulgae-command-result.v12` or later | `mulgae-doctor-result.v5` or later | Native supported configuration, Config v4 at the minimum | ZCode, Grok, and Codex at v0.1.23; later canonical families are accepted as reported by the native Doctor contract |

Reject prereleases, versions below the minimum, and responses below a machine-contract floor. Accept later numbered schemas, additive fields, bounded reason codes, and canonical provider family identifiers while continuing to require the baseline typed fields on every reported provider row. Provider membership and order remain native Doctor authority so a later stable release may add, reorder, or retire families without an Aquarium-only version block. If the minimum Doctor contract is absent, report the capability as unsupported; never fabricate failed dimensions or reconstruct them from `.mulgae/config.yaml` or `.mulgae/local.yaml`.

User-global setup intentionally observes only the stable release floor and Apple Silicon platform. Its `version_supported` result does not claim that a repository's command, Doctor, configuration, or review contracts have been verified. Repository setup owns command and Doctor verification after the native configuration pair is available. Review execution separately requires `mulgae-review-preflight.v5` or later through the same-release `$use-mulgae` skill and the shared review contract.

The supported Doctor contract reports `config_v3`, `local_configuration`, `provider_identity`, `configured_readiness`, and `role_route_readiness` independently. The `config_v3` field name remains present in Doctor v5 and does not identify the project's Config version. Preserve each Doctor's `verified`, `failed`, `unverifiable`, and `not_applicable` states and each configured `provider_inventory[]` row's `binary_available`, `cli_compatible`, and `application_compatible` fields. Preserve application compatibility separately because it is independent from CLI or protocol compatibility. Treat an applicable compatibility result as ready only when its `eligibility` is `eligible`; `newer_than_verified` remains ready under that eligibility. Treat setup as configured only when `configured_readiness.state=ready` and `exit_code=0`. Do not gate or report setup on static evidence, heartbeat, historical reviews, or `review_qualified`, and never report native homes, executable paths, credential-profile homes, credentials, diagnostic messages, request IDs, timestamps, or raw provider output.

Setup does not need `mulgae providers --output json`. If that command is explicitly inspected outside the default setup flow, keep `offline_ready_provider_count` and `static_evidence_ready_provider_count` distinct; missing static evidence is not a generic unavailable provider.

For a new Codex user-scoped skill installation, use only these files from the automatically fetched and verified `https://raw.githubusercontent.com/irootkernel/mulgae/<tag>/skills/use-mulgae/` payload: `SKILL.md`, `references/lifecycle.md`, `references/authoring.md`, and `references/recovery.md`. Verify the complete file set, SHA-256 digests, and `name: use-mulgae` frontmatter before atomically moving it to `~/.agents/skills/use-mulgae`. Repeat every raw GitHub endpoint and the user-global target in the installation proposal even though the comparison fetch itself needs no separate approval.

If the target already exists, compare it with the verified source, show the complete diff, follow the shared backup policy, and obtain separate replacement approval. Under the no-backup policy, remove only the exact approved target after the incoming file set is fully verified; disclose that local modifications will not be recoverable from the release ref. Never overwrite, merge, delete, or repair another discovered copy silently. After installation or replacement, tell the user to restart Codex so a new session loads the skill snapshot.

Mulgae configuration has two authorities. `.mulgae/config.yaml` is Git-shareable project policy; `.mulgae/local.yaml` is untracked mode-`0600` machine configuration. Keep `execution.workspace_access: none`. Load the installed same-release `$use-mulgae` authoring guidance before proposing configuration. At the v0.1.23 minimum, Config v4 supports ZCode, Grok, and Codex; ZCode requires app version 3.12.3 or newer, Grok requires CLI 1.0.34 or newer, and Codex requires CLI 0.154.0 or newer. Consume the selected Doctor's `cli_compatible` and `application_compatible` results instead of reproducing Mulgae's version decisions. Show discovered executable, app-bundle, launcher, data-home, and credential-home paths only in the exact private setup proposal, never in the diagnostic report.

Before proposing initialization, resolve one effective setup selection: the provider portfolio, enabled roles, provider-specific shared policy, and intended role assignments. A new project with no explicit selection uses ZCode, Grok, and Codex with the six non-UI roles enabled and ZCode as every role's primary provider. Its shared policy pins Grok to `grok-4.7` with `medium` reasoning effort and Codex to `gpt-5.6-sol` with `medium` reasoning effort.

An explicit user selection becomes the effective setup selection. Complete any omitted dimensions through the same-release `$use-mulgae` authoring contract, preserving native provider defaults where the user did not request a pin. Do not add an unselected default provider, role, model, or assignment to that selection.

Resolve the exact machine-local paths for the effective selection before the proposal and carry that same selection through initialization and verification. For the default selection, run the following command with the resolved paths only after approval:

```bash
mulgae init \
  --providers zcode,grok,codex \
  --roles logic,security,maintainability,product,documentation,testing \
  --zcode-app-bundle <canonical-zcode-app-bundle> \
  --grok-executable <canonical-grok-executable> \
  --grok-model grok-4.7 \
  --grok-reasoning-effort medium \
  --codex-executable <canonical-codex-executable> \
  --codex-model gpt-5.6-sol \
  --codex-reasoning-effort medium \
  --output json
```

Mulgae's `auto` selection includes only ZCode and Grok, so it does not satisfy the default selection. Its build-owned role preferences assign the six roles to ZCode when all three families are selected. Verify those assignments from admitted configuration rather than rewriting the generated file. Add `artist` only for an explicitly declared UI project.

ZCode imports its selected API-key personal provider and model from the user's native ZCode configuration. Setup must not read or edit that file, expose the selected values, authenticate the user, or invent a project-level ZCode model field. Consume only Mulgae's redacted provider identity and readiness results. Grok and Codex model and reasoning values remain shared project policy bound through qualification and execution.

After initialization, require verified `config_v3`, `local_configuration`, and `provider_identity` checks plus ready `configured_readiness` and `role_route_readiness` with exit code `0`. Compare the structured initialization result and redacted Doctor output with the effective setup selection. The result's configured provider IDs must match the selected portfolio. Every selected provider row must be configured and eligible, every applicable compatibility result must be eligible, and the provider inventory's role references must match the intended assignments. Every explicitly pinned model or reasoning-effort value must also remain identical in the approved request and returned command envelope.

Do not require an unselected provider or role. For the default selection, these rules require all three providers to be eligible and all six roles to route to ZCode. If any applicable condition fails, a Mulgae-scoped setup is `failed` and an otherwise successful full setup is `partial`; neither may report Mulgae as ready. Preserve any native initialization failure without hand-editing a partial result. Provider CLI installation and authentication remain outside both setup skills.

Initialization creates the selected release's Config pair and does not edit Git ignore state. For an existing valid Config v4 file, derive the effective setup selection from Mulgae's redacted Doctor inventory and role references; do not apply the new-project defaults or read raw configuration during diagnosis, bootstrap, refresh, or unrelated repair. When a clone contains only shared `config.yaml`, plain `mulgae init --output json` bootstraps only `local.yaml` and rejects project-policy options.

When provider paths move or the shared provider set changes, propose `mulgae init --refresh-local --output json`, which preserves `config.yaml` and replaces only `local.yaml`; apply the shared backup policy to the replaced local file. Keep new initialization, clone bootstrap, and refresh as distinct approvals.

Config v1, v2, and v3 are unsupported at the minimum release, which does not migrate them automatically. Show the exact legacy files without reading or printing their contents and apply the shared backup policy before any approved replacement or removal. Never migrate configuration merely because setup diagnosis found a release mismatch.

Under the backup policy, separately propose a user-chosen mode-`0700` backup directory outside the repository, preserve both files and their modes with `cp -p`, privately verify file names, modes, and SHA-256 digests, and disclose the exact `cp -p` restoration commands.

Under the no-backup policy, disclose that legacy project policy, private paths, modes, and other local-only values will not be recoverable unless the user independently versioned them. Obtain separate approval for the exact destructive legacy-file removal under either policy.

If initialization fails, preserve the failure and do not partially edit either authority. Offer the disclosed restoration only when a verified backup exists; otherwise report that no rollback copy is available. Never reinterpret legacy provider policy or private paths automatically.

When the user selects Codex, require the minimum for the selected Mulgae release and let Mulgae diagnose its authenticated readiness; never sign in, read `auth.json`, or accept an API-key environment variable on the user's behalf. A single-profile configuration uses the selected native Codex login with `mulgae init --providers codex --roles <roles> --output json`. Optional model and reasoning-effort values are shared project policy; omission preserves Codex CLI defaults.

For several Codex identities, keep the two authorities separate using the selected release's native configuration shape; it is sufficient for the active setup session even when a newly replaced `$use-mulgae` skill will not load until Codex restarts:

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

Use operator-chosen lowercase kebab-case aliases, map exactly the default and role override aliases in lexical order, and use one common real Codex executable. Obtain separate approval for the shared policy and private local mapping, show the exact proposed YAML privately, and preserve unrelated fields in the selected Config version. Mulgae may project only the selected home's `auth.json` into a disposable runtime; do not expose profile paths or credential material. After writing, require the selected Doctor contract to verify provider identity, report the intended role-to-profile aliases through redacted role references, and mark Codex binary and CLI compatibility ready without returning any home or executable path.

Review execution, extraction, and recovery belong to the paired `$use-mulgae` skill. [mulgae-review-contract.md](mulgae-review-contract.md) defines how Aquarium consumes published reports and structured findings; setup does not run or inspect extraction artifacts.

Repository setup verification remains limited to version, the minimum command and Doctor contracts, and effective MCP registration. Do not infer new setup probes from extraction, recovery, runtime diagnostics, or lifecycle support. Doctor's adapter-owned local version command is offline: it uses no credential projection, project working directory, provider API, or network request. Do not inspect config contents or runs, and do not invoke heartbeat, qualification, preflight, review, source transmission, or MCP startup to validate setup.

Heartbeat is outside setup. Only after a separate explicit user request acknowledging possible authentication, network access, cost, and remote logging may an agent propose `mulgae heartbeat --provider <family> --authorize-live-request --output json`, adding `--credential-profile <profile>` only for an explicitly selected named Codex configuration. Never add `--authorize-live-request` automatically. Require `mulgae-provider-heartbeat-result.v3` or later and preserve its typed outcome without retry. Do not promote success into offline readiness or review qualification. Without authorization, preserve Mulgae's `attempted=false` and `live_authorization_required` result.

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

Show the complete diff and target scope before approval; for a local target also show whether `.codex/config.toml` is tracked. Verify three views independently without starting the server: query the global registration from a neutral filesystem-root cwd with the active Codex home, query the local registration from the same neutral cwd with `CODEX_HOME=<absolute-git-root>/.codex`, and query the effective registration from the repository with the active Codex home. A failed named lookup may use a successful `codex mcp list --json` inventory within the same timeout budget. The supported inventory shape is a top-level array whose entries each have a unique non-empty string `name`; absence from one such inventory proves `missing`, presence means the named lookup is degraded, and a timed-out lookup or failed, malformed, or duplicate-name inventory is unverifiable. Never classify registration state from stderr wording.

The effective entry must be enabled STDIO, resolve to the selected binary, be required, and use startup and tool timeouts at least as large as the proposed defaults. Global scope requires exact `args = ["mcp"]` and no fixed `cwd`; local scope requires exact `mcp --project-root <canonical-root>` arguments and repository-bound `cwd`. The 7501-second tool timeout covers the admitted two-hour review deadline plus retry and finalization margin; preserve any larger existing value. Record the Codex version and output capability separately. An observable `required: true` is verified, observable `false` is a registration mismatch, and an absent field is `required_unverifiable`; absence alone is not a mismatch because supported Codex output may omit the configured property.

Whenever an isolated local Mulgae registration exists, ask whether that scope is intentional. If confirmed, preserve it even when global is preferred. If not, show and separately approve removal of only the local `mulgae` table, using `CODEX_HOME=<absolute-git-root>/.codex codex mcp remove mulgae` or an equivalent exact TOML edit. Reinspect the file afterward. Delete `.codex/config.toml` only when parsed TOML has no remaining semantic content, and delete `.codex/` only when the directory is then empty; preserve comments with retained settings, every unrelated table, and every nonempty directory. Apply the shared backup policy before removal, never remove the global registration as part of local cleanup, and never stage the file during setup. Repository configuration paths must be regular non-symlink paths before `mulgae doctor` or any owning Codex CLI probe may read them.

Never stage it during setup. Tell the user to restart Codex after registration changes. Registration does not prove that the current session exposes the selected release's tools, including `compose_review`. Use already-exposed tool metadata when available without starting another server. The paired `$use-mulgae` skill owns asynchronous execution and native fallback; Aquarium consumes results through [mulgae-review-contract.md](mulgae-review-contract.md).

Verify configuration, provider readiness, skill files, and MCP registration only. Do not start the MCP server or run heartbeat, review, qualification, preflight, follow-up, delta, rerun, compose, report, export, or any command that captures, transmits, or writes review source or artifacts during setup. Mulgae owns its same-provider retry. Setup never starts recovery work; authorized review recovery follows [mulgae-review-contract.md](mulgae-review-contract.md) and the paired skill.

## Gaori

Official source: `https://github.com/irootkernel/gaori`

Supported release line: stable `v0.1.17` through `v0.1.x`. Resolve the newest non-draft, non-prerelease tag in that range. Use the same exact tag for the CLI and its optional `use-gaori` and `use-gaori-status` skills. Do not automatically cross into `v0.2+`. CLI JSON reports exactly `name` and a `v`-prefixed `version`; it no longer carries source commit identity. MCP `serverInfo.version` uses the internal version representation. Development producer manifests retain their separate exact source commit and executable checksum identities. Verify each transport independently: a CLI on PATH does not prove the attached server version, and a missing CLI does not disable connected MCP execution. If host initialization metadata is unavailable, report the MCP version as unverified and follow the requesting repository's pinned-tool policy.

Install an approved tag:

```bash
go install github.com/irootkernel/gaori@<tag>
```

The binary does not install the agent skill. Diagnose the CLI and repository with `command -v gaori`, `gaori version --json`, and, when `.gaori/tester.yaml` exists, `gaori --json config check`. Diagnose `use-gaori`, `use-gaori-status`, and global, local, and effective MCP registration independently. Config check validates schema-v2 config and all stored rules without resolving executables, running commands, or creating evidence.

For a new Codex user-scoped skill installation, use only these files from the automatically fetched and verified `https://raw.githubusercontent.com/irootkernel/gaori/<tag>/skills/use-gaori/` payload: `SKILL.md`, `references/authoring.md`, `references/existing-logs.md`, `references/fallbacks.md`, `references/lifecycle.md`, `references/recovery.md`, and `references/retention.md`. Verify the complete seven-file set, SHA-256 digests, and `name: use-gaori` frontmatter before atomically moving it to `~/.agents/skills/use-gaori`. Repeat every raw GitHub endpoint and the user-global target in the installation proposal even though the comparison fetch itself needs no separate approval.

For `use-gaori-status`, fetch the single `SKILL.md` from `https://raw.githubusercontent.com/irootkernel/gaori/<tag>/skills/use-gaori-status/SKILL.md`. Verify its SHA-256 digest, complete one-file tree, and `name: use-gaori-status` frontmatter before proposing installation at `~/.agents/skills/use-gaori-status`. Apply the same per-target comparison, duplicate, backup, approval, and restart rules to each skill. A selected Gaori component diagnoses both skills, but a missing status skill does not degrade CLI, execution-skill, or MCP health.

If the target already exists, compare it with the verified source, show the complete diff, follow the shared backup policy, and obtain separate replacement approval. Under the no-backup policy, remove only the exact approved target after the incoming file set is fully verified; disclose that local modifications will not be recoverable from the release ref. Never overwrite, merge, delete, or repair another discovered copy silently. After installation or replacement, tell the user to restart Codex if the skill does not appear in the active session.

Discover required checks from repository instructions, task runners, manifests, and CI before proposing `.gaori/tester.yaml` schema version 2. Map each configured command ID to an existing argv array, non-empty tags, explicit parser, and timeout. Use `gaori --json parsers list` as the authoritative live registry before selecting a parser. Use `gaori --json parsers catalog` (`gaori-parser-catalog.v1`) for each label's code-owned support tier and output family. `dart-test`, `patrol`, `dotnet-test` and `gradle-test` are Experimental; their bounded summaries may require manual confirmation. Use `gaori --json parsers detect <raw-log>` only to diagnose an explicitly selected existing log: it reports candidates without selecting a parser, loading configuration, creating evidence, or changing the command result. Do not add secrets, absolute paths, or machine-specific arguments to portable configuration.

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

Show the complete diff and target scope before approval; for a local target also show whether `.codex/config.toml` is tracked. Never stage it during setup. Verify global, isolated local, and effective registrations with the same three-view procedure used for Mulgae. Global scope requires exact `args = ["mcp"]` and no fixed `cwd`; local scope requires exact `--repo <canonical-root> mcp` arguments and no fixed `cwd`. Do not start the server or a test. Require a numeric, non-boolean `tool_timeout_sec` of at least 3601 seconds so the host deadline exceeds a one-hour command and evidence finalization, while preserving any larger existing value. Report missing or inadequate timeout, disabled, non-STDIO, unresolvable-command, wrong-repository, and inactive or untrusted entries as degraded.

Whenever an isolated local Gaori registration exists, ask whether that scope is intentional. If not, show and separately approve removal of only the local `gaori` table, using `CODEX_HOME=<absolute-git-root>/.codex codex mcp remove gaori` or an equivalent exact TOML edit. Apply the same backup, semantic-empty-file, empty-directory, unrelated-setting preservation, and no-staging rules as Mulgae local cleanup. Never remove the global registration as part of local cleanup.

Tell the user to restart Codex after registration changes. Verify connected capabilities from already-exposed tool metadata when available; neither registration nor a PATH CLI proves the active MCP surface. `$use-gaori` owns asynchronous execution and native fallback. [gaori-integration.md](gaori-integration.md) owns Aquarium's command and evidence handoff.

Diagnose the optional `$use-gaori-status` skill independently. It owns historical statistics and detailed timing explanations; its absence does not block execution or a live estimate supported by `$use-gaori`. Setup never queries run history or estimates automatically.

Every present repository configuration path that Gaori may inspect, including `.gaori/tester.yaml`, every descendant of `.gaori/tester/rules/`, and `.gaori/toolchain.yaml`, must have regular non-symlink lexical ancestry before any owning CLI probe may read it; an absent primary path stops that probe rather than consulting ambient state.

## Sorage

Official source: `https://github.com/irootkernel/sorage`

Supported release line: stable `v0.1.1` through `v0.1.x`, native Apple Silicon macOS only. Sorage v0.1.0 predates the required explicit broker-operation and Review Note workflow contract. Resolve the newest non-draft, non-prerelease tag in the supported range and use the same exact tag for the CLI and `use-sorage` skill. Do not automatically cross into `v0.2+`.

The official release provides `sorage-<tag>-darwin-arm64`, `sorage-<tag>-darwin-arm64.sha256`, and `sorage-<tag>-darwin-arm64.manifest.json`. Before installation, verify the checksum file, require the manifest's version, target, binary name, digest, and revision to match the selected tag, asset, and peeled tag commit, and run `codesign --verify --strict` against the binary. Disclose that the release is ad-hoc signed and not notarized. Install the separately approved regular executable to the exact user-owned target, normally `~/.local/bin/sorage`, without `sudo`; the packaged binary needs no Bun runtime. Verify the installed target with `sorage version --json`.

The binary does not install the agent skill. For a new Codex user-scoped skill installation, use only the automatically fetched and verified `https://raw.githubusercontent.com/irootkernel/sorage/<tag>/skills/use-sorage/SKILL.md` payload as `SKILL.md`. Verify the complete one-file set, its SHA-256 digest, and `name: use-sorage` frontmatter before atomically moving it to `~/.agents/skills/use-sorage`. Repeat the raw GitHub endpoint and user-global target in the installation proposal even though the comparison fetch itself needs no separate approval.

Treat missing, extra, modified, duplicate, or symlinked content as a separate skill gap. Show the complete diff and follow the shared backup and approval rules before installing or replacing it. Tell the user to restart Codex if the current session does not expose the newly installed skill.

Repository inspection diagnoses the supported CLI with the explicit `--include-sorage` path, which runs `sorage version --json`, `sorage doctor --json`, and, only when doctor has no blocking check, Project resolution. Global inspection always checks the version and uses `--include-sorage-initialization` to add only the doctor path. The version command returns the bare `{name, version}` object; doctor returns a versioned Sorage envelope. Accept doctor state only when all 20 v0.1 catalog IDs appear once in their specified order with valid fields and `ok`, `warning`, or `blocking` severity. Doctor exits `0` when no check is blocking and `1` when any check is blocking. The all-blocking catalog with `sorage init` recovery identifies an uninitialized installation. Any partial, reordered, or otherwise invalid catalog is unverifiable.

These commands make no network request. Doctor opens the local database for some checks, and Project resolution uses Sorage's native open-and-migrate path, so the selected diagnosis may update local database or journal state. Disclose this before running the selected Sorage diagnosis. Without the applicable include flag, inventory runs only version and platform checks: a supported CLI reports `not_inspected`, while an unsupported version or platform reports `degraded`.

Summarize only check counts by `ok`, `warning`, and `blocking`. Never copy check messages, request IDs, Installation IDs, Vault paths, database paths, tokens, or other private state into the setup report. A warning does not block the minimal local profile, while any blocking check prevents readiness.

When Sorage is not initialized, separately propose this minimal profile:

```bash
sorage init --non-interactive --json
```

Show the exact effective `SORAGE_HOME` and default Vault paths before approval. This command creates the home tree, config, database, API token, and managed Vault, but does not start the daemon, install a LaunchAgent, initialize Vault Git, enable backup, or configure push. Preserve an existing valid installation. Treat `--reconfigure`, daemon or service setup, Vault movement, backup, restore, and uninstall as distinct native Sorage operations with their own exact proposals; never edit the managed Vault directly.

After initialization, run `sorage project resolve --path <canonical-git-root> --json`. Read no inbox, outbox, Handoff title, Review Note, or Artifact during setup. Readiness requires an active Project whose selected binding kind is `git_repository`; a containing `directory` binding does not register the repository itself.

If resolution returns a registered Project through a containing `directory` binding, report a non-ready binding-kind gap and preserve the existing binding. Stop automatic setup for that repository, require a separate explicit native repair decision, and do not propose `project add` or `project bind` from that result.

Treat only a successful `unregistered_workspace` result as `registration_required`. Unless Master explicitly requested Project setup, report that status and stop before listing Projects or preparing a registration proposal. For explicitly requested setup, disclose that `sorage project list --json` opens the same local database and may apply native migrations, then obtain separate explicit approval before running it. Only after that approved listing may you ask whether to create a new Project or bind an existing active one. A native resolution error is `resolution_error`. Preserve its symbolic code, leave Project registration unverifiable, and do not propose `project add` or `project bind`.

Require an exact user-confirmed display name and immutable slug for creation:

```bash
sorage project add --name <name> --slug <slug> --dir <canonical-git-root> --json
sorage project bind <existing-active-slug> --dir <canonical-git-root> --json
```

Do not guess Project identity, use `--allow-unregistered`, or silently unarchive a Project. An archived Project requires a separately approved `sorage project unarchive <slug> --as-user --json`. On `AMBIGUOUS_PROJECT`, `BINDING_DUPLICATE`, `PROJECT_SLUG_CONFLICT`, `VAULT_CONTAINMENT`, or another native error, preserve state and return its symbolic code. Re-resolve the exact Git root after mutation and require the active `git_repository` result before reporting registration complete.

Require the whole `.sorage/` directory to be ignored by the repository root `.gitignore`, with no tracked descendant and no symlinked `.sorage/` path. Preserve existing content and an equivalent rule without duplication. If `.gitignore` is absent, propose creating it; if only another exclude source ignores `.sorage/`, report the repository-policy gap and propose the root `.gitignore` addition. Show the complete diff and obtain separate approval before either change. If any `.sorage/` path is already tracked, report the conflict and stop rather than editing, deleting, or untracking it. The Sorage CLI never edits Git ignore files.

A healthy supported CLI remains `installed` when initialization, registration, Project state, binding kind, skill, ignore, tracking, or symlink readiness is incomplete. Use `degraded` for an unhealthy runtime, invalid command contract, or blocking doctor result other than the exact uninitialized catalog. Report that catalog as `installed` with `readiness_status: initialization_required`, and use `configured` only for complete readiness. `$aquarium:dev-setup` owns explicitly requested Project setup, including identity confirmation, approval, and fresh resolution. It also owns separately approved root `.gitignore` preparation whenever Sorage readiness is diagnosed. An effective per-target `sorage` selection in an explicitly supplied `dev-setup-bundle` manifest counts as a Project setup request for that target, but does not authorize Project listing or mutation without the separately required approvals. Once setup is ready, load and invoke `$use-sorage` only for an explicit broker operation. Check only the requested inbox or outbox and report its result without starting another operation. Within requested Handoff processing, the same-release skill owns the Review Note read before sender revision and any optional bounded event timeline read, together with every fetch, review, revision, acceptance, retention, deletion, backup, and Vault operation.

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

The clone and fetch contact GitHub, and `npx` contacts npm and writes `lore-commits` and `lore-query` to `~/.agents/skills/lore-commits` and `~/.agents/skills/lore-query`. Require the detached `HEAD` to equal the approved ref before installation. Do not install or invoke Lora's `lore-setup`; it copies the full Lore protocol into AGENTS.md and conflicts with the reference-and-override policy. If `lore-setup` is already installed, report it without removing or rewriting it.

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

## Humanizer

Official source: `https://github.com/blader/humanizer`

Support stable releases `>=v2.11.1` without an upper bound. Resolve the latest stable release by default or the user's selected supported release through official GitHub release metadata. Prepare a temporary detached checkout at that exact tag and require `HEAD` to equal the resolved release commit. Require a regular non-symlink root `SKILL.md` and `LICENSE`, `name: humanizer`, and a frontmatter version matching the selected tag. Include any additional regular skill files required by that release's upstream guidance in the verified install payload.

The current upstream guidance does not name `$CODEX_HOME` as its default; use `~/.agents/skills/humanizer` unless the selected release documents a different default. The offline inspector accepts a sole shared or active-home copy as a structural candidate; confirm the selected release's installation guidance before treating either target as canonical. Install only after separate approval. Compare the complete selected payload and target trees and every digest, rejecting missing or extra paths, symlinks, invalid frontmatter, a below-minimum or mismatched version, and copies that would be loaded beside the selected target. Never execute Humanizer or rewrite prose during setup.

## im-not-ai

Official source: `https://github.com/epoko77-ai/im-not-ai`

Support stable releases `>=v2.3.2` without an upper bound. Resolve the latest stable release by default or the user's selected supported release through official GitHub release metadata, prepare a temporary detached checkout at that exact tag, and require `HEAD` to equal the resolved release commit. Read the checked-out `install.sh` and require every write target to derive from the isolated temporary `CODEX_HOME`. Disclose the exact `./install.sh --codex-only --copy` command and temporary target and obtain separate approval for that upstream-code execution, then run it without `--force`. Reject unexpected writes outside that isolated directory, then add the checkout's root LICENSE to the generated `humanize-korean` directory.

Require the materialized payload to contain only regular non-symlink files, the exact generated tree, and `name: humanize-korean`. Install that complete payload at `<active CODEX_HOME>/skills/humanize-korean` only after separate approval, using `~/.codex` when `CODEX_HOME` is unset. Never install it at `~/.agents/skills/humanize-korean`. Compare every path and digest after installation. Treat copies in other Codex homes as independent installations; report a copy in `~/.agents/skills/humanize-korean` as a duplicate and migrate or remove it only with separate approval and the shared backup policy. Never point the active skill target at a checkout, run the installer against the active Codex home, invoke the skill, or create `_workspace/` during setup.

## Podway

Official source: `https://github.com/irootkernel/podway`

Supported release line: stable `v0.2.10` through `v0.2.x`, native Apple Silicon macOS only. Resolve the newest non-draft, non-prerelease tag in that range. Use the same exact release tag for the CLI and daemon. Podway v0.2.5 has migrated reset-receipt read-back, degraded-store reset recovery, and bounded correlated daemon-log guarantees; v0.2.6 satisfies Aquarium's Procedure and prepared-session contracts but lacks the exact-workspace removal contract and matching source-distributed skill guidance, while v0.2.7 lacks named runtime modes and daemon-status v3, and v0.2.8 lacks successful UUID-fenced workspace-removal replay. Do not automatically cross into `v0.3+`.

Pin the optional `use-podway` skill independently to full commit `9014225982e4c316237e0d6e35052414d2dbc770`. This skill hotfix adds context recovery and Codex goal coordination guidance on top of v0.2.9 without requiring a new runtime. Keep this skill pin until an explicit catalog update replaces it; a newer release, including v0.2.10, does not change the pin.

Resolve the exact release from GitHub Releases and download the Apple Silicon archive plus its published `.sha256` file. Disclose that release binaries are unsigned and not notarized. Verify with `shasum -a 256 -c` before installing both `podway` and `podwayd` at the approved user-local paths. Do not accept a prerelease, a version before v0.2.10, `v0.3+`, an unverified archive, mixed CLI and daemon versions, or unsupported platform.

The binaries do not install the agent skill. Diagnose `use-podway` independently in the Codex skill roots. For a new Codex user-scoped installation, use only `SKILL.md`, `references/lifecycle.md`, `references/goal.md`, and `references/recovery.md` from the automatically fetched and verified `https://raw.githubusercontent.com/irootkernel/podway/9014225982e4c316237e0d6e35052414d2dbc770/skills/use-podway/` payload. Verify the commit through the official repository, the complete file set, SHA-256 digests, and `name: use-podway` frontmatter before atomically moving it to `~/.agents/skills/use-podway`. Repeat every raw GitHub endpoint and the user-global target in the installation proposal even though the comparison fetch itself needs no separate approval. Keep `create-podway-procedure` as a separately installed maintainer authoring dependency; neither setup skill installs, compares, or requires it.

If the target exists, compare it with the verified source, show the complete diff, follow the shared backup policy, and obtain separate replacement approval. Under the no-backup policy, remove only the exact approved target after the incoming file set is fully verified; disclose that local modifications will not be recoverable from the pinned source commit. Never overwrite, merge, delete, or repair another discovered copy silently. After installation or replacement, tell the user to restart Codex so a new session loads the skill snapshot.

Install or refresh the per-user service only after separate approval:

```bash
podway daemon install --daemon-path <absolute-podwayd-path>
podway daemon status --json
```

If that install is interrupted after authenticated service metadata is prepared, rerun the same approved command with the same absolute daemon path and no `--socket` override. Podway v0.2.5 reconciles the prepared receipt and waits for the prior launchd label to unload before replacement bootstrap. Never edit service metadata, sockets, receipts, or LaunchAgent files to recover the installation.

Podway v0.2.5 writes daemon events as bounded fixed-schema `podway.daemon-log/v1` JSONL with opaque request, workspace, session, job, and diagnostic correlation. It keeps at most ten 1-MiB daemon-log files and a separate daemon-owned five-file bootstrap stream while LaunchAgent standard output and error go to `/dev/null`. Treat these logs as bounded diagnostics, not lifecycle authority, and never expose raw log contents in setup reports.

The LaunchAgent runs after GUI login under the same OS user and is not a multi-user security boundary. Verify the compact `podway version --json` result, bounded `podway --json daemon wait-ready --timeout 120s` output with a `podway.output/v3` envelope and `podway.daemon-status-result/v3`, daemon reachability and exact version match, and the `podway.output/v3` doctor envelope when the worktree is initialized. Require `mode=prod`, `readiness_state=ready`, `readiness_stage=ready`, null or bounded activity counts, and closed `worktree_recovery` with every worktree completed; a nonzero failed count may describe quarantined completed recovery and is not independently unhealthy. The read-only readiness inspector may inventory a session through `podway.status-result/v3` or `podway.compact-status-result/v3`; managed workflow automation must use `podway observe --json --wait-for-idle` and require `podway.observation-result/v3`. Treat `readback[].items[].preview` as bounded metadata, never a complete item value. Read a selected complete value with digest-bound `podway --json evidence read --source <source> --item <item>`, continue with each returned page token until complete, and on `EVIDENCE_PAGE_TOKEN_STALE` re-observe and restart the read. Prepared lifecycle mutations use `podway.session-start-result/v3`, `podway.session-begin-result/v1`, `podway.terminal-disposition-result/v1`, and `podway.session-reset-result/v1`; prepared-aware lifecycle jobs use `podway.job-result/v4` and `podway.job-lookup-result/v4`. Errors remain `podway.error/v1`.

`start` creates a prepared revision-0 session without a cursor, attempt, or goal. The owning handler must re-observe it and use the fresh fenced `session.begin` mutation template to create attempt 1 and any initial goal before recording evidence. Derive every lifecycle mutation from the latest observation template and current `podway help <route>` grammar. The current start policy preserves a prepared or running session unless an explicitly authorized `--on-existing delete` is selected; plain `start` automatically archives an eligible disposed terminal predecessor. `list`, `show`, and `archive purge` expose inactive history, whose hard limit is 32 sessions; never auto-purge or evict history. Terminal sessions expose a disposition template until the exact current revision records `handed_off` or `not_required`. Never infer a removed replacement flag from the internal `session.start_replace` template name or substitute force reset for missing handoff authority.

Treat that bounded inventory as readiness evidence only. Never use dev-setup to observe, cancel, discard, or reset a routine supported Procedure v2 current session; return an exact standalone `$use-podway` lifecycle request instead. Keep `LEGACY_PROCEDURE_STATE_UNSUPPORTED` and its separately approved workspace-wide `podway reset --all` recovery as the only session-state reset exception in this catalog.

`workspace remove` is not a dev-setup repair, cleanup, uninstallation, or readiness action. A missing session, stale registry entry, setup opt-out, or request to remove one session never authorizes complete `.podway` deletion. Only an explicit request to stop using Podway in one exact Git worktree may hand off to the pinned `$use-podway` lifecycle flow, which must disclose complete `.podway` deletion, preserve the Git worktree, re-read the exact root and workspace UUID immediately before mutation, and require `podway.workspace-removal-result/v1` before reporting success.

`workspace mode apply` is not a dev-setup repair or readiness action. Dev-setup may report a mode mismatch, but it must not plan or apply a mode move. Only an explicit exact-worktree and target-mode request may hand off to the pinned `$use-podway` lifecycle flow. That flow must disclose the tracked `.podway/config.yaml` rewrite and complete runtime-history deletion. It must also keep the plan token ephemeral, revalidate the source workspace UUID and both modes, and obtain separate approval immediately before apply. After apply or recovery replay, require current target-mode observation and report the configuration change without staging or committing it.

Repository initialization and Aquarium readiness configuration require another approval. `podway init` creates `.podway/config.yaml` and `.podway/.gitignore` for the repository to track, plus ignored `.podway/runtime/`. Install missing or explicitly selected canonical Procedure v2 sources to `.podway/procedures/` byte-for-byte and validate each safe present file with the selected Podway v0.2.10 binary:

```bash
podway procedure check --warnings-as-errors <procedure-file>
podway procedure preview <procedure-file>
```

The five required IDs are `aquarium-task-v2`, `aquarium-goal-v2`, `aquarium-validation-v2`, `aquarium-design-v2`, and `aquarium-war-room-v2`. Their presence describes readiness, never workflow activation. Require regular non-symlink files and non-symlink path components before hashing or invoking Podway; a symlinked managed path is degraded and must never be read or executed. Match each expected filename to the `procedure_id` returned by preview, and let Podway own document validity. Report each file's source provenance as `canonical`, `valid_customization`, `invalid`, `missing`, `unsafe`, or `unverifiable`. Report its independent `handler_contract_status` as `compatible`, `unqualified`, `incompatible`, or `not_checked`, with stable reason codes. All absent means `readiness_status=not_configured`; all five tracked, same-ID, Podway-valid files with compatible handler contracts and healthy runtime state mean `readiness_status=ready`. Partial, invalid, unsafe, unverifiable, unqualified, incompatible, or required-but-`not_checked` handler state, unsupported runtime, or unhealthy state means `readiness_status=degraded`. Repository inspection omits Podway unless invoked with `--include-podway`.

For every valid customization, show the exact current-to-canonical diff and its handler-contract result, then ask whether to preserve the local file or replace it with canonical bytes. Preserve means no write and no metadata. A compatible customization may remain ready; an incompatible customization remains degraded but is still preserved until its owner approves replacement. Replacement applies the shared backup policy, rechecks the exact target snapshot, and requires approval for that one diff. Never overwrite, merge, normalize, or reformat local content under a broader setup approval; an active session retains its immutable snapshot and is never reinterpreted under new source bytes.

The renamed inspector reports `migration_required=true` and `migration_kinds.product_rename=true` when any tracked or untracked `root-kernel-task-v2.yaml`, `root-kernel-goal-v2.yaml`, or `root-kernel-validation-v2.yaml` remains in `.podway/procedures/`. This is a product-rename migration and forces degraded readiness until the old files are separately removed and the `aquarium-*` files are installed. Finish or explicitly dispose of any active old session first; never convert or delete its runtime history as part of managed-file replacement.

The repository inspector keeps exact prior-canonical digests and the deterministic v0.2.5 workaround identity only as per-file `update_explanation` values. These values can explain an offered canonical update but never create a separate native-validity, migration, or ownership class. Any same-ID file that Podway accepts remains a `valid_customization`; its handler compatibility is evaluated independently, and any replacement still requires its exact current-to-canonical diff and explicit choice. Do not create an ownership manifest, provenance registry, or second workaround source.

`LEGACY_PROCEDURE_STATE_UNSUPPORTED` has a different meaning: the runtime contains Procedure v1 task state. Do not convert, edit, or delete that state automatically. Report the exact worktree and error and apply the shared backup policy before separately proposing the supported `podway reset --all` recovery. Under the no-backup policy, disclose that the reset permanently deletes the legacy runtime history and that Git cannot restore it, then require separate explicit approval.

Podway v0.2.5 also preserves explicit confirmed `podway reset --all` recovery when the workspace binding is readable but disposable full-store openability or internal-codec inspection fails. Treat that condition as degraded, preserve the exact stable error evidence, apply the shared backup policy, and require a separate reset proposal and explicit approval; recoverability never grants deletion authority.

## Ouroboros

Official source: `https://github.com/Q00/ouroboros`. Python package: `ouroboros-ai`. Support stable releases `>=0.51.1` without an upper bound. Use the selected package's native Codex assets and verify the interfaces needed by the requested workflow. Seed QA in 0.53 is advisory; do not add a blocking QA-until-PASS loop.

### Package and Home Discovery

The CLI is installed once per user. Codex integration belongs to each Codex home: `<home>/rules/ouroboros*` and `<home>/skills/ouroboros-*`. Never install Ouroboros skills into `~/.agents/skills`, use that location to satisfy readiness, or treat valid installations in different Codex homes as duplicates.

Run `dev-setup-global/scripts/inspect_global_tools.py --component ouroboros --verify-ouroboros-release`. Disclose `https://pypi.org/pypi/ouroboros-ai/json` before the read-only request. The lookup excludes prereleases and withdrawn releases and reports the installed version, latest stable release, and latest release at or above the minimum. A failed lookup, including an HTTP protocol error, is `freshness_unverifiable` and preserves the other inspection results. If the CLI exists but its version probe fails or returns no parseable version, freshness is `freshness_unverifiable` with reason `cli_version_unverifiable`; successfully fetched release metadata remains available. Only an absent CLI is `missing` after a successful lookup. Without the flag, freshness is `not_checked` and the inspector makes no network request. Resolve and approve an exact package version; do not install a moving range.

The inspector includes the active `$CODEX_HOME` (default `~/.codex`), an existing `~/.codex`, and immediate `~/.codex-*` directories with Codex configuration or Ouroboros artifacts. Add arbitrary user-selected locations with repeatable `--codex-home <path>`. Resolve relative paths against the invocation directory, merge aliases of the same directory, and never search repository trees. A missing active or explicitly selected home remains a missing installation target; an unrelated directory is not a discovered home.

Reject blank `--codex-home` values before probing; preserve spaces in nonblank paths. An explicit home that is a regular file remains an `invalid_codex_home` input error. If the automatically selected active home is a regular file, return a degraded home row with reason `home_not_a_directory` and skip its doctor and MCP probes. Keep the CLI observation and continue inspecting other homes and components. If an automatic home cannot be resolved, retain its original spelling with `home_resolution_failed` and skip its probes. Discovery failures and otherwise unhandled path errors during home inspection degrade the affected home with `home_inspection_failed`; artifact read failures remain component-specific. Do not convert diagnosis failures into explicit-input errors.

Propose all discovered homes by default and list them before approval. Separate `current_home_readiness` from `all_discovered_homes_readiness`. A failure in another home does not block an otherwise ready current home. Report partial results without rolling back successful independent homes.

### Independent Inspection

Inspect the CLI through `ooo --version` once. Resolve packaged artifacts through the interpreter beside the selected uv-installed CLI. Compare each home's complete rules and skill file trees independently using SHA-256. Compare the primary rules file with `load_packaged_codex_rules()` output, which includes upstream-generated runtime guidance; compare other assets with their packaged bytes. Missing files, changed bytes, extra managed files, and symlinks are gaps. Do not infer artifact health from `ooo codex doctor`: that command also checks MCP. If the selected package's assets cannot be resolved or its version differs from the CLI observation, report artifact verification as unavailable rather than using a shared skill copy.

Run `ooo codex doctor` and inspect the target registration with `codex mcp get ouroboros --json`, using `codex mcp list --json` only as the bounded structural absence fallback described above, with the target `CODEX_HOME` explicitly set and a neutral filesystem-root working directory. Registration is `configured` only for an enabled named `ouroboros` STDIO entry matching either the selected `ooo` executable with exactly `args = ["mcp", "serve"]` or the canonical isolated launcher. The isolated form uses the selected `uvx`, ordered `--isolated --python >=3.12 --from ouroboros-ai[mcp]` arguments with an optional supported exact pin, and `ouroboros mcp serve`. It selects Codex through `OUROBOROS_AGENT_RUNTIME=codex` and `OUROBOROS_LLM_BACKEND=codex`, or the exact suffix `--runtime codex --llm-backend codex`. Optional `OUROBOROS_RUNTIME` must also equal `codex`. Allow `CODEX_HOME` in the environment; reject other keys, conflicting selectors, inherited nested-runtime sentinels, missing extras, and extra arguments.

Report `home_binding` separately: an explicit absolute `CODEX_HOME` must resolve to the inspected home. A different home is `home_mismatch`; absent binding is `home_not_explicit`, not proof that a live server inherited the intended home. Report the MCP package version independently. An unpinned isolated launcher is a recognized upstream registration, but its package version is unverifiable; a pin different from the CLI is a version gap. Neither qualifies as complete home readiness.

Run `ooo mcp doctor --json` only for a direct selected-CLI registration. For an isolated launcher, report configured runtime state from its own launcher contract without probing the unrelated base MCP environment. These local probes do not start an MCP server, contact a provider, authenticate, or expose credentials. Normalize errors and reason codes; never print raw registration output or secrets. Only a valid structural inventory may prove absence after a failed named lookup; malformed, disabled, timed-out, or otherwise unresolved probes are degraded, and an absent Codex CLI is unverifiable.

### Approved Upgrade and Migration

Installation requires an existing `uv`. Show `uv tool install ouroboros-ai==<exact-version>` or the exact native upgrade command and package endpoints. Do not install `uv` as a side effect. Show the CLI action, every selected home, rules/skills changes, MCP changes, expected shared Ouroboros configuration effects, backup policy, and verification together. One approval may cover all listed actions; do not ask again for individual homes already covered. Changes outside that proposal require additional approval. Re-read targets before mutation and invalidate approval if they changed.

For existing integration, use `CODEX_HOME=<absolute-home> ooo codex refresh` as the rules-and-skills repair alternative. For full configuration, use `CODEX_HOME=<absolute-home> ooo setup --runtime codex --non-interactive --mcp-mode auto`. Do not run `ooo codex refresh` before full setup. Refresh does not prune obsolete managed artifacts; if those remain, propose full setup with its complete effects. Do not copy or patch upstream skill content.

`--mcp-mode auto` may preserve a user-managed mismatch and return success. Reinspect the actual registration; that result is not a completed repair. Offer preservation with the unresolved gap or an explicitly approved canonical replacement using `--mcp-mode stdio` on supported hosts. Include the exact MCP adjustments needed after native setup in the original proposal: bind `CODEX_HOME` to that configuration file's home and pin the isolated MCP package to the approved CLI version. Use the owning Codex CLI or an exact TOML edit confined to the Ouroboros entry; preserve unrelated settings and comments. Never write one active home into every discovered home's registration. Respect native platform limitations instead of substituting an unsupported mode.

Report `legacy_shared_skills` as migration candidates, not removal authority. Identify prefixed copies only for skill names in the selected package and compare unprefixed copies against verified upstream content before including them. Report an unprefixed shared skill with a matching frontmatter name or unsafe symlink as `shared_skill_conflicts` when its provenance is unverified. The conflict prevents home readiness without proving Ouroboros ownership. Inspect its owner before proposing any removal. Show the exact paths and backup/removal steps for approved migrations. Prepare and verify the selected home payloads before migration, and require the final inspection to show no shared conflicts. Never delete unrelated shared skills or require removing a valid copy in another home.

### Completion and Runtime Switching

Verify package version, independent rules/skills, aggregate doctor, registration, package pin, and home binding after each action. The read-only inspector reports configuration readiness and leaves `live_runtime` as `not_observed`. After changing homes or MCP settings, restart the affected Codex/MCP session as needed and use safely observable host evidence to confirm the running server and child Codex use the same home. Tool exposure alone does not prove the process environment. If that evidence is unavailable, report it explicitly rather than claiming runtime verification.

No setup action authorizes a provider call, authentication, repository-source transmission, `auto`, `run`, `ralph`, `evolve`, Seed creation, or an Aquarium design workflow. Do not switch accounts automatically or clear persisted quota-pause state. Correct home routing does not by itself prove an earlier usage-limit failure is resolved.
