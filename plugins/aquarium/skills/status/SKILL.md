---
name: status
description: "Report Aquarium production setup history and freshness, refresh official release metadata on request, or forget one exact recorded repository after approval. Use only when the user invokes $aquarium:status or asks for Aquarium production setup status."
---

# Production Setup Status

Use the installed `aquarium-status` runtime to report the local production setup
ledger. This skill does not run setup, infer live tool health, repair a checkout,
or remove records implicitly.

## Establish Runtime Readiness

First run the `dev-setup-global` inspector scoped to `aquarium-status` so its
bundled inspector compares the installed and current packaged identities. Run
`aquarium-status show --format json` only after that result is `current`.
Report any other exact diagnosis and route installation, update, or repair to a
separate `$aquarium:dev-setup-global` action. An unsafe or unknown launcher
requires explicit owner resolution or removal; it is never a replacement
target. Do not work around the managed runtime by importing the plugin cache
directly.

## Report Status

- Use `show --format text` for an ordinary human report and `--format json` when
  structured evidence is useful.
- Add `--refresh` only after disclosing the read of the official GitHub latest
  Release endpoint and when the user requested current release freshness.
- Add `--source-root <absolute-path>` only for an explicitly named Aquarium
  source checkout.
- Describe a recorded attempt as setup history, not current tool health.
- Keep configuration freshness, release freshness, live root identity, and
  `aquarium-dev` enrollment independent. Preserve partial-report warnings.

## Forget One Exact Row

Deletion is destructive and requires an explicit approval for the exact current
row.

1. Run `aquarium-status show --format json` and select one exact canonical
   `git_root`. Never scan for moved or deleted repositories.
2. Present the full selected row and current `ledger.file_revision` and
   `row_revision`. Remove only the derived `root_state`,
   `configuration_freshness`, and `enrollment` fields, then compute the row
   SHA-256 with the specification's canonical-JSON algorithm: NFC-normalize all
   strings, sort object keys, use compact UTF-8 JSON with no ASCII escaping, and
   append one newline. Explain that deletion removes only local history and
   cannot be reconstructed except from an external backup or Git history of a
   separately recorded report.
3. Obtain approval naming that exact row. Re-run JSON show after approval.
4. If any displayed field, file revision, row revision, or digest changed,
   invalidate approval and stop.
5. Invoke `forget` with `--git-root`, `--if-file-revision`,
   `--if-row-revision`, and `--if-row-sha256`. Report the receipt. A conflict
   requires a new show and new approval; never weaken the preconditions.

Do not edit the YAML ledger, runtime receipt, selector, or launcher directly.

## Report

Lead with the status or exact deletion result. Include warnings, observations
that were not checked, network access performed, and any runtime or row conflict.
State explicitly that reporting did not run setup and that forgetting did not
change repository files, enrollment, tools, commits, or publication.
