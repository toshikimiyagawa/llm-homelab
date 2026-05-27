# llm-homelab

自宅実家に設置するLLM推論サーバーを、Ansibleで再現可能に構築・運用するためのリポジトリです。

## 目的

- 大型LLM推論をローカルで動かす。
- 軽量モデル、Web UI、検索エージェント、監視基盤を同じホストで運用する。
- 24時間稼働・リモート運用を前提に、構成をInfrastructure as Codeで管理する。

## 想定ワークロード

| 種別 | 内容 |
|------|------|
| メイン推論 | vLLM + RTX Pro 6000 Blackwell |
| 軽量推論 | Ollama + GTX 1650 |
| UI | Open WebUI |
| 検索 | SearXNG |
| 監視 | Prometheus, Grafana, node-exporter |
| リモートアクセス | Tailscale |

## 現在の状態

- ホスト名: `llm01`
- OS: Ubuntu 26.04 LTS
- GPU: GTX 1650のみ装着済み
- RTX Pro 6000 Blackwell Workstation Edition 600W版は2026-05-29または2026-05-30装着予定
- ストレージ初期構成済み:
  - `/`
  - `/var/lib/rancher`
  - `/opt`
- 初期構築用に一時的なpasswordless sudoを設定中。構築完了後に削除または限定化する。

## 構築フェーズ

### Phase 0: 手動セットアップ

Ubuntuをインストールし、SSHで接続できる状態にする。BIOSではSecure Bootを無効化し、Above 4G Decoding、Re-Size BAR、IOMMUを有効化する。

現在、Ubuntuインストール、SSHログイン、ホスト名設定、ストレージ初期構成までは完了済み。

### Phase 1: GTX 1650のみで構築

RTX Pro 6000装着前に、以下をAnsibleで構築する。

```bash
ansible-playbook playbooks/site.yml --skip-tags vllm
```

対象:

- OS基本設定
- NVIDIAドライバ
- containerd / k3s
- NVIDIA Device Plugin
- Tailscale
- 監視基盤
- Ollama
- Open WebUI
- SearXNG
- Antec Flux Pro温度ディスプレイ

### Phase 2: RTX Pro 6000追加

物理装着後、GPU認識とUUIDを確認してからvLLMをデプロイする。

```bash
ansible-playbook playbooks/site.yml --tags vllm
```

### Phase 3: 運用

- Open WebUI: `http://100.x.x.x:3000`
- Grafana: `http://100.x.x.x:3001`
- vLLM API: `http://100.x.x.x:8000/v1`
- Ollama API: `http://100.x.x.x:11434`

## ドキュメント

- [docs/hardware.md](docs/hardware.md)
- [docs/storage.md](docs/storage.md)
- [docs/software-stack.md](docs/software-stack.md)
- [docs/operations.md](docs/operations.md)
- [docs/security-and-secrets.md](docs/security-and-secrets.md)
- [docs/repository-guidelines.md](docs/repository-guidelines.md)
- [AGENTS.md](AGENTS.md)

## ライセンス

MIT等を予定。現時点では未確定。
