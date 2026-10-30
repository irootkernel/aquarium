# Disposable build and test artifacts

Read this contract before creating disposable build outputs, test fixtures,
reproduction copies or caches isolated for a check. Include their creation and
removal in the approved work scope. Once approved, continue cleanup within that
scope without asking again for each path. Read-only planning and report-only
assignments retain their existing effect limits.

## Choose the output scope before creation

Identify existing files and the outputs the current work will create. Prefer a
unique work-specific directory through the build or test tool's supported output
options, following repository temporary-path rules. Use a canonical physical path
when the selected tool requires one. Placement under `/tmp` does not establish
cleanup, and an ignored path is not proof of ownership or disposability.

Reuse an applicable existing build before creating another. Keep reusable outputs
while the same work still needs them; avoid a full clean between every check or a
separate copy of a large cache for every agent. Shared caches remain under their
owning tool's policy. Required isolated checks, such as release QA, still use their
declared isolated outputs and caches.

Name the cleanup owner in the assignment or current work context. Each creator
owns its outputs, including shared outputs created by the Coordinator. The
Coordinator also verifies other participants' cleanup. If an assignment permits
output creation but excludes deletion, name an authorized cleanup owner before
execution. Use the existing plan, assignment and handoff fields, without a new
manifest, ledger or repository state file.

## Clean after the last consumer

Remove disposable outputs as soon as verification, review and any named
downstream use no longer need them. Check this at phase handoff, before replacing
an output-producing agent, before the next Task and at final closeout. Do not
wait for the whole Epic to end. A phase handoff may retain an output needed by a
later phase of that same work.

Before deletion, verify that the creating process has settled, no participant
still uses the output, and the actual path remains within the declared owned
scope. Do not follow a symlink outside that scope or run a broad clean command
whose effects include existing files or another participant's outputs. Preserve
source, tracked deliverables, unrelated work and release payloads still needed
for verification or publication. Uncertain ownership or active use prevents
deletion and returns to the Coordinator for resolution.

Keep native runtime, review and recovery evidence under
[evidence residency](evidence-residency.md) and the producing tool's retention
contract. This guidance grants no sweep of shared caches, tool homes, managed
Jobs, installed generations or other repositories. Use their native owner and
separately applicable authority for any cleanup there.

## Retain only what still has a consumer

For each retained output, state its path, reason, next consumer or responsible
owner, and the event that ends retention. Retain only the files needed for that
purpose. A failed test may need diagnostics or a reproducer without needing its
entire build tree. Preserve original evidence and candidate bindings required to
interpret the failure.

Temporary reports stay available until the recipient has read them under the
[result handoff contract](review-result-handoff.md); reviewer-owned files keep
their selected route's cleanup permissions. Release-QA confirmation records and
their referenced evidence remain available through the owning release workflow's
reuse and recovery obligations. VM collection and export follow the Job owner's
lifecycle; this contract cannot shorten those obligations.

Before retiring an agent or crossing a Task boundary, the Coordinator verifies
retained paths and assigns any remaining cleanup to the receiving owner. A named
handoff with a concrete consumer and retention end condition permits continuation;
an unexplained leftover does not. When the condition ends, the responsible owner
cleans the output within the carried authority. On resume, recheck the path,
ownership and current users before acting on an earlier cleanup instruction.

## Report cleanup separately from check results

Return the removed outputs, retained paths with their reason, owner and end
condition, and any failed or uncertain cleanup with its next owner. Use existing
Executor `results`, `evidence`, `gaps` and `next_owner` fields and Coordinator
checkpoints or the workflow's existing result channel. Keep runtime paths out of
tracked execution records. Report reclaimed space only when actually measured.

The Coordinator verifies cleanup from the owned output paths and actual results;
a clean Git status alone is insufficient. An unresolved cleanup failure or
unexplained leftover blocks the next Task and successful workflow completion.
Preserve the check's actual exit and verdict separately: a passing test does not
prove cleanup, and failed cleanup does not rewrite a passing test as failed.
Cleanup alone does not require another test or review unless it changes a
required input, deliverable or evidence dependency.

At an ordinary stop, perform only authorized cleanup after active producers and
consumers have settled, retaining what recovery needs. An explicit emergency stop
or instruction to preserve state stops cleanup too; report the outstanding paths
without further deletion. Resume only within the current authority.
