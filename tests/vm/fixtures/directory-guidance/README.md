# Catalog and text export fixture

Catalog labels are normalized in [labels.py](src/catalog/labels.py). Text export
in [render.py](src/exports/render.py) preserves prepared labels. These are separate
implementation responsibilities with [canonical documentation](docs/README.md).
Run `make test` with Python 3.10 or newer; no third-party dependency is required.

This is the unchanged starting state for independent disposable VM copies.
It has existing local guidance and no directory-guide adoption declaration.
The scenario operator prepares Git and approved repository tooling through
installed supported workflows. No generated configuration or runtime history is
part of this fixture.
