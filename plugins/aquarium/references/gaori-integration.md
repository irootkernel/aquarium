# Gaori Integration

Use the supported Gaori release and matching `$use-gaori` skill from
[tool-catalog.md](tool-catalog.md). The paired skill owns asynchronous execution,
waiting, cancellation, transport fallback, retention, and recovery. Aquarium owns
which check is required, its authorization, and how its result supports the
current task. Follow [evidence-residency.md](evidence-residency.md) for handoffs.

## Select and Delegate a Check

Resolve the exact command from repository authority and the current verification
requirements. Pass its configured command ID or authorized argv, repository,
parser and tags, and applicable timeout to `$use-gaori`. Parser mapping belongs
to `test-setup`; neither a parser nor Gaori chooses a test gate. Preserve existing
user-run evidence when the owning workflow accepts it for the exact target.

Before requesting a new execution, preserve any already-started invocation and
its command scope. Let the paired skill continue that execution. Only a native terminal result establishes completion; a pending invocation,
observer timeout, or cancellation acknowledgement leaves the outcome open. Completed run inventory identifies durable evidence, not a live
invocation that can be reattached. Keep invocation identity separate from the
returned command and artifact identities.

CLI availability, connected MCP capability, and registration are independent.
Use the paired skill's transport requirements; do not require unrelated tools or
a PATH CLI for a usable MCP execution. A required global CLI or paired-skill gap
routes to `$aquarium:dev-setup-global`; a required project MCP or repository
configuration gap routes to `$aquarium:dev-setup`. If the integration is optional
and unavailable, run the exact repository-owned command directly and report the
missing evidence compression. If the command itself is unknown, return an
evidence gap rather than inventing it.

## Interpret the Result

Keep these decisions separate:

- The command's exit code and terminal outcome describe the selected check.
- Gaori's artifact status, extraction status, and truncation describe execution
  and evidence availability. `no_match` alone does not fail a successful command.
- Aquarium accepts a verification requirement only when the exact current target
  has the required result and sufficient evidence under repository authority.

A Gaori `internal_error`, lost outcome, or unavailable required evidence cannot
be reported as successful verification merely because a child may have exited
zero. Preserve a verified child result separately and delegate native recovery
or evidence inspection to `$use-gaori`. Do not reclassify failure from an exit
integer alone: child commands can use the same codes as Gaori failures.

Return the exact command and target, terminal outcome and exit code, invocation
identity when available, artifact status, `extractor_status`, truncation when
reported, returned summary paths, whether raw evidence was opened, and remaining
checks or gaps. Never invent fields that the native result did not expose.
Runtime paths remain local evidence and are not copied into tracked documents.

## Timing and Retention

Delegate a user-requested live timing observation to `$use-gaori` for the existing
invocation. `$use-gaori-status` owns historical statistics and detailed timing
explanations. Its absence does not block execution or a supported one-off live
estimate. Use only native calculations and keep the existing execution active.

The paired skill owns retention discovery and cleanup guidance. An advisory does
not delay a required check or grant deletion authority. Neither timing nor
retention evidence changes command authorization or verification acceptance.
