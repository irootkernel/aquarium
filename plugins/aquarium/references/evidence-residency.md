# Evidence Residency and Promotion

Read this reference whenever an Aquarium workflow consumes evidence from Mulgae, Gaori, Podway, a disposable validation root, or another ignored runtime location. Evidence quality and evidence residency are separate contracts: a verified result may support the active workflow without becoming repository authority.

## Classify Evidence Before Using It

- **Runtime evidence** lives in ignored, disposable, or provider-owned state such as `.mulgae/**`, `.gaori/runs/**`, `.podway/runtime/**`, `/tmp/**`, or `~/.claude/**`. Its paths, run IDs, invocation IDs, and session IDs may be recorded in the active conversation or Podway session for bounded recovery and adjudication, but Git does not preserve it and its retention remains owned by the producing tool or user.
- **Orchestration evidence** is the bounded command, actor, exit status, target identity, result quality, finding disposition, and runtime reference returned between Aquarium phases. It is not repository documentation and must not be copied into a roadmap or handoff as an execution log.
- **Canonical repository information** states the current goal, lifecycle, requirement, contract, accepted risk, actionable handoff, or revalidation condition. It must remain useful without any ignored runtime directory.
- **Promoted evidence** is an exceptional tracked package created only when downstream correctness requires durable evidence that current code, tests, specifications, and Git history cannot express more clearly.

Never use a runtime path or runtime identity as authoritative evidence in tracked documentation, roadmap entries, generated documents, commit messages, or other durable repository material. Literal runtime paths may still appear where needed to document configuration, privacy, ignore policy, cleanup, or tool behavior; those descriptions are not evidence references.

## Keep Canonical Documents Current

Do not add routine `Validation remediation`, `Validation record`, completion-history, command-log, test-report, reviewed-snapshot, or provider-run sections to a roadmap. A successful validation that changes no lifecycle state, current requirement, accepted risk, or actionable downstream instruction produces no documentation diff and no validation-record commit.

Record a remediation in canonical documentation only when the correction changes current behavior that the specification must describe, changes lifecycle state, creates or resolves a current risk, or leaves an actionable handoff. Git owns implementation history; Podway and native tools own workflow evidence.

## Promote Evidence Explicitly

Promotion must be disclosed in the approved workflow envelope or separately approved before files are created or staged. Use `evidence/aquarium/` unless the applicable repository `AGENTS.md` contains exactly one Project Configuration entry in the form `Aquarium evidence root: <repository-relative-path>`. No other evidence-path mention is a declaration. Stop on an ambiguous, malformed, absolute, ignored, outside-repository, or symlinked declaration instead of falling back to the default; do not create another Aquarium state file to configure it.

```text
evidence/aquarium/<work-unit-id>/<purpose>/<target-content-sha256>/
```

The target digest directory uses the lowercase 64-character hex portion of the verified native target SHA-256 without the `sha256:` prefix. `target.content_sha256` must equal that exact native digest. If the evidence producer does not expose an authoritative target SHA-256 that can be verified against the reviewed target, promotion is unavailable and the workflow stops with an evidence gap.

Once committed, a package is immutable. Changed content requires a new target-digest directory. Never stage a modification, replacement, move, or deletion of an existing tracked package.

At most one package may exist for the same work unit, purpose, and target digest. Combine approved payloads before its first commit. If the same triple needs additional evidence after commit, stop with an evidence gap; never overload or replace the immutable package.

Each package contains `manifest.json` with this closed top-level shape:

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

- Mulgae may contribute only a bounded structured JSON projection of verified target digest, capture kind, coverage, CI decision, publication status, structured extraction status, and locally adjudicated finding ID, severity, disposition, and affected repository-relative paths. Obtain the native digest from `target.content_sha256` in the final artifact identified by the exact-run status `final_artifact_uri`; no other digest field is authoritative.
  Accepted Markdown reports, finding descriptions or recommendations, evidence quotes, excerpts, transcripts, and extraction artifacts remain private runtime state.
- Gaori may contribute only finalized redacted status or summary output that satisfies the common content restrictions above. Raw logs and excerpts remain original unredacted evidence and are never promoted.
- Podway databases, history, recorded claims, and runtime handoff files are never promotion sources. Promote the native evidence or approved canonical document that Podway referenced instead.

Inspect every payload before staging. If no safe bounded artifact exists, record an evidence gap and stop instead of promoting raw or sensitive material. A package manifest indexes copied evidence; it does not make an unverified claim true.

Create and stage the package only after the native review of its target is operationally complete. The package is a commit-boundary projection of already reviewed native evidence, is excluded from the Mulgae review target, and does not make that review stale. Any post-review change to code, tests, generated product artifacts, or canonical documentation remains stale under the owning workflow's normal rule.

## Reference Promoted Evidence

Use one repeatable Lore trailer per promoted package:

```text
Aquarium-Evidence: <repository-relative-manifest-path> sha256:<64-hex-manifest-digest>
```

Before handoff, the owning workflow verifies the live native evidence, native target digest, and copied payload bytes and supplies that result with the package. At the commit boundary, verify the supplied native target binding, every staged payload digest, staged manifest, and manifest digest; hardening deferrals additionally require the live exact-run query defined by the commit skill.

The manifest digest is the lowercase SHA-256 of the exact staged `manifest.json` bytes, and the trailer contains the `sha256:` prefix exactly once. After committing, consumers verify the tracked manifest and payload digests without requiring the ignored runtime to exist.

Do not write new `Mulgae-Deferred-Run` or `Mulgae-Deferred-Finding` trailers. Existing commits may retain them without history rewriting. When a legacy trailer is the only reference, use the named local run if it remains available. If it is gone, do not attempt to promote the missing run: record an evidence gap and cover the affected paths and current requirements in the current remediation-eligible whole-target audit.

After such a legacy gap, only a new finding that takes the normal member-task hardening-deferral route may produce a new `hardening-deferral` package. This restriction does not affect an independently approved `accepted-risk`, `external-handoff`, or `repository-required` package.
