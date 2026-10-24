#!/usr/bin/env python3
"""Guest recipe driver for Aquarium's Haepari VM suites.

The guest identity is verified before any write, every recipe stages its
declared outputs, and recipe-owned consumer cleanup finishes with a verified
post-cleanup inventory before workload exit or `manual complete`. The driver
never submits a Job and never operates the VM.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

import recipe_lib as lib

PROBE_LEFTOVER = ".aquarium-vm-probe-leftover"
PRIOR_KIND = "prior-artifact"
CANDIDATE_KIND = "artifact"


def allowed_runtime_changes(_scope: str, path: str) -> bool:
    return (
        path.startswith(
            (
                ".codex/plugins/cache/root-kernel/",
                ".aquarium/status-runtime",
                ".aquarium-vm-marketplaces/",
            )
        )
        or path == ".local/bin/aquarium-status"
    )


class Context:
    """Identity first: constructing a Context never writes to the guest."""

    def __init__(self) -> None:
        self.root = lib.job_root()
        self.inputs = lib.load_inputs()
        self.identity = lib.verify_guest_identity()
        self.job = lib.job_identity()
        self.home = Path(lib.context_value("AQUARIUM_GUEST_HOME"))
        self.codex = lib.context_value("AQUARIUM_GUEST_CODEX")
        self.python = lib.context_value("AQUARIUM_GUEST_PYTHON")
        self.marketplace = lib.context_value("AQUARIUM_MARKETPLACE_NAME")
        self._checkout: Path | None = None
        self.dev_version = self.inputs["candidate"]["development_version"]

    @property
    def checkout(self) -> Path:
        if self._checkout is None:
            self._checkout = lib.ensure_checkout(self.root)
        return self._checkout

    @property
    def candidate_source(self) -> Path:
        return self.root / f"{CANDIDATE_KIND}/plugins/aquarium/tools/aquarium-status"

    @property
    def prior_source(self) -> Path:
        return self.root / f"{PRIOR_KIND}/plugins/aquarium/tools/aquarium-status"

    def marketplace_path(self, kind: str) -> Path:
        return lib.marketplace_dir(self.home, kind)

    def profile(self, name: str) -> dict[str, Any]:
        return json.loads((self.root / f"profile/{name}.json").read_text())

    def profile_digest(self, name: str) -> str:
        return lib.sha256_file(self.root / f"profile/{name}.json")

    def scope_roots(self) -> list[tuple[str, Path, str]]:
        # The plugin-cache scope covers every marketplace's cache under
        # `.codex/plugins/cache` only: Codex-internal state beside it (for
        # example `.plugin-appserver` or `.remote-plugin-install-staging`)
        # belongs to the Codex component and stays out of the inventory.
        return [
            (
                "user-global",
                self.home / ".aquarium-vm-marketplaces",
                ".aquarium-vm-marketplaces",
            ),
            ("user-global", self.home / ".aquarium", ".aquarium"),
            (
                "codex-plugin-cache",
                self.home / ".codex/plugins/cache",
                ".codex/plugins/cache",
            ),
            (
                "shared-agents-skills",
                self.home / ".agents/skills",
                ".agents/skills",
            ),
        ]

    def snapshot(
        self, suite: str, phase: str, profile: str = "candidate"
    ) -> list[dict[str, Any]]:
        from tree_digest import TreeDigestError, inventory_entries

        entries: list[dict[str, Any]] = []
        for scope, root, base in self.scope_roots():
            if not root.exists():
                continue
            try:
                entries += inventory_entries(root, scope, base)
            except TreeDigestError as error:
                raise lib.RecipeError(
                    f"unsafe inventoried scope ({scope}): {error}"
                ) from error
        _runtime, launcher = lib.runtime_locations(self.home)
        if launcher.is_file() and not launcher.is_symlink():
            entries.append(
                {
                    "installation_scope": "user-global",
                    "relative_path": ".local/bin/aquarium-status",
                    "executable": True,
                    "sha256": lib.sha256_file(launcher),
                }
            )
        document = lib.write_inventory(
            lib.results_directory(suite) / f"inventory-{phase}.json",
            phase,
            entries,
            self.profile_digest(profile),
            lib.sha256_file(Path(__file__)),
        )
        lib.record_inventory(suite, phase, document)
        return document["entries"]

    def established_plugin_version(self) -> str | None:
        row = lib.installed_aquarium(self.codex, self.marketplace)
        if row is None or not isinstance(row.get("version"), str):
            return None
        return row["version"]

    def install_plugin(self) -> None:
        result = lib.plugin_add(self.codex, "aquarium", self.marketplace)
        if result.returncode != 0:
            raise lib.RecipeError(f"plugin installation failed: {result.stderr[-400:]}")

    def ensure_prior_stable(
        self, ledger: lib.RunLedger, *, predecessors: tuple[str, ...] = ()
    ) -> dict[str, Any]:
        lib.establish_marketplace(
            self.codex,
            self.home,
            self.root / PRIOR_KIND,
            PRIOR_KIND,
            ledger,
            self.marketplace,
            declared_predecessors=predecessors,
        )
        if self.established_plugin_version() != self.inputs["prior"]["version"]:
            if lib.installed_aquarium(self.codex, self.marketplace) is not None:
                lib.plugin_remove(self.codex, "aquarium", self.marketplace)
            self.install_plugin()
        if self.established_plugin_version() != self.inputs["prior"]["version"]:
            raise lib.RecipeError(
                f"prior stable {self.inputs['prior']['version']} is not installed"
            )
        observation = lib.observe_install(
            self.python, self.prior_source, self.home, ledger
        )
        return {
            "prior_version": self.inputs["prior"]["version"],
            "runtime_observation": observation,
        }

    def ensure_candidate_installed(
        self, ledger: lib.RunLedger, *, predecessors: tuple[str, ...] = ()
    ) -> None:
        if self.established_plugin_version() == self.dev_version.removeprefix("v"):
            return
        lib.establish_marketplace(
            self.codex,
            self.home,
            self.root / CANDIDATE_KIND,
            CANDIDATE_KIND,
            ledger,
            self.marketplace,
            declared_predecessors=predecessors,
        )
        if lib.installed_aquarium(self.codex, self.marketplace) is not None:
            lib.plugin_remove(self.codex, "aquarium", self.marketplace)
        self.install_plugin()
        if self.established_plugin_version() != self.dev_version.removeprefix("v"):
            raise lib.RecipeError("candidate plugin installation did not bind")

    def install_candidate_runtime(self, ledger: lib.RunLedger) -> dict[str, Any]:
        return lib.observe_install(
            self.python, self.candidate_source, self.home, ledger
        )

    def remove_candidate_state(self, ledger: lib.RunLedger) -> dict[str, Any]:
        report: dict[str, Any] = {}
        candidate_dir = self.marketplace_path(CANDIDATE_KIND)
        active = lib.marketplace_registrations(self.codex).get(self.marketplace)
        registered_dir = Path(active) if active else None
        owned = (
            registered_dir is not None
            and registered_dir.parent == self.home / ".aquarium-vm-marketplaces"
            and lib._harness_directory_owned(self.home, registered_dir.name)
        )
        if (
            active == str(candidate_dir)
            and owned
            and lib.installed_aquarium(self.codex, self.marketplace) is not None
        ):
            result = lib.plugin_remove(self.codex, "aquarium", self.marketplace)
            report["plugin_removed"] = result.returncode == 0
            if result.returncode != 0:
                raise lib.RecipeError(
                    f"candidate plugin removal failed: {result.stderr[-300:]}"
                )
        report["marketplace"] = lib.remove_owned_marketplace(
            self.codex, self.home, CANDIDATE_KIND, ledger, self.marketplace
        )
        report["runtime"] = lib.remove_runtime(self.home, ledger)
        return report


def discovery(context: Context, repository: Path) -> dict[str, Any]:
    from native_observation import discover

    return discover(context.codex, repository)


def normalize_foreign_registration(context: Context) -> dict[str, Any]:
    """J-BASE's declared one-time normalization of the foreign registration.

    The pre-normalization registration and installed row are persisted as
    required evidence BEFORE either removal, so a later failure still hands
    off the original source and installed row.
    """
    evidence = lib.record_foreign_registration(context.codex, context.marketplace)
    preimage = lib.write_document(
        lib.results_directory("baseline") / "pre-normalization.json", evidence
    )
    try:
        if evidence["installed_row"] is not None:
            result = lib.plugin_remove(context.codex, "aquarium", context.marketplace)
            if result.returncode != 0:
                raise lib.RecipeError(
                    f"normalization plugin removal failed: {result.stderr[-300:]}"
                )
        if evidence["source"] is not None:
            result = lib.marketplace_unregister(context.codex, context.marketplace)
            if result.returncode != 0:
                raise lib.RecipeError(
                    f"normalization marketplace removal failed: {result.stderr[-300:]}"
                )
    except lib.RecipeError:
        raise lib.RecipeError(
            "normalization of the recorded pre-normalization.json target failed: "
            + str(preimage)
        ) from None
    lib.assert_registration(context.codex, context.marketplace, None)
    return evidence


def run_baseline(context: Context) -> int:
    ledger = lib.run_ledger("baseline")
    identities = {
        "codex": lib.codex_component_identity(context.codex, context.home),
        "installed_plugin": lib.installed_aquarium(context.codex, context.marketplace),
    }
    try:
        identities["runtime"] = dict(
            zip(("generation", "receipt"), lib.read_current_generation(context.home))
        )
    except lib.RecipeError:
        identities["runtime"] = None
    stable = context.profile("stable")
    pinned_codex = next(
        component["version"]
        for component in stable["components"]
        if component["name"] == "codex"
    )
    if identities["codex"]["version"] != f"codex-cli {pinned_codex}":
        return lib.finish(
            "baseline",
            "fail",
            {
                "identities": identities,
                "problem": f"guest Codex {identities['codex']['version']} differs "
                f"from the aligned pin {pinned_codex}",
            },
            consumer_cleanup="unverified",
        )
    before = context.snapshot("baseline", "before", profile="stable")
    normalization = normalize_foreign_registration(context)
    try:
        # Every failure after normalization references the persisted
        # preimage: the install, the post-install snapshot, the final
        # registration assertion and the preservation comparison all run
        # under this one handler.
        context.ensure_prior_stable(ledger, predecessors=(CANDIDATE_KIND,))
        ledger.save()
        after = context.snapshot("baseline", "candidate", profile="stable")
        lib.assert_registration(
            context.codex,
            context.marketplace,
            str(context.marketplace_path(PRIOR_KIND)),
        )
        violations = lib.postcondition_violations(
            before, after, allowed_runtime_changes
        )
    except lib.RecipeError as error:
        return lib.finish(
            "baseline",
            "fail",
            {
                "identities": identities,
                "normalization": normalization,
                "preimage": "results/baseline/pre-normalization.json",
                "problem": (
                    f"post-normalization failure ({error}); the original "
                    "registration evidence is in "
                    "results/baseline/pre-normalization.json"
                ),
            },
            consumer_cleanup="unverified",
        )
    if violations:
        return lib.finish(
            "baseline",
            "fail",
            {
                "identities": identities,
                "normalization": normalization,
                "preimage": "results/baseline/pre-normalization.json",
                "violations": violations,
                "problem": (
                    "preservation violations after normalization "
                    f"({violations}); the original registration evidence is "
                    "in results/baseline/pre-normalization.json"
                ),
            },
            consumer_cleanup="failed",
        )
    return lib.finish(
        "baseline",
        "pass",
        {
            "identities": identities,
            "normalization": normalization,
            "violations": violations,
        },
        consumer_cleanup="verified",
    )


def install_cleanup_problems(
    context: Context, ledger: lib.RunLedger, cleanup: dict[str, Any]
) -> list[str]:
    """J-A's declared product-absent end state after the final cleanup.

    Nothing is deleted, replaced or unregistered here: every unmet
    expectation is only recorded, quoting what the cleanup report
    preserved.
    """
    problems: list[str] = []
    if lib.installed_aquarium(context.codex, context.marketplace) is not None:
        problems.append(f"candidate plugin still installed for {context.marketplace}")
    try:
        lib.assert_registration(context.codex, context.marketplace, None)
    except lib.RecipeError as error:
        problems.append(str(error))
    # Every absence check below is type-independent: os.path.lexists counts
    # a dangling symlink, a regular file or a directory as present residue.
    directory = context.marketplace_path(CANDIDATE_KIND)
    if os.path.lexists(directory):
        problems.append(f"candidate marketplace directory remains: {directory}")
    sidecar = lib.owner_sidecar_path(context.home, CANDIDATE_KIND)
    if os.path.lexists(sidecar):
        problems.append(f"candidate owner sidecar remains: {sidecar}")
    marketplace_report = cleanup.get("marketplace")
    if isinstance(marketplace_report, dict):
        if "preserved" in marketplace_report:
            problems.append(
                "marketplace cleanup preserved the directory: "
                + str(marketplace_report["preserved"])
            )
        if "registration_left_alone" in marketplace_report:
            problems.append(
                "marketplace cleanup left the registration alone: "
                + str(marketplace_report["registration_left_alone"])
            )
    runtime_root, launcher = lib.runtime_locations(context.home)
    for label, path in (
        ("current marker", runtime_root / "current"),
        ("launcher", launcher),
    ):
        if os.path.lexists(path):
            problems.append(f"status runtime {label} remains: {path}")
    versions = runtime_root / "versions"
    for name in sorted(ledger.document.get("generations", [])):
        if os.path.lexists(versions / name):
            problems.append(f"run-owned generation remains: {name}")
    return problems


def run_install(context: Context) -> int:
    ledger = lib.run_ledger("install")
    pre_cleanup = context.remove_candidate_state(ledger)
    predecessors = (PRIOR_KIND,)
    before = context.snapshot("install", "before")
    fixture = lib.seed_fixture(context.checkout, context.root / "install-fixture")
    context.ensure_candidate_installed(ledger, predecessors=predecessors)
    import run_acceptance

    version = context.established_plugin_version()
    installed_cache = (
        context.home
        / ".codex/plugins/cache"
        / context.marketplace
        / "aquarium"
        / (version or "")
    )
    native_row = run_acceptance.installed_plugin(
        {"tools": {"codex": context.codex}},
        context.marketplace_path(CANDIDATE_KIND),
        installed_cache,
    )
    discovery_observation = discovery(context, context.root / "install-fixture")
    context.install_candidate_runtime(ledger)
    ledger.save()
    context.snapshot("install", "candidate")
    cleanup = context.remove_candidate_state(ledger)
    cleanup_problems = install_cleanup_problems(context, ledger, cleanup)
    after = context.snapshot("install", "post_cleanup")
    violations = lib.postcondition_violations(before, after, allowed_runtime_changes)
    outcome = "pass" if not violations and not cleanup_problems else "fail"
    consumer_cleanup = "failed" if violations or cleanup_problems else "verified"
    return lib.finish(
        "install",
        outcome,
        {
            "fixture": fixture,
            "installed_plugin_version": native_row.get("version"),
            "discovery_skills": sorted(
                skill["name"]
                for row in discovery_observation.get("data", [])
                for skill in row.get("skills", [])
                if skill.get("name", "").startswith("aquarium:")
            ),
            "pre_cleanup": pre_cleanup,
            "cleanup": cleanup,
            "cleanup_problems": cleanup_problems,
            "violations": violations,
        },
        consumer_cleanup=consumer_cleanup,
    )


def synthetic_state(context: Context, name: str) -> dict[str, Any]:
    fixture = lib.seed_fixture(context.checkout, context.root / name)
    marker = context.root / name / "SYNTHETIC-STATE.md"
    marker.write_text(
        "Synthetic prior state created through public interfaces.\n",
        encoding="utf-8",
    )
    for argv in (
        ["git", "-C", str(context.root / name), "add", "."],
        ["git", "-C", str(context.root / name), "commit", "-qm", "[TEST] Add state"],
    ):
        result = lib.run(argv, timeout=120)
        if result.returncode != 0:
            raise lib.RecipeError("synthetic state commit failed")
    return {
        "fixture": fixture,
        "custom_file": str(marker),
        "custom_sha256": lib.sha256_file(marker),
        "head": lib.run(
            ["git", "rev-parse", "HEAD"], cwd=context.root / name
        ).stdout.strip(),
    }


def attach_fixture_checks(context: Context, fixture: Path) -> dict[str, Any]:
    """The regression oracle, fixture gate and restart checks run inside the
    upgrade suite's post-upgrade assertions."""
    import run_acceptance

    lock = context.inputs.get("fixture_requirements")
    if not isinstance(lock, str) or not (context.root / lock).is_file():
        raise lib.RecipeError(
            "the sealed hash-locked fixture requirements are required for the "
            "regression oracle; the check did not run",
            "incomplete",
        )
    venv_python = lib.create_venv(context.python, fixture / ".venv")
    installed = lib.pip_install_locked(venv_python, context.root / lock)
    if installed["exit"] != 0:
        raise lib.RecipeError("hash-locked fixture dependencies failed to install")
    oracle = run_acceptance.oracle(str(venv_python), fixture, uppercase=False)
    gate = lib.run(["make", "test"], cwd=fixture, timeout=1800)
    checks = {
        "exit": gate.returncode,
        "tail": gate.stdout[-800:] + gate.stderr[-800:],
    }
    return {"oracle": oracle, "make_test": checks, "venv": True}


def run_upgrade(context: Context) -> int:
    ledger = lib.run_ledger("upgrade")
    context.ensure_prior_stable(ledger, predecessors=(CANDIDATE_KIND,))
    state = synthetic_state(context, "upgrade-fixture")
    status_yaml = context.home / ".aquarium/status.yaml"
    status_before = lib.sha256_file(status_yaml) if status_yaml.is_file() else None
    before = context.snapshot("upgrade", "before")
    context.ensure_candidate_installed(ledger, predecessors=(PRIOR_KIND,))
    update = context.install_candidate_runtime(ledger)
    receipt = update["receipt"]
    functional: list[str] = list(
        lib.assert_runtime_identity(
            receipt,
            plugin_version=context.dev_version,
            python_sha256=lib.sha256_file(Path(context.python)),
        )
    )
    if lib.sha256_file(Path(state["custom_file"])) != state["custom_sha256"]:
        functional.append("synthetic prior state was not preserved")
    if status_before is not None and lib.sha256_file(status_yaml) != status_before:
        functional.append("preserved status.yaml bytes changed during upgrade")
    context.snapshot("upgrade", "candidate")
    restart = discovery(context, context.root / "upgrade-fixture")
    diagnose = lib.diagnose_runtime(context.python, context.candidate_source)
    regression = attach_fixture_checks(context, context.root / "upgrade-fixture")
    if regression["make_test"]["exit"] != 0:
        functional.append("existing-behavior fixture gate failed after upgrade")
    context.ensure_prior_stable(ledger, predecessors=(CANDIDATE_KIND,))
    current_name, _receipt = lib.read_current_generation(context.home)
    for name in list(ledger.document.get("generations", [])):
        if name != current_name:
            lib.remove_owned_generation(context.home, name, ledger)
    ledger.save()
    shutil.rmtree(context.root / "upgrade-fixture")
    after = context.snapshot("upgrade", "post_cleanup")
    postcondition = lib.postcondition_violations(before, after, allowed_runtime_changes)
    violations = functional + postcondition
    return lib.finish(
        "upgrade",
        "pass" if not violations else "fail",
        {
            "synthetic_state": state,
            "runtime_observation": {
                key: update[key] for key in ("selected", "created", "reused")
            },
            "runtime_receipt": receipt,
            "restart_discovery": bool(restart.get("data")),
            "runtime_diagnose": diagnose,
            "regression_assertions": regression,
            "functional_violations": functional,
            "postcondition_violations": postcondition,
            "violations": violations,
        },
        consumer_cleanup="verified" if not postcondition else "failed",
    )


def run_migration_failure(context: Context) -> int:
    ledger = lib.run_ledger("migration-failure")
    context.ensure_prior_stable(ledger, predecessors=(CANDIDATE_KIND,))
    state = synthetic_state(context, "migration-fixture")
    before = context.snapshot("migration-failure", "before")
    current_before, receipt_before = lib.read_current_generation(context.home)
    foreign: list[str] = []
    removed: list[str] = []
    for name, receipt in sorted(lib.generation_receipts(context.home).items()):
        if name == current_before:
            continue
        if receipt.get("plugin_version") != context.dev_version:
            continue
        if lib.remove_owned_generation(context.home, name, ledger):
            removed.append(name)
        else:
            foreign.append(name)
    if foreign:
        return lib.finish(
            "migration-failure",
            "fail",
            {
                "problem": "a foreign candidate generation is present; foreign "
                "state is preserved and the staging path cannot be forced",
                "foreign_generations": foreign,
            },
            consumer_cleanup="unverified",
        )
    remaining = [
        name
        for name, receipt in lib.generation_receipts(context.home).items()
        if receipt.get("plugin_version") == context.dev_version
    ]
    if remaining:
        return lib.finish(
            "migration-failure",
            "fail",
            {"problem": "target generation is present; staging path not forced"},
            consumer_cleanup="unverified",
        )
    interruption = lib.interrupted_update(
        context.python, context.candidate_source, context.home, ledger
    )
    if not interruption.get("interrupted"):
        return lib.finish(
            "migration-failure",
            "fail",
            {"problem": interruption.get("reason"), "synthetic_state": state},
            consumer_cleanup="unverified",
        )
    current_after, receipt_after = lib.read_current_generation(context.home)
    functional: list[str] = []
    if current_after != current_before or receipt_after != receipt_before:
        functional.append("interruption published a generation or changed the selector")
    if lib.sha256_file(Path(state["custom_file"])) != state["custom_sha256"]:
        functional.append("migration state was not preserved until assertions")
    recovery = lib.observe_install(
        context.python, context.candidate_source, context.home, ledger
    )
    generation = recovery["selected"]
    receipt = recovery["receipt"]
    findings: list[str] = []
    if "-r" in generation:
        findings.append(f"recovery produced a repair-suffixed generation: {generation}")
    functional += lib.assert_runtime_identity(
        receipt,
        plugin_version=context.dev_version,
        python_sha256=lib.sha256_file(Path(context.python)),
    )
    duplicates = [
        name
        for name, item in lib.generation_receipts(context.home).items()
        if item.get("plugin_version") == context.dev_version
    ]
    if len(duplicates) != 1:
        functional.append(f"recovery duplicated logical work: {duplicates}")
    refusal = lib.unsafe_launcher_refusal(
        context.python, context.candidate_source, context.home
    )
    if not refusal["refused"]:
        functional.append("unsafe launcher did not produce an explicit safe failure")
    context.ensure_prior_stable(ledger, predecessors=(CANDIDATE_KIND,))
    current_name, _receipt = lib.read_current_generation(context.home)
    for name in list(ledger.document.get("generations", [])):
        if name != current_name:
            lib.remove_owned_generation(context.home, name, ledger)
    ledger.save()
    shutil.rmtree(context.root / "migration-fixture")
    after = context.snapshot("migration-failure", "post_cleanup")
    postcondition = lib.postcondition_violations(before, after, allowed_runtime_changes)
    violations = functional + postcondition
    return lib.finish(
        "migration-failure",
        "pass" if not violations else "fail",
        {
            "interruption": interruption,
            "removed_generations": removed,
            "recovered_generation": generation,
            "safe_failure_refused": refusal["refused"],
            "synthetic_state": state,
            "findings": findings,
            "functional_violations": functional,
            "postcondition_violations": postcondition,
            "violations": violations,
        },
        consumer_cleanup="verified" if not postcondition else "failed",
    )


def run_manual_hold(context: Context, phase: str) -> int:
    lib.verify_guest_identity()
    results = lib.results_directory("manual-hold")
    if phase == "smoke":
        # S5.2: every starting-state check is read-only and runs before any
        # mutation. Only after all of them pass does J-H perform the
        # successor repair (removing J-F's leftover with its preimage
        # recorded), create the fixture, and write smoke.json with the
        # repair record and the retained-state baseline the cleanup must
        # later verify against.
        from tree_digest import inventory_entries

        # Validate the declared retained state BEFORE capturing the baseline:
        # the prior marketplace directory exists, its ownership sidecar
        # exists and parses, and the sidecar's tree digest equals the
        # directory's actual tree digest. Two empty inventories can never
        # pass these checks.
        prior_dir = context.marketplace_path(PRIOR_KIND)
        retained_problems: list[str] = []
        if not prior_dir.is_dir():
            retained_problems.append("prior marketplace directory missing")
            retained = []
            sidecar_digest = None
        else:
            try:
                retained = inventory_entries(
                    prior_dir,
                    "user-global",
                    ".aquarium-vm-marketplaces/prior-artifact",
                )
            except Exception as error:  # noqa: BLE001 - fail closed on scope
                retained_problems.append(f"prior marketplace inventory failed: {error}")
                retained = []
            sidecar = lib.read_owner_sidecar(context.home, PRIOR_KIND)
            if sidecar is None:
                retained_problems.append(
                    "prior marketplace sidecar missing or unparsable"
                )
                sidecar_digest = None
            else:
                sidecar_path = lib.owner_sidecar_path(context.home, PRIOR_KIND)
                sidecar_digest = lib.sha256_file(sidecar_path)
                try:
                    actual_tree = lib.tree_sha256_from_directory(prior_dir)
                except lib.TreeDigestError as error:
                    retained_problems.append(
                        f"prior marketplace tree digest failed: {error}"
                    )
                else:
                    if sidecar.get("artifact_tree_sha256") != actual_tree:
                        retained_problems.append(
                            "prior marketplace sidecar digest does not match "
                            "its directory"
                        )
        # The declared prior-stable state across three scopes: the plugin,
        # the native registration and the status runtime. Any mismatch is a
        # retained problem; the hold does not begin, and nothing is
        # deleted, unregistered or installed to repair it.
        prior_version = context.inputs["prior"]["version"]
        plugin_row = lib.installed_aquarium(context.codex, context.marketplace)
        if plugin_row is None:
            retained_problems.append("prior plugin is not installed")
        elif plugin_row.get("version") != prior_version:
            retained_problems.append(
                f"prior plugin version is {plugin_row.get('version')}, "
                f"expected {prior_version}"
            )
        registration = lib.marketplace_registrations(context.codex).get(
            context.marketplace
        )
        if registration != str(context.marketplace_path(PRIOR_KIND)):
            retained_problems.append(
                f"marketplace registration is {registration!r}, expected the "
                "prior harness marketplace"
            )
        runtime_root, _launcher = lib.runtime_locations(context.home)
        generation = None
        try:
            generation, receipt = lib.read_current_generation(context.home)
        except lib.RecipeError as error:
            retained_problems.append(f"status runtime generation unreadable: {error}")
        else:
            if receipt.get("plugin_version") != f"v{prior_version}":
                retained_problems.append(
                    f"runtime generation binds {receipt.get('plugin_version')}, "
                    f"expected v{prior_version}"
                )
        leftover = context.home / PROBE_LEFTOVER
        if retained_problems:
            # Nothing was mutated: the leftover keeps its exact bytes, no
            # fixture exists, and the successor repair did not run.
            return lib.finish(
                "manual-hold",
                "fail",
                {
                    "phase": phase,
                    "retained_problems": retained_problems,
                    "successor_repair": {
                        "probe_leftover_path": str(leftover),
                        "probe_leftover_present": leftover.is_file(),
                        "removed": False,
                    },
                    "note": "retained-state validation failed; the hold did "
                    "not begin and the successor repair was not performed",
                },
                consumer_cleanup="unverified",
            )
        successor_repair = {
            "probe_leftover_path": str(leftover),
            "probe_leftover_present": leftover.is_file(),
            "removed": False,
        }
        if leftover.is_file():
            successor_repair.update(
                {
                    "removed": True,
                    "sha256": lib.sha256_file(leftover),
                }
            )
            leftover.unlink()
        fixture = context.root / "manual-hold-fixture"
        fixture.mkdir(parents=True, exist_ok=True)
        marker = fixture / "TRIVIAL-FIXTURE.txt"
        marker.write_text("trivial manual-hold fixture\n", encoding="utf-8")
        # The receipt digest is computed only after validation passed.
        receipt_path = runtime_root / "versions" / generation / "runtime.json"
        lib.write_document(
            results / "smoke.json",
            {
                "fixture": str(marker),
                "created": True,
                "successor_repair": successor_repair,
                "retained_state_baseline": {
                    "entries": retained,
                    "sidecar_sha256": sidecar_digest,
                    "prior_state": {
                        "plugin_row": plugin_row,
                        "registration": registration,
                        "generation": generation,
                        "receipt_sha256": lib.sha256_file(receipt_path),
                    },
                },
            },
        )
        return 0
    if phase == "consumer-cleanup":
        from tree_digest import TreeDigestError, inventory_entries

        fixture = context.root / "manual-hold-fixture"
        fixture_removed = False
        if fixture.is_symlink() or fixture.is_file():
            fixture.unlink()
            fixture_removed = True
        elif fixture.is_dir():
            shutil.rmtree(fixture)
            fixture_removed = True
        fixture_absent = not fixture.exists() and not fixture.is_symlink()
        leftover_absent = not (context.home / PROBE_LEFTOVER).exists()
        problems: list[str] = []
        # Retained-state verification: the prior-plugin marketplace tree
        # and its sidecar must match the smoke phase's recorded baseline.
        # A smoke.json that is not a JSON object, or a non-object baseline,
        # counts as a missing baseline.
        baseline_document = lib.read_json_safe(results / "smoke.json")
        baseline = None
        if isinstance(baseline_document, dict):
            baseline = baseline_document.get("retained_state_baseline")
        if not isinstance(baseline, dict):
            baseline = None
        baseline_entries = baseline.get("entries") if baseline else None
        baseline_sidecar = baseline.get("sidecar_sha256") if baseline else None
        try:
            current = inventory_entries(
                context.marketplace_path(PRIOR_KIND),
                "user-global",
                ".aquarium-vm-marketplaces/prior-artifact",
            )
        except (TreeDigestError, OSError) as error:
            current = None
            problems.append(f"retained-state inventory failed: {error}")
        if baseline_entries is None:
            problems.append("smoke retained-state baseline is missing")
        elif current is not None:
            expected = {
                (entry["installation_scope"], entry["relative_path"]): entry
                for entry in baseline_entries
            }
            observed = {
                (entry["installation_scope"], entry["relative_path"]): entry
                for entry in current
            }
            for key in sorted(set(expected) - set(observed)):
                problems.append(f"retained entry missing: {key[0]}:{key[1]}")
            for key in sorted(set(observed) - set(expected)):
                problems.append(f"retained entry extra: {key[0]}:{key[1]}")
            for key in sorted(set(expected) & set(observed)):
                if expected[key]["sha256"] != observed[key]["sha256"]:
                    problems.append(f"retained entry changed: {key[0]}:{key[1]}")
                elif expected[key].get("executable") != observed[key].get("executable"):
                    problems.append(
                        f"retained entry executable bit changed: {key[0]}:{key[1]}"
                    )
        # The sidecar's exact bytes must match the recorded baseline.
        sidecar = lib.owner_sidecar_path(context.home, PRIOR_KIND)
        if not sidecar.is_file():
            problems.append("prior marketplace sidecar missing")
        elif baseline_sidecar is None:
            problems.append("baseline sidecar digest is missing")
        elif lib.sha256_file(sidecar) != baseline_sidecar:
            problems.append("prior marketplace sidecar changed")
        # The three prior-stable scopes must still equal the smoke
        # baseline: plugin row, native registration and runtime selection.
        baseline_prior = baseline.get("prior_state") if baseline else None
        if not isinstance(baseline_prior, dict):
            baseline_prior = None
        prior_version = context.inputs["prior"]["version"]
        plugin_row = lib.installed_aquarium(context.codex, context.marketplace)
        if plugin_row is None:
            problems.append("prior plugin no longer installed")
        elif plugin_row.get("version") != prior_version:
            problems.append(
                f"prior plugin version changed to {plugin_row.get('version')}"
            )
        registration = lib.marketplace_registrations(context.codex).get(
            context.marketplace
        )
        if registration != str(context.marketplace_path(PRIOR_KIND)):
            problems.append(f"marketplace registration changed to {registration!r}")
        runtime_root, _launcher = lib.runtime_locations(context.home)
        generation = None
        try:
            generation, receipt = lib.read_current_generation(context.home)
        except lib.RecipeError as error:
            problems.append(f"status runtime generation unreadable: {error}")
        else:
            if receipt.get("plugin_version") != f"v{prior_version}":
                problems.append(
                    f"runtime generation binds {receipt.get('plugin_version')}"
                )
        if baseline_prior is None:
            problems.append("smoke prior-state baseline is missing")
        else:
            if plugin_row != baseline_prior.get("plugin_row"):
                problems.append("prior plugin row differs from the smoke baseline")
            if registration != baseline_prior.get("registration"):
                problems.append("registration differs from the smoke baseline")
            if generation != baseline_prior.get("generation"):
                problems.append("runtime generation differs from the smoke baseline")
            baseline_receipt = baseline_prior.get("receipt_sha256")
            if baseline_receipt is not None and generation is not None:
                receipt_path = runtime_root / "versions" / generation / "runtime.json"
                if lib.sha256_file(receipt_path) != baseline_receipt:
                    problems.append("runtime receipt differs from the smoke baseline")
        postcondition_ok = fixture_absent and leftover_absent and not problems
        document = {
            "fixture_removed": fixture_removed,
            "fixture_absent": fixture_absent,
            "probe_leftover_absent": leftover_absent,
            "problems": problems,
            "candidate_plugin_version": context.established_plugin_version(),
        }
        lib.write_document(
            results / "post-cleanup-inventory.json",
            {
                "entries": current if current is not None else [],
                "postcondition_ok": postcondition_ok,
                "problems": problems,
            },
        )
        lib.write_document(results / "consumer-cleanup.json", document)
        return lib.finish(
            "manual-hold",
            "pass" if postcondition_ok else "fail",
            {"phase": phase, "cleanup": document, "note": "minimal offline hold"},
            consumer_cleanup="verified" if postcondition_ok else "failed",
        )
    raise lib.RecipeError(f"unknown manual-hold phase: {phase}")


def run_guard_failure_probe(context: Context) -> int:
    """J-F: stage every declared output, then exit nonzero from the guard
    probe so the native verdict is FAIL; the recipe never reports pass."""
    correct = lib.guard(context.root)
    probe_identity = dict(correct)
    probe_identity["hardware_uuid"] = lib.wrong_uuid()
    guard_rejected = False
    problem = ""
    try:
        lib.verify_guest_identity(identity=probe_identity)
        problem = "the wrong-UUID guard probe did not reject the guest"
    except lib.RecipeError as error:
        guard_rejected = True
        problem = str(error)
    leftover = context.home / PROBE_LEFTOVER
    leftover.write_text(
        "Declared consumer leftover from the guard-failure probe.\n",
        encoding="utf-8",
    )
    return lib.finish(
        "guard-failure-probe",
        "fail",
        {
            "guard_rejected": guard_rejected,
            "guard_problem": problem,
            "declared_leftover": str(leftover),
        },
        consumer_cleanup="failed",
    )


def run_immutability_probe(context: Context) -> int:
    verified = lib.verify_sealed_inputs(context.root)
    return lib.finish(
        "immutability-probe",
        "pass",
        {"sealed": verified, "consumer_state": "none created"},
        consumer_cleanup="verified",
    )


def run_vm_blocked_probe(context: Context) -> int:
    return lib.finish(
        "vm-blocked-probe",
        "pass",
        {"identity": context.identity, "consumer_state": "none created"},
        consumer_cleanup="verified",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", required=True)
    parser.add_argument("--phase", default="run")
    parser.add_argument("--fixture")
    arguments = parser.parse_args()
    if not os.environ.get("HAEPARI_PARENT_CONTEXT"):
        print("guest recipes require the managed runner context", file=sys.stderr)
        return 2
    runners = {
        "baseline": run_baseline,
        "install": run_install,
        "upgrade": run_upgrade,
        "migration-failure": run_migration_failure,
        "guard-failure-probe": run_guard_failure_probe,
        "immutability-probe": run_immutability_probe,
        "vm-blocked-probe": run_vm_blocked_probe,
    }
    try:
        context = Context()
    except lib.IdentityError as error:
        # An identity rejection performs no write: no result, inventory or
        # ledger file, no HOME change and no clone.
        print(
            json.dumps(
                {
                    "schema": lib.RESULT_SCHEMA,
                    "suite": arguments.suite,
                    "outcome": "incomplete",
                    "problem": str(error),
                    "writes": "none",
                }
            )
        )
        return 2
    try:
        if arguments.suite == "manual-hold":
            return run_manual_hold(context, arguments.phase)
        if arguments.suite not in runners:
            raise lib.RecipeError(f"unknown suite: {arguments.suite}")
        lib.guard(context.root)
        return runners[arguments.suite](context)
    except lib.RecipeError as error:
        return lib.finish(
            arguments.suite,
            error.outcome,
            {"problem": str(error)},
            consumer_cleanup="unverified",
        )
    except lib.TreeDigestError as error:
        # Safety net: an unconverted strict-validation error still produces
        # a structured non-pass result instead of a traceback.
        return lib.finish(
            arguments.suite,
            "incomplete",
            {"problem": f"TreeDigestError: {error}"},
            consumer_cleanup="unverified",
        )
    except OSError as error:
        return lib.finish(
            arguments.suite,
            "incomplete",
            {"problem": f"OSError: {error}"},
            consumer_cleanup="unverified",
        )
    except ValueError as error:
        # Defense in depth for decoding paths outside the structured
        # readers, for example subprocess text decoding and the ledger.
        return lib.finish(
            arguments.suite,
            "incomplete",
            {"problem": f"ValueError: {error}"},
            consumer_cleanup="unverified",
        )


if __name__ == "__main__":
    raise SystemExit(main())
