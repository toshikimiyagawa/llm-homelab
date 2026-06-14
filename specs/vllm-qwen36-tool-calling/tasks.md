# Tasks: vLLM Qwen3.6 tool calling for Hermes agent

> 実装 agent は `spec.md` を読み、この tasks を過不足なく実装する。`specs/` 配下は実装中に変更しない。

## Task 1: static tests を Qwen3.6 tool calling 設定に更新する

**Files**

- Modify: `tests/vllm/test_role.py`

**Steps**

- [ ] Update `test_deployment_enables_tool_call_options` to assert:
  - `--enable-auto-tool-choice`
  - `--reasoning-parser`
  - `qwen3`
  - `--tool-call-parser`
  - `qwen3_coder`
  - no `"hermes"` parser in the deployment template
- [ ] Run `uvx pytest tests/vllm/test_role.py::test_deployment_enables_tool_call_options -q`.
- [ ] Confirm it fails before implementation.

**Acceptance Criteria**

- AC-1
- AC-2
- AC-3

## Task 2: vLLM Deployment args を更新する

**Files**

- Modify: `roles/vllm/templates/vllm-deployment.yml.j2`

**Steps**

- [ ] Add `--reasoning-parser` and `qwen3` near the model/tool args.
- [ ] Change the `--tool-call-parser` value from `hermes` to `qwen3_coder`.
- [ ] Run `uvx pytest tests/vllm/test_role.py -q`.

**Acceptance Criteria**

- AC-1
- AC-2
- AC-3
- AC-5

## Task 3: docs を更新する

**Files**

- Modify: `docs/software-stack.md`
- Modify: `docs/operations.md`

**Steps**

- [ ] Document that Hermes agent / OpenAI-compatible tools require vLLM to run with `--enable-auto-tool-choice`, `--reasoning-parser qwen3`, and `--tool-call-parser qwen3_coder`.
- [ ] Run `yamllint roles/vllm/ docs/software-stack.md docs/operations.md`.

**Acceptance Criteria**

- AC-4
- AC-6

## Task 4: verify and publish

**Steps**

- [ ] Run `uvx pytest tests/vllm/test_role.py -q`.
- [ ] Run `uvx pytest -q`.
- [ ] Run `yamllint roles/vllm/ docs/software-stack.md docs/operations.md`.
- [ ] Commit with Conventional Commits.
- [ ] Create a PR with `sdd:tier-1`.
- [ ] After merge, run `ansible-playbook playbooks/09-vllm.yml --tags vllm` to apply to `llm01`.

**Acceptance Criteria**

- AC-5
- AC-6

