import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_default():
    result = subprocess.run(
        [sys.executable, "-B", str(ROOT / "greet.py")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == "Hello, world!\n"


def test_name():
    result = subprocess.run(
        [sys.executable, "-B", str(ROOT / "greet.py"), "Ada"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == "Hello, Ada!\n"
