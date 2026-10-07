# Herdr migration

Use this contract to diagnose the selected review route and migrate Orca workflow
state. The upstream `$herdr` skill owns host setup and native control;
`$use-podway` owns session lifecycle. A migration plan grants only its explicitly
approved effects.

## Diagnose the selected route

Require Herdr only when the user selects Herdr or requests its migration
readiness. Mulgae, Independent Review and waiver checkpoints keep their own
prerequisites. Use the [Herdr catalog entry](tool-catalog.md#herdr) and
[supervision contract](herdr-supervision.md) to check CLI, server, upstream skill,
requested reviewer and caller context independently. CLI presence or version
does not establish server or reviewer readiness.

Before native session inspection or control, require `HERDR_ENV=1` in the
executing process and explicit caller context or returned IDs. Missing variables
in a tool shell can reflect an inheritance gap. Resume from the intended managed
pane or obtain the user's actual caller context; do not discover another client's
focused session or create a replacement backend.

Repository setup diagnoses managed sources from the canonical Git root using
the exact installed plugin's inspector:

```text
python3 <plugin-root>/skills/dev-setup/scripts/inspect_tools.py --repository <git-root> --include-podway
```

Use this setup probe for an authorized diagnosis or update, not at every workflow
step. Routine session observation remains with `$use-podway`. Inspect the Git
target, existing index and unrelated work before proposing repository changes.

## Distinguish source and snapshot readiness

| Observed state | Supported handling |
| --- | --- |
| Current canonical source | Verify native validity, the complete handler contract and the selected route. |
| Recognized prior canonical source | Retain its exact identity and update explanation. Consume the inspector's separate handler-compatibility and selected-route results; recognized provenance does not establish Herdr eligibility. |
| Valid same-ID customization | Preserve the local bytes. Compare its complete handler contract and selected route; propose any necessary change as an exact diff. |
| Native-invalid, handler-incompatible or unqualified source | Report the distinct gap. Do not overwrite it or dispatch a review merely because its ID matches. |
| Existing session snapshot | Inspect its immutable declarations through native observation. New source bytes do not change that snapshot. |

The inspector recognizes a bounded set of prior-source identities. Known Task
and Design sources may also have verified generic handler compatibility; consume
that result separately from route eligibility and the current caller's complete
contract. A historical snapshot may retain a working peer route while lacking
Herdr or a newer handler branch. Admit only the route actually supported by that
snapshot and the current caller. Preserve old route names in historical evidence;
never relabel Orca as Herdr or revive retired `native-codex` dispatch.

## Handle legacy checkpoints and workers

| Existing checkpoint or session | Safe continuation |
| --- | --- |
| Completed Orca review | Retain the original report, identity, findings and dispositions. Check its target applicability and consumed assessment ordinal separately; do not rerun it merely to rename the route. |
| Incomplete Orca checkpoint with no active worker | Record the retired-route prerequisite gap. Use an explicitly authorized supported peer route or eligible waiver, or stop. The pending ordinal remains unconsumed. |
| Failed or incomplete checkpoint with a terminal worker | Verify the worker's authoritative terminal state through its owner or the user's supplied evidence. Preserve native references and findings before an authorized transition. The new package never invokes Orca to settle it. |
| Active or uncertain legacy worker | Leave the operation intact and start no replacement review. Its owner must establish a safe state before a route change or successor. Missing output is not proof of termination. |
| Snapshot cannot record the requested route, evidence or acceptance | Leave unsupported decisions unset. Use its supported stop path and separately authorized native lifecycle settlement before an eligible successor. Epic delegation cannot satisfy a user-only gate. |
| Disposed terminal session with a verified handoff | Re-observe it and use only its currently eligible successor template under the approved plan. Preserve its history through native archival. |

Carry findings, disposition evidence, goal revision, assessment kind and
remaining correction authority across any transition. A completed assessment
consumes its ordinal even when it reports findings; failed or incomplete work
does not. A new session or route does not reset that history or the remediation
budget. Follow the [routing contract](review-routing-contract.md) for explicit
`resume-current`, `switch-route`, `waive` or `stop` decisions.

## Update a repository under separate authority

Prepare a `$aquarium:dev-setup` proposal for the target repository naming the exact
installed plugin, current source identities, intended diff, preserved
customizations and session state. Updating this repository grants no rollout to
another checkout and no host installation, upstream skill replacement, server
restart or Orca removal. Those effects retain their native owners and separate
authority.

Apply only approved managed-source or guidance changes. Follow the selected
[backup policy](tool-catalog.md#choose-a-backup-policy-for-existing-state):
verify the disclosed backup and restoration path when backups are selected, or
disclose the exact loss and recovery boundary when proceeding without backups.
Preserve custom files outside the approved replacement and all runtime history.
Compare the installed assets with the intended source bytes and stable IDs,
then check each changed Procedure:

```text
podway procedure check <procedure-file> --warnings-as-errors --json
podway procedure preview <procedure-file> --json
```

Record the native preview's canonical digest separately from the source-file
hash. Verify the complete handler and selected-route contract through the
inspector. Native validation alone does not qualify Herdr, and source replacement
applies only to later sessions.

After setup hands the verified source update back, the owning workflow handler
uses `$use-podway` for its separately authorized successor. When that successor
follows a disposed terminal session, the handler executes its fresh plain `start`
template. Podway atomically archives the predecessor and creates the prepared
successor; re-observe its source snapshot and perform the separate fenced `begin`.
Do not reset first or invent a replacement flag. Preserve
a prepared or running session unless its exact lifecycle change is authorized.

## Verify and recover

Verify source identity, native Procedure acceptance, handler and route readiness,
preserved customization bytes and existing snapshot/history independently.
Actual Herdr qualification additionally requires the selected host context,
reviewer identity, observed activity and complete result under the supervision
contract. Structural checks cannot prove these or host skill discovery.

On a rejected or partial update, inspect the actual remaining bytes and session
state and stop at the affected gap. Under an approved rollback scope, restore
sources from a verified backup or the exact prior bytes already in Git history,
then repeat the affected checks. Without either source, report the recovery gap;
do not claim that uncommitted customizations can be restored. Restoring a file
does not roll back a live worker or session. Escalate host readiness to the
upstream Herdr owner, session settlement to `$use-podway`, and an unsupported checkpoint to the
workflow owner and user. Never delete history or choose another route as recovery
without its required authority.
