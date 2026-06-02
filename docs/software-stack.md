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
