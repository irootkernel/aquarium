# State and Evidence

Aquarium deliberately keeps several authority planes separate. A value observed in one plane cannot silently update or prove another.

## Authority Planes

| Plane | Owner | What it proves |
| --- | --- | --- |
| Product and workflow contract | Manifest, skill, reference, Procedure source, and tests | What the shipped plugin declares and checks |
| Delivery planning | Canonical roadmap, TODO, and deferred-feedback owners | Adopted identity, status, ordering, and remaining work |
| Procedure runtime | Podway repository-local state | The observed session, node, transition, and runtime record |
| Source control | Git objects, refs, index, and worktree | Exact content identity and repository mutation state |
| Codex goal state | Host-managed goal lifecycle | The current conversational objective and completion status |
| External tool runtime | The invoked tool | Tool-specific run, review, test, terminal, or session evidence |
| Distribution | Tags, release artifacts, checksums, and remote release state | What exact artifact or release was published and observed |

No central `.aquarium` file reconciles these planes. Workflows read the authoritative source needed for the current decision and record only the bounded handoff the next owner requires.

## Evidence Classes

- Contract evidence shows that source, schemas, validators, or tests define a behavior.
- Development evidence shows that a local candidate passed a bounded check.
- Runtime evidence shows what an invoked tool or Procedure session observed.
- Distribution evidence ties an exact published artifact or remote release to a verified candidate.

A green structural inspector does not prove semantic correctness. A local tool run does not prove release publication. A cross-repository consumer claim does not prove the producer commit or its deployment.

## Residency

Ignored `.podway`, `.gaori`, Mulgae, terminal, and similar runtime artifacts stay with their native tools. They are not tracked documentation authority. When a downstream workflow needs durable proof, Aquarium promotes only a reviewed, bounded, non-sensitive structured artifact under `evidence/aquarium/`, unless repository configuration declares another relative Aquarium evidence root.

Promoted evidence records bounded work-unit identity, purpose, producer, exact target binding, payload digests, and limitations. It omits credentials, raw transcripts, unrelated source, timestamps, and ambient runtime history. Promotion is a deliberate documentation change, not an automatic side effect of a successful run.
