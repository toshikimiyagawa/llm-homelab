# Spec: Disable Qwen3.6 thinking for vLLM tool calls

**Status**: frozen
**Tier**: 1
**Created**: 2026-06-14

## 目的

Hermes agent が検索などの tool call を自動発火できるよう、vLLM の Qwen3.6 chat template default で thinking を無効化する。

実機確認では `--enable-auto-tool-choice`、`--reasoning-parser qwen3`、`--tool-call-parser qwen3_coder` により `tool_choice:auto` は 400 なしで受理された。しかし検索が必要な質問でも `tool_calls: []` になり、reasoning に入っていた。同じリクエストに `chat_template_kwargs.enable_thinking=false` を付けると `web_search` tool call が生成されたため、起動時 default として設定する。

## スコープ

### 含む

- vLLM Deployment args に `--default-chat-template-kwargs` を追加する。
- 値は `{"enable_thinking": false}` に固定する。
- `--enable-auto-tool-choice`、`--reasoning-parser qwen3`、`--tool-call-parser qwen3_coder` は維持する。
- static tests と docs を更新する。

### 含まない

- Hermes agent 側のプロンプト変更。
- vLLM image tag / model / context / GPU 設定変更。
- request ごとの tool_choice 制御。

## 受け入れ基準

1. vLLM Deployment args に `--default-chat-template-kwargs` と `{"enable_thinking": false}` が含まれる。
2. vLLM Deployment args は `--enable-auto-tool-choice`、`--reasoning-parser qwen3`、`--tool-call-parser qwen3_coder` を維持する。
3. docs が tool calling 用に thinking を無効化する理由と確認方法を説明する。
4. `uvx pytest tests/vllm/test_role.py -q` が pass する。
5. `yamllint roles/vllm/ docs/software-stack.md docs/operations.md` が pass する。
6. 実機 rollout 後、`tool_choice:auto` の smoke request が `finish_reason=tool_calls` と `web_search` tool call を返す。

## テスト方針

- `tests/vllm/test_role.py`
  - `--default-chat-template-kwargs` があること。
  - JSON 値に `enable_thinking` と `false` があること。
  - 既存 tool/reasoning parser flags が残ること。
- Runtime
  - WARP/cluster 経由で `/v1/chat/completions` に tool 定義つき request を送り、tool call が返ることを確認する。

