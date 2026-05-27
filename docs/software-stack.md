# Software Stack

## OS

- Ubuntu 26.04 LTS
- Linux 7.0系
- Secure Bootは無効化

## コンテナ・オーケストレーション

- k3s（シングルノード）
- containerd（k3s標準ランタイム）
- NVIDIA Container Toolkit
- NVIDIA Device Plugin for Kubernetes

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

## 外部AI連携

ローカルLLMをメインにし、必要時のみクラウドAPIを呼ぶ。

```text
ローカルLLM (Qwen3.6 on RTX Pro 6000)
├── ローカルで完結する処理
├── Web検索 -> Gemini API
└── 複雑な推論 -> Anthropic API
```

Anthropic連携はAPIキー利用を基本にする。サブスクの自動化利用は避ける。
