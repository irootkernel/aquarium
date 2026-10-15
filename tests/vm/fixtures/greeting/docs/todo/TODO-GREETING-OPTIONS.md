# Greeting options

The roadmap owns EPIC-001 and its member identities and lifecycle. Implement
TASK-001, then TASK-002 in separate task-owned changes under the operator's
approved execution scope.

TASK-001 adds `--uppercase`. `python3 greet.py --uppercase` prints
`HELLO, WORLD!` followed by one newline. `python3 greet.py --uppercase Ada`
prints `HELLO, ADA!` followed by one newline. Existing default and named
greetings remain byte-identical. Add meaningful tests and update user guidance.

TASK-002 adds `--repeat N`. A positive integer prints exactly N complete greeting
lines. A missing option retains one line. Zero, negative and noninteger counts
fail with a nonzero exit status. Combine `--uppercase` and `--repeat`. Preserve
TASK-001 and original behavior; add tests and user guidance.

Use the installed handlers, native Codex Workers, an independent Codex Judge and
the explicitly selected three-agent Codex Independent Review route. Run the
complete fixture Make gate. The operator accepts each ready plan or exact
candidate through the normal handler boundary; no document grants acceptance.

Release startup acceptance stops after real first-member delivery, checks,
independent assessment and semantic progression. It does not establish full
Epic delivery, final review, closeout or publication readiness. Full delivery
and recovery are separate development-verification obligations.
