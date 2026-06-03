# Spec: issue-66-open-webui-max-tokens

## Intent

Open WebUI の全体デフォルトの `max_tokens` を、vLLM の `max_model_len=40960` を超えにくい値に固定し、長い会話履歴で `vllm.exceptions.VLLMValidationError` が出る状況を避ける。

## Acceptance Criteria

1. `roles/open_webui/defaults/main.yml` に、Open WebUI の全体デフォルト推論パラメータとして `max_tokens` を持つ設定がある。
2. `roles/open_webui/templates/open-webui-deployment.yml.j2` がそのデフォルト推論パラメータを `DEFAULT_MODEL_PARAMS` としてコンテナ環境に渡す。
3. `docs/software-stack.md` と `docs/operations.md` に、Open WebUI の長い会話では `max_tokens` を下げる必要があることと、その回避策が記載されている。
4. `tests/open_webui/test_role.py` で、設定値と文書化が回帰テストされている。
