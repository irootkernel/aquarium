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

Add unit cases for each classification and failure path, then black-box fixtures for repository-root handling and emitted schema. Include unsafe symlinks, missing files, malformed input, unsupported versions, and non-UTF-8 or ambiguous content when relevant. Keep raw secrets out of fixtures even for negative tests.

After focused tests, run the Ruby validator to confirm schema names, script boundaries, references, and public disclosures remain aligned.
