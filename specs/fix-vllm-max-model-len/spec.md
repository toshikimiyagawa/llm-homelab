# Spec: fix-vllm-max-model-len

- Tier: 1
- Status: implement

## Intent

vLLM の max_model_len を 81920 に引き上げ、opencode が送る max_tokens=32000 と長めのプロンプトが重なっても超過しないようにする。
プロジェクトルートの opencode.json（未追跡ファイル）を削除し、devcontainer グローバル設定のみで管理する。

## Acceptance Criteria

1. `roles/vllm/defaults/main.yml` に `vllm_max_model_len: 81920` が定義される。
2. `roles/vllm/templates/vllm-deployment.yml.j2` の args に `--max-model-len` と `{{ vllm_max_model_len }}` が含まれる。
3. プロジェクトルートに `opencode.json` が存在しない。

## Verification

- `uvx pytest tests/vllm/test_role.py`
- `yamllint roles/vllm/`
