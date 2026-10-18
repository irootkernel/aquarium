# Evidence Residency and Promotion

Read this reference whenever an Aquarium workflow consumes evidence from Mulgae, Gaori, Sorage, Podway, a disposable validation root, or another ignored runtime location. Evidence quality and evidence residency are separate contracts: a verified result may support the active workflow without becoming repository authority.

## Classify Evidence Before Using It

- **Runtime evidence** lives in ignored, disposable, provider-owned, or host-owned state such as `.mulgae/**`, `.gaori/runs/**`, `.sorage/**`, `.podway/runtime/**`, `/tmp/**`, `~/.claude/**`, or a native subagent lifecycle. Its paths, run IDs, invocation IDs, session IDs, and delegation identities may be recorded in the active conversation or Podway session for bounded recovery and adjudication, but Git does not preserve them and retention remains owned by the producing tool, host, or user.
- **Orchestration evidence** is the bounded command, actor, exit status, target identity, result quality, criterion-level completion assessment, finding disposition, and runtime reference returned between Aquarium phases. A bounded completion assessment contains criterion identity and source, assessment state, remaining gap, and reviewer or coordinator provenance, but no raw report prose or provider payload. It is not repository documentation and must not be copied into a roadmap or handoff as an execution log.
- **Canonical repository information** states the current goal, lifecycle, requirement, contract, accepted risk, actionable handoff, or revalidation condition. It must remain useful without any ignored runtime directory.
- **Promoted evidence** is an exceptional tracked package created only when downstream correctness requires durable evidence that current code, tests, specifications, and Git history cannot express more clearly.

Never use a runtime path or runtime identity as authoritative evidence in tracked documentation, roadmap entries, generated documents, commit messages, or other durable repository material. Literal runtime paths may still appear where needed to document configuration, privacy, ignore policy, cleanup, or tool behavior; those descriptions are not evidence references.

## Keep Canonical Documents Current

Upstream PM documents and seed handoff files remain disposable draft evidence until Aquarium applies their accepted content to approved canonical paths. Use the approved draft location outside the repository and the cleanup scope in the [PM contract](ouroboros-integration.md#pm-files-and-clipboard). Do not stage generated drafts or copy their runtime paths into canonical documents as evidence. PM clipboard replacement requires separate authority in the execution envelope; it is not evidence promotion or document approval.

Do not add routine `Validation remediation`, `Validation record`, completion-history, command-log, test-report, reviewed-snapshot, or provider-run sections to a roadmap. A successful validation that changes no lifecycle state, current requirement, accepted risk, or actionable downstream instruction produces no documentation diff and no validation-record commit.

Record a remediation in canonical documentation only when the correction changes current behavior that the specification must describe, changes lifecycle state, creates or resolves a current risk, or leaves an actionable handoff. Git owns implementation history; Podway and native tools own workflow evidence.

## Promote Evidence Explicitly

Promotion must be disclosed in the approved workflow envelope or separately approved before files are created or staged. Use `evidence/aquarium/` unless the applicable repository `AGENTS.md` contains exactly one Project Configuration entry in the form `Aquarium evidence root: <repository-relative-path>`. No other evidence-path mention is a declaration. Stop on an ambiguous, malformed, absolute, ignored, outside-repository, or symlinked declaration instead of falling back to the default; do not create another Aquarium state file to configure it.

Choose the producer contract before preparing a package. Historical captured-source packages and other eligible producers retain v1 below. New Mulgae live-source results use [v2](#promote-live-source-evidence-v2). Never put a live source identity in a v1 content-digest field.

```text
evidence/aquarium/<work-unit-id>/<purpose>/<target-content-sha256>/
```

The target digest directory uses the lowercase 64-character hex portion of the verified native target SHA-256 without the `sha256:` prefix. `target.content_sha256` must equal that exact native digest. For v1, if the evidence producer does not expose an authoritative target SHA-256 that can be verified against the reviewed target, promotion is unavailable and the workflow stops with an evidence gap.

Once committed, a package is immutable. For v1, changed content requires a new target-digest directory. Never stage a modification, replacement, move, or deletion of an existing tracked package.

At most one v1 package may exist for the same work unit, purpose, and target digest. Combine approved payloads before its first commit. If the same triple needs additional evidence after commit, stop with an evidence gap; never overload or replace the immutable package.

Each v1 package contains `manifest.json` with this closed top-level shape:

```json
{
  "schema": "aquarium.promoted-evidence/v1",
  "work_unit": {"kind": "task", "id": "TASK-001"},
  "purpose": "hardening-deferral",
  "target": {
    "git_head": "<exact Git object ID at capture>",
    "capture_kind": "stage",
    "content_sha256": "sha256:<64-hex digest>"
  },
  "source": {"tool": "mulgae"},
  "payloads": [
    {
      "path": "evidence/aquarium/TASK-001/hardening-deferral/<digest>/findings.json",
      "media_type": "application/json",
      "sha256": "sha256:<64-hex digest>"
    }
  ]
}
```

`work_unit.kind` is `task` or `epic`, and its ID is the matching canonical roadmap identity; never derive either value from a runtime or session identity. `purpose` is `hardening-deferral`, `accepted-risk`, `external-handoff`, or `repository-required`. `capture_kind` is the native reviewed target kind. `target.git_head` is the exact object ID returned by `git rev-parse HEAD` at capture and may use the repository's object format.

`source.tool` names the native producer but contains no runtime, invocation, session, provider, or model identity. Payload paths are repository-relative regular files under the package directory, with regular non-symlink ancestry, and every digest covers the exact copied bytes.

Copy only the smallest reviewed, bounded, non-sensitive native artifact that supports the downstream need. Never promote raw logs, excerpts, reports containing provider prose, transcripts, quotes, private diagnostics, export bundles, credential material or paths, runtime identities, provider or model identities, timestamps, usernames, native-home paths, absolute paths, or machine-specific paths.

Use repository-relative paths only. Redact a safe structured projection before staging or stop with an evidence gap when any prohibited content is necessary to interpret the payload.

- Mulgae may contribute only a bounded structured JSON projection of verified target digest, capture kind, coverage, CI decision, publication status, structured extraction status, and locally adjudicated finding ID, reported severity, effective priority, validity, disposition, and affected repository-relative paths. For a historical captured result, obtain its authoritative target content digest through the paired skill's supported verified public reads. New live results expose a metadata identity instead and use v2 below. Do not parse private final artifacts or substitute a source identity for a content digest.
  Accepted Markdown reports, finding descriptions or recommendations, evidence quotes, excerpts, transcripts, and extraction artifacts remain private runtime state.
- Herdr lifecycle evidence, Subagent Review delegation evidence, and coordinator waiver records cannot produce a `hardening-deferral` package in the current contract. They expose no Aquarium-authoritative Mulgae target digest, publication, findings query, or exact run membership. Use ordinary Low dispositions and pass an explicit no-hardening-evidence result through the Epic and commit handoffs, or stop on a downstream requirement for promoted native evidence. Never convert their route evidence reference into a producer identity or native digest.
- Gaori may contribute only finalized redacted status or summary output that satisfies the common content restrictions above. Raw logs and excerpts remain original unredacted evidence and are never promoted.
- Sorage managed Vault content, Handoffs, and derived `.sorage/INBOX.md` are never promotion sources. Promote only the approved canonical document or bounded native evidence that a Handoff references.
- Podway databases, history, recorded claims, and runtime handoff files are never promotion sources. Promote the native evidence or approved canonical document that Podway referenced instead.

Inspect every payload before staging. If no safe bounded artifact exists, record an evidence gap and stop instead of promoting raw or sensitive material. A package manifest indexes copied evidence; it does not make an unverified claim true.

Create and stage the package only after the native review of its target is operationally complete. The package is a commit-boundary projection of already reviewed native evidence, is excluded from the Mulgae review target, and does not make that review stale. Any post-review change to code, tests, generated product artifacts, or canonical documentation remains stale under the owning workflow's normal rule.

## Promote Live-Source Evidence v2

New Mulgae results use `aquarium.promoted-evidence/v2`, defined by the [manifest schema](../assets/schemas/promoted-evidence-v2.schema.json). This version preserves a bounded observation and its native selection identity. It supplies no complete source archive, atomic content view or proof that a live workspace remained unchanged. Existing v1 packages retain their original schema, path and content binding; do not migrate or rewrite them.

v2 uses the top-level fields `schema`, `work_unit`, `purpose`, `target`, `source` and `payloads`. Set `source.tool` to `mulgae`. Replace the v1 target fields with these required fields:

- `identity`: the exact public preflight `target`, a `mulgae-live-source.v1` object with `schema_version`, `scope`, `operand`, `base_oid`, `head_oid` and `empty_base`;
- `source_identity_sha256`: the preflight metadata digest, matched to the receipt-bound inspection of the completed run;
- `consistency`: derive `caller_maintained` for workspace/stage or `resolved_git_objects` for head/commit/diff, following the native scope mapping.

Retain the exact preflight target and digest in the runtime handoff. Require the manifest identity to equal that target and `target.source_identity_sha256` to equal both the preflight digest and the completed run's receipt-bound `source_identity_sha256`. Public run inspection does not return the complete identity or consistency; do not reconstruct them by parsing private artifacts. Preserve the original operand, including the `..` or `...` operator, and resolved Git objects.

Validate the shipped JSON Schema, then recompute the identity digest with [source_identity_digest.py](../skills/task-commit/scripts/source_identity_digest.py), supplying only the identity JSON object on stdin. It uses compact UTF-8 JSON in native field order (`schema_version`, `scope`, `operand`, `base_oid`, `head_oid`, `empty_base`), without a trailing newline in the hashed bytes. Go's JSON encoding escapes `<`, `>`, `&`, U+2028 and U+2029; other non-ASCII characters remain UTF-8.

Require the resulting digest to match all three recorded digests. This helper computes metadata integrity only; it does not validate publication, provenance or source content.

The owning workflow supplies its actual source-consistency observation separately, with an `unchanged`, `changed` or `unknown` outcome and the staged Task's content binding when applicable. Committed scopes retain their resolved Git objects; workspace observations record how the caller maintained source stability without claiming a full-content fingerprint. Follow the [live-source contract](mulgae-review-contract.md) for staged candidate binding and source stability. An observed change, unknown reviewed basis, unavailable required evidence or unsupported consistency blocks promotion and hardening deferral. Equal metadata digests or equal endpoint observations cannot establish an atomic view or erase an observed intervening change.

Use this v2 directory layout:

```text
evidence/aquarium/<work-unit-id>/<purpose>/<manifest-sha256>/manifest.json
```

The directory name is the lowercase hex SHA-256 of the exact manifest bytes. Payload paths are package-relative JSON basenames such as `findings.json`, never repository-relative or absolute paths. Prepare payloads and their digests first, then serialize the manifest, compute its digest and place the complete package. This avoids a circular digest through its own directory name. Duplicate payload paths are invalid. One work-unit/purpose/manifest-digest triple identifies one package; identical bytes may reuse an existing verified package without changing it. Different evidence uses a new manifest digest, even when the native source metadata is identical.

The bounded JSON projection may contain the native source identity and consistency, coverage, CI, publication and extraction state, and locally adjudicated finding IDs, severity, priority, validity, disposition and repository-relative affected paths. All common private-content restrictions still apply. Retain exact run identities and publication receipts only in runtime handoffs for native verification; never copy them into the package. The package digest proves manifest and payload integrity, not whole-source content identity.

For a new live-source hardening deferral, require the owning epic-handler's exact run, successful complete receipt-bound findings query, committed publication and exact finding membership. Verify the manifest identity against retained preflight, the recomputed/preflight/publication digest equality and the scope-derived consistency as above. Recheck the native publication and supplied source-consistency observation at commit time. New terminally incomplete reviews cannot supply a complete-review deferral by composing reports from other runs.

As with v1, every payload and ancestor must be regular and non-symlinked, digests must match actual staged bytes, and a committed package is immutable. Create it only after operational review completion under existing promotion authority. Its addition preserves the reviewed source basis; other target changes retain the normal staleness and local-settlement rules.

## Reference Promoted Evidence

Use one repeatable Lore trailer per promoted package:

```text
Aquarium-Evidence: <repository-relative-manifest-path> sha256:<64-hex-manifest-digest>
```

Before handoff, the owning workflow verifies the live native evidence, native target binding appropriate to v1 or v2, and copied payload bytes and supplies that result with the package. At the commit boundary, verify the supplied native target binding, every staged payload digest, staged manifest, and manifest digest; hardening deferrals additionally require the live exact-run query defined by the commit skill.

The manifest digest is the lowercase SHA-256 of the exact staged `manifest.json` bytes, and the trailer contains the `sha256:` prefix exactly once. After committing, consumers verify the tracked manifest and payload digests without requiring the ignored runtime to exist.

Do not write new `Mulgae-Deferred-Run` or `Mulgae-Deferred-Finding` trailers. Existing commits may retain them without history rewriting. When a legacy trailer is the only reference, use the named local run if it remains available. If it is gone, do not attempt to promote the missing run: record an evidence gap and cover the affected paths and current requirements in the current remediation-eligible whole-target audit.

After such a legacy gap, only a new finding that takes the normal member-task hardening-deferral route may produce a new `hardening-deferral` package. This restriction does not affect an independently approved `accepted-risk`, `external-handoff`, or `repository-required` package.
