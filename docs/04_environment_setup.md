# 04 · Environment Setup

| | |
|---|---|
| **Project** | AI Real Estate Customer Support Chatbot |
| **Phase** | Stage 1 – Backend and AI knowledge base |
| **Task** | 1.1 Environment setup |
| **Last updated** | 13 November 2026 |
| **Status** | Completed |

## 1. Objective

Make sure the computer has the right tools and create a private Python
environment for this project.

## 2. Technical concepts

| Term | What it means | Why we need it | Example |
|---|---|---|---|
| **Terminal** | A window where you type commands. | Python tools are run by command. | VS Code → Terminal → New Terminal |
| **Virtual environment** | A private folder (`.venv`) holding this project's Python packages. | Stops this project's packages clashing with other projects. | Project A needs FastAPI 0.1, project B needs 0.2. Each gets its own. |
| **Activate** | Tell the terminal to use the virtual environment. | Otherwise packages install into the whole computer. | The prompt shows `(.venv)`. |
| **pip** | Python's package installer. | We will install FastAPI, ChromaDB and others. | `pip install fastapi` |
| **PATH** | The list of folders Windows searches for commands. | If Python isn't on PATH, the `python` command isn't found. | Tick "Add Python to PATH" in the installer. |

## 3. Tools and technologies

Python 3.14.10 (installed via the Python Install Manager), Visual Studio Code,
Git, Windows PowerShell.

**Version decision:** the newest Python at the time was 3.15.2, but new releases
often lack pre-built packages ("wheels"), which forces pip to compile from
source and fails on Windows without a C++ compiler. We chose the second-newest
series, 3.14.10, which still ships Windows installers and has mature package
support. Python 3.13 was considered first but has entered security-only mode:
3.13.18 is source-only, with no installer.

## 4. Implementation details

`backend/check_env.py` runs four checks and prints PASS or FAIL for each:
Python version, active virtual environment, Git installed, project folders
present. It only reads information and changes nothing.

## 5. Files created or modified

| File | Purpose |
|---|---|
| `backend/check_env.py` | Environment check script |
| `.venv/` | Virtual environment (created by you, ignored by Git) |

## 6. Instructions

1. Open VS Code → **File → Open Folder** → select `realestate-chatbot`.
2. Open a terminal: **Terminal → New Terminal**.
3. Create the virtual environment:
   ```powershell
   python -m venv .venv
   ```
4. Activate it:
   ```powershell
   .venv\Scripts\activate
   ```
   The line in the terminal should now start with `(.venv)`.
5. Upgrade pip:
   ```powershell
   python -m pip install --upgrade pip
   ```
6. Run the check:
   ```powershell
   python backend/check_env.py
   ```

Expected output (versions and paths will differ):

```
Checking project at: C:\Users\...\realestate-chatbot

[PASS] Python version is 3.12.4 (need 3.11 or newer)
[PASS] Virtual environment is active: C:\Users\...\realestate-chatbot\.venv
[PASS] Git found at C:\Program Files\Git\cmd\git.EXE
[PASS] Folder 'data/' exists
[PASS] Folder 'backend/' exists
[PASS] Folder 'web/' exists
[PASS] Folder 'docs/' exists
[PASS] Folder 'tests/' exists

All checks passed. The environment is ready.
```

## 7. Testing procedure

Run each test in the VS Code terminal and write the real result in the table.

## 8. Test results

| Test ID | Objective | Input | Expected result | Actual result | Status | Remarks |
|---|---|---|---|---|---|---|
| ENV-01 | Python is installed | `python --version` | 3.11 or newer | First run: `Python was not found` (App execution alias). After installing 3.14.10: `Python 3.14.10` | **Pass** (after fix) | Python was not installed at all |
| ENV-02 | Git is installed | `python backend/check_env.py` | A path to git.exe | `C:\Program Files\Git\cmd\git.EXE` | **Pass** | Already installed |
| ENV-03 | Virtual environment activates | `.venv\Scripts\Activate.ps1` | Prompt shows `(.venv)` | Prompt showed `(.venv)` | **Pass** | Needed `Set-ExecutionPolicy RemoteSigned` |
| ENV-04 | All checks pass | `python backend\check_env.py` | 8 PASS lines | 8 PASS lines, "All checks passed." | **Pass** | Run 13 Nov 2026, 16:11 PKT |
| ENV-05 | Script detects a missing environment | Run before activating | FAIL line for the virtual environment | `[FAIL] No virtual environment is active` | **Pass** | Seen on the first run, before activation |

## 9. Problems encountered

| # | Problem | Cause | Fix |
|---|---|---|---|
| 1 | `Python was not found; run without arguments to install from the Microsoft Store` | Python was never installed. Windows ships a fake `python` stub called an App execution alias. | Installed Python 3.14.10 via the Python Install Manager. |
| 2 | `.venv\Scripts\activate : The module '.venv' could not be loaded` | Knock-on effect: `python -m venv` had failed, so no `.venv` existed. | Disappeared once Python worked. |
| 3 | Commands appeared merged, e.g. `python -m venv .venvate:String)` | Several lines pasted into PowerShell at once. | Paste one command at a time. |
| 4 | Chose Python 3.13.17, then found it superseded by 3.13.18 | 3.13 entered security-only mode; 3.13.18 is source-only with no Windows installer. | Switched to 3.14.10, which still ships installers and is the second-newest series. |
| 5 | `pip install --upgrade pip` upgraded the global Python, not the project | The virtual environment had not been activated. | Activated `.venv`, then re-ran pip. Confirmed by the path `.\.venv\Lib\site-packages`. |

## 10. Solutions: common errors

| Error | Cause | Fix |
|---|---|---|
| `'python' is not recognized` | Python missing or not on PATH | Install from python.org and tick "Add Python to PATH". Reopen VS Code. |
| `running scripts is disabled on this system` | PowerShell blocks the activate script | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then activate again. |
| `'git' is not recognized` | Git not installed | Install from git-scm.com and reopen VS Code. |
| Python is older than 3.11 | Old installation | Install a newer Python, delete `.venv`, create it again. |

## 11. Evidence

- [x] Screenshot: terminal showing `(.venv)` and 8 PASS lines (13 Nov 2026, 16:11 PKT)

## 12. Completion status

**Completed** on 13 November 2026. Python 3.14.10 installed, `.venv` created and
activated, pip 26.3 installed inside the environment, and all 8 checks pass on
the project machine.

## 13. Next steps

Record the test results above, then start Task 1.2 (requirements document).

---

# Task 1.4 · Project Dependencies

| | |
|---|---|
| **Task** | 1.4 Install dependencies |
| **Status** | Completed 16 Nov 2026 — all 7 packages installed and verified. DEP-01..05 all Pass. |

## Objective

Install the Python packages the backend needs, confirm they work on
Python 3.14, then record the exact versions so the project can be rebuilt
identically on Hugging Face Spaces later.

## Technical concepts

| Term | What it means | Why we need it | Example |
|---|---|---|---|
| **Package** | Reusable code written by someone else, installed with pip. | Writing a web server or a vector database from scratch would take months. | `fastapi` |
| **Dependency** | A package our project needs in order to run. | Without it the code fails at the `import` line. | `import fastapi` fails if it is not installed. |
| **`requirements.txt`** | A text file listing the packages. | Anyone can recreate the environment with one command instead of guessing. | `pip install -r backend/requirements.txt` |
| **Transitive dependency** | A package that one of our packages needs. | They get installed automatically, which is why one install line produces dozens of packages. | `chromadb` pulls in `numpy`. |
| **Version pinning** | Writing an exact version, such as `fastapi==0.121.2`. | Guarantees the server installs the same code that worked on your laptop. | A loose list could install a newer, broken version next month. |
| **Lock file** | A file holding every exact version after a successful install. | It is generated from reality, not guessed. | `requirements.lock.txt` |
| **Extra** | An optional add-on to a package, written in brackets. | `uvicorn[standard]` adds faster networking than plain `uvicorn`. | `uvicorn[standard]` |

## Packages chosen and why

| Package | Role in this project |
|---|---|
| `fastapi` | Provides the `/chat` and `/lead` web addresses |
| `uvicorn[standard]` | The server that runs FastAPI |
| `google-genai` | Gemini SDK: writes answers and creates embeddings |
| `chromadb` | Vector database holding the document chunks |
| `python-dotenv` | Reads `backend/.env` so the API key stays out of the code |
| `httpx` | Sends leads to the n8n webhook |
| `pytest` | Runs the tests in `tests/` |

### Why versions are not pinned yet

`backend/requirements.txt` lists package names with a minimum version only
where one is genuinely required (`google-genai>=3.3.0` for Python 3.14 support,
`chromadb>=1.5.9`). Writing exact pins before installing would mean inventing
version numbers that have not been tested on this machine. The correct order is:
install, verify, then freeze the real versions into a lock file.

## Instructions

With the virtual environment active and the prompt showing `(.venv)`:

```powershell
pip install -r backend\requirements.txt
```

This downloads a few hundred megabytes and takes several minutes. `chromadb`
alone pulls in many transitive dependencies.

Then record what was actually installed:

```powershell
pip freeze > backend\requirements.lock.txt
```

And confirm the three critical packages import cleanly:

```powershell
python -c "import fastapi, chromadb; from google import genai; print('imports OK')"
```

## Testing procedure

| Test ID | Objective | Input | Expected result |
|---|---|---|---|
| DEP-01 | Install completes | `pip install -r backend\requirements.txt` | Ends with `Successfully installed ...`, no red errors |
| DEP-02 | Packages import | the `python -c` line above | Prints `imports OK` |
| DEP-03 | Lock file created | `pip freeze > backend\requirements.lock.txt` | File exists and lists exact versions |
| DEP-04 | Installed into the project, not globally | Read the install path in pip's output | Path contains `.venv` |

## Test results

Run on the project machine, 16 November 2026, 09:57 PKT.
Python 3.14.10, virtual environment active.

| Test ID | Objective | Result | Evidence |
|---|---|---|---|
| DEP-01 | Install completes | **Pass** | Command finished and returned to the prompt with no error. The `Successfully installed ...` summary had scrolled out of the window, so the install was confirmed instead by DEP-02 and DEP-03 below. |
| DEP-02 | Packages import | **Pass**, but see note | `python -c "import fastapi, chromadb; from google import genai; print('imports OK')"` printed `imports OK`. **This test was too weak.** On 16 Nov it still printed `imports OK` while ChromaDB was in fact unusable, because the Rust engine loads lazily on client creation, not on import. See `docs/07_ingestion.md`. Replaced by a real smoke test in Task 1.8. |
| DEP-03 | Lock file created | **Pass** | `backend/requirements.lock.txt` created, 98 packages listed. |
| DEP-04 | Installed into the project, not globally | **Pass** | Every dependency line in pip's output read `in .\.venv\Lib\site-packages`, and the prompt showed `(.venv)`. |
| DEP-05 | Lock file is readable as plain text | **Fail**, then **Pass** on re-test | First attempt produced UTF-16 LE (see Problems below). Regenerated with `-Encoding ascii` and re-checked: file is now ASCII, 98 packages, readable. Re-test 16 Nov 2026, 10:10 PKT. |

### Versions actually installed

These are read from `requirements.lock.txt`, not from documentation.

| Package | Version installed |
|---|---|
| `fastapi` | 0.162.7 |
| `uvicorn` | 0.54.0 |
| `google-genai` | 3.3.0 |
| `chromadb` | 1.5.9 |
| `python-dotenv` | 1.2.4 |
| `httpx` | 0.28.1 |
| `pytest` | 9.2.0 |

Notable packages pulled in automatically: `numpy` 2.5.4, `onnxruntime` 1.32.0,
`pydantic` 2.14.3, `starlette` 1.10.0, `tokenizers` 0.23.3, `grpcio` 1.85.1.
98 packages in total from 7 requested.

## Problems encountered

| # | Problem | Cause | Fix |
|---|---|---|---|
| 6 | `requirements.lock.txt` was written as UTF-16 LE instead of plain text. | Windows PowerShell 5.1 writes UTF-16 when you redirect output with `>`. The file looks correct in VS Code but reads as binary to other tools. | Regenerated with an explicit encoding: `pip freeze \| Out-File -Encoding ascii backend\requirements.lock.txt`. Verified ASCII afterwards. **Resolved.** |

Why this matters: in Stage 3 the Docker image on Hugging Face Spaces will read
this file on Linux. A UTF-16 file causes `pip install -r` to fail there with a
confusing error that names the first package rather than the encoding. Fixing it
now costs one command; finding it during deployment would cost an hour.

## Known risks — outcome

The risk recorded before the install was that Python 3.14 is recent enough that
some package might have no pre-built wheel, forcing pip to compile from source
and fail on Windows without a C++ compiler. The named candidates were `numpy`
and `onnxruntime`.

**This did not happen.** Both installed cleanly (`numpy` 2.5.4,
`onnxruntime` 1.32.0), which confirms the Python version choice made in
Task 1.1 was sound. The risk is now closed.

One risk remains open and moves to Stage 3: the versions above were resolved on
Windows with Python 3.14. The Hugging Face Spaces image runs Linux. Pinning
from this lock file reduces the difference but does not remove it, so the
deployment task must budget time for a first build that fails.
