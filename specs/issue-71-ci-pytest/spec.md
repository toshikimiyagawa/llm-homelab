# Spec: issue-71 - CI で pytest を実行する

## Background

Issue #71 originally covered two related problems:

- `tests/*/test_role.py` files collided during full pytest collection.
- `.github/workflows/sdd-check.yml` did not run pytest, so static test regressions could pass CI.

The import mismatch has already been fixed by #96 by package-izing the test directories.
This spec covers the remaining CI gap: pull requests must run the repository's static pytest suite.

## Goal

Add pytest execution to the existing SDD Check workflow so CI catches static test regressions in pull requests.

## Non-Goals

- Do not rename existing `test_role.py` files.
- Do not use `pytest --import-mode=importlib` as a permanent CI workaround.
- Do not audit or rewrite historical SDD specs that mention `python -m pytest`; that remains tracked by #75.
- Do not make `ansible-lint` blocking in this issue.

## Design

Use the existing `.github/workflows/sdd-check.yml` `Tests` step as the authoritative CI gate for static repository checks.

The step must install `uv` on GitHub Actions' `ubuntu-latest` runner, keep the existing `yamllint -s .` check, and run the repository-wide pytest suite with:

```bash
uvx pytest -q
```

This keeps CI aligned with the current devcontainer and recent SDD artifacts, which use `uvx pytest` as the practical pytest entrypoint.

Add a static pytest contract test for the workflow itself so future workflow edits cannot silently remove pytest from CI.

## Acceptance Criteria

1. **AC-1**: `.github/workflows/sdd-check.yml` installs both `yamllint` and `uv` before repository tests run.
2. **AC-2**: The SDD Check `Tests` step still runs `yamllint -s .`.
3. **AC-3**: The SDD Check `Tests` step runs `uvx pytest -q`.
4. **AC-4**: The SDD Check `Tests` step does not use `pytest --import-mode=importlib`, `python -m pytest`, or `python3 -m pytest` as the CI pytest command.
5. **AC-5**: A static pytest test verifies AC-1 through AC-4 against `.github/workflows/sdd-check.yml`.
6. **AC-6**: The repository-wide local verification command `uvx pytest -q` passes.

## Verification

- `uvx pytest tests/ci/test_sdd_check_workflow.py -q`
- `uvx pytest -q`
- `yamllint .github/workflows/sdd-check.yml`
- `git diff --check`

## Related Issues

- #96 fixed the pytest import mismatch that blocked full-suite execution.
- #75 tracks broader documentation/spec alignment around pytest invocation.
