# CI Pytest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the SDD Check workflow run the repository-wide static pytest suite with `uvx pytest -q`.

**Architecture:** Keep the existing `sdd` GitHub Actions job and extend only its `Tests` step. Add a focused static pytest contract test that reads `.github/workflows/sdd-check.yml` and verifies the expected CI commands.

**Tech Stack:** GitHub Actions YAML, `pip`, `uvx pytest`, `yamllint`, Python stdlib pytest tests.

---

## File Structure

- `.github/workflows/sdd-check.yml` — extend the existing `Tests` step to install `uv` and run `uvx pytest -q` after `yamllint -s .`.
- `tests/ci/test_sdd_check_workflow.py` — new static contract tests for the workflow's `Tests` step.
- `tests/ci/__init__.py` — package marker for the new CI test package.

## Approach

Use the existing SDD Check job rather than a separate job. The issue is about making the current CI gate catch static pytest regressions, and the current `Tests` step already represents the lightweight required checks.

The CI command should be:

```yaml
- name: Tests
  run: |
    pip install yamllint uv
    yamllint -s .
    uvx pytest -q
```

This preserves the current lint gate, installs `uv` explicitly for GitHub Actions, and standardizes CI on the same pytest entrypoint used by recent local verification.

## Alternatives Considered

- **Separate pytest job**: Clearer separation, but unnecessary overhead for this small workflow and not needed to satisfy #71.
- **`pytest --import-mode=importlib`**: Useful as a temporary workaround, but #96 fixed the import mismatch directly. Keeping this in CI would hide future packaging regressions.
- **`python -m pytest` / `python3 -m pytest`**: Diverges from current devcontainer practice and the `uvx pytest` commands already used in recent specs.

## Acceptance Criteria Mapping

| Acceptance Criterion | Test / Verification |
| --- | --- |
| AC-1 | `tests/ci/test_sdd_check_workflow.py::test_tests_step_installs_yamllint_and_uv` |
| AC-2 | `tests/ci/test_sdd_check_workflow.py::test_tests_step_runs_yamllint` |
| AC-3 | `tests/ci/test_sdd_check_workflow.py::test_tests_step_runs_uvx_pytest_quiet` |
| AC-4 | `tests/ci/test_sdd_check_workflow.py::test_tests_step_avoids_temporary_or_nonstandard_pytest_commands` |
| AC-5 | `uvx pytest tests/ci/test_sdd_check_workflow.py -q` |
| AC-6 | `uvx pytest -q` |

## Verification Commands

```bash
uvx pytest tests/ci/test_sdd_check_workflow.py -q
uvx pytest -q
yamllint .github/workflows/sdd-check.yml
git diff --check
```
