# Publication Recovery

Read this reference only when the intended version already has a conforming local release commit or any remote `main`, publication-remote annotated tag, or hosted Release publication state to reconcile.

Recovery is stateless. Reconstruct it from current Git and hosting objects plus exact prior QA, QA-binding, QA reuse-attempt, and release-gate evidence still present in the active conversation or supplied by the user. Never create `.aquarium`, a tracked marker, or a `/tmp` resume manifest. If the direct-QA candidate SHA, release-basis candidate SHA, QA binding, exact reuse-attempt fact, or gate-bound release commit SHA is unavailable, classify recovery as `unproven` and stop `INCOMPLETE`; do not rerun release QA or infer success from a commit title.

Resolve and independently verify:

- the intended version and conforming `[REL] Release v<version>` commit, its sole release-basis parent, and its repository-authorized metadata-only delta;
- either a direct release-qa `PASS` for the release-basis candidate, or one explicitly approved QA-neutral binding from the direct-QA candidate to its sole direct-child release-basis candidate under [gate-convergence.md](gate-convergence.md);
- the exact zero-or-one reuse attempt and release-gate evidence bound to the release commit;
- current local and live remote `main` SHAs plus the verified remote relationship to the release-basis candidate;
- publication-remote target tag absence or an annotated publication-remote tag whose peeled target is the release commit; and
- hosted Release absence or its exact tag, resolved target commit, draft state, and prerelease state.

Send only those bounded facts as one `aquarium-release-publication-observation/v4` JSON object through non-expanding stdin to `scripts/inspect_publication_state.py`. Do not interpolate observations into a shell command.

The object contains these bounded facts:

- `version`, `release_basis_candidate_sha`, and `release_commit` (`sha`, `parent_sha`, `title`);
- `qa_evidence_candidate_sha`, `qa_evidence_relation_to_release_basis` (`equal` or `direct_parent`), `qa_binding` (`exact` or `approved_qa_neutral_descendant`), and `qa_reuse_attempt` (`0` or `1`);
- `gate_evidence_release_commit_sha`, `local_main_sha`, `remote_main_sha`, and `remote_main_relation_to_release_basis` (`equal`, `ancestor`, `descendant`, or `diverged`); and
- `tag` (`state`, `annotated`, `peeled_sha`) describing the live publication-remote tag, and `hosted_release` (`state`, `tag`, `target_sha`, `draft`, `prerelease`). A local-only tag is remote `absent` and must not suppress `create_and_push_tag`; a draft or prerelease hosted object is a conflict, never a completed stable Release.

For `exact`, require the evidence and release-basis SHAs to match, relation `equal`, and attempt `0`. For `approved_qa_neutral_descendant`, require distinct SHAs, relation `direct_parent`, and attempt `1`. The helper checks this closed structural binding; the handler remains responsible for proving the Git relationship, retained QA record, first-and-only reuse-attempt fact, non-distributed surface, semantic neutrality, and explicit approval before constructing the observation.

Compute the relation from the freshly queried live remote SHA and local Git objects immediately before every observation; inability to prove it without fetching stops as `INCOMPLETE`. Use `null` only for absent evidence or absent-object fields allowed by the schema.

The helper returns exactly one next action:

- `push_main` when remote `main` still equals or is a verified ancestor of the release-basis candidate;
- `create_and_push_tag` when both main refs match and the tag is absent;
- `create_hosted_release` when main and tag match and the hosted Release is absent;
- `verify_complete` when every object matches; or
- `stop` for `conflict` or `unproven` state.

Re-observe and rerun the helper immediately before each mutation and after it succeeds. Obtain the normal separate authority for the returned mutation; earlier authority does not survive a new invocation. Never recreate a matching object, skip an earlier missing step, or repair a conflict by rewriting or deleting published state.
