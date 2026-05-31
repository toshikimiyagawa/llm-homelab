# Plan: issue-19-ollama

## アプローチ

Ansible role `ollama` を新規作成し、`playbooks/20-ollama.yml` から呼び出す。
インストールは Ollama 公式 GitHub Releases からバイナリを version 固定で取得することで冪等性を確保する。
systemd override ファイルで環境変数（`OLLAMA_HOST`、`OLLAMA_MODELS`、`CUDA_VISIBLE_DEVICES`）を設定する。

## 影響範囲 / 主要ファイル

```
roles/ollama/
├── defaults/main.yml          # version・パス・port 変数
├── tasks/main.yml             # install + dir + systemd override + enable/start
├── handlers/main.yml          # systemd daemon-reload + restart ollama
└── templates/
    └── override.conf.j2       # systemd override（ENV 3変数）

playbooks/20-ollama.yml        # 新規
playbooks/site.yml             # import 追加
docs/operations.md             # Ollama 動作確認セクション追加
```

## インストール方式の詳細

1. `defaults/main.yml` で `ollama_version` を固定（`0.24.0`、2026-05時点の最新安定版）
2. tasks で `/usr/local/bin/ollama` の現バージョンを確認
3. バージョン不一致またはバイナリ未存在の場合のみ GitHub Releases から `ollama-linux-amd64` をダウンロードして配置
4. `systemd` の user service として公式が提供する unit ファイルを使う（install 時に `/etc/systemd/system/ollama.service` に生成される）
5. `/etc/systemd/system/ollama.service.d/override.conf` で ENV を上書き

## 検討した代替案とトレードオフ

| 案 | 利点 | 欠点 | 判定 |
|----|------|------|------|
| 公式 install.sh | 簡単 | curl-pipe-sh、冪等性なし | 不採用 |
| バイナリ直接配置（本案） | 冪等、version 固定 | 自前で unit 管理が必要 | **採用** |
| Docker コンテナ | 環境分離 | GPU passthrough 設定が複雑、GTX 1650 の 4GB では余裕なし | 不採用 |

## CUDA device index の扱い

GTX 1650 のデバイス番号は実機依存。`defaults/main.yml` の `ollama_cuda_visible_devices` を変数化し、
inventory で上書き可能にする。デフォルト値は `"0"` とし、実機確認後に調整する。

## リスク / ロールバック

- **バイナリ DL 失敗**: GitHub Releases URL が変わった場合、`ollama_version` を更新するだけ
- **CUDA device index 誤り**: `CUDA_VISIBLE_DEVICES` を変更して `systemctl restart ollama` で即時反映
- **ロールバック**: `systemctl stop ollama && systemctl disable ollama` + バイナリ削除で完全除去可能
