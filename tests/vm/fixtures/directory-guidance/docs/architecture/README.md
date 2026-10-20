# Architecture

[Catalog](../../src/catalog/labels.py) normalizes labels.
[Export](../../src/exports/render.py) serializes prepared values without
normalizing them. Callers compose the operations; neither module imports the
other. The existing catalog guide applies to its implementation boundary.
Export has a nested instruction file whose migration requires explicit scope.
