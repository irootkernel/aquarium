# Migrating review workflows to Herdr

Use this runbook when diagnosing or updating an Aquarium repository that still
has Orca-era managed sources, review evidence or session snapshots. The supported
target is one canonical local Git checkout. The installed Aquarium plugin owns
repository guidance; upstream Herdr owns its host runtime and reviewer control,
and Podway owns session lifecycle.

Qualification uses a local Herdr session on a host supported by the native
runtimes. The baseline is Apple Silicon macOS with Herdr v0.9.3; admit v0.9.3 or
newer, its installed upstream skill and a supported Podway runtime. Native
contracts own client/server and reviewer compatibility; this runbook adds no
upper version bound or host installation authority.

The [Herdr migration contract](../../plugins/aquarium/references/herdr-migration.md)
defines the read-only diagnosis, source and snapshot readiness, legacy-worker
handling, separately approved update, verification and recovery procedure.
Read it and the selected route's prerequisites before proposing a change.
Migration preserves custom Procedures and old evidence and refuses new Orca
dispatch. An update proposal must name the exact repository, installed plugin,
source diff and affected session; this runbook grants no installation, rollout,
host-tool removal or lifecycle mutation.

After an approved update, compare source bytes, run native Procedure checks and
confirm the complete handler and selected route. Existing snapshots remain
unchanged. A disposed terminal predecessor can be archived by an authorized
native successor start; an active or uncertain legacy worker needs settlement
through its owner before any replacement review.

Apply the selected shared backup policy before an approved source replacement.
Rollback can restore a verified backup or exact bytes already in Git history;
without either, report the recovery gap for lost local changes. Restore only
within an approved rollback scope and recheck readiness. A source rollback does
not settle a live operation. Escalate host gaps to upstream Herdr, session gaps
to `$use-podway`, and unsupported workflow decisions to the workflow owner and
user. Actual native review and host skill
discovery require separate observed qualification; static package checks do not
establish them.
