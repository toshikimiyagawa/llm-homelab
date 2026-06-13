# Spec: issue-124-vllm-qwen36

- Tier: 2
- Status: frozen
- Issue: #124

## Intent

vLLM が提供するメインモデルを Qwen3-32B（dense）から **Qwen3.6-35B-A3B**（スパース MoE、総 35B / アクティブ 3B）へ完全に置き換える。

設計合意（issue #124 / 2026-06-14）:

- **完全置き換え**: Qwen3-32B はサーブしない。RTX Pro 6000 96GB は 1 枚のため両モデル同時提供はしない。
- **テキスト専用で開始**: Qwen3.6-35B-A3B は vision encoder 付きだが、画像/動画入力は有効化しない（後続 issue で拡張余地）。
- **コンテキスト長は VRAM 内で最大化**: ネイティブ 262K のため、現行の YaRN RoPE スケーリング（`original_max_position_embeddings: 32768` → `92736`）は不要。YaRN 設定を廃止し、`config.json` を改変せず、ネイティブコンテキストから VRAM に収まる範囲で `--max-model-len` を設定する。

モデルウェイトの取得手順（`/opt/models/Qwen3.6-35B-A3B`）は手動運用のままとし、本 spec は Ansible 設定の追従と検証を対象とする（モデル `pull` の Ansible 化は対象外）。

## Acceptance Criteria

### 設定（静的・テスト対象）

1. `inventory/group_vars/all/vars.yml` の `vllm_model` が `/models/Qwen3.6-35B-A3B`、`vllm_served_model_name` が `qwen3.6-35b-a3b` である。
2. `roles/vllm/defaults/main.yml` の `vllm_model_dir` が `Qwen3.6-35B-A3B` である。
3. `roles/vllm/defaults/main.yml` に YaRN 関連設定（`vllm_rope_scaling_dict`、`yarn`）が含まれない。
4. `roles/vllm/defaults/main.yml` の `vllm_max_model_len` が現行値 `92736` より大きい値で、YaRN を伴わずに設定されている（ネイティブコンテキスト由来）。
5. `roles/vllm/tasks/main.yml` が `config.json` の YaRN RoPE スケーリング改変（`slurp` + `vllm_rope_scaling_dict` の注入）を行わない。
6. `roles/vllm/templates/vllm-deployment.yml.j2` が引き続き `--max-model-len`、`--enable-auto-tool-choice`、`--tool-call-parser hermes`、`Recreate` strategy を含む。
7. 画像/動画入力を有効化する vLLM 起動オプション（例: `--limit-mm-per-prompt` 等のマルチモーダル有効化フラグ）を deployment に追加しない（テキスト専用）。

### ドキュメント（静的・テスト対象）

8. `docs/software-stack.md` の vLLM セクションのモデル記載が Qwen3.6-35B-A3B を反映する。
9. `docs/operations.md` の動作確認 `curl` 例の `"model"` 値が `qwen3.6-35b-a3b` である。

### ランタイム（実機 playbook で検証・テスト対象外）

10. `ansible-playbook playbooks/09-vllm.yml` 実行後、vLLM Pod が `Running` になり rollout が成功する。
11. `/v1/models` が `qwen3.6-35b-a3b` を含む `{"object":"list"}` を返す。
12. Open WebUI から `qwen3.6-35b-a3b` への推論リクエストが成功する。
13. 実機で `--max-model-len` が 96GB VRAM（`vllm_gpu_memory_utilization: 0.90`）に収まることを確認し、最終値を確定する。

## Non-Goals

- モデルウェイトの自動ダウンロード（`huggingface-cli download` 等）の Ansible 化。
- 画像/動画（マルチモーダル）入力の有効化。
- Qwen3-32B との並行提供 / モデル切り替え機構。
- vLLM イメージのバージョン固定方針変更（現行 `latest` を踏襲）。

## Risks / Notes

- **vLLM イメージの対応**: `vllm/vllm-openai:latest` が Qwen3.6 / Gated DeltaNet（線形アテンション）アーキテクチャに対応している必要がある。未対応なら Pod 起動失敗。AC10 の rollout 検証で検出する。非対応時は STOP して人間にエスカレーション（イメージ tag 固定は別 issue）。
- **VRAM**: MoE 総 35B のウェイトサイズ次第で長コンテキストの KV キャッシュ確保が制約される。AC13 で `--max-model-len` を実機調整する。`defaults` の値は起点であり、実機で確定する。

## Verification

- `uvx pytest tests/vllm/test_role.py`
- `yamllint roles/vllm/ inventory/group_vars/all/vars.yml`
- `ansible-lint`
- 実機: `ansible-playbook playbooks/09-vllm.yml`（AC10–13）
