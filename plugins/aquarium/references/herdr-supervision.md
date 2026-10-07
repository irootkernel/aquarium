# Herdr review supervision

The upstream `$herdr` skill and installed CLI own native syntax, pane and agent
control, submission, waiting, output reads and recovery. Aquarium supplies the
target and complete Review Brief, admits the report and adjudicates its content.
Review semantics belong to [review-contract.md](review-contract.md); native
control remains upstream-owned. Do not emulate Orca Run, Task, Dispatch, Delivery or settlement objects.

## Readiness and caller context

The qualification baseline is [Herdr v0.9.3](https://github.com/herdrdev/herdr/releases/tag/v0.9.3)
with its [release-matched upstream skill](https://github.com/herdrdev/herdr/blob/v0.9.3/skills/herdr/SKILL.md).
Require the installed upstream skill. Inspect client, server, skill and requested
reviewer readiness independently; a version string cannot prove all four.
The baseline does not establish what is installed or running on the host.

Use the [catalog](tool-catalog.md#herdr) for selected-route setup diagnosis and
the [migration contract](herdr-migration.md) for legacy state. Peer routes do not
acquire Herdr prerequisites.

Before any session inspection or control, require `HERDR_ENV=1`. If absent,
return the selected route's prerequisite gap. A tool shell may lack inherited
context; resume from the intended managed pane or obtain the user's actual
caller context without inspecting another client's focused session or creating
a replacement backend. Within Herdr, learn current syntax
through `herdr --help` and the agent and pane groups; use `herdr status` before
depending on server features. A client/server mismatch requires separate host
action, never an automatic upgrade or lowered baseline.

Use explicit caller context or native returned IDs. Preserve the current local
session, canonical checkout and caller working directory. Remote review and
different workspace topology are outside this initial migration. Do not rely
on another client's focused pane or infer IDs from examples.

## Fresh reviewer and submission

Follow upstream geometry rules to split a sibling pane in the caller's tab,
preserving cwd and `--no-focus`. Verify the returned pane is an available shell
and record that this operation created it. Start one fresh uniquely named agent
of the explicitly selected kind in that pane. Pass requested native model or
effort arguments through the supported native interface, after `--` where
required. Verify the kind and identity actually established.

A startup-blocked or not-ready agent remains available for observation. Inspect
it, preserve the operation, and ask the user before answering approval or
question UI. Do not submit until that same requested agent is ready for input.
Do not switch kind, reuse another reviewer or create a second pane as recovery.

Submit the complete Review Brief and restrictions through `agent prompt --wait`
using the native syntax. Preserve the returned submission and wait outcomes.
A submission response alone proves neither observed work nor a completed review.
Correlate the requested fresh agent with observed activity. The native settled
state wait is lifecycle evidence, not a report or a per-turn completion receipt.
Use upstream waiting behavior without Aquarium retry caps or cumulative wait
budgets; a bounded observer timeout does not terminate the reviewer.

## Complete output and uncertain results

Read the same agent through the native agent surface, preferring unwrapped
output and expanding the native read when necessary. Require the complete
purpose-specific result and every completion criterion, not a screen excerpt.
When a larger read cannot recover the completed report, follow the upstream
fallback: ask the same reviewer to write its existing result as Markdown to an
allowed temporary location, then read the whole file. Use this only for output
recovery, never as initial delivery or a new assessment.

On timeout, `agent_prompt_stalled`, blocked UI or lost observation, inspect that
same agent and available output before any supported recovery. A timeout does
not prove submission failed. Never blindly resubmit, answer UI on the user's
behalf, or replace the agent. Retain earlier reports and findings. Replacement,
identity mismatch, missing output, `unknown` state or changed target prevents
completion; report `failed` or `incomplete` with every available native reference.

An embedded route change needs explicit authority and authoritative safe state
under the shared routing contract. Keep the current operation while active or
uncertain, and preserve findings, consumed ordinals and remaining correction
authority. A failed or incomplete operation consumes no assessment ordinal.

## Review output boundary

Review-related temporary files, native state, tool output and reports may use
external temporary locations or Git-ignored runtime paths in the checkout.
Examples such as `/tmp`, `/private/tmp` and `$TMPDIR` are not an allowlist;
applicable repository temporary-file guidance still applies. Select an allowed
location under that guidance for the output-recovery fallback. This permission
does not cover tracked or non-ignored files, Git state, or a symbolic link that
writes into a protected path. Report retained files used to deliver the result;
routine temporary output needs no inventory or automatic cleanup.

## Admission and pane disposition

Admit completion only when readiness, fresh reviewer identity, submission/activity
correlation, applicable target and Brief, and the complete result are established.
Before admission, recheck the applicable Git target through the authorized
read-only Git surface. For `staged`, confirm the live HEAD-to-index transition
still matches the inspected candidate; for committed targets, retain the
resolved object basis. A changed mutable target prevents approval. This does
not create a fingerprint, snapshot or guarantee that bytes stayed unchanged
between reads.

Record bounded native references and outcomes separately from technical findings
and workflow acceptance. Use `backend-check-result=not-provided`; Herdr provides
no backend CI or Aquarium immutable-capture guarantee.

After successful result admission and evidence recording, close only the pane
created by this operation, using the native pane command and its exact returned
ID. Verify its disposition. While active, failed, blocked or uncertain, leave it
intact for same-operation recovery or the user's decision. Never close another
pane, tab, workspace or session, and never stop or restart the server.

Keep reports and transient identities under the [evidence residency contract](evidence-residency.md).
Do not promote them as Mulgae hardening-deferral evidence. Static checks do not
prove native agent behavior; `TASK-109` owns actual observed-agent qualification.
