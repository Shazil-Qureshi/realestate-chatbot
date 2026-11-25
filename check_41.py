"""
check_41.py - one-click check for Task 4.1 (rule 10, near matches).

What it does, in order:

  1. Starts a SECOND backend on port 8001, using the current code.
  2. Waits for it to finish loading, and prints what it reports about
     itself (prompt version, number of areas known).
  3. Runs the chat tests against that server.
  4. Stops it again.
  5. Writes everything to check_41_output.txt.

The backend you already have running on port 8000 is never touched, never
stopped and never tested. If that one is still on the old prompt, this run
tells you nothing misleading, because it is not the one being asked.

Delete this file and check_41.bat when Task 4.1 is finished; they are a
convenience, not part of the project.
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
PORT = 8001
URL = f"http://127.0.0.1:{PORT}"
OUTPUT = ROOT / "check_41_output.txt"

lines = []


def say(text=""):
    print(text, flush=True)
    lines.append(text)


def health():
    try:
        with urllib.request.urlopen(f"{URL}/health", timeout=5) as response:
            return json.load(response)
    except Exception:
        return None


def main():
    if not PYTHON.exists():
        say(f"Could not find {PYTHON}")
        say("Run this from the project folder, with .venv already created.")
        return 1

    say("=" * 70)
    say(f"Task 4.1 check - temporary backend on port {PORT}")
    say("=" * 70)
    say()

    if health() is not None:
        say(f"Something is already answering on port {PORT}. Stop it and try again.")
        return 1

    say("[1/4] Starting a temporary backend...")
    server = subprocess.Popen(
        [str(PYTHON), "-m", "uvicorn", "main:app", "--host", "127.0.0.1",
         "--port", str(PORT), "--log-level", "warning"],
        cwd=str(ROOT / "backend"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )

    try:
        say("[2/4] Waiting for it to load (up to 2 minutes)...")
        report = None
        for _ in range(60):
            if server.poll() is not None:
                say(f"The server stopped on its own (exit code {server.returncode}).")
                return 1
            report = health()
            if report and report.get("status") == "ok":
                break
            time.sleep(2)

        if not report or report.get("status") != "ok":
            say("The server did not become ready in time.")
            return 1

        say()
        say("      It reports:")
        say(f"        chunks:         {report.get('chunks')}")
        say(f"        prompt version: {report.get('prompt_version')}")
        say(f"        area filtering: {report.get('area_filtering')} areas")
        say()

        if not report.get("area_filtering"):
            say("      WARNING: 0 areas. The index has no area metadata.")
            say("      Run: python backend\\ingest.py")
            say()
        if "rule 10" not in str(report.get("prompt_version", "")):
            say("      WARNING: this is not the updated prompt. Is main.py saved?")
            say()

        say("[3/4] Running the chat tests against it...")
        say()
        env = dict(os.environ)
        env["BELLA_TEST_URL"] = URL
        result = subprocess.run(
            [str(PYTHON), "-m", "pytest", "tests/test_chat.py", "-v", "-s"],
            cwd=str(ROOT), env=env,
            capture_output=True, text=True,
        )
        for line in (result.stdout + result.stderr).splitlines():
            say(line)
        say()
        say(f"[4/4] pytest finished with exit code {result.returncode}")
        return result.returncode

    finally:
        say()
        say("Stopping the temporary backend...")
        server.terminate()
        try:
            server.wait(timeout=15)
        except subprocess.TimeoutExpired:
            server.kill()
        say("Stopped. Your own backend on port 8000 was not touched.")
        OUTPUT.write_text("\n".join(lines), encoding="utf-8")
        print()
        print(f"Saved to {OUTPUT}")


if __name__ == "__main__":
    sys.exit(main() or 0)
