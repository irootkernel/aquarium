# Historical Podway input

`generation-13-populated.sql` is the frozen legacy Store dump shipped by Podway
v0.2.14 at `tests/fixtures/storage/daemon-era-v2dfc/generation-13-populated.sql`.
Its SHA-256 is `5ddef98c1d92a88eb16ed3ef83fd3fbfb808280203fcbbdb75d8254429c617f3`.
Its original producer commit is `6e771f265391309733d9aef796056bcabac7f047`.
It contains a current session, a completed job and a delegation receipt. The
compatibility helper materializes it only in its disposable fixture to check
unchanged legacy refusal and an explicitly scoped destructive reset. This is
rejected historical input, not current DDL or a production conversion path.

The direct-writer fixture uses the current generation-15 Store with only its
writer-manifest digest set to the exact v0.2.13 manifest. Podway v0.2.13 and
v0.2.14 ship identical generation-15 DDL. This models writer admission; it does
not establish an installed v0.2.13-to-v0.2.14 upgrade or skill functionality.
Those outcomes require separate UTM verification.
