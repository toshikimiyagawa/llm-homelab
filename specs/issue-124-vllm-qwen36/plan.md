# Plan: issue-124-vllm-qwen36

## アプローチ

既存 vLLM role の構造（image=latest、hostPath で `/opt/models` をマウント、OpenAI 互換 API、Recreate strategy）を維持したまま、提供モデルの設定値を Qwen3-32B → Qwen3.6-35B-A3B に差し替える。

最大の構造変更は **YaRN RoPE スケーリングの廃止**。現行は `roles/vllm/tasks/main.yml` で対象モデルの `config.json` を `slurp` し、`max_position_embeddings` と `rope_scaling` を書き換えていた（Qwen3-32B の native 40960 を超えて使うため）。Qwen3.6-35B-A3B は native 262K のため拡張不要で、`config.json` 改変タスク自体を削除する。`--max-model-len` は引き続き deployment で指定し、VRAM に収まる範囲に制限する。

## 影響ファイル

| ファイル | 変更内容 |
|----------|----------|
| `inventory/group_vars/all/vars.yml` | `vllm_model` / `vllm_served_model_name` を Qwen3.6-35B-A3B に更新 |
| `roles/vllm/defaults/main.yml` | `vllm_model` / `vllm_served_model_name` / `vllm_model_dir` 更新、`vllm_max_model_len` 更新、`vllm_rope_scaling_dict` 削除 |
| `roles/vllm/tasks/main.yml` | `config.json` の YaRN 改変タスク（slurp + copy）2 件を削除 |
| `roles/vllm/templates/vllm-deployment.yml.j2` | 変更なし（`--max-model-len` 等は維持）。テキスト専用のためマルチモーダルフラグは追加しない |
| `tests/vllm/test_role.py` | YaRN 関連テストを「YaRN 不在」検証に置換、max_model_len / model_dir テストを更新 |
| `docs/software-stack.md` | vLLM セクションのモデル記載を更新 |
| `docs/operations.md` | `curl` 動作確認例の model 名を更新 |
| `.devcontainer/project-tools.yml` | opencode プロバイダの model 名 / models キー / context を更新（spec 拡張 AC14–15） |
| `tests/opencode/test_devcontainer_config.py` | 旧 `qwen3-32b` / `92736` 検証を Qwen3.6 値に更新 |

## トレードオフ / 代替案

- **YaRN タスク削除 vs 条件分岐で残す**: 将来別モデルで再び YaRN が要るかもしれないが、YAGNI に従い削除する。必要時は git 履歴から復元できる。
- **`vllm_max_model_len` の値**: 実機 VRAM 依存のため `defaults` 値は起点（spec AC4 を満たす native 由来の値）とし、最終確定は AC13 の実機検証で行う。spec の受け入れ基準は「YaRN なし・現行 92736 より大」に留め、特定数値を固定しない。
- **image tag**: `latest` のまま。Qwen3.6 非対応リスクは rollout 検証（AC10）で検出し、非対応なら別 issue で tag 固定。

## 検証戦略

- 静的 AC（1–9）→ `tests/vllm/test_role.py` + lint。
- ランタイム AC（10–13）→ 実機 `ansible-playbook playbooks/09-vllm.yml`（手動）。CI ではモデルウェイト不在のため実行しない。
