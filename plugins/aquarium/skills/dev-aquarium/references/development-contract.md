# Aquarium Development Channel Contract

This reference is the canonical shared contract for development-channel producers and the Aquarium host manager. The initial supported platform is Darwin on arm64. Development artifacts are local integration evidence, never stable release or distribution evidence.

## Producer commands

Every producer implements these exact Make targets:

```text
make aquarium-dev-describe
make aquarium-dev-build AQUARIUM_DEV_OUTPUT=<absolute-directory>
```

`aquarium-dev-describe` is read-only and writes exactly one `aquarium-dev-producer-description/v1` JSON object followed by a newline to stdout. `aquarium-dev-build` requires a clean local `main` checkout whose `HEAD` equals `refs/heads/main`, writes only beneath the supplied existing empty staging directory, and writes exactly one `aquarium-dev-artifact-manifest/v1` JSON object followed by a newline to stdout. Human diagnostics go to stderr. Success exits `0`; contract or precondition rejection exits `2`; build failure exits `1`.

No producer may infer a staging directory, emit multiple JSON documents, write outside `AQUARIUM_DEV_OUTPUT`, use working-tree bytes, or substitute a branch name for the exact commit.

## Producer description

The object has exactly these fields:

| Field | Contract |
| --- | --- |
| `schema` | `aquarium-dev-producer-description/v1` |
| `project_id` | `aquarium`, `podway`, `mulgae`, `gaori`, `sanho`, or `dolgorae` |
| `next_version` | stable semantic version with a leading `v`, such as `v0.1.14` |
| `artifact_kind` | `codex-plugin` or `executable` |
| `artifact_path` | normalized non-empty relative path with no `.` or `..` component |

## Artifact manifest

The object has exactly these fields:

| Field | Contract |
| --- | --- |
| `schema` | `aquarium-dev-artifact-manifest/v1` |
| `project_id` | same identity as the admitted description and enrollment |
| `git_sha` | full 40-character lowercase hexadecimal commit ID |
| `development_version` | `v<next>-dev.<first-12-git-sha>` |
| `artifact_kind` | same kind as the admitted description |
| `artifact_path` | normalized relative path beneath `AQUARIUM_DEV_OUTPUT` |
| `sha256` | `sha256:` plus the lowercase digest of the file, or of the canonical directory tree for a plugin |

The manager compares the manifest with the description, enrolled project, requested SHA, actual artifact, and checksum. It rejects unknown fields and mismatches.

The canonical plugin-directory digest visits regular files in ascending UTF-8 artifact-relative POSIX-path order. For each file, it hashes the path bytes, one NUL byte, the 32 raw bytes of that file's SHA-256 digest, and one newline. Empty directories do not contribute bytes. Symbolic links and special files are invalid. A file artifact uses the SHA-256 digest of its exact bytes.

## Manager result and error

A successful manager command emits exactly one `aquarium-dev-manager-result/v1` object containing `schema`, `operation`, `status`, `project_id`, `message`, and `details`. Operations are `diagnose`, `enroll`, `rebuild`, `publish`, `resolve`, `launch`, `repair`, or `configure-codex`; status is `success`, `no-change`, or `diagnosed`. `project_id` may be `null` only when diagnosis cannot identify a supported project. `details` is a bounded object and must not contain credentials or raw tool output. Successful `launch` is the sole transport exception: after validation it replaces the manager process with the resolved executable, passes through its arguments and streams unchanged, keeps the artifact lease descriptor open, and returns the child process's exit behavior. A rejected launch still emits the normal error object.

A rejected command emits exactly one `aquarium-dev-error/v1` object to stderr with `schema` and an `error` object containing exactly `code`, `message`, `action`, `stage`, `project_id`, and `git_sha`. The last two values may be null. Stable codes are:

- `unsupported_host`, `not_git_root`, `symlink_git_root`, `unsupported_project`
- `producer_contract_missing`, `producer_description_invalid`, `producer_build_failed`, `producer_manifest_invalid`
- `not_local_main`, `dirty_worktree`, `sha_mismatch`, `output_escape`, `checksum_mismatch`
- `enrollment_missing`, `enrollment_conflict`, `enrollment_broken`, `hook_conflict`
- `artifact_missing`, `artifact_invalid`, `lease_unavailable`, `publication_failed`
- `codex_not_configured`, `codex_login_required`, `approval_required`, `invalid_arguments`

Contract rejection exits `2`; an admitted operation that fails exits `1`. Diagnosis may exit `0` with `status: diagnosed` when it successfully reports an unhealthy state.

## Host-local layout

All manager state is below `~/.aquarium/`:

```text
enrollments/<project-id>.json
artifacts/<project-id>/<full-git-sha>/
current/<project-id>
locks/publisher/<project-id>.lock
locks/artifacts/<project-id>/<full-git-sha>.lock
queue/<project-id>/<full-git-sha>.json
diagnostics/<project-id>/latest.json
runtime/<project-id>/
codex/
```

There is no top-level `bin/`. Enrollment records only the schema, project ID, canonical real checkout path, hook identity, and enrollment timestamp. They never own Git, roadmap, Procedure, review, or release state and never contain secrets.

Artifacts are immutable after promotion. A relative temporary sibling is atomically renamed into `artifacts`, and a relative temporary symbolic link is atomically renamed over `current/<project-id>`. Staging and destination must share a filesystem.

## Enrollment, hooks, resolution, and leases

One project ID has at most one canonical checkout. Same-checkout enrollment is idempotent. A different checkout requires explicit re-enrollment approval and transfers only the Aquarium marker block from the previously recorded regular native hook. Symbolic hooks, external `core.hooksPath`, duplicate or malformed markers, and changed owned bytes are `hook_conflict` failures.

No enrollment permits ordinary unguarded stable fallback. Once an enrollment record exists, a missing or mismatched checkout, current selector, artifact, manifest, version, SHA, or checksum fails closed with its repair action. The sole exception is an explicit Dolgorae stable identity with its absolute path, exact supported release version, and official executable checksum; that path bypasses but never mutates or repairs the enrollment.

Resolution acquires a shared BSD advisory lock for the selected immutable artifact before returning its path. Launch holds the open lock descriptor for the complete child lifetime and never re-resolves `current`. Publication and cleanup require exclusive locks. Cleanup removes a superseded artifact immediately when its exclusive non-blocking lease succeeds; otherwise an asynchronous cleanup worker waits for operating-system ownership to become available. PIDs, timestamps, and grace periods are not lease authority.

An exact development-candidate launch supplies `--expected-git-sha`, `--expected-development-version`, and `--expected-sha256` as one complete guard set. An exact stable Dolgorae launch supplies `--stable`, `--expected-stable-version`, and `--expected-stable-sha256` as a mutually exclusive complete set. Partial, mixed, or malformed guards are rejected before resolution, and Dolgorae source-bearing review operations reject an omitted set. A plain stable fallback never satisfies guarded launch. Guarded launch creates an owner-only identity-bound execution copy, opens and rehashes it, proves its inode differs from the canonical artifact, executes that copy, and inherits the identity lease. Canonical-path replacement therefore cannot change the executed bytes.

## Scheduling and failure behavior

The native `post-commit` marker only queues the completed local-main SHA and starts the per-project asynchronous worker. The worker serializes on the publisher lock and coalesces duplicate SHA requests. Build and validation happen in a fresh same-filesystem staging directory. Any failure preserves the prior current selector and writes one bounded latest diagnostic. Git commit success and HEAD are never rewritten or rolled back.

An Aquarium marketplace generation referenced by isolated Codex configuration is retained across current advancement. Reconfiguration retains superseded bytes through marketplace replacement, plugin installation, post-configuration diagnosis, and login readiness. Only a fully successful terminal configuration releases and cleans superseded Aquarium generations; a failed or interrupted reconfiguration preserves the prior bytes needed for recovery. Other projects retain ordinary lease-driven prompt cleanup.

## Isolated Codex home

The development runtime sets `CODEX_HOME=~/.aquarium/codex`. It configures the exact local Aquarium plugin snapshot, paired skills, MCP servers, and resolved enrolled artifacts through separate approval. It never reads, copies, or mutates the stable Codex home or authentication. Missing isolated login returns `codex_login_required` with the exact user action; Aquarium never authenticates.

The Aquarium artifact is a local marketplace containing the committed marketplace metadata and complete committed plugin tree. The derived plugin manifest uses `v<next>-dev.<sha12>` identity; its bundled skills therefore share the plugin generation. Approved configuration installs that leased marketplace into the isolated home. Enrolled Mulgae and Gaori MCP entries invoke the manager from the installed plugin generation and resolve the external artifact at launch; Dolgorae, Podway, and Sanho are CLI-only integrations. Diagnosis reports the selected checkout, enrollment, hook, current artifact, isolated plugin and bundled-skill version, enabled owned MCP names, login readiness, and the validated current artifact identity or explicit state for every supported project.
