# Software Stack

## OS

- Ubuntu 26.04 LTS
- Linux 7.0系
- Secure Bootは無効化

## コンテナ・オーケストレーション

- k3s v1.35.5+k3s1（シングルノード）
- containerd 2.2.3-k3s1（k3s標準ランタイム）
- NVIDIA Container Toolkit 1.19.1
- NVIDIA Device Plugin for Kubernetes 0.17.1

k3sは公式install scriptでsystemd serviceとして導入する。設定は`/etc/rancher/k3s/config.yaml`に置き、install scriptの一時引数に依存しない。K3sは起動時に`nvidia-container-runtime`を自動検出する。

NVIDIA Device Pluginはk3s Helm ControllerのHelmChart addonとして導入する。chartは`https://nvidia.github.io/k8s-device-plugin`を使い、`runtimeClassName: nvidia`、`nfd.enabled: false`を指定する。ノードにはchartの既定affinityに合わせて`nvidia.com/gpu.present=true`を付与する。

## NVIDIA

- 要求ドライバ: 575系open kernel module
- 実機導入結果: Ubuntu 26.04の`nvidia-driver-575-open`は`nvidia-driver-580-open`へ依存するため、実ドライバは580.159.03
- CUDA: 13.0（`nvidia-smi`表示）
- Blackwell世代のため、オープンソースカーネルモジュールを前提にする。

RTX Pro 6000装着後は、GPU UUIDをinventoryに記録する。

## 推論エンジン

| エンジン | GPU | 用途 |
|----------|-----|------|
| vLLM | RTX Pro 6000 | メイン推論、並列処理、OpenAI互換API |
| Ollama | GTX 1650 | 軽量モデル、ホットスワップ、4GB VRAM向け |

## 周辺サービス

- Open WebUI
- SearXNG
- Prometheus
- Grafana
- node-exporter
- Tailscale
- Antec Flux Pro温度ディスプレイ

### vLLM

k3s Deployment として `vllm` namespace に導入する。

| 項目 | 設定値 |
|------|--------|
| image | `vllm/vllm-openai:latest` |
| GPU | RTX Pro 6000（UUID: `GPU-079e606a-926e-e5d4-dcd3-6322c089ef8a`） |
| モデル | `/opt/models` に手動配置（例: `Qwen/Qwen3-30B-A3B`） |
| API | OpenAI 互換（`/v1/chat/completions`, `/v1/models`） |

アクセス URL（要 Tailscale 接続）:

- API: `https://vllm.solvelio.com/v1`

事前に Cloudflare で以下の DNS A レコードを手動登録する（Tailscale IP）:

- `vllm.solvelio.com` → `100.107.191.51`

Ansible での適用:

```bash
ansible-playbook playbooks/09-vllm.yml --vault-password-file ~/.vault_pass
```

### Open WebUI

Open WebUI は k3s Deployment として `open-webui` namespace に導入し、vLLM と Ollama のブラウザ UI として利用する。

| 項目 | 設定値 |
|------|--------|
| image | `ghcr.io/open-webui/open-webui:main` |
| URL | `https://open-webui.solvelio.com` |
| 永続化 | `/opt/open-webui-data` を `/app/backend/data` に hostPath mount |
| vLLM 接続 | `https://vllm.solvelio.com/v1` (`OPENAI_API_BASE_URLS`) |
| Ollama 接続 | `http://llm01:11434` (`OLLAMA_BASE_URLS`) |

Open WebUI のユーザー、設定、SQLite データベースは `/opt/open-webui-data` に保持する。replica は hostPath とローカル state 前提のため 1 に固定する。

Ollama は認証なし API を外部公開しないため `127.0.0.1:11434` のみに bind する。Open WebUI pod は `hostNetwork: true` と `llm01 to 127.0.0.1` の hostAlias により、Ollama の bind 設定を変更せずに接続する。

Open WebUI の全体デフォルト推論パラメータは `DEFAULT_MODEL_PARAMS` で与え、`max_tokens` は `8192` に固定する。これは `vLLM` の `max_model_len=40960` を長い会話履歴で超えにくくするための初期値で、必要な場合は Open WebUI のモデルごとの設定で上書きする。

アクセス URL（要 Tailscale 接続）:

- UI: `https://open-webui.solvelio.com`

事前に Cloudflare で以下の DNS A レコードを手動登録する（Tailscale IP）:

- `open-webui.solvelio.com` to `100.107.191.51`

Ansible での適用:

```bash
ansible-playbook playbooks/21-open-webui.yml --vault-password-file ~/.vault_pass
```

### Tailscale

公式 APT リポジトリ（`https://pkgs.tailscale.com/stable/ubuntu`）からインストールする。
`tailscaled.service` を systemd で管理し、再起動後も自動復帰する。

| 項目 | 設定値 |
|------|--------|
| auth key 種別 | Reusable（1Password "LLM Server Infrastructure" > "Tailscale Auth Key"）|
| Tailscale SSH | 無効（通常 sshd を使用）|
| サブネットルーティング | 未設定（必要時に `tailscale_up_flags` で追加）|
| ACL ポリシー | Tailscale admin console で管理（Ansible 外）|

接続確認:

```bash
tailscale status
```

Ansible での適用:

```bash
ansible-playbook playbooks/07-tailscale.yml
```

### Prometheus / Grafana / node-exporter / DCGM Exporter

k3s HelmChart addon として `monitoring` namespace に導入する。

| コンポーネント | chart | namespace |
|--------------|-------|-----------|
| cert-manager | jetstack/cert-manager v1.16.x | cert-manager |
| kube-prometheus-stack | prometheus-community/kube-prometheus-stack v68.x | monitoring |
| DCGM Exporter | nvidia/dcgm-exporter v3.3.x | monitoring |

アクセス URL（要 Tailscale 接続）:

- Grafana: `https://grafana.solvelio.com`
- Prometheus: `https://prometheus.solvelio.com`

TLS 証明書は cert-manager が Let's Encrypt DNS01 チャレンジ（Cloudflare）で自動取得する。

Ansible での適用:

```bash
ansible-playbook playbooks/08-prometheus.yml --vault-password-file ~/.vault_pass
```

事前に Cloudflare で以下の DNS A レコードを手動登録する（Tailscale IP）:

- `grafana.solvelio.com` → `100.107.191.51`
- `prometheus.solvelio.com` → `100.107.191.51`

Antec Flux Pro の温度表示は Linux ネイティブ実装として
`nishtahir/antec-flux-pro-display` を採用する。
`af-pro-display` systemd service により、CPU+GPU 温度を起動時から継続表示する。

## 外部AI連携

ローカルLLMをメインにし、必要時のみクラウドAPIを呼ぶ。

```text
ローカルLLM (Qwen3.6 on RTX Pro 6000)
├── ローカルで完結する処理
├── Web検索 -> Gemini API
└── 複雑な推論 -> Anthropic API
```

Anthropic連携はAPIキー利用を基本にする。サブスクの自動化利用は避ける。
