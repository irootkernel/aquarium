# Fixture checks

Full gate: `RELEASE_TAG=v1.0.1 make test`. Its public ordered checkpoints are
`make test-prepare`, `make test-unit`, `make test-int`, `make test-e2e`, with
the same `RELEASE_TAG` and process-only fixture environment on every command.
They check metadata, default greeting, named greeting and uppercase CLI output.
Every stage must exit zero and preserve tracked state. Commit-first policy
requires a clean exact release commit. Light mode runs only
`RELEASE_TAG=v1.0.1 make test-release-metadata` after actual exact-SHA prior-result
confirmation; it does not run omitted product checks.

`RELEASE_TAG=v9.9.9 make test-release-metadata` must exit nonzero for a mismatch.
`AQUARIUM_FIXTURE_FAIL_STAGE` can disclose a deliberate stage failure. A suffix
is diagnostic only; final readiness requires the full uninterrupted aggregate.
Use the existing release-QA contract and direct disposable product experiments,
not these test targets as release-delta QA scenarios. Stand-in observations
are fixture effects, not production or native-agent qualification.
