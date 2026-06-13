# Tasks: issue-124-vllm-qwen36

順序付きの実装ステップ。各タスクに対応する受け入れ基準（AC）と、それを証明するテストを併記する。
TDD（RED→GREEN→REFACTOR）で進めること。

## T1. テスト更新（RED）

`tests/vllm/test_role.py` を新仕様に合わせて更新する。

- `test_default_max_model_len_and_rope_scaling` を改名/改修し、
  - `vllm_max_model_len` が `92736` より大きい（例: `131072`）こと
  - `defaults/main.yml` に `yarn` / `vllm_rope_scaling_dict` が**含まれない**こと
  を検証する。 → AC3, AC4
- `test_tasks_configure_yarn_rope_scaling_in_model_config` を改修し、`tasks/main.yml` が
  `vllm_rope_scaling_dict` / `YaRN RoPE` / `config.json` の `slurp` 改変を**含まない**ことを検証する。 → AC5
- `test_deployment_sets_max_model_len_for_128k_context` は `--max-model-len` と `vllm_max_model_len` の存在維持を検証（据え置き）。 → AC6
- 新規: `group_vars/all/vars.yml` の `vllm_model` / `vllm_served_model_name` が Qwen3.6 値であることを検証。 → AC1
- 新規: `defaults/main.yml` の `vllm_model_dir` が `Qwen3.6-35B-A3B` であることを検証。 → AC2
- 新規: deployment にマルチモーダル有効化フラグ（`--limit-mm-per-prompt` 等）が**含まれない**ことを検証。 → AC7
- `test_deployment_enables_tool_call_options` / `test_deployment_uses_recreate_strategy_for_fixed_gpu` は据え置き（AC6 維持確認）。
- `test_api_verification_uses_service_endpoint_not_pod_tools` は据え置き。

この時点で `uvx pytest tests/vllm/test_role.py` は RED。

## T2. 設定値の更新（GREEN）

- `inventory/group_vars/all/vars.yml`:
  - `vllm_model: /models/Qwen3.6-35B-A3B`
  - `vllm_served_model_name: qwen3.6-35b-a3b`
  → AC1
- `roles/vllm/defaults/main.yml`:
  - `vllm_model: /models/Qwen3.6-35B-A3B`（defaults も整合させる）
  - `vllm_served_model_name: qwen3.6-35b-a3b`
  - `vllm_model_dir: Qwen3.6-35B-A3B`
  - `vllm_max_model_len: 131072`（起点値。AC13 で実機調整）
  - `vllm_rope_scaling_dict` ブロックを削除
  → AC2, AC3, AC4

## T3. YaRN タスク削除（GREEN）

`roles/vllm/tasks/main.yml` から以下 2 タスクを削除する:

- `Read current model config.json`（`slurp`）
- `Configure YaRN RoPE scaling in model config.json`（`copy`）

→ AC5

## T4. deployment テンプレート確認（GREEN）

`roles/vllm/templates/vllm-deployment.yml.j2` は変更不要であることを確認する。
`--max-model-len` / tool-call オプション / Recreate strategy が維持され、マルチモーダルフラグが無いこと。
→ AC6, AC7

## T5. ドキュメント更新

- `docs/software-stack.md` vLLM セクション（モデル行）を `Qwen3.6-35B-A3B`（MoE 35B/3B、テキスト専用、native 262K）に更新。 → AC8
- `docs/operations.md` の `curl` 動作確認例の `"model":"qwen3-32b"` を `"qwen3.6-35b-a3b"` に更新。 → AC9

## T6. 静的検証（GREEN 確認）

- `uvx pytest tests/vllm/test_role.py` が全 PASS。 → AC1–9
- `yamllint roles/vllm/ inventory/group_vars/all/vars.yml`
- `ansible-lint`

## T7. 実機検証（手動・PR レビュー後）

- `ansible-playbook playbooks/09-vllm.yml` を実行。 → AC10
- Pod `Running` / rollout 成功 / `/v1/models` が `qwen3.6-35b-a3b` を返す。 → AC10, AC11
- Open WebUI から推論成功。 → AC12
- `--max-model-len` が 96GB VRAM に収まることを確認し、必要なら `vllm_max_model_len` を確定値へ調整。 → AC13
- vLLM イメージが Qwen3.6 非対応で Pod が起動失敗する場合は **STOP** し人間にエスカレーション（イメージ tag 固定は別 issue）。

## 完了後

- `.sdd/state.json` を `phase=verify` に更新。
- sdd-reviewer で凍結 spec との整合を確認後、PR を作成（description は日本語）。
