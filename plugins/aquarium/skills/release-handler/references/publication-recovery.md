# Publication Recovery

Read this reference only when the intended version already has a conforming local release commit or any remote `main`, annotated tag, or hosted Release publication state to reconcile.

Recovery is stateless. Reconstruct it from current Git and hosting objects plus exact prior QA and release-gate evidence still present in the active conversation or supplied by the user. Never create `.aquarium`, a tracked marker, or a `/tmp` resume manifest. If the prior QA candidate SHA or gate-bound release commit SHA is unavailable, classify recovery as `unproven` and stop `INCOMPLETE`; do not rerun release QA or infer success from a commit title.

Resolve and independently verify:

- the intended version and conforming `[REL] Release v<version>` commit, its sole parent, and its repository-authorized metadata-only delta;
- the prior `PASS` candidate SHA equal to that parent and release-gate evidence bound to the release commit;
- current local and remote `main` SHAs;
- target tag absence or an annotated tag whose peeled target is the release commit; and
- hosted Release absence or its exact tag and resolved target commit.

Send only those bounded facts as one `aquarium-release-publication-observation/v1` JSON object through non-expanding stdin to `scripts/inspect_publication_state.py`. Do not interpolate observations into a shell command.

The object contains `version`, `qa_candidate_sha`, `release_commit` (`sha`, `parent_sha`, `title`), `qa_evidence_candidate_sha`, `gate_evidence_release_commit_sha`, `local_main_sha`, `remote_main_sha`, `tag` (`state`, `annotated`, `peeled_sha`), and `hosted_release` (`state`, `tag`, `target_sha`). Use `null` only for absent evidence or absent-object fields allowed by the schema.

The helper returns exactly one next action:

- `push_main` when remote `main` still equals the QA candidate;
- `create_and_push_tag` when both main refs match and the tag is absent;
- `create_hosted_release` when main and tag match and the hosted Release is absent;
- `verify_complete` when every object matches; or
- `stop` for `conflict` or `unproven` state.

Re-observe and rerun the helper immediately before each mutation and after it succeeds. Obtain the normal separate authority for the returned mutation; earlier authority does not survive a new invocation. Never recreate a matching object, skip an earlier missing step, or repair a conflict by rewriting or deleting published state.
