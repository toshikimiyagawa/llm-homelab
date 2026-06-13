# Spec: issue-126-vllm-max-num-seqs

- Tier: 1
- Status: frozen
- Issue: #126

## Intent

Qwen3.6-35B-A3B（Gated DeltaNet ハイブリッド MoE）で vLLM が
`max_num_seqs (1024) exceeds available Mamba cache blocks (754)` により
CUDA graph capture に失敗し EngineCore がクラッシュループする問題を解消する。

各 decode シーケンスが 1 Mamba cache block を要するため、`gpu_memory_utilization: 0.90`
で確保できる Mamba ブロック数（実機 llm01 で 754）を超える `max_num_seqs` を指定できない。
空冷優先方針のため `gpu_memory_utilization` は引き上げず、`--max-num-seqs` で concurrency を
上限に合わせる。

## Acceptance Criteria

1. `roles/vllm/defaults/main.yml` に `vllm_max_num_seqs: 754` が定義される。
2. `roles/vllm/templates/vllm-deployment.yml.j2` の args に `--max-num-seqs` と
   `{{ vllm_max_num_seqs | string }}` が含まれる。
3. （実機・テスト対象外）`ansible-playbook playbooks/09-vllm.yml` で vLLM Pod が
   Ready になり rollout 成功、`/v1/models` が `qwen3.6-35b-a3b` を返す。

## Verification

- `uvx pytest tests/vllm/test_role.py`
- `yamllint roles/vllm/`
- `ansible-lint roles/vllm/`
- 実機: `ansible-playbook playbooks/09-vllm.yml`（AC3）
