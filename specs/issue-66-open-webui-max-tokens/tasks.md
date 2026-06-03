# Tasks: issue-66-open-webui-max-tokens

## Implementation Tasks

- [ ] T1: Open WebUI のデフォルト推論パラメータに `max_tokens` を追加する。対応AC: AC1, AC2
- [ ] T2: Deployment テンプレートで `DEFAULT_MODEL_PARAMS` をコンテナ環境に渡す。対応AC: AC2
- [ ] T3: `docs/software-stack.md` に Open WebUI の max_tokens 方針を追記する。対応AC: AC3
- [ ] T4: `docs/operations.md` に長い会話時の失敗条件と回避策を追記する。対応AC: AC3
- [ ] T5: `tests/open_webui/test_role.py` に回帰テストを追加する。対応AC: AC1-AC4

## Tests

- [ ] AC1, AC2, AC4 -> `uvx pytest tests/open_webui/test_role.py -q`
- [ ] AC3 -> `rg -n "DEFAULT_MODEL_PARAMS|max_tokens|vLLM|40960" docs/software-stack.md docs/operations.md`
