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
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import tomllib

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
        # The codex-home-skills scope covers the active per-home skills the
        # native client can load, so a planted or shadowing copy there is
        # visible to every snapshot and comparison.
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
            (
                "codex-home-skills",
                self.home / ".codex/skills",
                ".codex/skills",
            ),
        ]

    def snapshot(
        self,
        suite: str,
        phase: str,
        profile: str = "candidate",
        capture: str | None = None,
    ) -> list[dict[str, Any]]:
        """Capture the scoped inventories under a fixed file name.

        Without `capture` the file is `inventory-<phase>.json` keyed by the
        semantic phase (the TASK-088 suites' contract). With `capture`, the
        J-RA suites write `inventory-<capture>.json` and merge that capture
        into the suite's aggregate `inventories.json` by read-modify-write,
        so captures taken by separate phase processes all survive.
        """
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
        name = capture if capture is not None else phase
        document = lib.write_inventory(
            lib.results_directory(suite) / f"inventory-{name}.json",
            phase,
            entries,
            self.profile_digest(profile),
            lib.sha256_file(Path(__file__)),
        )
        if capture is None:
            lib.record_inventory(suite, phase, document)
        else:
            aggregate_path = lib.results_directory(suite) / "inventories.json"
            aggregate = lib.read_json_safe(aggregate_path)
            if not isinstance(aggregate, dict) or not isinstance(
                aggregate.get("inventories"), dict
            ):
                aggregate = {
                    "schema": "aquarium.vm-suite-inventories/v1",
                    "inventories": {},
                }
            aggregate["inventories"][capture] = document
            aggregate_path.write_text(
                json.dumps(aggregate, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
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


STALE_SKILL_NAME = "task-handler"
EVIDENCE_CASES = (
    "baseline",
    "upgrade",
    "task-setup",
    "epic-setup",
    "preservation-setup",
    "runtime-update",
    "task-startup",
    "epic-startup",
    "release-startup",
    "stale-skill",
)
ARCHIVE_BYTES_BOUND = lib.EVIDENCE_ARCHIVE_BYTES_BOUND
ARCHIVE_TOTAL_BYTES_BOUND = lib.EVIDENCE_TOTAL_BYTES_BOUND


def baseline_combination_from_profile(stable: dict[str, Any]) -> dict[str, str]:
    """Driver-reported shapes: bare aquarium/codex, `v`-prefixed Podway."""

    def component_version(name: str) -> str:
        for component in stable.get("components", []):
            if isinstance(component, dict) and component.get("name") == name:
                version = component.get("version")
                if isinstance(version, str):
                    return version
        raise lib.RecipeError(
            f"the stable profile does not pin the {name} version", "incomplete"
        )

    podway_version = component_version("podway")
    return {
        "aquarium": component_version("aquarium-plugin"),
        "codex": component_version("codex"),
        "podway": podway_version
        if podway_version.startswith("v")
        else "v" + podway_version,
    }


def podway_identity_record(context: Context) -> dict[str, Any]:
    """Observed Podway identity against the stable profile's pins.

    The digest comparison happens before any Podway-dependent step; a
    same-version executable with different bytes refuses with no mutation.
    """
    stable = context.profile("stable")
    pinned = None
    for component in stable.get("components", []):
        if isinstance(component, dict) and component.get("name") == "podway":
            pinned = component.get("executable_sha256")
    executable = Path(lib.context_value("AQUARIUM_GUEST_PODWAY"))
    observed = "sha256:" + lib.sha256_file(executable)
    if pinned != observed:
        raise lib.RecipeError(
            "the retained test VM does not match the selected released baseline; "
            "select a matching baseline before mutation. Podway digest differs from the stable "
            f"profile pin ({observed} != {pinned}); the unverified executable "
            "is never executed",
            "incomplete",
        )
    # Only a digest-matching executable is executed.
    version_output = lib.run([str(executable), "version", "--json"], timeout=120)
    try:
        reported = json.loads(version_output.stdout)
    except ValueError:
        reported = {"raw": version_output.stdout.strip()[:200]}
    return {
        "executable": str(executable),
        "executable_sha256": observed,
        "profile_pin": pinned,
        "match": True,
        "version_json": reported,
    }


def codex_identity_record(context: Context) -> dict[str, Any]:
    """Non-secret Codex identity, recorded before any model turn."""
    version = lib.run([context.codex, "--version"]).stdout.strip()
    login = lib.run([context.codex, "login", "status"], timeout=120)
    login_lines = [
        line.strip()
        for stream in (login.stdout, login.stderr)
        for line in stream.splitlines()
    ]
    if login.returncode != 0 or "Logged in using ChatGPT" not in login_lines:
        raise lib.RecipeError(
            "the guest Codex ChatGPT login cannot be verified", "incomplete"
        )
    config_model = "installation-default"
    config = context.home / ".codex/config.toml"
    if config.is_file():
        try:
            parsed = tomllib.loads(config.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
            parsed = {}
        if isinstance(parsed.get("model"), str) and parsed["model"]:
            config_model = parsed["model"]
    return {
        "version": version,
        "login_status": {
            "exit": login.returncode,
            "mode": "chatgpt",
            "line": "Logged in using ChatGPT",
        },
        "model": config_model,
    }


def preservation_fixture(context: Context) -> dict[str, Any]:
    """The driver's baseline expects a preservation repository with a
    customized managed source, meaningful Git work and a report."""
    destination = context.root / "acceptance-run/preservation"
    fixture = lib.seed_fixture(context.checkout, destination)
    procedures = destination / ".podway/procedures"
    procedures.mkdir(parents=True, exist_ok=True)
    custom = procedures / "aquarium-task-v2.yaml"
    shutil.copyfile(
        context.root
        / f"{PRIOR_KIND}/plugins/aquarium/assets/podway/procedures/aquarium-task-v2.yaml",
        custom,
    )
    custom.write_text(custom.read_text() + "# preserved customization\n")
    (destination / "HISTORICAL-REPORT.md").write_text(
        "Historical synthetic report from the prior release.\n"
    )
    status = lib.run(
        ["git", "-C", str(destination), "status", "--porcelain"], timeout=120
    )
    return {
        "fixture": fixture,
        "custom_source": str(custom),
        "custom_sha256": lib.sha256_file(custom),
        "uncommitted": bool(status.stdout.strip()),
    }


def _scope_entries(root: Path, scope: str, base: str) -> list[dict[str, Any]] | None:
    """Content identities (path, sha256, executable bit, symlink target) of
    one scope root; None when the root is absent."""
    from tree_digest import TreeDigestError, inventory_entries

    if not root.exists():
        return None
    try:
        return inventory_entries(root, scope, base)
    except TreeDigestError as error:
        raise lib.RecipeError(
            f"unsafe inventoried scope ({scope}): {error}", "incomplete"
        ) from error


SECRET_SETTING_RE = re.compile(
    r"token|key|secret|password|auth|credential", re.IGNORECASE
)


def _normalize_toml_value(value: Any, prefix: str, redacted: list[str]) -> Any:
    """Recursively normalize a parsed TOML value while redacting secret keys."""
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in sorted(value.items()):
            path = f"{prefix}.{key}" if prefix else key
            if SECRET_SETTING_RE.search(key):
                redacted.append(path)
                continue
            result[key] = _normalize_toml_value(item, path, redacted)
        return result
    if isinstance(value, list):
        return [_normalize_toml_value(item, prefix, redacted) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _collect_secret_keys(value: Any, prefix: str, redacted: list[str]) -> None:
    """Record secret key paths inside tables excluded from normalized settings."""
    if isinstance(value, dict):
        for key, item in sorted(value.items()):
            path = f"{prefix}.{key}" if prefix else key
            if SECRET_SETTING_RE.search(key):
                redacted.append(path)
                continue
            _collect_secret_keys(item, path, redacted)
    elif isinstance(value, list):
        for item in value:
            _collect_secret_keys(item, prefix, redacted)


def _is_skill_setting_key(key: str) -> bool:
    lowered = key.lower()
    return (
        lowered in {"skill", "skills"}
        or lowered.startswith("skill_")
        or lowered.endswith(("_skill", "_skills"))
    )


def effective_configuration_record(context: Context) -> dict[str, Any]:
    """Effective Codex configuration with secret values redacted.

    The whole config file is read to compute its digest and parsed with
    `tomllib`; a setting whose name matches a secret pattern is recorded
    only as redacted-by-name, and auth files outside the config are never
    opened. Settings are normalized by exact table identity (`plugins.<id>`,
    `features`, explicit skill tables/keys, and top-level non-secret
    settings), with an explicit note when features or skill settings are
    absent and `parse_error` recorded when `config.toml` cannot be parsed.
    """
    config = context.home / ".codex/config.toml"
    document: dict[str, Any] = {
        "provenance": "~/.codex/config.toml (secret values redacted by name)",
        "marketplaces": {
            name: source
            for name, source in sorted(
                lib.marketplace_registrations(context.codex).items()
            )
        },
        "installed_plugin": lib.installed_aquarium(context.codex, context.marketplace),
        "enabled_plugins": {},
        "settings": {},
        "features": {},
        "skill_settings": {},
        "redacted_key_names": [],
    }
    if not config.is_file():
        document["provenance"] += "; config.toml absent"
        document["features_note"] = "no config file"
        document["skill_settings_note"] = "no config file"
        return document
    document["config_sha256"] = lib.sha256_file(config)
    try:
        parsed = tomllib.loads(config.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        document["parse_error"] = str(error)
        return document
    redacted: list[str] = []
    plugins_table = parsed.get("plugins")
    if isinstance(plugins_table, dict):
        for plugin_id, plugin_entry in sorted(plugins_table.items()):
            prefix = f'plugins."{plugin_id}"'
            if isinstance(plugin_entry, dict):
                normalized_entry = _normalize_toml_value(plugin_entry, prefix, redacted)
                document["enabled_plugins"][plugin_id] = normalized_entry.get("enabled")
            elif SECRET_SETTING_RE.search(plugin_id):
                redacted.append(prefix)
            else:
                document["enabled_plugins"][plugin_id] = _normalize_toml_value(
                    plugin_entry, prefix, redacted
                )
    if "features" in parsed and isinstance(parsed.get("features"), dict):
        document["features"] = _normalize_toml_value(
            parsed["features"], "features", redacted
        )
    else:
        document["features_note"] = "no [features] table in the config"
    for key, value in sorted(parsed.items()):
        if key in {"plugins", "features"}:
            continue
        if _is_skill_setting_key(key):
            if SECRET_SETTING_RE.search(key):
                redacted.append(key)
            else:
                document["skill_settings"][key] = _normalize_toml_value(
                    value, key, redacted
                )
            continue
        if isinstance(value, dict):
            _collect_secret_keys(value, key, redacted)
            continue
        if SECRET_SETTING_RE.search(key):
            redacted.append(key)
            continue
        document["settings"][key] = _normalize_toml_value(value, key, redacted)
    document["redacted_key_names"] = sorted(redacted)
    if not document["skill_settings"]:
        document["skill_settings_note"] = "no key or table names skills"
    return document


def _declared_skill_name(directory: Path) -> str | None:
    """A skill's declared name from its SKILL.md front matter, falling back
    to the directory name; None when the entry is not a skill directory."""
    if not directory.is_dir():
        return None
    front = directory / "SKILL.md"
    if front.is_file():
        try:
            lines = front.read_text(encoding="utf-8").splitlines()
        except (OSError, ValueError):
            lines = []
        if lines and lines[0].strip() == "---":
            for line in lines[1:]:
                if line.strip() == "---":
                    break
                match = re.match(r"name:\s*(.+)", line)
                if match:
                    return match[1].strip().strip("\"'")
    return directory.name


def skill_identity_document(
    context: Context, stage: str, *, candidate_profile: str = "candidate"
) -> dict[str, Any]:
    """Whole-tree skill identity across the native scopes the dossier names.

    Each applicable scope is inspected separately with provenance and
    content identities; the installed plugin's own skill tree is compared
    against the profile pin of `stage`, the pinned shared skill trees are
    compared with their profile pins where a content pin exists, duplicate
    and shadowing copies are detected by skill name across every loadable
    scope, and `comparisons.all_passed` binds the scenario predicate to
    every recorded comparison.
    """
    profile_name = "stable" if stage == "prior" else candidate_profile
    profile = context.profile(profile_name)
    plugin_pin = None
    pinned_skills: dict[str, dict[str, Any]] = {}
    for component in profile.get("components", []):
        if not isinstance(component, dict):
            continue
        if component.get("name") == "aquarium-plugin":
            tree = component.get("skill_tree")
            if isinstance(tree, dict):
                plugin_pin = tree.get("sha256")
            continue
        skill_tree = component.get("skill_tree")
        # Only guest-role content pins belong to the guest predicate; the
        # host use-haepari pin stays with the host inspection.
        if (
            isinstance(skill_tree, dict)
            and component.get("role") == "guest"
            and isinstance(skill_tree.get("sha256"), str)
        ):
            pinned_skills[skill_tree.get("name", "")] = {
                "pin": skill_tree["sha256"],
                "component": component.get("name"),
                "scope": skill_tree.get("installation_scope"),
            }
    installed_root: Path | None = None
    plugin_cache = (
        context.home
        / ".codex/plugins/cache"
        / context.marketplace
        / "aquarium"
        / (context.established_plugin_version() or "")
    )
    if plugin_cache.is_dir():
        installed_root = plugin_cache / "skills"
    scopes: list[dict[str, Any]] = []
    for scope, root, base in (
        ("shared-agents-skills", context.home / ".agents/skills", ".agents/skills"),
        ("codex-home-skills", context.home / ".codex/skills", ".codex/skills"),
        ("codex-rules", context.home / ".codex/rules", ".codex/rules"),
    ):
        entries = _scope_entries(root, scope, base)
        scopes.append(
            {
                "scope": scope,
                "root": f"~/{base}",
                "entries": entries,
                "applicability": (
                    "absent" if entries is None else f"{len(entries)} content entries"
                ),
                "provenance": "guest starting state",
            }
        )
    plugin_assets: dict[str, Any] = {"scope": "plugin-assets", "applicability": "n/a"}
    if plugin_cache.is_dir() and (plugin_cache / "assets").is_dir():
        try:
            plugin_assets["digest"] = lib.inventory_tree_sha256_from_directory(
                plugin_cache / "assets"
            )
            plugin_assets["applicability"] = "installed plugin assets"
        except lib.TreeDigestError as error:
            plugin_assets["problem"] = str(error)
    scopes.append(plugin_assets)
    discovery_roots = []
    for label, repository in (
        ("candidate-checkout", context.checkout),
        ("task-fixture", context.root / "acceptance-run/task"),
        ("epic-fixture", context.root / "acceptance-run/epic"),
        ("preservation-fixture", context.root / "acceptance-run/preservation"),
    ):
        if not repository.is_dir():
            continue
        roots = []
        for name in (".agents", ".codex", "AGENTS.md"):
            path = repository / name
            if not path.exists():
                continue
            if path.is_file():
                roots.append(
                    {
                        "path": name,
                        "sha256": lib.sha256_file(path),
                        "executable": bool(path.stat().st_mode & 0o111),
                    }
                )
            else:
                roots.append(
                    {
                        "path": name,
                        "entries": _scope_entries(
                            path, "project-discovery", f"{label}/{name}"
                        ),
                    }
                )
        discovery_roots.append({"root": label, "content": roots})
    scopes.append(
        {
            "scope": "project-discovery",
            "roots": discovery_roots,
            "applicability": "candidate checkout and acceptance fixtures",
        }
    )
    trees: dict[str, Any] = {}
    plugin_problems: list[str] = []
    if installed_root is not None and installed_root.is_dir():
        digest = lib.skill_tree_digest(context.checkout, installed_root)
        trees["installed-plugin-skills"] = {
            "algorithm": lib.SKILL_TREE_DIGEST_ALGORITHM,
            "sha256": digest,
            "profile_pin": plugin_pin,
            "found": True,
            "match": plugin_pin == digest,
            "root": str(installed_root),
        }
        if plugin_pin != digest:
            plugin_problems.append(
                "installed-plugin-skills: observed tree differs from the pin"
            )
    else:
        trees["installed-plugin-skills"] = {
            "algorithm": lib.SKILL_TREE_DIGEST_ALGORITHM,
            "profile_pin": plugin_pin,
            "found": False,
            "match": False,
        }
        plugin_problems.append("installed-plugin-skills: tree not found")
    pinned_problems: list[str] = []
    for name, pinned in sorted(pinned_skills.items()):
        tree = context.home / ".agents/skills" / name
        if not tree.is_dir():
            trees[name] = {
                "algorithm": lib.SKILL_TREE_DIGEST_ALGORITHM,
                "root": str(tree),
                "profile_pin": pinned["pin"],
                "found": False,
                "match": False,
            }
            pinned_problems.append(f"{name}: pinned tree not found")
            continue
        digest = lib.skill_tree_digest(context.checkout, tree)
        match = pinned["pin"] == digest
        trees[name] = {
            "algorithm": lib.SKILL_TREE_DIGEST_ALGORITHM,
            "sha256": digest,
            "root": str(tree),
            "profile_pin": pinned["pin"],
            "found": True,
            "match": match,
        }
        if not match:
            pinned_problems.append(f"{name}: observed tree differs from the pin")
    # Duplicate and shadowing detection by skill name across every loadable
    # scope: the installed plugin's skills, the active per-home skills, the
    # shared agents skills and the loadable project scopes. A skill's
    # declared name comes from its SKILL.md front matter, falling back to
    # the directory name only when no name is declared.
    loadable: dict[str, set[str]] = {}
    if installed_root is not None and installed_root.is_dir():
        loadable["installed-plugin-skills"] = {
            "aquarium:" + (name or entry.name)
            for entry in installed_root.iterdir()
            if entry.is_dir()
            for name in (_declared_skill_name(entry),)
        }
    for label, root in (
        ("codex-home-skills", context.home / ".codex/skills"),
        ("shared-agents-skills", context.home / ".agents/skills"),
        ("project-discovery:candidate-checkout", context.checkout / ".agents/skills"),
        (
            "project-discovery:task-fixture",
            context.root / "acceptance-run/task/.agents/skills",
        ),
        (
            "project-discovery:epic-fixture",
            context.root / "acceptance-run/epic/.agents/skills",
        ),
        (
            "project-discovery:preservation-fixture",
            context.root / "acceptance-run/preservation/.agents/skills",
        ),
    ):
        if root.is_dir():
            loadable[label] = {
                name
                for name in (_declared_skill_name(entry) for entry in root.iterdir())
                if name is not None
            }
    duplicates: list[str] = []
    plugin_names = {
        name.removeprefix("aquarium:"): name
        for name in loadable.get("installed-plugin-skills", set())
    }
    seen: dict[str, list[str]] = {}
    for scope, names in loadable.items():
        for name in names:
            seen.setdefault(name, []).append(scope)
    for name, scopes_of in sorted(seen.items()):
        if len(scopes_of) > 1:
            duplicates.append(f"{name}: loadable in {', '.join(sorted(scopes_of))}")
        elif name in plugin_names and "installed-plugin-skills" not in scopes_of:
            duplicates.append(
                f"{name}: un-namespaced copy in {scopes_of[0]} shadows "
                f"{plugin_names[name]}"
            )
    required = ["installed-plugin-skills", *sorted(pinned_skills)]
    problems = plugin_problems + pinned_problems
    comparisons = {
        name: trees[name].get("match") is True for name in required if name in trees
    }
    return {
        "schema": "aquarium.vm-skill-identity/v1",
        "stage": stage,
        "scopes": scopes,
        "skill_trees": trees,
        "duplicates": duplicates,
        "comparisons": {
            "checked": sorted(comparisons),
            "required": sorted(required),
            "problems": problems,
            "all_passed": (
                sorted(comparisons) == sorted(required)
                and all(comparisons.values())
                and not duplicates
            ),
        },
        "effective_configuration": effective_configuration_record(context),
    }


def acceptance_request(context: Context) -> Path:
    request_path = context.root / "acceptance/request.json"
    if request_path.is_file():
        return request_path
    stable = context.profile("stable")
    combination = baseline_combination_from_profile(stable)
    baseline_podway = next(
        component for component in stable["components"] if component["name"] == "podway"
    )
    release = context.inputs.get("podway_upgrade", {})
    generation = 1
    if combination["podway"] == release.get("version") and baseline_podway.get(
        "executable_sha256"
    ) == "sha256:" + release.get("binary_sha256", ""):
        generation = release.get("contract_generation")
    elif combination["podway"] != "v0.2.14":
        raise lib.RecipeError(
            "baseline requires its matching sealed Podway contract generation",
            "incomplete",
        )
    import run_acceptance as driver

    driver.podway_generation_options({"podway_contract_generation": generation})
    request = {
        "schema": "aquarium.vm-acceptance-request/v1",
        "expected_guest_uuid": lib.context_value("AQUARIUM_EXPECTED_GUEST_UUID"),
        "run_root": str(context.root / "acceptance-run"),
        "released_plugin_root": str(
            context.home
            / ".codex/plugins/cache"
            / context.marketplace
            / "aquarium"
            / context.inputs["prior"]["version"]
        ),
        "released_marketplace_root": str(context.marketplace_path(PRIOR_KIND)),
        "tools": {
            "codex": context.codex,
            "podway": lib.context_value("AQUARIUM_GUEST_PODWAY"),
            "python": context.python,
        },
        "codex_args": [
            "--sandbox",
            "workspace-write",
            "--add-dir",
            str(context.home / ".aquarium"),
            "--add-dir",
            str(context.home / ".local/bin"),
        ],
        "baseline_combination": combination,
        "podway_contract_generation": generation,
        "authority": {
            "kind": "explicit-vm-test",
            "reference": "epic-019-vm-test-authority",
            "observer": "coordinator-fixture-operator",
        },
        "baseline_setup": {},
    }
    lib.write_document(request_path, request)
    return request_path


def _receipt_plugin_version(receipt: dict[str, Any]) -> str:
    """Return a string `plugin_version` from a generation receipt, or `""`."""
    value = receipt.get("plugin_version") if isinstance(receipt, dict) else None
    return value if isinstance(value, str) else ""


def abort_preimage(context: Context) -> dict[str, Any]:
    """Build and persist the abort-residue preimage before any effect.

    The successor refuses without mutation when a declared residue exists
    outside the normalization's scope, or when the current runtime
    selection is unreadable (an uncertain selection can never prove a
    generation unselected). The bounded preimage is durably written before
    `ensure_prior_stable` or any deletion runs, so a mid-loop failure still
    hands over the original receipts.
    """
    planted = context.home / ".codex/skills" / STALE_SKILL_NAME
    if planted.exists() or planted.is_symlink():
        raise lib.RecipeError(
            f"stale-skill residue exists outside the Job root: {planted}; "
            "it is preserved and the successor refuses to start",
            "incomplete",
        )
    leftover = context.home / PROBE_LEFTOVER
    if leftover.exists() or leftover.is_symlink():
        raise lib.RecipeError(
            f"probe leftover exists outside the Job root: {leftover}; "
            "it is preserved and the successor refuses to start",
            "incomplete",
        )
    current, _receipt = lib.read_current_generation(context.home)
    versions = context.home / ".aquarium/status-runtime/versions"
    generations = []
    for name, receipt in sorted(lib.generation_receipts(context.home).items()):
        if _receipt_plugin_version(receipt) != context.dev_version:
            continue
        receipt_path = versions / name / "runtime.json"
        generations.append(
            {
                "generation": name,
                "selected_at_preimage": name == current,
                "receipt_sha256": lib.sha256_file(receipt_path)
                if receipt_path.is_file()
                else None,
                "receipt": receipt,
            }
        )
    foreign_preserved = []
    for name, receipt in sorted(lib.generation_receipts(context.home).items()):
        plugin_version = _receipt_plugin_version(receipt)
        if "-dev." not in plugin_version:
            continue
        if plugin_version == context.dev_version:
            continue
        receipt_path = versions / name / "runtime.json"
        foreign_preserved.append(
            {
                "generation": name,
                "plugin_version": plugin_version,
                "receipt_sha256": lib.sha256_file(receipt_path)
                if receipt_path.is_file()
                else None,
            }
        )
    record = {
        "runtime_selection_at_preimage": current,
        "runtime_generations": generations,
        "foreign_dev_generations_preserved": foreign_preserved,
        "marketplace_registration_before": lib.marketplace_registrations(
            context.codex
        ).get(context.marketplace),
    }
    # Durable before any effect: a crash in the removal loop still leaves
    # the original receipts for the abort settlement. The preparation log
    # also carries the record.
    print(json.dumps(record, ensure_ascii=False))
    lib.write_document(
        lib.results_directory("release-acceptance") / "abort-normalization.json",
        record,
    )
    return record


def finish_abort_normalization(
    context: Context, record: dict[str, Any]
) -> dict[str, Any]:
    """Remove the dev-stamped generations after prior selection is restored.

    `ensure_prior_stable` has re-selected the prior generation, so an
    approved-update generation that was selected at the abort is now unselected and is
    removed with the persisted preimage as evidence. The marketplace
    predecessor swap and the final residue disposition are recorded in the
    same abort record.
    """
    current, current_receipt = lib.read_current_generation(context.home)
    versions = context.home / ".aquarium/status-runtime/versions"
    removed = []
    already_absent = []
    for entry in record["runtime_generations"]:
        name = entry["generation"]
        if name == current:
            continue
        if versions.joinpath(name).exists():
            shutil.rmtree(versions / name)
            removed.append(name)
        else:
            already_absent.append(name)
    remaining = [
        name
        for name, receipt in lib.generation_receipts(context.home).items()
        if _receipt_plugin_version(receipt) == context.dev_version
    ]
    record["runtime_generations_removed"] = removed
    record["runtime_generations_already_absent"] = already_absent
    record["runtime_selection_after"] = current
    record["marketplace_registration_after"] = lib.marketplace_registrations(
        context.codex
    ).get(context.marketplace)
    record["marketplace_predecessor_normalized"] = record[
        "marketplace_registration_after"
    ] == str(context.marketplace_path(PRIOR_KIND)) and record[
        "marketplace_registration_before"
    ] != str(context.marketplace_path(PRIOR_KIND))
    # The dev-stamp check reads the selected receipt's plugin_version,
    # never the generation directory name; a None selection refuses.
    selected_plugin_version = current_receipt.get("plugin_version")
    record["runtime_selection_plugin_version"] = selected_plugin_version
    selection_dev_stamped = "-dev." in _receipt_plugin_version(current_receipt)
    record["residue_disposition_verified"] = not remaining and not selection_dev_stamped
    record["dev_stamped_generations_remaining"] = remaining
    print(json.dumps(record, ensure_ascii=False))
    lib.write_document(
        lib.results_directory("release-acceptance") / "abort-normalization.json",
        record,
    )
    if remaining:
        raise lib.RecipeError(
            "this candidate's dev-stamped generations remain after "
            f"normalization: {remaining}; the successor refuses to continue",
            "incomplete",
        )
    if selection_dev_stamped:
        raise lib.RecipeError(
            "the post-restoration runtime selection is dev-stamped "
            f"({current!r} binds {selected_plugin_version}); the successor "
            "refuses to continue",
            "incomplete",
        )
    return record


def _operation_prefixes(members: list[str]) -> list[str]:
    """Find native windows even when interruption prevented their receipt."""
    suffixes = {
        "input",
        "jsonl",
        "stderr",
        "last",
        "invocation.json",
        "setup-before.json",
        "setup-after.json",
    }
    prefixes = set()
    for member in members:
        path = Path(member)
        ordinal, separator, suffix = path.name.partition(".")
        if (
            separator
            and ordinal.isdecimal()
            and (
                suffix in suffixes
                or (suffix.startswith("reconciled-") and suffix.endswith(".json"))
            )
        ):
            prefixes.add((path.parent / ordinal).as_posix())
    return sorted(prefixes)


def _window_requirements(
    run_root: Path, case: str, members: list[str], include_last: bool, gaps: list[str]
) -> list[str]:
    """Require wrapper-produced originals from every operation window.

    The class is defined independently of what exists: a case whose
    operations directory holds no complete latest window records the gap.
    """
    directory = Path("operations") / case
    prefixes = _operation_prefixes(
        [member for member in members if Path(member).parent == directory]
    )
    if not prefixes:
        # The required window class, named so a partial run records the
        # gap in its manifest instead of raising.
        return [f"operations/{case}/ operation window"]
    required = []
    for prefix in prefixes:
        required += [
            f"{prefix}.invocation.json",
            f"{prefix}.input",
            f"{prefix}.jsonl",
            f"{prefix}.stderr",
        ]
        if case.endswith("-setup"):
            required += [f"{prefix}.setup-before.json", f"{prefix}.setup-after.json"]
        if include_last and prefix == prefixes[-1]:
            required.append(f"{prefix}.last")
    return required


def _setup_observation_evidence(
    run_root: Path, case: str
) -> tuple[list[str], list[str], list[str]]:
    """Transport native setup captures and verify their producer bindings."""
    members: set[str] = set()
    required: set[str] = set()
    gaps: list[str] = []
    fixtures = (
        ("task", "epic", "preservation")
        if case in {"baseline", "upgrade"}
        else (case.removesuffix("-setup"),)
    )
    phases = ("baseline",) if case == "baseline" else ("update", "recovery")
    for phase in phases:
        for fixture in fixtures:
            if case == "upgrade":
                continue
            directory = run_root / "setup-observations" / phase / fixture
            try:
                contained = directory.resolve().is_relative_to(run_root.resolve())
            except (OSError, RuntimeError, ValueError):
                contained = False
            if directory.is_symlink() or not contained:
                gaps.append(f"{phase}/{fixture} has an unsafe capture directory")
                continue
            for path in sorted(directory.rglob("*.json")):
                relative = path.relative_to(run_root).as_posix()
                if path.is_symlink() or not path.is_file():
                    gaps.append(f"{relative} is not a regular capture")
                    continue
                members.add(relative)
                if path.stem != lib.sha256_file(path):
                    gaps.append(f"{relative} differs from its capture digest")

    def references(value: Any, fixture: str) -> None:
        if isinstance(value, list):
            for entry in value:
                references(entry, fixture)
        elif isinstance(value, dict):
            if "public_observation" in value or "observation_sha256" in value:
                source = value.get("public_observation")
                digest = value.get("observation_sha256")
                if not isinstance(source, str) or not isinstance(digest, str):
                    gaps.append(f"{fixture} has an invalid setup capture binding")
                    return
                path = Path(source)
                if not path.is_absolute():
                    path = run_root / path
                try:
                    relative = path.resolve().relative_to(run_root.resolve())
                except (OSError, RuntimeError, ValueError):
                    gaps.append(f"{fixture} references a capture outside the run root")
                    return
                parts = relative.parts
                if (
                    len(parts) != 4
                    or parts[0] != "setup-observations"
                    or parts[1]
                    not in (
                        {"baseline"}
                        if case == "baseline"
                        else {"baseline", "update", "recovery"}
                    )
                    or parts[2] != fixture
                ):
                    gaps.append(f"{fixture} references another setup capture family")
                    return
                if case != "upgrade" and parts[1] in phases:
                    required.add(relative.as_posix())
                if path.is_symlink() or not path.is_file():
                    gaps.append(f"{relative} is missing or not a regular capture")
                elif digest != "sha256:" + lib.sha256_file(path):
                    gaps.append(f"{relative} differs from its observation binding")
            for entry in value.values():
                references(entry, fixture)

    if case in {"baseline", "upgrade"}:
        document = lib.read_json_safe(
            run_root
            / ("baseline.json" if case == "baseline" else "upgrade-observation.json")
        )
        setup = document.get("setup", {}) if isinstance(document, dict) else {}
        for fixture in fixtures:
            record = setup.get(fixture) if isinstance(setup, dict) else None
            capture = (
                record
                if case == "baseline"
                else record.get("setup")
                if isinstance(record, dict)
                else None
            )
            if not isinstance(capture, dict) or "public_observation" not in capture:
                gaps.append(f"{fixture} has no {case} setup capture binding")
            else:
                references(record, fixture)
        if case == "upgrade":
            result = lib.read_json_safe(run_root / "result.json")
            for row in result.get("cases", []) if isinstance(result, dict) else []:
                setup = row.get("setup", {}) if isinstance(row, dict) else {}
                for fixture in fixtures:
                    if isinstance(setup, dict) and fixture in setup:
                        references(setup[fixture], fixture)
    else:
        directory = run_root / "operations" / case
        prefixes = _operation_prefixes(
            [path.name for path in directory.iterdir()] if directory.is_dir() else []
        )
        records = []
        for prefix in prefixes:
            records += [
                directory / f"{prefix}.setup-before.json",
                directory / f"{prefix}.setup-after.json",
            ]
            records += sorted(directory.glob(f"{prefix}.reconciled-*.json"))
        for path in records:
            record = lib.read_json_safe(path)
            if not isinstance(record, dict):
                gaps.append(f"{path.relative_to(run_root)} is missing or malformed")
            else:
                references(record, fixtures[0])
        if prefixes and not required:
            gaps.append(f"{fixtures[0]} has no candidate setup capture binding")
    return sorted(members), sorted(required), gaps


def _startup_requirements(
    run_root: Path, case: str, members: list[str], gaps: list[str]
) -> list[str]:
    """Required records of a startup case, following the driver's writers.

    The driver writes `<case>/startup-evidence.json` with assignment and
    report references, and `<name>-native-observation.json` and
    `<name>-checks.json` beside the run root (task-startup writes
    task-native-observation.json and task-checks.json). Every referenced
    child artifact must be an archive member. Every window's wrapper
    originals and the latest last-message file are required beside it.
    """
    name = case.removesuffix("-startup")
    required = [
        f"{case}/startup-evidence.json",
        f"{name}-native-observation.json",
        f"{name}-checks.json",
    ]
    evidence_path = run_root / case / "startup-evidence.json"
    if not evidence_path.is_file():
        gaps.append(f"{case}/startup-evidence.json is absent")
    else:
        raw = evidence_path.read_text(encoding="utf-8")
        try:
            evidence = json.loads(raw)
        except ValueError:
            evidence = None
        if not isinstance(evidence, dict):
            gaps.append(
                f"{case}/startup-evidence.json is malformed or not a JSON "
                "object and its child references cannot be validated"
            )
        else:
            for key in (
                "executor_assignment",
                "evaluator_assignment",
                "executor_result",
                "evaluator_assessment",
            ):
                reference = evidence.get(key)
                if not isinstance(reference, str):
                    gaps.append(
                        f"{case}/startup-evidence.json lacks its {key} reference"
                    )
                    continue
                candidate = Path(reference)
                if not candidate.is_absolute():
                    candidate = run_root / candidate
                try:
                    relative = (
                        candidate.resolve().relative_to(run_root.resolve()).as_posix()
                    )
                except ValueError:
                    gaps.append(
                        f"{case} references evidence outside the run root: {reference}"
                    )
                    continue
                required.append(relative)
    # The startup operation window lives under operations/<case>; an
    # absent window class is a named gap, so a partial run records it.
    required += _window_requirements(run_root, case, members, True, gaps)
    return required


def evidence_members(
    run_root: Path, case: str
) -> tuple[list[str], list[str], list[str]]:
    """Fixed archive members per case: (members, required, gaps).

    Required record classes are defined by the producers' contracts, not by
    what happens to exist on disk. Producer-record gaps (a malformed
    startup-evidence document, an absent window class) are returned as
    named gap strings, so every case stages its existing originals and the
    caller keeps `ok` false while any gap remains.
    """
    gaps: list[str] = []
    if case == "release-startup":
        directory = run_root / "originals/release-startup/release-startup"
        members = sorted(
            path.relative_to(run_root).as_posix()
            for path in directory.rglob("*")
            if path.is_file()
        )
        required = ["originals/release-startup/release-startup/startup-evidence.json"]
        for pattern in (
            "operations/*.request.json",
            "operations/*.input",
            "operations/*.jsonl",
            "operations/*.stderr",
            "operations/*.invocation.json",
            "native-*.json",
            "capture-*.json",
        ):
            matches = list(directory.glob(pattern))
            if not matches:
                gaps.append(f"release-startup lacks {pattern}")
            required.extend(path.relative_to(run_root).as_posix() for path in matches)
        evidence = lib.read_json_safe(directory / "startup-evidence.json")
        if isinstance(evidence, dict):
            for key in (
                "executor_assignment",
                "evaluator_assignment",
                "executor_result",
                "evaluator_assessment",
            ):
                try:
                    path = Path(evidence[key])
                    if path.is_symlink() or not path.is_relative_to(directory):
                        raise ValueError("outside case directory")
                    required.append(path.relative_to(run_root).as_posix())
                except (KeyError, TypeError, ValueError):
                    gaps.append(f"release-startup lacks safe {key}")
        else:
            gaps.append("release-startup original role evidence is missing or invalid")
        return members, required, gaps
    if case == "baseline":
        members = [
            f"released-{fixture}.last" for fixture in ("task", "epic", "preservation")
        ] + [
            f"released-{fixture}.jsonl" for fixture in ("task", "epic", "preservation")
        ]
        required = list(members)
        for optional in ("podway-procedure-check.json", "podway-observe.json"):
            if (run_root / optional).is_file():
                members.append(optional)
        captures, capture_requirements, capture_gaps = _setup_observation_evidence(
            run_root, case
        )
        members += captures
        required += capture_requirements
        gaps += capture_gaps
        return members, required, gaps
    if case == "upgrade":
        members = ["baseline.json", "upgrade-observation.json", "result.json"]
        required = list(members)
        if (run_root / "result.stale.json").is_file():
            members.append("result.stale.json")
        _captures, _capture_requirements, capture_gaps = _setup_observation_evidence(
            run_root, case
        )
        gaps += capture_gaps
        return members, required, gaps
    if case in {"task-setup", "epic-setup", "preservation-setup", "runtime-update"}:
        directory = run_root / "operations" / case
        members = []
        if directory.is_dir():
            members = sorted(
                entry.relative_to(run_root).as_posix()
                for entry in directory.rglob("*")
                if entry.is_file()
            )
        required = _window_requirements(
            run_root,
            case,
            members,
            include_last=(case == "runtime-update"),
            gaps=gaps,
        )
        if case.endswith("-setup"):
            captures, capture_requirements, capture_gaps = _setup_observation_evidence(
                run_root, case
            )
            members += captures
            required += capture_requirements
            gaps += capture_gaps
        return members, required, gaps
    if case in {"task-startup", "epic-startup"}:
        name = case.removesuffix("-startup")
        members = []
        directory = run_root / case
        if directory.is_dir():
            members += sorted(
                entry.relative_to(run_root).as_posix()
                for entry in directory.rglob("*")
                if entry.is_file()
            )
        for sidecar in (f"{name}-native-observation.json", f"{name}-checks.json"):
            if (run_root / sidecar).is_file():
                members.append(sidecar)
        operations = run_root / "operations" / case
        if operations.is_dir():
            members += sorted(
                entry.relative_to(run_root).as_posix()
                for entry in operations.rglob("*")
                if entry.is_file()
            )
        required = _startup_requirements(run_root, case, members, gaps)
        return members, required, gaps
    if case == "stale-skill":
        directory = run_root / "stale-skill-originals"
        members = []
        if directory.is_dir():
            members = sorted(
                entry.relative_to(run_root).as_posix()
                for entry in directory.rglob("*")
                if entry.is_file()
            )
        required = [
            "stale-skill-originals/skills-list.json",
            "stale-skill-originals/plant-record.json",
        ]
        return members, required, gaps
    raise lib.RecipeError(f"unknown evidence case: {case}")


def _run_driver_phase(
    function: Any, *arguments: Any, **keywords: Any
) -> dict[str, Any]:
    """Run one in-process driver operation, keeping its outcome class."""
    try:
        outcome = function(*arguments, **keywords)
    except Exception as error:  # noqa: BLE001 - record the real boundary
        return {
            "exit": {"fail": 1}.get(getattr(error, "outcome", ""), 2),
            "driver_outcome": getattr(error, "outcome", "incomplete"),
            "problem": str(error)[-1200:],
        }
    return {
        "exit": 0,
        "driver_outcome": outcome.get("outcome"),
        "thread_id": outcome.get("thread_id"),
    }


def _merge_phase_record(results: Path, name: str, document: dict[str, Any]) -> None:
    """Create-once phase record; later writes (replies) append attempts.

    Each earlier attempt is stored as a detached copy without its own
    `attempts` list, so no cycle can enter the record.
    """
    path = results / name
    existing = lib.read_json_safe(path)
    if isinstance(existing, dict):
        attempts = list(existing.get("attempts", []))
        detached = {key: value for key, value in existing.items() if key != "attempts"}
        attempts.append(detached)
        merged = {**detached, **document, "attempts": attempts}
        lib.write_document(path, merged)
    else:
        lib.write_document(path, document)


def run_release_acceptance(context: Context, phase: str, fixture: str) -> int:
    lib.guard(context.root)
    results = lib.results_directory("release-acceptance")
    run_root = context.root / "acceptance-run"
    request = acceptance_request(context)

    def request_json() -> dict[str, Any]:
        return json.loads(request.read_text(encoding="utf-8"))

    def runtime_request_json() -> dict[str, Any]:
        document = request_json()
        # The approved installer retrieves pinned wheels inside this turn.
        # Keep its network permission out of other calls and saved settings.
        document["codex_args"] = [
            *document.get("codex_args", []),
            "-c",
            "sandbox_workspace_write.network_access=true",
        ]
        return document

    def save_request(document: dict[str, Any]) -> None:
        request.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    if phase == "machine-prepare":
        from tree_digest import tree_sha256_from_directory

        artifact_digest = tree_sha256_from_directory(context.root / CANDIDATE_KIND)
        if artifact_digest != context.inputs["candidate"]["artifact_tree_sha256"]:
            raise lib.RecipeError("sealed artifact bytes differ from the bound digest")
        ledger = lib.run_ledger("release-acceptance")
        normalization = abort_preimage(context)
        podway_identity = podway_identity_record(context)
        context.ensure_prior_stable(ledger, predecessors=(CANDIDATE_KIND,))
        normalization = finish_abort_normalization(context, normalization)
        acceptance_request(context)
        import run_acceptance as driver_module

        try:
            seeded = driver_module.seed(request_json(), run_root)
        except Exception as error:
            raise lib.RecipeError(
                f"driver seed failed: {str(error)[-800:]}", "incomplete"
            ) from error
        preservation = preservation_fixture(context)
        lock = context.inputs.get("fixture_requirements")
        if not isinstance(lock, str) or not (context.root / lock).is_file():
            raise lib.RecipeError(
                "the sealed fixture requirements are required for J-RA", "incomplete"
            )
        venv = lib.create_venv(context.python, run_root / "task/.venv")
        locked = lib.pip_install_locked(venv, context.root / lock)
        if locked["exit"] != 0:
            raise lib.RecipeError("hash-locked fixture dependencies failed")
        identity = codex_identity_record(context)
        before = context.snapshot(
            "release-acceptance", "before", profile="stable", capture="prior-baseline"
        )
        skill_identity = skill_identity_document(context, "prior")
        lib.write_document(results / "skill-identity.json", skill_identity)
        ledger.save()
        if not skill_identity.get("comparisons", {}).get("all_passed"):
            raise lib.RecipeError(
                "the prior-stage skill identity comparison failed; the "
                "successor refuses to continue",
                "incomplete",
            )
        lib.write_document(
            results / "machine-prepare.json",
            {
                "identity": context.identity,
                "podway_identity": podway_identity,
                "codex_identity": identity,
                "preservation": preservation,
                "seed_outcome": seeded.get("outcome"),
                "abort_normalization": normalization,
                "inventoried_entries": len(before),
                "venv": bool(venv),
            },
        )
        return 0
    if phase == "record-setup":
        if fixture not in {"task", "epic", "preservation"}:
            raise lib.RecipeError("record-setup needs a fixture name")
        thread = context_value_argument("thread")
        document = request_json()
        document.setdefault("baseline_setup", {})[fixture] = thread
        save_request(document)
        lib.write_document(
            results / f"record-setup-{fixture}.json",
            {"fixture": fixture, "thread": thread},
        )
        return 0
    if phase == "capture":
        # The unchanged driver's baseline in-process, so the capture record
        # binds to this Job's driver import. The old runtime stays selected.
        import run_acceptance as driver_module

        document = request_json()
        backup = run_root / "baseline-podway"
        if not backup.exists():
            shutil.copy2(document["tools"]["podway"], backup)
        document["baseline_tools"] = {**document["tools"], "podway": str(backup)}
        save_request(document)
        capture = _run_driver_phase(driver_module.baseline, document, run_root)
        lib.write_document(results / "capture.json", capture)
        return 0 if capture["exit"] == 0 else 2
    if phase == "podway-upgrade":
        import podway_upgrade
        import run_acceptance as driver_module

        captured = lib.read_json_safe(results / "capture.json")
        if not isinstance(captured, dict) or captured.get("exit") != 0:
            raise lib.RecipeError(
                "capture the released baseline before upgrading", "incomplete"
            )
        tools = podway_upgrade.observe_tools(context, "candidate")
        document = request_json()
        driver_module.prepare_candidate_fixtures(document, run_root)
        for name in driver_module.FIXTURES:
            environment = lib.create_venv(
                context.python, run_root / "candidate-fixtures" / name / ".venv"
            )
            lib.pip_install_locked(
                environment, context.root / context.inputs["fixture_requirements"]
            )
        document["separate_candidate_fixtures"] = True
        document["podway_contract_generation"] = 2
        save_request(document)
        lib.write_document(results / "podway-upgrade.json", tools)
        return 0
    if phase == "candidate-install":
        if request_json().get("podway_contract_generation") != 2:
            raise lib.RecipeError(
                "verify the sealed Podway v0.2.16 upgrade first", "incomplete"
            )
        ledger = lib.run_ledger("release-acceptance")
        context.ensure_candidate_installed(ledger, predecessors=(PRIOR_KIND,))
        ledger.save()
        import run_acceptance as driver_module

        document = request_json()
        marketplace_dir = context.marketplace_path(CANDIDATE_KIND)
        version = context.established_plugin_version()
        installed_root = (
            context.home
            / ".codex/plugins/cache"
            / context.marketplace
            / "aquarium"
            / (version or "")
        )
        try:
            row = driver_module.installed_plugin(
                {"tools": document["tools"]}, marketplace_dir, installed_root
            )
        except Exception as error:
            raise lib.RecipeError(
                f"installed plugin verification failed: {str(error)[-800:]}",
                "incomplete",
            ) from error
        document["candidate"] = {
            "git_sha": context.inputs["candidate"]["git_sha"],
            "source_root": str(context.checkout),
            "artifact_root": str(marketplace_dir),
            "artifact_manifest": str(context.root / "artifact-manifest.json"),
            "installed_plugin_root": str(installed_root),
            "marketplace_root": str(marketplace_dir),
        }
        save_request(document)
        context.snapshot(
            "release-acceptance",
            "candidate",
            profile="podway-candidate",
            capture="post-install",
        )
        lib.write_document(
            results / "candidate-install.json",
            {"plugin": row.get("version"), "candidate": document["candidate"]},
        )
        return 0
    if phase == "skill-identity":
        document = skill_identity_document(
            context, "candidate", candidate_profile="podway-candidate"
        )
        previous = lib.read_json_safe(results / "skill-identity.json")
        if isinstance(previous, dict):
            document["prior_stage"] = previous
        lib.write_document(results / "skill-identity.json", document)
        if not document.get("comparisons", {}).get("all_passed"):
            return 2
        return 0
    if phase == "runtime-update":
        import run_acceptance as driver_module

        prompt = (
            "Invoke the normally discovered installed $aquarium:dev-setup for "
            "the user-global aquarium-status runtime, scoped to its managed "
            "update. Route the global update through the named "
            "$aquarium:dev-setup-global continuation and its normal approval "
            "boundary; the repository workflow never installs or repairs the "
            "global runtime itself. Use the current installed source. This "
            "transaction's fixture operator is coordinator-fixture-operator; "
            f"scope authority is epic-019-vm-test-authority. Target version "
            f"{context.dev_version}. Return the concrete proposal; this "
            "request does not accept an unseen proposal."
        )
        runtime_record_path = results / "runtime-update.json"
        if runtime_record_path.exists() or runtime_record_path.is_symlink():
            # Create-once baseline: a rerun must never overwrite the initial
            # observation or an existing record (even if malformed).
            raise lib.RecipeError(
                "runtime-update record already exists; preserve the initial "
                "record and continue with runtime-reply or reconcile the "
                "existing thread instead of restarting the phase",
                "incomplete",
            )
        before = lib._version_names(context.home)
        thread = driver_module.invoke(
            runtime_request_json(), run_root, "runtime-update", prompt
        )
        receipts = sorted(
            (run_root / "operations/runtime-update").glob("*.invocation.json")
        )
        initial = json.loads(receipts[-1].read_text()) if receipts else {}
        lib.write_document(
            results / "runtime-update.json",
            {
                "phase": "runtime-update",
                "initial_thread": thread,
                "initial_exit": initial.get("exit"),
                "initial_input_sha256": initial.get("input_sha256"),
                "versions_before_initial": sorted(before),
                "replies": [],
                "note": "read NNN.last, continue with the runtime-reply phase",
            },
        )
        return 0
    if phase == "runtime-reply":
        import run_acceptance as driver_module

        recorded = lib.read_json_safe(results / "runtime-update.json")
        if not isinstance(recorded, dict) or not recorded.get("initial_thread"):
            raise lib.RecipeError("runtime-update must precede runtime-reply")
        reply_file = Path(lib.context_value("AQUARIUM_VM_REPLY_FILE"))
        if not reply_file.is_file():
            raise lib.RecipeError("runtime-reply needs the operator reply file")
        reply_text = reply_file.read_text(encoding="utf-8")
        before_reply = lib._version_names(context.home)
        invoke_error: str | None = None
        try:
            driver_module.invoke(
                runtime_request_json(),
                run_root,
                "runtime-update",
                "",
                reply=reply_text,
            )
        except Exception as error:  # noqa: BLE001 - persist failed reply attempt
            invoke_error = str(error)[-1200:]
        receipts = sorted(
            (run_root / "operations/runtime-update").glob("*.invocation.json")
        )
        reply_receipt = json.loads(receipts[-1].read_text()) if receipts else {}
        after_reply = lib._version_names(context.home)
        created_in_reply = sorted(after_reply - before_reply)
        ledger = lib.run_ledger("release-acceptance")
        for name in created_in_reply:
            ledger.record_generation(name)
        ledger.save()
        expected_version = f"v{context.dev_version.removeprefix('v')}"
        # One guarded read feeds the whole predicate; an unreadable runtime
        # is a structured phase failure, never an uncaught traceback.
        selected_generation: str | None = None
        receipt: dict[str, Any] = {}
        selection_error: str | None = None
        try:
            selected_generation, receipt = lib.read_current_generation(context.home)
        except lib.RecipeError as error:
            selection_error = f"the runtime selection is unreadable: {error}"
        known_generations = set(recorded.get("versions_before_initial", []))
        for reply_record in recorded.get("replies", []):
            if isinstance(reply_record, dict):
                known_generations.update(
                    reply_record.get("generations_created_in_reply_window", [])
                )
        known_generations.update(created_in_reply)
        try:
            all_receipts = lib.generation_receipts(context.home)
        except lib.RecipeError:
            all_receipts = {}
        dev_stamped_outside_windows = sorted(
            name
            for name, generation_receipt in all_receipts.items()
            if _receipt_plugin_version(generation_receipt) == context.dev_version
            and name not in known_generations
        )
        recipe_ran_installer = bool(dev_stamped_outside_windows)
        approval_completed = (
            invoke_error is None
            and selection_error is None
            and recorded.get("initial_exit") == 0
            and bool(recorded.get("initial_thread"))
            and reply_receipt.get("exit") == 0
            and reply_receipt.get("thread_id") == recorded.get("initial_thread")
            and str(reply_receipt.get("input_sha256", "")).removeprefix("sha256:")
            == lib.sha256_file(reply_file)
            and _receipt_plugin_version(receipt) == expected_version
            and selected_generation in created_in_reply
        )
        problem = selection_error or invoke_error
        # Append-only reply history: the initial-invocation evidence and
        # every earlier reply window survive this write.
        reply_entry: dict[str, Any] = {
            "reply_thread": reply_receipt.get("thread_id"),
            "same_thread": reply_receipt.get("thread_id")
            == recorded.get("initial_thread"),
            "reply_exit": reply_receipt.get("exit"),
            "reply_input_sha256": reply_receipt.get("input_sha256"),
            "reply_file": str(reply_file),
            "reply_sha256": lib.sha256_file(reply_file),
            "versions_before_reply": sorted(before_reply),
            "versions_after_reply": sorted(after_reply),
            "generations_created_in_reply_window": created_in_reply,
            "selected_generation": selected_generation,
            "receipt_plugin_version": receipt.get("plugin_version")
            if selection_error is None
            else None,
            "approval_completed": approval_completed,
        }
        if problem is not None:
            reply_entry["problem"] = problem
        reply_history = list(recorded.get("replies", []))
        reply_history.append(reply_entry)
        latest = reply_history[-1]
        updated_record: dict[str, Any] = {
            "phase": "runtime-reply",
            "initial_thread": recorded.get("initial_thread"),
            "initial_exit": recorded.get("initial_exit"),
            "initial_input_sha256": recorded.get("initial_input_sha256"),
            "versions_before_initial": recorded.get("versions_before_initial"),
            "replies": reply_history,
            "reply_thread": latest["reply_thread"],
            "same_thread": latest["same_thread"],
            "reply_exit": latest["reply_exit"],
            "reply_input_sha256": latest["reply_input_sha256"],
            "reply_file": latest["reply_file"],
            "reply_sha256": latest["reply_sha256"],
            "generations_created_in_reply_window": latest[
                "generations_created_in_reply_window"
            ],
            "selected_generation": latest["selected_generation"],
            "receipt_plugin_version": latest["receipt_plugin_version"],
            "workflow_exit": latest["reply_exit"],
            "approval_completed": approval_completed,
            "recipe_ran_installer": recipe_ran_installer,
            "dev_stamped_outside_windows": dev_stamped_outside_windows,
        }
        if problem is not None:
            updated_record["problem"] = problem
        lib.write_document(results / "runtime-update.json", updated_record)
        return 0 if approval_completed else 2
    if phase == "managed-updates":
        if fixture not in {"task", "epic", "preservation"}:
            raise lib.RecipeError("managed-updates needs a fixture name")
        import run_acceptance as driver_module

        document = _run_driver_phase(
            driver_module.setup_update,
            request_json(),
            run_root,
            fixture,
        )
        _merge_phase_record(results, f"managed-update-{fixture}.json", document)
        return 0 if document["exit"] == 0 else 2
    if phase == "reply":
        case = context_value_argument("case")
        reply_file = context_value_argument("reply-file")
        if not case.endswith("-setup"):
            raise lib.RecipeError(
                "the reply phase serves setup cases; startup replies run "
                "through the driver CLI between gate invocations"
            )
        import run_acceptance as driver_module

        reply_text = Path(reply_file).read_text(encoding="utf-8")
        name = case.removesuffix("-setup")
        document = _run_driver_phase(
            driver_module.setup_update,
            request_json(),
            run_root,
            name,
            reply=reply_text,
        )
        # The reply outcome folds into the fixture's declared phase record;
        # no undeclared reply-<case> file is produced.
        _merge_phase_record(results, f"managed-update-{name}.json", document)
        return 0 if document["exit"] == 0 else 2
    if phase == "startup-smokes":
        interpreter = shutil.which("python3")
        # A stale result cannot speak for this invocation: move it aside
        # before the gate runs, so a passing summary below was necessarily
        # written by this invocation.
        result_path = run_root / "result.json"
        if result_path.is_file():
            shutil.move(str(result_path), str(run_root / "result.stale.json"))
        gate = lib.run(
            ["make", "test-vm"],
            cwd=context.checkout,
            env={**os.environ, "AQUARIUM_VM_REQUEST": str(request)},
            timeout=7200,
        )
        summary: dict[str, Any] = {
            "exit": gate.returncode,
            "interpreter": interpreter,
            "tail": (gate.stdout + gate.stderr)[-1500:],
        }
        required_cases = ("VM-UPGRADE-01", "VM-TASK-START-01", "VM-EPIC-START-01")
        if result_path.is_file():
            document = json.loads(result_path.read_text(encoding="utf-8"))
            summary["outcome"] = document.get("outcome")
            # A row without an explicit outcome stays unobserved; only an
            # explicit "pass" passes.
            summary["cases"] = [
                {
                    "id": case.get("id"),
                    "outcome": case.get("outcome") or "unobserved",
                }
                for case in document.get("cases", [])
            ]
            upgrade = next(
                (case for case in summary["cases"] if case["id"] == "VM-UPGRADE-01"),
                None,
            )
            if upgrade is None:
                raise lib.RecipeError(
                    "the driver result lacks the VM-UPGRADE-01 case row",
                    "incomplete",
                )
        else:
            summary["outcome"] = "unobserved"
            summary["problem"] = "the driver wrote no result.json"
        if gate.returncode != 0 and summary.get("outcome") == "pass":
            summary["problem"] = (
                "the gate invocation exited nonzero; its result cannot "
                "establish this phase"
            )
            summary["outcome"] = "unobserved"
        rows = {case["id"]: case["outcome"] for case in summary.get("cases", [])}
        unobserved_cases = [
            case_id for case_id in required_cases if rows.get(case_id) != "pass"
        ]
        summary["unobserved_cases"] = unobserved_cases
        if unobserved_cases and summary.get("outcome") == "pass":
            summary["problem"] = (
                f"required case rows are unobserved: {unobserved_cases}"
            )
            summary["outcome"] = "unobserved"
        lib.write_document(results / "startup-smokes.json", summary)
        if gate.returncode == 0 and summary.get("outcome") == "pass":
            return 0
        return {"fail": 1}.get(summary.get("outcome"), 2)
    if phase == "release-startup":
        import release_orchestration

        skills = lib.read_json_safe(results / "skill-identity.json") or {}
        smokes = lib.read_json_safe(results / "startup-smokes.json") or {}
        if (
            skills.get("comparisons", {}).get("all_passed") is not True
            or smokes.get("exit") != 0
            or smokes.get("outcome") != "pass"
        ):
            raise lib.RecipeError(
                "complete installed identity and existing startup smokes first",
                "incomplete",
            )
        return release_orchestration.startup(context, results, run_root)
    if phase == "stale-skill":
        planted = context.home / ".codex/skills" / STALE_SKILL_NAME
        source = (
            context.root / f"{PRIOR_KIND}/plugins/aquarium/skills" / STALE_SKILL_NAME
        )
        if planted.exists() or planted.is_symlink():
            raise lib.RecipeError(
                f"the stale-skill plant target already exists: {planted}; "
                "the scenario refuses to mutate",
                "incomplete",
            )
        if not source.is_dir():
            raise lib.RecipeError(
                "the sealed prior artifact lacks the task-handler skill tree",
                "incomplete",
            )
        registrations_before = lib.marketplace_registrations(context.codex)
        config_before = effective_configuration_record(context)
        rules_before = _scope_entries(
            context.home / ".codex/rules", "codex-rules", ".codex/rules"
        )
        before = context.snapshot(
            "release-acceptance",
            "candidate",
            profile="podway-candidate",
            capture="stale-pre",
        )
        planted.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, planted)
        record: dict[str, Any] = {
            "schema": "aquarium.vm-stale-skill/v1",
            "planted": {
                "path": str(planted),
                "source": str(source),
                "tree_sha256": lib.skill_tree_digest(context.checkout, planted),
            },
        }
        observation = discovery(context, run_root / "candidate-fixtures/task")
        (run_root / "stale-skill-originals").mkdir(parents=True, exist_ok=True)
        lib.write_document(
            run_root / "stale-skill-originals/skills-list.json", observation
        )
        installed_root = (
            context.home
            / ".codex/plugins/cache"
            / context.marketplace
            / "aquarium"
            / (context.established_plugin_version() or "")
        ).resolve()
        planted_resolved = planted.resolve()
        rows = [
            skill
            for row in observation.get("data", [])
            for skill in row.get("skills", [])
        ]
        planted_rows = [
            skill
            for skill in rows
            if Path(str(skill.get("path", "")))
            .resolve()
            .is_relative_to(planted_resolved)
        ]
        shadowed = [
            skill
            for skill in rows
            if skill.get("name", "").startswith("aquarium:")
            and not Path(str(skill.get("path", "")))
            .resolve()
            .is_relative_to(installed_root)
        ]
        if shadowed:
            outcome = "shadowing"
            decision = (
                "the namespaced installed skill resolves outside the installed "
                "plugin root; the driver's stale-or-shadowed diagnostic is the "
                "observed failure"
            )
        elif planted_rows:
            outcome = "duplication"
            decision = (
                "the planted un-namespaced copy is loadable beside the "
                "installed namespaced skill; the codex-home-skills scope "
                "comparison is the observed failure"
            )
        else:
            outcome = "ignored-scope"
            decision = (
                "the native loader ignored the planted scope; this is a "
                "reported gap and can never pass"
            )
        record["observation"] = {
            "outcome": outcome,
            "decision": decision,
            "planted_rows": planted_rows,
            "shadowed_rows": shadowed,
        }
        shutil.rmtree(planted)
        after = context.snapshot(
            "release-acceptance",
            "candidate",
            profile="podway-candidate",
            capture="stale-post",
        )
        registrations_after = lib.marketplace_registrations(context.codex)

        # Full-identity restoration over all Aquarium-relevant scopes plus the
        # relevant rules and normalized configuration: path, sha256,
        # executable bit and symlink target (encoded in each entry's identity)
        # must match the pre-scenario state. Differences under non-`root-kernel`
        # marketplace caches (`openai-bundled`, `openai-primary-runtime`, etc.)
        # during the native `skills/list` read are recorded as Codex-owned
        # observations rather than restoration failures. The whole-file config
        # digest is recorded for information only.
        def _is_non_aquarium_marketplace_cache(scope: str, relative_path: str) -> bool:
            if scope != "codex-plugin-cache":
                return False
            prefix = ".codex/plugins/cache/"
            if not relative_path.startswith(prefix):
                return False
            marketplace_segment = relative_path.removeprefix(prefix).split("/", 1)[0]
            return (
                bool(marketplace_segment) and marketplace_segment != context.marketplace
            )

        all_inventory_diffs = lib.postcondition_violations(
            before, after, lambda _scope, _path: False
        )
        restoration_problems = lib.postcondition_violations(
            before, after, _is_non_aquarium_marketplace_cache
        )
        codex_owned_cache_observations = [
            item
            for item in all_inventory_diffs
            if item not in set(restoration_problems)
        ]
        if registrations_before != registrations_after:
            restoration_problems.append(
                "marketplace registrations changed during the scenario"
            )
        rules_after = _scope_entries(
            context.home / ".codex/rules", "codex-rules", ".codex/rules"
        )
        if rules_before != rules_after:
            restoration_problems.append(
                "per-home rule content identities changed during the scenario"
            )
        config_after = effective_configuration_record(context)
        if config_before.get("parse_error") or config_after.get("parse_error"):
            restoration_problems.append(
                "effective configuration config.toml failed to parse: "
                f"before={config_before.get('parse_error')!r}, "
                f"after={config_after.get('parse_error')!r}"
            )
        for key in (
            "marketplaces",
            "enabled_plugins",
            "features",
            "skill_settings",
            "settings",
        ):
            if config_before.get(key) != config_after.get(key):
                restoration_problems.append(
                    f"effective configuration '{key}' changed during the scenario"
                )
        config_digests = {
            "before": config_before.get("config_sha256"),
            "after": config_after.get("config_sha256"),
            "informational_only": True,
        }
        record["restoration"] = {
            "problems": restoration_problems,
            "verified": not restoration_problems,
            "codex_owned_cache_observations": codex_owned_cache_observations,
            "config_sha256": config_digests,
        }
        # The plant record and decision are archived originals: staging
        # requires them.
        lib.write_document(
            run_root / "stale-skill-originals/plant-record.json",
            {
                "planted": record["planted"],
                "observation": record["observation"],
            },
        )
        lib.write_document(results / "stale-skill.json", record)
        if outcome == "ignored-scope" or restoration_problems:
            return 2
        return 0
    if phase == "stage-evidence":
        # Attempt every case: existing originals always travel in the
        # declared outputs, each case's manifest names its missing required
        # records, and `ok` stays false while any gap remains.
        staged: list[dict[str, Any]] = []
        total = 0
        problems: list[str] = []
        lib.write_document(
            results / "stage-evidence.json",
            {"ok": False, "problem": "evidence staging is in progress", "archives": []},
        )
        # Withdraw only this suite's declared outputs before rebuilding.
        # A stopped retry cannot retain a previous successful phase claim.
        for case in EVIDENCE_CASES:
            (results / f"evidence/{case}.tar").unlink(missing_ok=True)
            (results / f"evidence/{case}.manifest.json").unlink(missing_ok=True)
            (results / f"evidence/{case}.tar.partial").unlink(missing_ok=True)
        try:
            for case in EVIDENCE_CASES:
                members, required, case_gaps = evidence_members(run_root, case)
                problems.extend(f"{case}: {gap}" for gap in case_gaps)
                archive = results / f"evidence/{case}.tar"
                temporary = archive.with_name(f"{case}.tar.partial")
                document = lib.stage_evidence_archive(
                    temporary, run_root, members, required
                )
                size = temporary.stat().st_size
                missing = list(document.get("missing_required", []))
                bound_gap: str | None = None
                if size > ARCHIVE_BYTES_BOUND:
                    bound_gap = f"archive exceeds the {ARCHIVE_BYTES_BOUND}-byte bound"
                    problems.append(
                        f"{case}: the evidence archive exceeds the "
                        f"{ARCHIVE_BYTES_BOUND}-byte bound"
                    )
                elif total + size > ARCHIVE_TOTAL_BYTES_BOUND:
                    bound_gap = (
                        f"archive would exceed the {ARCHIVE_TOTAL_BYTES_BOUND}-byte "
                        f"total bound ({total + size} > {ARCHIVE_TOTAL_BYTES_BOUND})"
                    )
                    problems.append(
                        f"{case}: the staged evidence would exceed the "
                        f"{ARCHIVE_TOTAL_BYTES_BOUND}-byte total bound "
                        f"({total + size} > {ARCHIVE_TOTAL_BYTES_BOUND})"
                    )
                if bound_gap is not None:
                    temporary.unlink(missing_ok=True)
                    archive.unlink(missing_ok=True)
                    missing_with_bound = [*missing, bound_gap]
                    gaps_with_bound = [*case_gaps, bound_gap]
                    lib.write_document(
                        archive.with_name(f"{case}.manifest.json"),
                        {
                            "schema": lib.EVIDENCE_ARCHIVE_SCHEMA,
                            "archive": archive.name,
                            "archive_present": False,
                            "sha256": None,
                            "algorithm": "sha256",
                            "members": [],
                            "required": document["required"],
                            "missing_required": missing_with_bound,
                            "gaps": gaps_with_bound,
                        },
                    )
                    staged.append(
                        {
                            "case": case,
                            "archive": (
                                f"results/release-acceptance/evidence/{case}.tar"
                            ),
                            "archive_present": False,
                            "members": 0,
                            "required": len(document["required"]),
                            "missing_required": missing_with_bound,
                            "gaps": gaps_with_bound,
                            "size": 0,
                        }
                    )
                    continue
                temporary.replace(archive)
                lib.write_document(archive.with_name(f"{case}.manifest.json"), document)
                total += size
                if missing:
                    problems.append(
                        f"{case}: required evidence records are missing: {missing}"
                    )
                staged.append(
                    {
                        "case": case,
                        "archive": f"results/release-acceptance/evidence/{case}.tar",
                        "archive_present": True,
                        "members": len(document["members"]),
                        "required": len(document["required"]),
                        "missing_required": missing,
                        "gaps": case_gaps,
                        "size": size,
                    }
                )
        except lib.RecipeError as error:
            # The failed attempt keeps its own shape so a later phase or a
            # review can see exactly which records were missing.
            lib.write_document(
                results / "stage-evidence.json",
                {
                    "ok": False,
                    "problem": str(error),
                    "problems": [*problems, str(error)],
                    "archives": staged,
                    "bounds": {
                        "per_archive": ARCHIVE_BYTES_BOUND,
                        "total": ARCHIVE_TOTAL_BYTES_BOUND,
                    },
                },
            )
            return 2
        lib.write_document(
            results / "stage-evidence.json",
            {
                "ok": not problems,
                "problems": problems,
                "archives": staged,
                "total_size": total,
                "bounds": {
                    "per_archive": ARCHIVE_BYTES_BOUND,
                    "total": ARCHIVE_TOTAL_BYTES_BOUND,
                },
            },
        )
        return 0 if not problems else 2
    if phase == "consumer-cleanup":
        expected_version = f"v{context.dev_version.removeprefix('v')}"
        required = {
            "machine-prepare.json": lambda document: isinstance(document, dict),
            "record-setup-task.json": lambda document: isinstance(document, dict),
            "record-setup-epic.json": lambda document: isinstance(document, dict),
            "record-setup-preservation.json": lambda document: isinstance(
                document, dict
            ),
            "capture.json": lambda document: document.get("exit") == 0,
            "podway-upgrade.json": lambda document: (
                document.get("identity", {}).get("result", {}).get("version")
                == "v0.2.16"
            ),
            "candidate-install.json": lambda document: isinstance(document, dict),
            "skill-identity.json": lambda document: (
                document.get("comparisons", {}).get("all_passed") is True
                and isinstance(document.get("prior_stage"), dict)
                and document["prior_stage"].get("comparisons", {}).get("all_passed")
                is True
            ),
            "runtime-update.json": lambda document: (
                document.get("approval_completed") is True
                and document.get("workflow_exit") == 0
                and document.get("receipt_plugin_version") == expected_version
            ),
            "managed-update-task.json": lambda document: document.get("exit") == 0,
            "managed-update-epic.json": lambda document: document.get("exit") == 0,
            "managed-update-preservation.json": lambda document: (
                document.get("exit") == 0
            ),
            "startup-smokes.json": lambda document: (
                document.get("outcome") == "pass" and document.get("exit") == 0
            ),
            "release-startup.json": lambda document: (
                document.get("outcome") == "pass"
                and document.get("exit") == 0
                and document.get("candidate_sha")
                == context.inputs["candidate"]["git_sha"]
            ),
            "stale-skill.json": lambda document: (
                document.get("observation", {}).get("outcome")
                in {"shadowing", "duplication"}
                and document.get("restoration", {}).get("verified") is True
            ),
            "stage-evidence.json": lambda document: document.get("ok") is True,
        }
        unsuccessful: list[str] = []
        for name, predicate in required.items():
            document = lib.read_json_safe(results / name)
            if not isinstance(document, dict) or not predicate(document):
                unsuccessful.append(name)
        if unsuccessful:
            return lib.finish(
                "release-acceptance",
                "fail",
                {
                    "phase": phase,
                    "problem": f"unsuccessful phases prevent cleanup: {unsuccessful}",
                },
                consumer_cleanup="unverified",
            )
        baseline = lib.read_json_safe(results / "inventory-prior-baseline.json")
        if (
            not isinstance(baseline, dict)
            or baseline.get("schema") != lib.INVENTORY_SCHEMA
            or not isinstance(baseline.get("entries"), list)
        ):
            raise lib.RecipeError(
                "the released baseline inventory is unavailable", "incomplete"
            )
        import podway_upgrade

        context.snapshot(
            "release-acceptance",
            "candidate",
            profile="podway-candidate",
            capture="cleanup-before",
        )
        tools = podway_upgrade.observe_tools(context, "candidate")
        skills = skill_identity_document(
            context, "candidate", candidate_profile="podway-candidate"
        )
        current_name, receipt = lib.read_current_generation(context.home)
        violations = []
        if _receipt_plugin_version(receipt) != expected_version:
            violations.append(
                "the selected status runtime does not match the candidate"
            )
        if skills.get("comparisons", {}).get("all_passed") is not True:
            violations.append("the retained installed skill identities do not match")
        lib.assert_registration(
            context.codex,
            context.marketplace,
            str(context.marketplace_path(CANDIDATE_KIND)),
        )
        after = context.snapshot(
            "release-acceptance",
            "post_cleanup",
            profile="podway-candidate",
            capture="post-cleanup",
        )

        def allowed_upgrade(scope: str, path: str) -> bool:
            return (
                allowed_runtime_changes(scope, path)
                or scope == "codex-plugin-cache"
                or (
                    scope == "user-global"
                    and path in {".aquarium/status.yaml", ".aquarium/status.lock"}
                )
                or (
                    scope == "shared-agents-skills"
                    and (
                        path == ".agents/skills/use-podway"
                        or path.startswith(".agents/skills/use-podway/")
                    )
                )
            )

        violations += lib.postcondition_violations(
            baseline["entries"], after, allowed_upgrade
        )
        lib.write_document(
            results / "consumer-cleanup.json",
            {
                "violations": violations,
                "tools": tools,
                "runtime_end_state": {
                    "selected_generation": current_name,
                    "declared": "retain the tested Aquarium candidate, Podway v0.2.16, paired skills and selected candidate status runtime",
                },
            },
        )
        outcome = "pass" if not violations else "fail"
        return lib.finish(
            "release-acceptance",
            outcome,
            {"phase": phase, "violations": violations},
            consumer_cleanup="verified" if not violations else "failed",
        )
    if phase == "complete-template":

        def observed(document: str, predicate: Any) -> bool:
            loaded = lib.read_json_safe(results / document)
            return isinstance(loaded, dict) and bool(predicate(loaded))

        def evidence_reference(name: str) -> list[str]:
            path = f"results/release-acceptance/{name}"
            return [path] if (results / name).is_file() else []

        scenarios = [
            {
                "id": "release-startup",
                "status": "pass"
                if observed(
                    "release-startup.json",
                    lambda d: (
                        d.get("exit") == 0
                        and d.get("outcome") == "pass"
                        and d.get("candidate_sha")
                        == context.inputs["candidate"]["git_sha"]
                    ),
                )
                else "unobserved",
                "evidence_references": [
                    "results/release-acceptance/release-startup.json",
                    "results/release-acceptance/evidence/release-startup.tar",
                ],
            },
            {
                "id": "released-baseline",
                "status": "pass"
                if observed("capture.json", lambda d: d.get("exit") == 0)
                and (run_root / "baseline.json").is_file()
                else "unobserved",
                "evidence_references": [
                    "results/release-acceptance/capture.json",
                    "results/release-acceptance/evidence/baseline.tar",
                ],
            },
            {
                "id": "candidate-upgrade",
                "status": "pass"
                if observed("startup-smokes.json", lambda d: d.get("outcome") == "pass")
                else "unobserved",
                "evidence_references": [
                    "results/release-acceptance/startup-smokes.json",
                    "results/release-acceptance/evidence/upgrade.tar",
                ],
            },
            {
                "id": "runtime-approval",
                "status": "pass"
                if observed(
                    "runtime-update.json",
                    lambda d: (
                        d.get("approval_completed") is True
                        and d.get("workflow_exit") == 0
                        and d.get("recipe_ran_installer") is False
                    ),
                )
                else "unobserved",
                "evidence_references": [
                    "results/release-acceptance/runtime-update.json",
                    "results/release-acceptance/evidence/runtime-update.tar",
                ],
            },
            {
                "id": "skill-identity",
                "status": "pass"
                if observed(
                    "skill-identity.json",
                    lambda d: (
                        d.get("comparisons", {}).get("all_passed") is True
                        and isinstance(d.get("prior_stage"), dict)
                        and d["prior_stage"].get("comparisons", {}).get("all_passed")
                        is True
                    ),
                )
                else "unobserved",
                "evidence_references": evidence_reference("skill-identity.json"),
            },
            {
                "id": "task-startup",
                "status": "pass"
                if observed(
                    "startup-smokes.json",
                    lambda d: any(
                        case.get("id") == "VM-TASK-START-01"
                        and case.get("outcome") == "pass"
                        for case in d.get("cases", [])
                    ),
                )
                else "unobserved",
                "evidence_references": [
                    "results/release-acceptance/startup-smokes.json",
                    "results/release-acceptance/evidence/task-startup.tar",
                ],
            },
            {
                "id": "epic-startup",
                "status": "pass"
                if observed(
                    "startup-smokes.json",
                    lambda d: any(
                        (
                            case.get("id") == "VM-EPIC-START-01"
                            and case.get("outcome") == "pass"
                        )
                        for case in d.get("cases", [])
                    ),
                )
                else "unobserved",
                "evidence_references": [
                    "results/release-acceptance/startup-smokes.json",
                    "results/release-acceptance/evidence/epic-startup.tar",
                ],
            },
            {
                "id": "stale-skill-failure",
                "status": "pass"
                if observed(
                    "stale-skill.json",
                    lambda d: (
                        d.get("observation", {}).get("outcome")
                        in {"shadowing", "duplication"}
                    ),
                )
                else "unobserved",
                "evidence_references": [
                    "results/release-acceptance/stale-skill.json",
                    "results/release-acceptance/evidence/stale-skill.tar",
                ],
            },
            {
                "id": "stale-skill-restoration",
                "status": "pass"
                if observed(
                    "stale-skill.json",
                    lambda d: d.get("restoration", {}).get("verified") is True,
                )
                else "unobserved",
                "evidence_references": ["results/release-acceptance/stale-skill.json"],
            },
            {
                "id": "evidence-staging",
                "status": "pass"
                if observed("stage-evidence.json", lambda d: d.get("ok") is True)
                else "unobserved",
                "evidence_references": [
                    "results/release-acceptance/stage-evidence.json"
                ],
            },
            {
                "id": "consumer-cleanup",
                "status": "pass"
                if observed(
                    "consumer-cleanup.json", lambda d: d.get("violations") == []
                )
                else "unobserved",
                "evidence_references": [
                    "results/release-acceptance/consumer-cleanup.json"
                ],
            },
        ]
        template = {
            "schema": "haepari.manual-result/v1",
            "job_id": "<admitted-job-id>",
            "installation_id": "<run.json installation_id>",
            "profile_id": context.profile("podway-candidate")["profile_id"],
            "profile_digest": context.profile_digest("podway-candidate"),
            "expected_revision": "<current awaiting job_revision>",
            "observer": "coordinator-fixture-operator",
            "scenarios": scenarios,
        }
        lib.write_document(results / "manual-complete-template.json", template)
        print(json.dumps(template, ensure_ascii=False))
        return 0
    raise lib.RecipeError(f"unknown release-acceptance phase: {phase}")


def context_value_argument(name: str) -> str:
    value = os.environ.get(f"AQUARIUM_VM_{name.upper().replace('-', '_')}", "")
    if not value:
        raise lib.RecipeError(f"phase argument {name} is required")
    return value


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
    finish_options = (
        {"preserve_invalid_inventory": True}
        if (arguments.suite == "epic-squad" and arguments.phase == "stage-evidence")
        or arguments.suite
        in {"sorage-adoption", "mulgae-adoption", "release-orchestration"}
        else {}
    )
    try:
        if arguments.suite == "release-orchestration":
            import release_orchestration

            return release_orchestration.run(
                context, arguments.phase, arguments.fixture or ""
            )
        if arguments.suite == "mulgae-adoption":
            import mulgae_adoption

            return mulgae_adoption.run(context, arguments.phase)
        if arguments.suite == "sorage-adoption":
            import sorage_adoption

            return sorage_adoption.run(context, arguments.phase)
        if arguments.suite == "manual-hold":
            return run_manual_hold(context, arguments.phase)
        if arguments.suite in {"podway-upgrade", "epic-squad"}:
            import podway_upgrade

            return podway_upgrade.run(
                context,
                arguments.phase,
                lambda stage: skill_identity_document(
                    context, stage, candidate_profile="podway-candidate"
                ),
                suite=arguments.suite,
            )
        if arguments.suite == "release-acceptance":
            return run_release_acceptance(
                context, arguments.phase, arguments.fixture or ""
            )
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
            **finish_options,
        )
    except RuntimeError as error:
        # Safety net for driver GateError and similar runtime errors raised
        # across the lazy driver import: a structured result, never a bare
        # traceback.
        return lib.finish(
            arguments.suite,
            "incomplete",
            {"problem": f"{type(error).__name__}: {error}"},
            consumer_cleanup="unverified",
            **finish_options,
        )
    except lib.TreeDigestError as error:
        # Safety net: an unconverted strict-validation error still produces
        # a structured non-pass result instead of a traceback.
        return lib.finish(
            arguments.suite,
            "incomplete",
            {"problem": f"TreeDigestError: {error}"},
            consumer_cleanup="unverified",
            **finish_options,
        )
    except OSError as error:
        return lib.finish(
            arguments.suite,
            "incomplete",
            {"problem": f"OSError: {error}"},
            consumer_cleanup="unverified",
            **finish_options,
        )
    except ValueError as error:
        # Defense in depth for decoding paths outside the structured
        # readers, for example subprocess text decoding and the ledger.
        return lib.finish(
            arguments.suite,
            "incomplete",
            {"problem": f"ValueError: {error}"},
            consumer_cleanup="unverified",
            **finish_options,
        )


if __name__ == "__main__":
    raise SystemExit(main())
