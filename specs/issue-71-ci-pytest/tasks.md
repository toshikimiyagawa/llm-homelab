# Tasks: issue-71 - CI で pytest を実行する

> 実装エージェントはこの tasks を上から順に実行する。`spec.md` / `plan.md` / `tasks.md` は変更しない。

## Task 1: Add the failing workflow contract test

**Files:**
- Create: `tests/ci/__init__.py`
- Create: `tests/ci/test_sdd_check_workflow.py`

- [ ] **Step 1: Create the CI test package marker**

Create an empty file:

```text
tests/ci/__init__.py
```

- [ ] **Step 2: Add the workflow contract test**

Create `tests/ci/test_sdd_check_workflow.py` with this complete content:

```python
from pathlib import Path


WORKFLOW = Path(".github/workflows/sdd-check.yml")
TESTS_STEP_MARKER = "      - name: Tests\n        run: |\n"


def _tests_step_run_block() -> str:
    text = WORKFLOW.read_text()
    start = text.index(TESTS_STEP_MARKER) + len(TESTS_STEP_MARKER)
    next_step = text.find("\n      - name:", start)
    next_job = text.find("\n  ansible-lint:", start)

    candidates = [position for position in (next_step, next_job) if position != -1]
    end = min(candidates) if candidates else len(text)
    return text[start:end]


def test_tests_step_installs_yamllint_and_uv() -> None:
    block = _tests_step_run_block()

    assert "pip install yamllint uv" in block


def test_tests_step_runs_yamllint() -> None:
    block = _tests_step_run_block()

    assert "yamllint -s ." in block


def test_tests_step_runs_uvx_pytest_quiet() -> None:
    block = _tests_step_run_block()

    assert "uvx pytest -q" in block


def test_tests_step_avoids_temporary_or_nonstandard_pytest_commands() -> None:
    block = _tests_step_run_block()

    assert "--import-mode=importlib" not in block
    assert "python -m pytest" not in block
    assert "python3 -m pytest" not in block
```

- [ ] **Step 3: Run the focused test and confirm it fails before workflow implementation**

Run:

```bash
uvx pytest tests/ci/test_sdd_check_workflow.py -q
```

Expected result:

```text
F..F
```

The failure must include missing `pip install yamllint uv` and/or missing `uvx pytest -q` in the workflow `Tests` step.

## Task 2: Add pytest execution to SDD Check

**Files:**
- Modify: `.github/workflows/sdd-check.yml`
- Test: `tests/ci/test_sdd_check_workflow.py`

- [ ] **Step 1: Update the `Tests` step**

In `.github/workflows/sdd-check.yml`, change the existing `Tests` step to exactly:

```yaml
      - name: Tests
        run: |
          pip install yamllint uv
          yamllint -s .
          uvx pytest -q
```

- [ ] **Step 2: Run the focused test and confirm it passes**

Run:

```bash
uvx pytest tests/ci/test_sdd_check_workflow.py -q
```

Expected result:

```text
4 passed
```

## Task 3: Run full verification

**Files:**
- Verify: `.github/workflows/sdd-check.yml`
- Verify: `tests/ci/test_sdd_check_workflow.py`

- [ ] **Step 1: Run repository-wide pytest**

Run:

```bash
uvx pytest -q
```

Expected result:

```text
all tests pass
```

- [ ] **Step 2: Run workflow yamllint**

Run:

```bash
yamllint .github/workflows/sdd-check.yml
```

Expected result:

```text
no output and exit code 0
```

- [ ] **Step 3: Check whitespace**

Run:

```bash
git diff --check
```

Expected result:

```text
no output and exit code 0
```

## Acceptance Criteria Traceability

| AC | Covered By |
| --- | --- |
| AC-1 | Task 1 test, Task 2 workflow edit |
| AC-2 | Task 1 test, existing `yamllint -s .` preserved in Task 2 |
| AC-3 | Task 1 test, Task 2 workflow edit |
| AC-4 | Task 1 test |
| AC-5 | Task 2 focused pytest run |
| AC-6 | Task 3 repository-wide pytest run |
