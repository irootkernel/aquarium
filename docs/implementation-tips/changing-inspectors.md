# Changing Inspectors

Aquarium inspectors produce conservative local evidence for setup, documentation, testing, release preparation, and publication observation. They are not general repository scanners and must not silently widen their inputs.

## Design Rules

- Resolve the canonical Git root and reject unsafe or ambiguous targets before reading content.
- Inspect regular repository files only. Treat symlinks, sensitive names, credential paths, ignored runtime evidence, and paths outside the intended root conservatively.
- Do not execute project code, start providers or MCP servers, authenticate, or contact the network unless a separate owning workflow explicitly defines that effect.
- Emit a stable versioned JSON schema. Add fields compatibly when possible; change the schema identifier when consumers cannot safely read the old shape.
- Report unknown or not-evaluated semantics honestly. A structural check must not manufacture a semantic pass.
- Keep stdout machine-readable when it is an interface. Send bounded diagnostics to the documented channel without leaking file contents or credentials.

## Implementation Pattern

Prefer small pure functions for path classification, parsing, normalization, and result construction. Keep filesystem or subprocess boundaries narrow and injectable enough for fixtures. Reuse the repository's existing safe-path and JSON-output patterns before adding a new abstraction.

Bundle normalization is allowed to parse the explicitly supplied manifest but not discover or persist bundle state. Publication observers may query the exact release surface authorized by their parent workflow; generic setup inspectors remain local and read-only.

## Tests

Keep automated cases focused on executable behavior: relevant output fields, error codes, and safe repository-root handling. Use representative unsafe paths, missing files, malformed input, and unsupported versions where the changed code handles them. Keep raw secrets out of fixtures even for negative tests.

For the test inspector, organize cases around observable contracts: stage order, failure propagation, runner evidence, parser selection, and safe file access. Assert relevant result fields and reason codes. Avoid pinning private helper names, implementation flags, diagnostic sentences, or the layout of equivalent inputs. Use representative equivalent inputs and actual behavioral counterexamples instead of a Cartesian product of whitespace variants. Retain distinct failure cases even when they share a parser branch.

After focused tests, run the Ruby validator for package structure and local references. It does not inspect Python source fragments or verify public prose. Master separately verifies the skills that interpret inspector output; report the affected manual checks without inferring their result from the automated tests.
