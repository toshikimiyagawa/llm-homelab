# Spec: issue-19-ollama

- Tier: 2
- Status: frozen
- Feature slug: issue-19-ollama

## 背景 / 意図

GTX 1650（4GB VRAM）側で軽量モデルを提供する推論基盤を Ansible で再現可能に構築する。
RTX Pro 6000 が vLLM（メイン推論）を担い、GTX 1650 は Ollama による軽量・ホットスワップ用途に充てる設計。

セキュリティ調査（2025–2026）で Ollama はデフォルトで認証なしのため、
`OLLAMA_HOST=127.0.0.1` に制限することを必須とする。

## 受入条件

- [ ] AC1: `ansible-playbook playbooks/20-ollama.yml` を実行すると `ollama.service` が `active (running)` になる
- [ ] AC2: モデルデータ保存先として `/opt/ollama/models` が作成・設定される（大容量 NVMe `/opt` を利用）
- [ ] AC3: Ollama が `127.0.0.1:11434` のみにバインドされ、ネットワーク外部に露出しない
- [ ] AC4: GTX 1650 のみを使う CUDA デバイス設定が systemd unit に入っている
- [ ] AC5: `llm01` 再起動後も `ollama.service` が自動起動する（`enabled: true`）
- [ ] AC6: `docs/operations.md` に Ollama の動作確認コマンドが記載されている

## スコープ外

- モデルの自動ダウンロード（`ollama pull`）の Ansible 化
- Open WebUI との統合設定
- vLLM / RTX Pro 6000 側の設定変更
- Prometheus / Grafana によるメトリクス収集

## 制約 / 前提

- 対象ホスト: `llm01`（Ubuntu 26.04 LTS）
- NVIDIA ドライバ（580系）・CUDA 13.0 導入済みを前提とする
- GTX 1650 の CUDA device index は実機で `nvidia-smi` により確認する（0 または 1）
- `/opt` は約 916GB ext4（`/dev/nvme1n1p1`）でモデル保存に十分な容量がある
- Ollama インストールは公式バイナリ（GitHub Releases）を version 固定で取得し冪等性を担保する
- シークレット不要。`no_log` 対象タスクなし
- Tailscale + ローカルネットワーク前提のため、Tailscale 側のアクセス制御は別途管理
