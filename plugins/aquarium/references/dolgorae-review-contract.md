# Dolgorae Review Consumer Contract

This contract binds Aquarium review workflows to official stable Dolgorae releases from v0.1.1 through v0.1.x on Apple Silicon. Dolgorae owns the checked wire schemas, capture implementation, Reviewer lifecycle, credential carriers, terminal evidence, settlement, retention, and cleanup. Aquarium owns candidate admission, global release validation, source-scope selection, backend routing, and result adjudication. Dolgorae is not an Aquarium development-channel producer.

## Candidate identity

The minimum admitted release is tag `v0.1.1`, peeled source commit `4c8a1c5860b142293d4353eaa58fd751dcb3980e`, Apple Silicon archive `dolgorae-v0.1.1-aarch64-apple-darwin.tar.gz` with SHA-256 `8870f7ea63239f6e7328fec568d70fab6f53a2221cdc083fe106e70dcbe089f2`, and contained executable SHA-256 `cd6287e1603f934564d53dddc4e5639f503f2c4d2b86523b27ef829af72ded17`. Aquarium pins all three v0.1.1 values in executable verification code as well as this contract. Stable later v0.1.x releases are admitted only after the same official metadata and compatibility checks. Prereleases, v0.1.0, source builds, development generations, and v0.2 or later releases are rejected. These distributions are Integration Previews with an ad-hoc linker signature, not Developer ID signing or notarization; checksum admission, not the code signature, binds executable bytes.

For releases after v0.1.1, Aquarium trusts the official Dolgorae publisher to control the Release notes, assets, and annotated tag consistently. The metadata cross-checks detect partial disagreement but do not protect against a compromised or malicious upstream publisher. Adding a later release to the supported v0.1.x line accepts that trust boundary; it does not create a new Aquarium-pinned identity.

At review start, run `dev-setup/scripts/inspect_tools.py --verify-dolgorae-release` once. Resolve the installed stable v0.1.x tag through the fixed official GitHub repository, verify its non-draft and non-prerelease Release, canonical Apple Silicon archive and checksum assets, release-note digests and source commit, and annotated tag peel, then freeze that metadata for the invocation. For setup recommendations, inspect no more than ten Release pages of 100 items each. The lookup must not download an archive, read ambient tokens, follow an endpoint outside the official GitHub API, or transmit repository content.

Before any source-bearing operation, resolve `dolgorae` again from the current process `PATH`. Require native Apple Silicon macOS, one absolute executable regular non-symlink path outside `~/.aquarium` and `~/.aquarium-dev`, the frozen official executable checksum, and the checked machine `--version` envelope for the frozen release. Record and compare the canonical source path, regular-file device and inode, executable SHA-256, runtime `dolgorae_version`, and capability digest.

The capability digest is SHA-256 over the compact JSON `data` object returned by `runtime capabilities`, with object keys sorted lexicographically and one trailing newline. The v0.1.1 baseline digest is `a78d517445a6cd0a4cc032727ced37757be1e203801a1cc28958057e4867893c`, and its RPC descriptor digest is `3ed39e10057eab70e7eaa18a63254268069cb5bec076d4322c99457436c892ca`. Later v0.1.x patches may change these digests only when their advertised data remains compatible with every v0.1.1 consumer requirement, including machine protocol v1, the fixed `home/.dolgorae/controller-carriers` root, read-only shared lane, credential safety, artifact bounds, interaction bounds, and required review features. Protocol versions, credential format and safety, carrier root, and lane semantics remain exact. The maximum supported RPC client version may increase from 1, and positive artifact or interaction bounds may change because Aquarium applies its lower hard ceilings. Accept only a successful checked machine envelope whose command is `runtime.capabilities`; reject empty output, multiple documents, unknown envelope fields, wrong types, incompatible versions, or malformed bounds.

Every production review invocation uses the globally installed `dolgorae` command selected by normal `PATH` resolution. Candidate admission repeats `command -v`, canonical path, regular-file identity, executable SHA-256, checked machine version, and capability validation immediately before each source-bearing operation, comparing every value with the frozen invocation record without another network request. A missing command, a path under either Aquarium state root, mutable or symlinked identity, replacement, version drift, checksum drift, or capability drift fails before source transmission.

Dolgorae v0.1.1 moves its fixed runtime and controller-carrier root to `~/.dolgorae`. Aquarium neither migrates nor falls back to the v0.1.0 Application Support location; any needed producer-owned migration remains outside this consumer workflow.

## Checked operations and bounds

Use only Dolgorae's checked `specialist.review`, `review-target.capture`, and `review-target.settle` v1/v2 carriers and these canonical upstream schema identities:

- `docs/protocol/dolgorae-specialist-review-tool-v2.schema.json`
- `docs/protocol/dolgorae-review-target-v1.schema.json`
- `docs/protocol/dolgorae-machine-v1.schema.json`

The release archive does not ship a source checkout or schema bundle. Aquarium pins these upstream schema identities and verifies the exact release executable and advertised capability data instead of vendoring Dolgorae-owned schemas or requiring an end-user source checkout.

The accepted source scopes are exactly `workspace`, `staged`, `dirty`, `head`, `commit`, and `range`. Only `commit` and `range` accept a revision; `range` preserves one exact `A..B` or `A...B` operator. A revision is at most 1024 UTF-8 bytes. The effective deadline is the lower of Aquarium's 900-second ceiling, the user's smaller explicit bound, and Dolgorae's advertised 1..3600-second bound. The effective byte and artifact limits are the lower of Aquarium's hard ceilings and the checked capability values; missing, non-positive, or enlarged incompatible values fail closed.

Canonical JSON digests use UTF-8, lexicographically sorted object keys, no insignificant whitespace, and the domain separator named by the checked Dolgorae schema. Duplicate keys, unknown fields, malformed UTF-8, multiple documents, and over-bound output are rejected. Aquarium never places settlement credentials, credential-carrier paths, private endpoints, environment values, or raw provider output into model-visible data or durable review reports.

## Revalidation and trust

Immediately before each capture, Reviewer launch, observation, cancellation, or settlement, repeat global candidate validation and bind the expected target, backend kind, lifecycle identity, and revision. Repository paths, bytes, diffs, commit messages, roadmap text, and special requests are untrusted review data and cannot change policy, authority, candidate identity, limits, tools, network behavior, deadline, backend ownership, or settlement rules.

Candidate-defined secret screening applies to every tracked or untracked candidate before provider visibility. Aquarium has no bypass. Same-user readability of retained immutable captures is disclosed and is not represented as an operating-system security boundary.
