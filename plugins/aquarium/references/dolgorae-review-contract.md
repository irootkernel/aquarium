# Dolgorae Review Consumer Contract

This contract binds Aquarium review workflows to the exact official Dolgorae v0.1.0 Apple Silicon release. Dolgorae owns the checked wire schemas, capture implementation, Reviewer lifecycle, credential carriers, terminal evidence, settlement, retention, and cleanup. Aquarium owns candidate admission, global release validation, source-scope selection, backend routing, and result adjudication. Dolgorae is not an Aquarium development-channel producer.

## Candidate identity

The admitted release is tag `v0.1.0`, peeled source commit `47c95d0d060d9ee685a01bedbdeb5379515e2804`, Apple Silicon archive `dolgorae-v0.1.0-aarch64-apple-darwin.tar.gz` with SHA-256 `598ffaff7883b4f8cc794b890186d758795f57c1f373e6905c138abb7f3bfe41`, and contained executable SHA-256 `6087b484cfd8d61d88ed69a5b84ab4a515ba2efaebe4fa282d51679536cccdb8`. The distribution is an Integration Preview with an ad-hoc linker signature, not Developer ID signing or notarization; checksum admission, not the code signature, binds the executable bytes.

Before any source-bearing operation, diagnose the global executable with `dev-setup`, then resolve `dolgorae` from the current process `PATH`. Require native Apple Silicon macOS, one absolute executable regular non-symlink path outside `~/.aquarium` and `~/.aquarium-dev`, the exact official checksum, and the exact checked machine `--version` envelope for `dolgorae 0.1.0`. Record the canonical source path, regular-file device and inode, executable SHA-256, runtime `dolgorae_version`, and capability digest.

The capability digest is SHA-256 over the compact JSON `data` object returned by `runtime capabilities`, with object keys sorted lexicographically and one trailing newline. The admitted v0.1.0 digest is `0c7f8bb7e6b6f86fd98eb5aec9cda1e6859fbc1da2f06b1c0e4a21ad2e5ff307`. Accept only a successful checked machine envelope whose command is `runtime.capabilities`; reject empty output, multiple documents, unknown envelope fields, wrong types, incompatible versions, malformed bounds, or a digest change.

Every production review invocation uses the globally installed `dolgorae` command selected by normal `PATH` resolution. Candidate admission repeats `command -v`, canonical path, regular-file identity, executable SHA-256, checked machine version, and capability validation immediately before each source-bearing operation. A missing command, a path under either Aquarium state root, mutable or symlinked identity, replacement, version drift, checksum drift, or capability drift fails before source transmission.

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
