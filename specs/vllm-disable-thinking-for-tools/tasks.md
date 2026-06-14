# Tasks: Disable Qwen3.6 thinking for vLLM tool calls

> 実装 agent は `spec.md` を読み、この tasks を過不足なく実装する。`specs/` 配下は実装中に変更しない。

## Task 1: static tests を追加する

**Files**

- Modify: `tests/vllm/test_role.py`

**Steps**

- [ ] Add assertions to `test_deployment_enables_tool_call_options` for:
  - `--default-chat-template-kwargs`
  - `enable_thinking`
  - `false`
- [ ] Run `uvx pytest tests/vllm/test_role.py::test_deployment_enables_tool_call_options -q`.
- [ ] Confirm the test fails before implementation.

**Acceptance Criteria**

- AC-1
- AC-2

## Task 2: Deployment args を更新する

**Files**

- Modify: `roles/vllm/templates/vllm-deployment.yml.j2`

**Steps**

- [ ] Add `--default-chat-template-kwargs` after `--reasoning-parser qwen3`.
- [ ] Add the JSON value `{"enable_thinking": false}` as the next arg.
- [ ] Run `uvx pytest tests/vllm/test_role.py -q`.

**Acceptance Criteria**

- AC-1
- AC-2
- AC-4

## Task 3: docs を更新する

**Files**

- Modify: `docs/software-stack.md`
- Modify: `docs/operations.md`

**Steps**

- [ ] Explain that Qwen3.6 thinking is disabled by default for the Hermes agent tool-calling path because runtime testing showed tool calls were generated only with `enable_thinking=false`.
- [ ] Run `yamllint roles/vllm/ docs/software-stack.md docs/operations.md`.

**Acceptance Criteria**

- AC-3
- AC-5

## Task 4: publish and apply

**Steps**

- [ ] Run `uvx pytest tests/vllm/test_role.py -q`.
- [ ] Run `uvx pytest -q`.
- [ ] Run `yamllint roles/vllm/ docs/software-stack.md docs/operations.md`.
- [ ] Commit and create PR with `sdd:tier-1`.
- [ ] Merge after CI passes.
- [ ] Apply `ansible-playbook playbooks/09-vllm.yml --tags vllm`.
- [ ] Verify smoke request returns `finish_reason=tool_calls`.

**Acceptance Criteria**

- AC-4
- AC-5
- AC-6

