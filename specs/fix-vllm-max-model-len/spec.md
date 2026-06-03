# Spec: fix-vllm-max-model-len

- Tier: 1
- Status: implement

## Intent

vLLM の --max-model-len 81920 指定を削除する。
Qwen3-32B の max_position_embeddings=40960 を超える値は設定不可で Pod が起動失敗するため。
opencode の token 超過問題は devcontainer グローバル設定の limit.output: 8192 で対処する。

## Acceptance Criteria

1. `roles/vllm/templates/vllm-deployment.yml.j2` に `--max-model-len` が含まれない。
2. `roles/vllm/defaults/main.yml` に `vllm_max_model_len` が含まれない。

## Verification

- `uvx pytest tests/vllm/test_role.py`
- `yamllint roles/vllm/`
