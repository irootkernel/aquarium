# Gaori Integration

Use the supported Gaori release and matching `$use-gaori` skill from
[tool-catalog.md](tool-catalog.md). The paired skill owns asynchronous execution,
waiting, cancellation, transport fallback, retention, and recovery. Aquarium owns
which check is required, its authorization, and how its result supports the
current task. Follow [evidence-residency.md](evidence-residency.md) for handoffs.

## Select and Delegate a Check

Resolve the exact command from repository authority and the current verification
requirements. Pass its configured command ID or authorized argv, canonical
repository root, required environment values, selected config and output-directory
overrides, parser and tags, and applicable timeout to `$use-gaori`. Parser mapping belongs
to `test-setup`; neither a parser nor Gaori chooses a test gate. Preserve existing
user-run evidence when the owning workflow accepts it for the exact target.

The agent that will select the transport or start the check must first load the
installed `$use-gaori` skill in its own execution context and follow the
applicable release-matched instructions. Naming the skill or loading it only in
a coordinator does not load it for a delegated worker. Already loaded guidance
may be reused while its version, scope, and relevant state remain applicable.
If the skill or a required capability is missing, use the prerequisite and
fallback routing below; do not reconstruct Gaori lifecycle behavior from memory.

Before requesting a new execution, preserve any already-started invocation and
its command scope. Let the paired skill continue that execution and own both
execution and completion waiting. Only a native terminal result establishes
completion; a pending invocation, observer timeout, or cancellation
acknowledgement leaves the outcome open. Completed run inventory identifies
durable evidence, not a live invocation that can be reattached. Keep invocation
identity separate from the returned command and artifact identities.

Once the paired skill starts an operation, Aquarium preserves its invocation or
process identity and does not add a competing observation loop. Do not issue
recurring native status queries, inspect files or processes for liveness, start
another observer while an earlier observer remains pending, or restart work to
produce a progress update. Repeated bounded host waits on the same deferred
handle are not native polling. If an observer actually ends, let `$use-gaori`
apply its supported re-await, revision-wait, recovery, or fallback behavior to
the existing operation. A user-requested progress observation uses only the
one-off native observation allowed by the paired skill and leaves the original
operation authoritative. Aquarium defines no polling interval, universal wait
duration, retry quota, or timeout policy.

CLI availability, connected MCP capability, and registration are independent.
Use the paired skill's transport requirements; do not require unrelated tools or
a PATH CLI for a usable MCP execution. A required global CLI or paired-skill gap
routes to `$aquarium:dev-setup-global`; a required project MCP or repository
configuration gap routes to `$aquarium:dev-setup`. If the integration is optional
and unavailable, run the exact repository-owned command directly and report the
missing evidence compression. If the command itself is unknown, return an
evidence gap rather than inventing it.

Before an MCP start, `$use-gaori` verifies the attached connection's actual
repository, required environment, selected config, and output-directory binding
from host evidence tied to that connection. A registration, server label, or
agent shell environment does not establish those launch inputs. When a binding
is uncertain, use the paired skill's CLI fallback for the selected target.
Start the CLI once and wait on that process handle. Do not launch another MCP
server, restart an attached server, or change host configuration to make MCP
eligible.

## Interpret the Result

Keep these decisions separate:

- The command's exit code and terminal outcome describe the selected check.
- Gaori's artifact status, extraction status, and truncation describe execution
  and evidence availability. `no_match` alone does not fail a successful command.
- Aquarium accepts a verification requirement only when the exact current target
  has the required result and sufficient evidence under repository authority.

Before reporting a pass, match the returned command ID and artifact paths to the
selected command, repository, and output destination. For both configured and
ad-hoc runs, retain the selected argv and compare it with the summary's redacted
`command_argv` where possible. An ad-hoc run's generated command ID cannot
establish its argv. If the argv differs, or redaction prevents verifying a
relevant argument and no other evidence binds it, leave the check unverified.

For a log larger than 256 KiB, extraction scans only complete lines in the final
256 KiB and reports `extractor_status: degraded`. Failures before that window
may be absent from the summary. Zero extracted failures does not prove the log
contains none, and this evidence limit does not change the child result.

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
explanations for the selected repository and command ID. A selected config
override validates that ID; it does not filter historical samples by config,
so another config's runs with the same ID may be included. An MCP server
launched with `--output-dir` cannot serve insights; follow the paired skill's
CLI history and live-estimate limits. The status skill's absence does not block
execution or a supported one-off live estimate. Use only native calculations
and keep the existing execution active.

The paired skill owns retention discovery and cleanup guidance. An advisory does
not delay a required check or grant deletion authority. Neither timing nor
retention evidence changes command authorization or verification acceptance.
