import subprocess
import sys


def test_required_dependencies_importable():
    import pydantic
    import yaml

    assert int(pydantic.__version__.split(".")[0]) >= 2
    assert hasattr(yaml, "safe_load")


def test_cli_executable_registered():
    result = subprocess.run(
        [sys.executable, "-m", "pyflowsheet.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "pyflowsheet" in result.stdout.lower()
