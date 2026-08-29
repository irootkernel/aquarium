# Deferred Feedback

This index owns small actionable findings intentionally postponed from current work. It is not a second roadmap, completion history, or runtime evidence store.

## DF-001: Bind the release confirmation claim immutably

- Actionable issue: `release-qa` creates its sole-attempt confirmation claim exclusively but leaves the file writable before final confirmation, so replacement can change the claimed attempt or evidence root.
- Owner: `release-qa`.
- Reason for deferral: the finding is independent of EPIC-003 review activation and does not affect its candidate, capture, supervision, or settlement correctness.
- Re-entry condition: resolve before the next release QA confirmation by making the claim immutable or binding finalization to the exact claim digest returned at creation.
