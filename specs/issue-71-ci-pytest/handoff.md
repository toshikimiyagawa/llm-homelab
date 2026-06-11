# Handoff: issue-71-ci-pytest

## Your scope

Implementation phase only. Do not touch `spec.md`, `plan.md`, or the verify phase.
If the spec needs changes, stop and escalate to a human.

Implement only the tasks in `specs/issue-71-ci-pytest/tasks.md`:

- Add static workflow contract tests under `tests/ci/`.
- Update `.github/workflows/sdd-check.yml` so the existing `Tests` step installs `uv` and runs `uvx pytest -q`.
- Run the verification commands listed in the spec and tasks.

## Done when

- [ ] All tasks in `specs/issue-71-ci-pytest/tasks.md` are complete
- [ ] Every acceptance criterion in `specs/issue-71-ci-pytest/spec.md` has a passing test
- [ ] Test suite passes

## Reference files

- spec:  `specs/issue-71-ci-pytest/spec.md`
- plan:  `specs/issue-71-ci-pytest/plan.md`
- tasks: `specs/issue-71-ci-pytest/tasks.md`

## If the spec is ambiguous or insufficient

1. Stop immediately.
2. Set `.sdd/tasks.json` status to `"blocked"`.
3. Fill in `blocked_reason`.
4. Wait for a human to escalate before resuming.
