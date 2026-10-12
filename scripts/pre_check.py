"""Script des vérifications qualité de heron (lancé par pre-commit ou à la main)."""

import os
import subprocess
from collections.abc import Sequence
from pathlib import Path

# Codes ANSI pour la couleur
RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"


def run_cmd(cmd: Sequence[str]) -> int:
    """Run a command and stream its output, returning the exit code.

    The command sequence is predefined (no user input), so subprocess.run
    is invoked with check=False to allow error handling in Python.
    """
    cmd_str = " ".join(cmd)
    print(f"\n=== Running: {cmd_str} ===")
    completed = subprocess.run(cmd, check=False)  # noqa: S603
    code = completed.returncode
    if code == 0:
        print(f"{GREEN}=== Success ! ==={RESET}")
    else:
        print(f"{RED}=== Error: {code} ==={RESET}")

    return code


def run_quality_checks(base_dir: Path | None = None) -> int:
    """Run the full quality pipeline from a given base directory.

    1. uv pip check
    2. uv run ruff format .
    3. uv run ruff check . --fix
    4. uv run mypy (cibles de [tool.mypy] : apps, heron, conftest.py)
    5. uv run ruff check apps heron conftest.py scripts
    6. uv run xenon --max-absolute C --max-modules B --max-average A apps heron (hors tests)

    Continues even if some commands fail, prints all errors in red and successes in green.
    Returns 0 if all succeed, otherwise the first non-zero exit code.
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent

    print(f"Changing working directory to: {base_dir}")
    os.chdir(base_dir)

    commands: list[list[str]] = [
        ["uv", "pip", "check"],
        ["uv", "run", "ruff", "format", "."],
        ["uv", "run", "ruff", "check", ".", "--fix"],
        # Application Django : le code est dans apps/ et heron/ (pas de src/ ni tests/)
        ["uv", "run", "python", "-m", "mypy"],
        ["uv", "run", "ruff", "check", "apps", "heron", "conftest.py", "scripts"],
        # Seuils radon : aucun bloc pire que C, aucun module pire que B, moyenne A ; les tests
        # (longs par nature), migrations et essais sont hors mesure
        [
            "uv",
            "run",
            "xenon",
            "--max-absolute",
            "C",
            "--max-modules",
            "B",
            "--max-average",
            "A",
            "--exclude",
            "*/tests/*,*/migrations/*,*/essais/*",
            "apps",
            "heron",
        ],
    ]

    first_error_code: int | None = None

    for cmd in commands:
        code = run_cmd(cmd)
        if code != 0:
            if first_error_code is None:
                first_error_code = code
            print(f"{RED}*** Command failed (exit code {code}): {' '.join(cmd)} ***{RESET}")

    if first_error_code is None:
        print(f"\n{GREEN}All quality checks passed.{RESET}")
        return 0

    print(
        f"\n{RED}Quality checks completed with errors. "
        f"First non-zero exit code: {first_error_code}{RESET}"
    )
    return first_error_code


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    print(f"=== Base Directory: {base}")
    raise SystemExit(run_quality_checks(base_dir=base))
