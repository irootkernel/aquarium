# Fixture checks

`make test` runs standard-library unittest against the catalog and export modules,
including their composition. It checks Unicode case folding, whitespace, output
ordering, trailing newlines and empty input. Extend behavior checks for approved
changes and retain the original default behavior.

These checks do not establish correct document adoption, native instruction
loading, review scope or successful installed workflow progression. The operator
records those observations separately.
