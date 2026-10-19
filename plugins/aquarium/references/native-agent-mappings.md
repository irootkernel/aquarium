# Native agent mapping profiles

## Status and scope

These v1 profiles serve declared formal delegation and historical records.
Ordinary work follows the [v3 contract](ordinary-agent-orchestration.md) and does
not require native qualification or a private executor-record collector. The
assignment preparer and renderer select the ordinary branch for
`aquarium.assignment/v3`: preparation validates and copies supplied assignment
content without reading a role snapshot; rendering returns
`aquarium.prepared-dispatch/v3` with operative `dispatch_text`. The retained
[v2 contract](ordinary-agent-orchestration-v2.md) routes `aquarium.assignment/v2`
to `aquarium.prepared-dispatch/v2` separately. Ordinary preparation creates no
accepted-task, configuration or result binding. Existing v1 inputs, outputs and
digest encodings below remain unchanged; formal binders reject ordinary v2 and v3.

These profiles describe the public surfaces and qualification obligations for
`aquarium.codex-native/v1` and `aquarium.claude-native/v1`. Local preparation and
delivery mapping establish only their declared binding domains. Required
delegation needs native qualification applicable to the exact operative role
snapshot, accepted assignment, complete result and supported recovery path.
Earlier qualification remains bound to its original inputs; changed operative
bytes need fresh acknowledgement. Read the
[formal v1 contract](formal-agent-orchestration-v1.md) and the installed `use-podway`
delegation contract for acceptance obligations. Source declarations do not
activate released managed copies or change an admitted session.

Pin the actual backend, host version, public schema, and integration revision in
qualification evidence. The inspected reference versions are Codex CLI 0.162.0,
Claude Code 2.1.295, and Claude Agent SDK 0.3.295. A matching version or schema
alone does not establish actual dispatch or acceptance. Hosted Responses agents
and local Codex app-server subagents require separate native provenance.

## Common mapping

| Acceptance field | Producing source and acceptance condition |
| --- | --- |
| `binding_ref`, `role_ref` | Exact declared binding and role resolved by the integration; compare them with the current package. |
| `role_snapshot_digest` | Digest of the complete immutable role instruction bytes and resolved instruction dependencies, with an inventory of their exact content. |
| `adapter_id`, `adapter_version`, `primary_host` | Actual executing integration identity, revision, and verified Primary host. Profile names are not runtime adapter identities. |
| `scope_kind`, `scope_ref`, `supervisor_ref`, `worker_ref`, `task_ref` | Correlated native scope, supervisor, agent, and accepted task records from the chosen host profile. |
| `agent_configuration_digest` | Complete accepted configuration bytes under the pinned integration encoding, including the role/dependency binding and applicable resolved execution controls, proven by supported durable native acknowledgement. |
| `accepted_task_digest` | Exact native-accepted task input, including node instructions and full selected evidence, bound to its acknowledged dispatch. |
| `result_digest` | Complete immutable delivered result bound to the accepted task and final native result identities. |
| `rounds_used` | Durable integration accounting of accepted assignment and feedback rounds linked to their native acknowledgements and results. |
| `worker_disposition` | Native settled state after explicit Primary acceptance: `idle` for retain or `released` for release, as declared. |

Use the installed Podway contract for package, session, attempt, revision, and
receipt fields. It computes `accepted_items_digest`. Those identities cannot
substitute for external task, configuration, or result identities.

Retain exact bytes and encoding for each digest domain. Pin a deterministic
encoding for structured values in the implementation revision; do not change it
mid-operation or normalize instruction text. A native raw digest is optional
when supported acknowledgement proves the exact accepted bytes. Saving a client
request or computing its digest alone does not prove native acceptance.

### Bind an inline role configuration

A mapping can supply the complete role and resolved dependencies as operative
instructions in the assignment instead of loading a separate native role file.
Pin the dispatch encoding and retain the exact role bytes, their inventory, and
the accepted assignment containing them. A base64 attachment alone does not show
that the content was supplied as instructions; the encoding must establish that
relationship.

Compare the dispatched assignment with the complete native-accepted input. Bind
applicable resolved execution controls through supported acknowledgement or
documented inheritance from acknowledged parent and child records. Compute a
separate configuration digest over that role snapshot and those controls. Keep
the role, configuration and task digest domains distinct. This route does not
prove that another native role definition or disk configuration was applied.
Requested settings, a child's acknowledgement sentence, and current settings
read after the task cannot replace the applicable native records.

### Prepare local assignment input

The caller can use
[prepare_assignment.py](../skills/goal-evaluator/scripts/prepare_assignment.py) with
`--source-root <absolute-source-directory> --input <request.json-or-dash>`.
The source directory contains the explicitly resolved role, dependencies and
selected evidence; a caller-owned disposable bundle can hold resources from
different approved sources. The helper preserves their exact bytes, rejects
symlinks, escapes and duplicate paths, and returns a self-contained assignment.
It performs no native dispatch, acceptance or runtime mutation.

The `aquarium.assignment-request/v1` input contains `role.path`,
`role.dependencies`, and a `node` object with `objective`, `purpose`,
`instructions`, `canonical_sources`, `context`, `selected_evidence`,
`permitted_effects`, `deliverables`, and `success_criteria`. Context contains
nonempty reference strings for `work_identity`, `goal_ref`, `goal_revision`,
`target`, `base`, `procedure`, and `node`; these are caller assertions, not native
wire fields. Effects contain `allowed` and `excluded` lists. Selected evidence
and dependencies are explicit relative file paths; source applicability and
dependency completeness remain the caller's responsibility.

The output's `local_prepared_role_snapshot_sha256` and
`local_prepared_assignment_sha256` hash compact, sorted-key ASCII JSON without
the CLI's final newline. File content is retained as base64 without newline
normalization. These local preparation digests cannot substitute for accepted
configuration or task digests. The integration still needs native acknowledgement
of the dispatched bytes. The Judge reads the resulting input and never runs this
preparation helper itself.

### Render operative instructions

[render_dispatch.py](../skills/goal-evaluator/scripts/render_dispatch.py) accepts
`--input <preparation.json-or-dash>`. It verifies the prepared domains, file
inventories, sizes and hashes, then supplies role and dependency text as operative
instructions. It includes the complete node assignment and selected evidence as
task data. File bodies retain their original UTF-8 bytes; framing newlines are
separate. Non-UTF-8 content is rejected. The output's
`local_dispatch_input_sha256` hashes the canonical JSON string containing the
dispatch text, rather than its raw UTF-8 representation. Rendering performs no
dispatch and establishes no native acceptance.

### Capture Codex thread records

[read_codex_thread.py](../skills/goal-evaluator/scripts/read_codex_thread.py) accepts
`--socket <existing-absolute-Unix-socket> --thread-id <actual-native-id>`.
It connects to that explicit existing WebSocket endpoint, initializes one client,
and issues `thread/read` with `includeTurns: true`. It does not discover sockets,
start a server, create or resume a Primary, or change configuration.

The `aquarium.codex-thread-capture/v1` output retains initialization and read
request/response objects. Pass `thread_read.response.result` into the mapper's
`parent_read` or `child_read`. Every returned turn must have full item content;
paginated history is accepted when the hydrated result is complete. Protocol,
identity, native RPC and incomplete-history failures produce bounded errors.
The client uses one overall deadline and validates WebSocket framing, UTF-8 and
complete JSON without an Aquarium history-size ceiling or truncation. Capture
from an explicit endpoint does not authenticate historical journals or establish
acceptance and settlement.

### Map a native delivery

[map_native_delivery.py](../skills/goal-evaluator/scripts/map_native_delivery.py)
accepts `--input <request.json-or-dash>`. Its
`aquarium.native-delivery-request/v1` contains `profile`, `expected`, and
`records`. Expected identities are `scope_ref`, `supervisor_ref`, `worker_ref`,
and ordered `rounds`, each with `dispatch_ref`, `task_ref`, and exact text `input`.
The caller must collect authentic complete records through supported readers.
The helper checks their correlation; it cannot authenticate supplied JSON.

The delivery-only `aquarium.codex-app-server-delivery/v1` profile consumes
`parent_read` and `child_read` public `ThreadReadResponse` objects for CLI 0.162.0.
It supports complete legacy history, text-only spawn and feedback assignments,
and completed final-answer turns. The
`aquarium.claude-agent-sdk-delivery/v1` profile consumes an SDK `invocation` and
`delivery` for one synchronous initial Agent call. It binds the tool-use ID,
session, returned agent ID, echoed prompt and full structured Agent output.
The invocation's `stop_reason` may be null or `tool_use`; neither proves completion.
Require the exact correlated successful tool result and complete structured
output, preserving the prompt's final newline. Continuation and harness metadata
remain opaque result fields and do not establish acceptance or settlement.
Background initial delivery and hosted Responses need separate mappings.
Public-history recovery preserves its own conversation projection; it cannot
reconstruct the original structured AgentOutput.

The `aquarium.claude-agent-sdk-rounds-delivery/v1` profile maps an initial Agent
delivery and one serialized `SendMessage` feedback delivery. Its `initial`
record retains the original `invocation` and `delivery`; its single `feedback`
record retains the SendMessage pair, ordered native `events`, `forwarded_result`
and complete `public_history`. The feedback `task_ref` is the actual native
`run_id`; `task_id` retains the actual agent identity. Exact `message` and
`task_started.prompt`, successful `resumedAgentId`, completed task events and
the matching public terminal UUID must correlate. Wrapped child input and
legacy SendMessage fields remain opaque.

Feedback uses `aquarium.claude-feedback-result/v1` inside its result domain:
the complete public child slice after the initial terminal through the matched
feedback terminal, full completion events, SendMessage delivery and forwarded
provenance. This preserves the initial complete AgentOutput as a separate round;
it does not reconstruct another AgentOutput from a summary or token totals.
Public terminal and forwarded content/model must agree within each run. Native
fallback can change runtime models between runs. Creation controls remain
separate from per-run model/background evidence. Pending or ambiguous events,
unmatched history, incomplete results and extra rounds remain unmapped;
reported completion and empty background snapshots do not prove settlement.

The separately versioned `aquarium.claude-agent-sdk-rounds-delivery/v2` profile
retains initial delivery and every serialized feedback assignment. Each feedback
has its own exact accepted prompt, acknowledgement, run, result domain and full
immediately preceding history prefix. Creation controls remain immutable while
task-bearing configuration envelopes change with their acknowledged assignments.
Tool-use/result pairs must correlate completely; original nested AgentOutput is
retained separately and never reconstructed from wrapper prose.

This helper profile is implemented but needs actual host qualification before
required placement activation. Preserve qualified original single/two-round v1
records and their digest domains. Complete logical-lifetime accounting may span
more than thirty-two assignments across different placements; Podway's native
`max_rounds=32` applies to its current placement/package, not the whole Judge
lifetime. Unknown dispatch, incomplete history, pending results or unverified
current target/descendant settlement require reconciliation without redispatch.

The `aquarium.claude-agent-sdk-hooks-delivery/v1` profile retains supported
SDK PreToolUse and PostToolUse records as their own native domain. Its
`records.rounds` list has one entry per assignment. Each entry contains the
original model `invocation`, complete `pre_hook` and `post_hook` captures,
original target/run `events`, cumulative `forwarded_history`, and
`nested_deliveries`. Feedback entries also retain their original `public_history`
capture with `session_id`, `target`, `agents`, `children` and `primary`.
An initial public-read snapshot is not fabricated when none was captured.

A hook capture preserves its original collector envelope, callback tool-use ID
and complete input. PreToolUse retains its complete response. The timestamped
collector uses `at`, `toolUseID`, `input` and, for PreToolUse, `output`. The other
qualified collector uses `event`, `toolUseId`, `input` and `callbackOutput`, with
its original additional metadata. Never manufacture a capture timestamp. When
PreToolUse has none, `invocation_projection` retains the original public parent
message with the matching UUID, session, caller, message ID, model, unchanged
tool content and native timestamp. Its public stop reason and usage projection
remain separate from the original SDK message. Serial dispatch must follow the
actual prior task completion time. A missing PostToolUse timestamp does not
establish completion or elapsed time. Correlate the original model
request with the PreToolUse requested input. A returned `updatedInput`, when
present, must equal the PostToolUse effective input. Require the exact effective
assignment in the native task start and original AgentOutput or SendMessage
acknowledgement. The task reference is the actual `run_id` for every round;
`task_id` remains the actual Worker identity. Do not rewrite an assistant message
to make a hook-applied assignment resemble a legacy invocation.

The SDK stream and public reader are different projections. Preserve both
without changing message bodies or stop reasons. A public reader may omit a
streamed tool reply or expose a completed terminal that the initial stream did
not forward. Correlate original UUIDs, content, model and timestamps across
those sources, preserving each immediately preceding prefix. Every tool use
needs its original reply. Nested Agent calls need their original invocation,
PreToolUse and PostToolUse captures with the complete structured AgentOutput;
a public handback cannot reconstruct it. Initial completion uses the original
AgentOutput and native completed events. Feedback completion requires its own
public terminal, matching original forwarded UUID and completed task events.
Parent completion alone does not establish child completion.

Each `aquarium.claude-hooks-result/v1` result preserves the complete original
operation and predecessor result digest. The helper can correlate supplied
records; the integration must establish their authenticity and any completeness
limits. Current settlement, writer and descendant quiescence, physical response
loss recovery and Podway acceptance remain separate qualification domains.

The `aquarium.codex-collaboration-spawn-delivery/v1` profile consumes `journal`,
`parent_read`, and `child_read`. Retain the complete `spawn_agent` request before
dispatch and capture the actual successful response from that invocation. The
request contains `task_name`, `fork_turns`, and `message`; explicit model/effort
selections require `fork_turns: none`. Join the response's returned canonical path
to a unique native `subAgentActivity` creation record, take the actual child ID
from `agentThreadId`, and verify child source, parent and session provenance.
Require one full completed initial child turn and its complete final messages.
This profile permits `historyMode: paginated` when all returned items are full.
Feedback, interactions, additional turns and missing successful responses require
reconciliation. Never backfill a historical journal from a result or a matching
path.

The `aquarium.codex-collaboration-rounds-delivery/v1` profile extends that route
with serialized feedback to the same idle agent. Its `initial` record retains
the preparation, journal and complete parent/child reads. Each `feedback` record
retains its preparation, exact `target` and `message` request, captured
`feedback_completion_output_utf8`, and complete reads before and after dispatch.
Capture the request before calling `followup_task` and the actual completion
output afterward. A correlated completed call can return an empty string;
omitting the completion field leaves acknowledgement unverified.

Each round requires an idle completed prior child history, the same native
worker, unchanged prior turns, one new parent interaction and completion, and
one full completed child turn. The mapper uses the actual turn ID from the
child record. It does not derive IDs from completion labels or count inference
turns as supervision rounds. Missing acknowledgement, active-turn feedback,
changed history or ambiguous linkage requires reconciliation without redispatch.

The separately versioned `aquarium.codex-collaboration-spawn-delivery/v2`
and `aquarium.codex-collaboration-rounds-delivery/v2` profiles pin the observed
retained Primary `cliVersion=0.162.0` and child `cliVersion=0.162.1` combination.
They keep the same original journal, complete read, ancestry and serialized
completion requirements, with separate digest domains. A different version
combination needs its own qualification. Existing `v1` domains remain pinned to
`0.162.0` and unchanged.

A `v2` feedback target may be the acknowledged canonical agent path or its exact
final path segment under the correlated parent and child. Preserve that actual
request string in the task domain. Do not silently rewrite a supported relative
alias into a canonical path or accept another path, ambiguous alias or changed
child ancestry. Native child turns can lack a user-message echo; the original
pre-dispatch request, successful completion and exact native operation linkage
remain necessary. Never reconstruct a missing journal from history.

In the initial-spawn profile, the accepted task input domain contains the
complete acknowledged spawn request. Each serialized feedback task domain
contains the exact acknowledged target/message request. In both cases, the
operative text is `input.message`. `creation_controls` separately retains the
initial native resolved model/effort and creation source identity across both
routes. A missing prompt echo does not invalidate the correlated
successful acknowledgement; a saved request alone does not establish it.

The `aquarium.native-delivery-mapping/v1` result retains request and record
digests, exact accepted task domains, task/result digests, native result
references, observed round count and reported status. Digests use compact,
sorted-key ASCII JSON without a trailing newline. A task domain binds the native
input to profile, scope, worker, dispatch and task identities. A result domain
binds complete delivered messages or Agent output to that task digest. Legacy
Claude task input contains its acknowledged prompt. The hook profile
contains the complete effective tool input and keeps the original request and
hook response separately; submitted controls require native acknowledgement.

Every result keeps `acceptance_ready: false` and `redispatch_allowed: false`.
Successful correlation leaves role/configuration acknowledgement, complete
supervision accounting, explicit Primary acceptance, settlement and durable host
recovery unresolved. Reported native status is not settled disposition. The CLI
exits zero for a mapped delivery and two for rejection or reconciliation; malformed
JSON produces an error without a partial mapping. Preserve the original request
and the returned recovery references. This output contains assignment content
and follows the [evidence-residency contract](evidence-residency.md); it is not a
Podway acceptance document.

### Bind a prepared delivery

[bind_prepared_delivery.py](../skills/goal-evaluator/scripts/bind_prepared_delivery.py)
accepts `--input <binding-request.json-or-dash>` containing
`aquarium.prepared-delivery-request/v1`, `preparation`, and `mapping_request`.
It reruns rendering and native correlation rather than trusting a supplied
mapping result. It supports the journal-backed Codex initial-spawn and serialized
feedback profiles and
requires the exact rendered message and nonempty native model/effort values.
For serialized feedback, the top-level `preparation` describes the final
assignment; `records.initial.preparation` and each feedback record retain their
own preparations. All must retain the same complete role snapshot, and each
rendered message must match its acknowledged request. The output retains each
round's task/result binding as well as the final delivery.

The role digest retains the preparer's complete role snapshot domain. The
`aquarium.accepted-agent-configuration/v1` domain contains that snapshot,
acknowledged fork policy, native resolved model/effort, creation provenance and
accepted-task binding. This pins the applicable configuration for the selected
spawn route; it does not inventory hidden host instructions or establish that a
separate disk role was loaded. Additional selected controls require their own
acknowledgement before extending this profile.

The output retains the full role/configuration/task/result domains and distinct
`sha256:` bindings. It still reports caller-supplied unverified authenticity,
`acceptance_ready: false`, and `redispatch_allowed: false`. The collector must
establish authentic records, pre-dispatch journal capture and dependency
completeness. The integration and Primary still own lifetime accounting,
explicit result acceptance, descendant settlement, current Podway package/context
binding and durable host qualification.

### Bind a prepared Claude delivery

[bind_claude_delivery.py](../skills/goal-evaluator/scripts/bind_claude_delivery.py)
accepts `--input <binding-request.json-or-dash>` containing
`aquarium.claude-prepared-delivery-request/v1`, `preparation` and `mapping_request`.
It reruns rendering and the synchronous Claude SDK delivery mapping, requiring
the exact operative prompt in both the native invocation and completed output.
The complete role snapshot retains its preparation digest.

For the serialized Claude rounds profile, `preparation` is an ordered two-entry
list. The binder independently verifies both preparations, requires identical
complete role snapshots, and compares each operative prompt with its native
acknowledgement. It retains both result domains and binds the final task/result.
Initial creation controls stay separate from feedback runtime evidence; Primary
acceptance, lifetime accounting, descendant settlement and Podway context remain
integration obligations.

The general `rounds-delivery/v2` and `hooks-delivery/v1` profiles use one
independently rendered preparation per serialized assignment. Every preparation
must retain the same complete operative role snapshot. The hook binder compares
each rendered assignment with its acknowledged effective input, preserving the
requested model input separately. Its
`aquarium.claude-hook-agent-creation-configuration/v1` domain retains the complete
role snapshot, acknowledged creation controls, native resolution and original
creation hooks. Each `aquarium.claude-hook-assignment-configuration/v1` domain
binds that creation configuration to its own accepted task, actual runtime and
original assignment hooks. The current top-level binding selects only the last
round; all earlier configuration, task and result domains remain intact.

Native hook context is caller context, not proof of hidden child controls.
Source checks and replaying retained native records establish correlation only;
combined native recovery qualification and installed workflow activation retain
their own gates.

The `aquarium.claude-accepted-agent-configuration/v1` domain binds that snapshot,
the acknowledged applicable Agent input controls, native source identities and
nonempty `AgentOutput.resolvedModel`. Requested model selectors remain separate
from resolved IDs. Effort is optional; `modelsUsed`, when present, retains its
native string-list type. The complete Agent output remains the result domain,
including optional fields. Finite nonnegative fractional durations are allowed;
counts remain integers.

This route requires explicit `run_in_background: false` and the built-in
general-purpose agent. Custom or fork definitions, isolation/worktree routes,
unknown controls and missing resolved model information require another
qualified mapping. Deprecated ignored controls remain recorded separately.
The host's other supported capabilities remain available. Synthetic tests verify
correlation and rejection behavior. Actual isolated Claude initial delivery and
serialized feedback have exercised Podway acceptance and retain settlement.
Successful binding retains the same authenticity, acceptance and redispatch
limits as the Codex binder; the integration establishes those remaining facts.

## Codex profile

Use actual app-server child records when that is the executing native backend.
Correlate parent `collabAgentToolCall` sender, receivers and item ID with child
`Thread.id`, `sessionId`, `parentThreadId`, its `source.subAgent.thread_spawn`
provenance, and `subAgentActivity.agentThreadId`. Bind the accepted assignment to
the child turn and persisted complete `userMessage` content, and the result to
that turn's terminal status and full final message items.

Recover persisted history through public `thread/read` with `includeTurns`, or
the supported turns/items readers. Exhaust pagination and require full item
content; summaries and truncated projections cannot prove the complete delivery.
Creation activity reports resolved model and effort. Settings responses and
`instructionSources` paths do not by themselves prove the exact loaded role and
dependency bytes. [App-server source contract](https://learn.chatgpt.com/docs/app-server).

For the separate hosted Responses backend, correlate `multi_agent_call` and
`multi_agent_call_output` using `call_id`, then preserve actual agent attribution
and complete delivered messages. Obtain the actual host's supported configuration
acknowledgement and durable recovery linkage before accepting. An available TUI
thread reader must demonstrate its complete child records and backend linkage;
its Primary thread ID alone supplies neither. [Hosted source contract](https://developers.openai.com/api/docs/guides/responses-multi-agent).

Verify retain through current native quiescence, including descendant work.
Archive, unsubscribe, interruption, and a completion label do not independently
prove release. Qualify the declared disposition; do not require release for a
retain placement or silently substitute retain for a release placement.

## Claude profile

Within an actual Claude Primary, correlate the `Agent` invocation's `tool_use.id`
with the returned `agentId`, its accepted `prompt`, and persistent subagent
messages. Bind SDK `session_id`, task events' `task_id` and `run_id`, and the
corresponding subagent `agent_id` to the correct invocation and delivery.
Completed Agent output supplies full `content`, prompt, status, and available
resolved model information. A task notification summary is insufficient.

Use public `listSubagents` and `getSubagentMessages` readers for persisted tasks
and results, exhausting their pagination. `Query.reinitialize()` can reconcile
the live background-task snapshot across a transport gap; that snapshot alone
does not prove that an uncertain dispatch never happened.

The pinned history readers return API-visible conversation projections and omit
the outer SDK `tool_use_result`. Preserve the original structured Agent output;
a mapping that recovers results from public history needs its own declared result
domain. Empty history does not prove that dispatch never happened. Historical
messages also do not establish current idle state or descendant quiescence.

Initialization and supported-agent information expose names, descriptions and
models, without acknowledging the full applied role configuration. Submitted
definitions and disk settings need a supported accepted-configuration binding.
The published [SDK package](https://registry.npmjs.org/@anthropic-ai/claude-agent-sdk/0.3.295)
owns the pinned public declarations. [Session storage](https://code.claude.com/docs/en/agent-sdk/session-storage)
can durably mirror records, but its opaque entries are not a private configuration
API. Use supported readers for interpreted evidence.

Current [subagent resume guidance](https://code.claude.com/docs/en/sub-agents#resume-subagents)
uses `SendMessage` to the actual agent ID or name. The inspected SDK Agent input
has no `resume` field. Qualify the actual feedback schema and durable delivery
acknowledgement rather than adopting an older example. Keep supervision rounds
distinct from inference turns, token totals and tool counts.

Verify retained quiescence from current task and descendant state after acceptance.
Cancellation does not establish release of a resumable agent. Starting an SDK
query or CLI session creates a Claude Primary; it is not a Claude child of a Codex
Primary and requires the applicable execution authority.

## Qualification and rejection

Both hosts have exercised actual result-read response withholding at an owned
client transport. Supported reads recovered identical complete public history
without redispatch. Claude recovery retains the original structured AgentOutput
separately because public history omits that outer result. Synthetic missing
acknowledgements establish rejection and reconciliation behavior only.

TASK-116 report-only native fixtures exercised four serialized assignments on
the same Codex child under the explicit `0.162.0` Primary / `0.162.1` child
profiles, and five on the same Claude Worker under the hook profile. The Claude
fifth assignment physically withheld one original successful SendMessage ACK
at the SDK-facing transport boundary after preserving it in an observer journal.
The original PostToolUse record, exact task start, completed native run and full
public terminal recovered the assignment without replay or redispatch. This
qualifies that SDK-facing feedback ACK boundary; initial Agent ACK loss,
inner-model ACK loss and Codex dispatch-response loss remain unqualified.

The Claude fixture's settlement evidence covers its known report-only tasks and
nested Agent, with original completion records, AgentOutput and SubagentStop,
and the owned CLI's observed exit and reaping after the fifth run. ListAgents
inside the original executor reported the direct Worker completed. An empty
ListAgents result from a later process describes that process's registry and
cannot establish historical Worker or descendant settlement. These bounded
fixtures do not qualify arbitrary active or outliving descendants, all required
Procedure placements, Podway acceptance, or installed candidate activation.
Retain those integration obligations and the original single/two-round evidence.

Before activation, demonstrate actual delegated Podway Action acceptance on both
host paths with complete package/input/configuration/result bindings, durable
acknowledgements, round accounting, and the declared settled disposition. Test lost
dispatch and result responses through the supported readers before redispatch.
Also test wrong role/configuration, task, candidate, attempt or goal bindings,
incomplete results, stale feedback, and unavailable required metadata.

Reject unsupported or ambiguous required provenance before submitting acceptance.
Keep the unresolved operation, exact requests, known identities and results for
reconciliation. Do not redispatch uncertain work, invent receipts, scrape private
state, switch Primaries, or perform required delegated work directly. Report the
missing surface and its actual integration or native-host owner. Mapping specs,
structural checks, role instructions, and synthetic protocol fixtures cannot
satisfy actual-host qualification.
