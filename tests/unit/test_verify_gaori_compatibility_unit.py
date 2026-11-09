"""Regression checks for Gaori evidence-consumer assertions."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "gaori_compatibility", Path(__file__).parents[1] / "verify_gaori_compatibility.py"
)
assert SPEC and SPEC.loader
compatibility = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compatibility)


def test_signature_hashes_preserve_duplicate_records():
    records = [{"signature": "same"}, {"signature": "other"}, {"signature": "same"}]
    expected = sorted(
        [
            compatibility.digest(b"same"),
            compatibility.digest(b"other"),
            compatibility.digest(b"same"),
        ]
    )
    assert compatibility.signature_hashes(records) == expected


@pytest.mark.parametrize(
    "excerpt",
    [
        b"TypeError: another failure\n",
        b"TypeError: late\n",
        b"TypeError: late token=secret\n",
        b"TypeError: late token=<redacted>\ncontext token=secret\n",
    ],
)
def test_excerpt_rejects_wrong_missing_or_unredacted_content(excerpt):
    with pytest.raises(RuntimeError):
        compatibility.require_excerpt(
            excerpt, b"TypeError: late token=secret\nsrc/late.ts:3:4\n"
        )


def test_excerpt_accepts_corresponding_redacted_header():
    compatibility.require_excerpt(
        b"context\nTypeError: late token=<redacted>\nsrc/late.ts:3:4\n",
        b"TypeError: late token=secret\nsrc/late.ts:3:4\n",
    )


def test_fixture_git_setup_failure_is_reported(monkeypatch, capsys):
    monkeypatch.setenv("GAORI_BIN", str(Path(sys.executable).resolve()))

    called = []

    def fail_setup(binary):
        called.append(binary)
        raise subprocess.CalledProcessError(1, ["git", "init"])

    monkeypatch.setattr(compatibility, "verify", fail_setup)
    assert compatibility.main() == 1
    assert called == [Path(sys.executable).resolve()]
    assert capsys.readouterr().err
