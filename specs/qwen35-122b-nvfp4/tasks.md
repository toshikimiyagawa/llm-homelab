# Tasks: Qwen3.5-122B-A10B NVFP4 vLLM migration

> 実装 agent は `spec.md` を読み、この tasks を過不足なく実装する。`specs/` 配下は実装中に変更しない。

## Task 1: vLLM static tests を新モデルへ更新する

**Files**

- Modify: `tests/vllm/test_role.py`

**Steps**

- [ ] Change Qwen3.6 assertions to Qwen3.5-122B-A10B-NVFP4.
- [ ] Assert `vllm_max_model_len: 32768`.
- [ ] Assert `vllm_max_num_seqs: 4`.
- [ ] Assert tool calling flags are retained.
- [ ] Assert `--quantization` and `moe_wna16` are absent.
- [ ] Run `uvx pytest tests/vllm/test_role.py -q` and confirm RED.

**Acceptance Criteria**

- AC-1
- AC-2
- AC-3
- AC-4
- AC-5

## Task 2: vLLM role / inventory を更新する

**Files**

- Modify: `roles/vllm/defaults/main.yml`
- Modify: `inventory/group_vars/all/vars.yml`
- Modify: `roles/vllm/templates/vllm-deployment.yml.j2` only if needed for a no-quantization assertion comment.

**Steps**

- [ ] Set `vllm_model` to `/models/Qwen3.5-122B-A10B-NVFP4`.
- [ ] Set `vllm_served_model_name` to `qwen3.5-122b-a10b-nvfp4`.
- [ ] Set `vllm_model_dir` to `Qwen3.5-122B-A10B-NVFP4`.
- [ ] Set `vllm_max_model_len` to `32768`.
- [ ] Set `vllm_max_num_seqs` to `4`.
- [ ] Keep tool calling args unchanged.
- [ ] Run `uvx pytest tests/vllm/test_role.py -q`.

**Acceptance Criteria**

- AC-1
- AC-2
- AC-3
- AC-4
- AC-5
- AC-8

## Task 3: opencode config を追従する

**Files**

- Modify: `.devcontainer/project-tools.yml`
- Modify: `tests/opencode/test_devcontainer_config.py`

**Steps**

- [ ] Set default opencode model to `vllm/qwen3.5-122b-a10b-nvfp4`.
- [ ] Set provider model key to `qwen3.5-122b-a10b-nvfp4`.
- [ ] Set display name to `Qwen3.5-122B-A10B-NVFP4`.
- [ ] Set context limit to `32768` and keep output `8192`.
- [ ] Run `uvx pytest tests/opencode/test_devcontainer_config.py -q`.

**Acceptance Criteria**

- AC-7
- AC-8

## Task 4: docs を更新する

**Files**

- Modify: `docs/software-stack.md`
- Modify: `docs/operations.md`

**Steps**

- [ ] Replace Qwen3.6 model references with Qwen3.5-122B-A10B-NVFP4 where they describe the current vLLM backend.
- [ ] Document NVFP4 4bit, local model path, `32768` initial context, `max_num_seqs=4`, and retained tool calling flags.
- [ ] Update curl examples to `qwen3.5-122b-a10b-nvfp4`.
- [ ] Run `yamllint roles/vllm/ inventory/group_vars/all/vars.yml docs/software-stack.md docs/operations.md .devcontainer/project-tools.yml`.

**Acceptance Criteria**

- AC-6
- AC-10

## Task 5: verify, PR, and runtime gate

**Steps**

- [ ] Run `uvx pytest tests/vllm/test_role.py tests/opencode/test_devcontainer_config.py -q`.
- [ ] Run `uvx pytest -q`.
- [ ] Run `yamllint roles/vllm/ inventory/group_vars/all/vars.yml docs/software-stack.md docs/operations.md .devcontainer/project-tools.yml`.
- [ ] Commit and create PR with `sdd:tier-2`.
- [ ] Merge after CI passes.
- [ ] Check `/opt/models/Qwen3.5-122B-A10B-NVFP4` on `llm01`.
- [ ] If model directory is absent, STOP and report the exact download requirement.
- [ ] If present, apply `ansible-playbook playbooks/09-vllm.yml --tags vllm`.
- [ ] Verify `/v1/models` and tool call smoke request.

**Acceptance Criteria**

- AC-8
- AC-9
- AC-10
- AC-11
- AC-12
- AC-13

