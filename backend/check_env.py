"""
check_env.py - checks that this computer is ready for the project.

Run it from the project's main folder:

    python backend/check_env.py

It only reads information. It does not install or change anything.
"""

import shutil
import sys
from pathlib import Path

# The project's main folder is one level above this file's folder (backend/).
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Folders that must exist for the project to work.
REQUIRED_FOLDERS = ["data", "backend", "web", "docs", "tests"]

# The oldest Python version this project supports.
MINIMUM_PYTHON = (3, 11)


def check_python_version() -> bool:
    """Return True if Python is new enough."""
    current = sys.version_info[:3]
    ok = current >= MINIMUM_PYTHON
    version_text = ".".join(str(part) for part in current)
    print_result(ok, f"Python version is {version_text} (need 3.11 or newer)")
    return ok


def check_virtual_environment() -> bool:
    """Return True if a virtual environment is active.

    Inside a virtual environment, sys.prefix points to the .venv folder,
    while sys.base_prefix still points to the main Python installation.
    If the two are different, a virtual environment is active.
    """
    ok = sys.prefix != sys.base_prefix
    if ok:
        print_result(True, f"Virtual environment is active: {sys.prefix}")
    else:
        print_result(False, "No virtual environment is active (run .venv\\Scripts\\activate)")
    return ok


def check_git() -> bool:
    """Return True if the 'git' command can be found."""
    git_path = shutil.which("git")
    ok = git_path is not None
    print_result(ok, f"Git found at {git_path}" if ok else "Git was not found (install from git-scm.com)")
    return ok


def check_folders() -> bool:
    """Return True if every required project folder exists."""
    all_ok = True
    for name in REQUIRED_FOLDERS:
        exists = (PROJECT_ROOT / name).is_dir()
        print_result(exists, f"Folder '{name}/' {'exists' if exists else 'is missing'}")
        all_ok = all_ok and exists
    return all_ok


def print_result(ok: bool, message: str) -> None:
    """Print one line that starts with PASS or FAIL."""
    print(f"[{'PASS' if ok else 'FAIL'}] {message}")


def main() -> int:
    print(f"Checking project at: {PROJECT_ROOT}\n")
    results = [
        check_python_version(),
        check_virtual_environment(),
        check_git(),
        check_folders(),
    ]
    print()
    if all(results):
        print("All checks passed. The environment is ready.")
        return 0
    print("Some checks failed. Fix the FAIL lines above and run this again.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
