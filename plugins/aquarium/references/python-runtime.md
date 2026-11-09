# Shared Aquarium Python runtime

`dev-setup-global` owns the `aquarium-python` component. Its environment supplies
PyYAML, `jsonschema` and their pinned transitive dependencies to Aquarium helpers
across projects. It contains no development tools or project dependencies.
The existing status reporter and development-channel runtimes remain separate.

## Diagnose and prepare

Bootstrap and diagnosis use an installed host Python 3.11 or newer. Creating or
repairing an environment additionally requires a matching pinned wheel set:
Apple Silicon macOS CPython 3.11, 3.12, 3.13 or 3.14 (including 3.14t). The five
PyYAML 6.0.3 wheel hashes map to those exact tags in its
[official release metadata](https://pypi.org/pypi/PyYAML/6.0.3/json). At the 2026-11-09 metadata check, no cp315
wheel was published for this pinned version. An unsupported creator returns
`unsupported-runtime` before creating runtime paths and names the observed
interpreter. Select an existing matching host interpreter; do not install or
modify a project's Python. A healthy existing environment can still be reused
from a newer bootstrap Python. Future support expands with reviewed pinned
artifacts, not a guessed permanent Python ceiling.

Bootstrap and diagnosis use only the
standard library, even when that Python cannot import YAML or `jsonschema`.
Resolve `<plugin-root>` from the invoking installed skill, not a development
checkout. Run:

```bash
python3 -I <plugin-root>/tools/aquarium-python/runtime.py inspect
```

The result identifies `aquarium-python`, the requirements digest, runtime root,
and either the selected interpreter or a `missing-prerequisite` reason. Missing,
damaged or incompatible state routes to a scoped `dev-setup-global` continuation
naming `aquarium-python`; this component name is a setup handoff, not a skill CLI.
Diagnosis never creates directories, downloads packages or installs anything.
Runtime-owned success and failure results are JSON on stdout; errors exit 2.
Invalid helper paths return `invalid-arguments`, missing install approval returns
`approval-required`, unsupported bootstrap Python returns `unsupported-runtime`,
and preparation subprocess/filesystem failures return `install-failed`. These
statuses carry no environment-repair continuation. Environment validation or
unsafe-path failures encountered during installation also return `install-failed`;
installation never routes a failure back to itself as a missing prerequisite. A damaged bundled requirements
file returns `invalid-package`. Argument-parser usage errors retain argparse's
stderr/exit-2 interface. After helper exec, the helper owns its streams and exit.


Before installation or repair, disclose the exact root
`~/.aquarium/python-runtime/`, existing state, pinned requirements and hashes,
and downloads from `https://pypi.org/simple` and `https://files.pythonhosted.org`.
Apply the catalog's existing action approval and backup rules. After approval:

```bash
python3 -I <plugin-root>/tools/aquarium-python/runtime.py install --approve-install
```

The installer disables pip configuration through `PIP_CONFIG_FILE=os.devnull`
for installation and consistency checking, without editing caller configuration.
It uses hash-checked binary wheels from the bundled requirements,
checks installed dependency consistency and imports, then selects the verified
environment. A requirements digest has its own selection and immutable completed
environments. An unchanged healthy selection is reused across projects and plugin
versions. Changed requirements get a separate environment; existing environments
are retained. Repair creates a replacement without modifying a prior environment.
Creation happens at the final path because venv entrypoints embed absolute paths.
Failed preparation removes only its newly created environment and preserves the
previous selection. An installation lock serializes installers for that digest.

Re-run `inspect` after installation. A changed or removed base interpreter needs
repair. Python installation itself is outside this component's scope. Plugin
updates do not install or repair environments implicitly.

## Execute helpers

```bash
python3 -I <plugin-root>/tools/aquarium-python/runtime.py run shared/manage_adaptive_procedure.py context <arguments>
```

Use the same prefix for preparation, qualification, promotion and setup scripts,
passing their plugin-relative paths. `run` checks the environment matching the
invoking plugin's requirements before executing. It isolates Python imports from
project and user packages, preserves helper-local imports, and inherits the
working directory, arguments, standard streams and native process exit behavior.
No activation, PATH change, project venv or global package installation is needed.
There is no fallback to another Python package environment and no runtime install.

Select Podway opt-out and non-Git `new-project` before this runtime lookup. Their
existing standard-library entrypoint branches remain available without the
environment. Global setup's bootstrap inspector also stays dependency-free.
Setup bundles prepare the environment once before YAML manifest normalization;
the component is infrastructure and adds no manifest tool name.

## Upgrade and verification

Existing users prepare this component once through `dev-setup-global` before
using the updated dependent workflows. This is a breaking setup transition.
Project files, project environments and global Python packages remain unchanged.
Low-level source tests may still invoke helpers directly in the development
environment; that does not qualify the installed runtime or skill behavior.

Real candidate installation and functional workflow checks run only in the
dedicated UTM VM under separate VM-test or release authority. Verify first
installation, reuse from a non-Python project, execution with a conflicting
project environment, repair, bundle bootstrap and actual handler startup.
Bind observations to the exact candidate; fixture checks do not establish these
installed results or Master's functional acceptance.
