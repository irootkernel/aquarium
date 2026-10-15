"""Exercise native metadata encoding through the shipped stdin CLI."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "plugins/aquarium/skills/task-commit/scripts/source_identity_digest.py"


def identity(scope="stage"):
    return {
        "schema_version": "mulgae-live-source.v1",
        "scope": scope,
        "operand": "",
        "base_oid": "a" * 40 if scope == "stage" else "",
        "head_oid": "",
        "empty_base": False,
    }


def invoke(text, *, stdin_encoding=None):
    environment = os.environ.copy()
    if stdin_encoding is not None:
        environment["PYTHONIOENCODING"] = stdin_encoding
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPT)],
        input=text,
        encoding="utf-8",
        env=environment,
        capture_output=True,
        check=False,
    )


@pytest.mark.parametrize(
    "scope,digest",
    [
        (
            "stage",
            "c995cbc2f4d133ee89bab213456761a553e4ee7f0611956ab5c4d41ec33201d4",
        ),
        (
            "workspace",
            "87baffbf5aebb20121d9176136272bf300e23b78c4203c0061f9b64e819a750f",
        ),
    ],
)
def test_official_v0125_example_digests(scope, digest):
    # Published preflight-v8 and artifact-v3 fixtures at b68d3e12e767687ab02ef9e04a602098922f5522.
    value = dict(reversed(list(identity(scope).items())))
    result = invoke(json.dumps(value, indent=2) + "\n")
    assert result.returncode == 0
    assert result.stdout == "sha256:" + digest + "\n"
    assert not result.stderr


@pytest.mark.parametrize("stdin_encoding", [None, "latin-1"])
def test_native_go_html_and_unicode_encoding(stdin_encoding):
    value = identity("commit")
    value.update(
        operand="topic/<&>\u2028\u2029/한글",
        base_oid="a" * 40,
        head_oid="b" * 40,
    )
    result = invoke(
        json.dumps(value, ensure_ascii=False), stdin_encoding=stdin_encoding
    )
    assert result.returncode == 0
    # Independently calculated with Go encoding/json over the native struct.
    assert result.stdout == (
        "sha256:1dd503bd5de150bb3ae8d82999fe5e991faed79cf68dc658fe7b382571ee2ac3\n"
    )


@pytest.mark.parametrize(
    "text",
    [
        "",
        "[]",
        "{}",
        json.dumps({**identity(), "extra": "field"}),
        json.dumps({**identity(), "empty_base": 0}),
        json.dumps({**identity(), "operand": None}),
        json.dumps({**identity(), "operand": "\ud800"}),
    ],
)
def test_invalid_encoding_inputs_fail_without_a_digest(text):
    result = invoke(text)
    assert result.returncode == 2
    assert not result.stdout
    assert result.stderr
