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
