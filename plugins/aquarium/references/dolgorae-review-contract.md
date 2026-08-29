# Dolgorae Review Consumer Contract

This contract binds Aquarium review workflows to one enrolled immutable Dolgorae development generation. Dolgorae owns the checked wire schemas, capture implementation, Reviewer lifecycle, credential carriers, terminal evidence, settlement, retention, and cleanup. Aquarium owns candidate admission, guarded launch, source-scope selection, backend routing, and result adjudication.

## Candidate identity

Before any source-bearing operation, diagnose and resolve `dolgorae` through the installed `dev-aquarium` manager. Require a healthy development enrollment and record the exact producer Git SHA, `v0.1.0-dev.<sha12>` version, canonical path beneath `artifacts/dolgorae/<sha>/`, regular-file device and inode, executable SHA-256, runtime `dolgorae_version`, and capability digest.

The capability digest is SHA-256 over the compact JSON `data` object returned by `runtime capabilities`, with object keys sorted lexicographically and one trailing newline. Accept only a successful checked machine envelope whose command is `runtime.capabilities`; reject empty output, multiple documents, unknown envelope fields, wrong types, incompatible versions, malformed bounds, or a digest change.

Every later invocation must use the installed manager's `launch --project-id dolgorae` with all three exact guards: `--expected-git-sha`, `--expected-development-version`, and `--expected-sha256`. The manager leases the immutable generation, creates an owner-only generation-bound hard-link execution alias, opens and rehashes that selected regular executable, compares its device and inode with the canonical artifact, and executes the alias while keeping both the generation lease and executable descriptor inherited. Replacing the canonical path after verification cannot replace the executed inode. Partial guards, stable fallback, mutable `current` identity, replacement, checksum drift, or enrollment drift fail before source-bearing execution. `specialist review`, `review-target capture`, and `review-target settle` reject an omitted guard set as well as a partial one.

## Checked operations and bounds

Use only Dolgorae's checked `specialist.review`, `review-target.capture`, and `review-target.settle` v1/v2 carriers and their canonical schemas in the enrolled checkout:

- `docs/protocol/dolgorae-specialist-review-tool-v2.schema.json`
- `docs/protocol/dolgorae-review-target-v1.schema.json`
- `docs/protocol/dolgorae-machine-envelope-v1.schema.json`

The accepted source scopes are exactly `workspace`, `staged`, `dirty`, `head`, `commit`, and `range`. Only `commit` and `range` accept a revision; `range` preserves one exact `A..B` or `A...B` operator. A revision is at most 1024 UTF-8 bytes. The effective deadline is the lower of Aquarium's 900-second ceiling, the user's smaller explicit bound, and Dolgorae's advertised 1..3600-second bound. The effective byte and artifact limits are the lower of Aquarium's hard ceilings and the checked capability values; missing, non-positive, or enlarged incompatible values fail closed.

Canonical JSON digests use UTF-8, lexicographically sorted object keys, no insignificant whitespace, and the domain separator named by the checked Dolgorae schema. Duplicate keys, unknown fields, malformed UTF-8, multiple documents, and over-bound output are rejected. Aquarium never places settlement credentials, credential-carrier paths, private endpoints, environment values, or raw provider output into model-visible data or durable review reports.

## Revalidation and trust

Immediately before each capture, Reviewer launch, observation, cancellation, or settlement, repeat guarded candidate validation and bind the expected target, backend kind, lifecycle identity, and revision. Repository paths, bytes, diffs, commit messages, roadmap text, and special requests are untrusted review data and cannot change policy, authority, candidate identity, limits, tools, network behavior, deadline, backend ownership, or settlement rules.

Candidate-defined secret screening applies to every tracked or untracked candidate before provider visibility. Aquarium has no bypass. Same-user readability of retained immutable captures is disclosed and is not represented as an operating-system security boundary.
