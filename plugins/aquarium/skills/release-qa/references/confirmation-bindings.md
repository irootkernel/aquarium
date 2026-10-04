# Confirmation execution bindings

Keep the full-pass record and confirmation manifest unchanged. Fresh execution changes the fixture instance and candidate identity while preserving the retained scenario conditions.

Rebind each normalized absolute path beneath the full evidence root to the same relative path beneath the confirmation root. Apply this binding to string values in the submitted `controlled_environment`, including values inside lists and objects. Replace a `source_sha` value equal to the full-pass candidate with the confirmation candidate. Baseline identities and other conditions remain unchanged.

## Native helper fixtures

A retained scenario may exercise a candidate helper that requires evidence roots directly beneath physical `/tmp`. Its frozen `controlled_environment.native_helper_roots` declares those fixture roots. Only these declarations authorize external fixture rebinding; other paths outside the full evidence root remain unchanged.

Use `confirmation_native_roots(environment, full_root, confirmation_root)` from `scripts/manage_release_qa.py` to derive the replacement paths. Each distinct declared root maps to a sibling named `release-qa.native-<sha256>`, where the digest covers the helper's canonical JSON bytes for `[confirmation_root, retained_root]`. This preserves shared roots across scenarios and derives the same bindings from the claim-bound confirmation root and frozen inventory. A declaration equal to the full evidence root uses the main root binding.

Before `begin-confirmation`, create each derived directory exclusively with mode `0700`. An existing path blocks preparation; do not reuse, clean or overwrite it. Assign the derived roots to the owning worker along with its main fixture. The helper checks that every derived root exists as a private physical directory during begin and settlement. A missing, public or symlinked directory blocks admission or settlement.

In the submitted environment, replace declared root values and their descendants with the derived paths, preserving each relative suffix. The helper requires these exact replacements and rejects stale paths, reordered root roles, undeclared substitutions and changes to other conditions. Leave retained roots untouched. Native fixture outputs may live in these derived sibling roots; copy the bounded regular evidence files into the main confirmation evidence root for submission.

## Replay instructions and provenance

Preserve the frozen procedure text as the retained replay instructions. Execute them with the confirmation candidate and fresh fixture paths. References to previous observations and construction scripts still identify retained evidence. Record actual commands and environments in the new evidence. The frozen worker label identifies the previous executor; capture the fresh worker's identity separately in execution evidence.
