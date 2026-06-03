# Spec: issue-73-opencode-token-limits

- Tier: 1
- Status: implement
- Issue: #73

## Intent

opencode の devcontainer 初期設定を、opencode が実際に読むグローバル設定パスへ配置し、vLLM の Qwen3-32B に適切な context/output limit を明示して `max_tokens` 超過による失敗を防ぐ。

## Acceptance Criteria

1. devcontainer post-install は opencode 設定を `~/.config/opencode/opencode.json` に作成する。
2. opencode 設定は singular `provider` キーで vLLM の OpenAI-compatible provider を定義する。
3. `vllm/qwen3-32b` の model 定義に `limit.context: 40960` と `limit.output: 8192` が含まれる。
4. API key は秘密値ではなく vLLM が受け付けるダミー値として管理される。

## Verification

- `python -m pytest tests/opencode/test_devcontainer_config.py`
- `yamllint .devcontainer/project-tools.yml`
