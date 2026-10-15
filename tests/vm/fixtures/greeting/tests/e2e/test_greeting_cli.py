import subprocess
import sys
from pathlib import Path


def test_cli_help():
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "-B", str(root / "greet.py"), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "name" in result.stdout
