# Spec: issue-23 — RTX Pro 6000 用 vLLM デプロイ

**Status**: implement
**Tier**: 2
**Issue**: #23

## 目的

Ansible で `llm01` の k3s 上に vLLM を導入し、RTX Pro 6000（96GB VRAM）を使った OpenAI 互換推論 API を再現可能・冪等に構築する。

## スコープ

### 含む

- `roles/vllm/` Ansible role の新規作成
- `09-vllm.yml` playbook の新規追加
- k3s Namespace `vllm` の作成
- vLLM Deployment（`vllm/vllm-openai` イメージ、`runtimeClassName: nvidia`）
- RTX Pro 6000 UUID による GPU 明示指定（`NVIDIA_VISIBLE_DEVICES`）
- `/opt/models` hostPath マウント（モデルは事前手動配置が前提）
- ClusterIP Service
- Traefik Ingress + cert-manager TLS（`letsencrypt-prod` ClusterIssuer 再利用）
- `docs/software-stack.md` への vLLM 設定方針の追記
- Cloudflare DNS への A レコード登録手順（手動、docs に記載）

### 含まない

- モデルのダウンロード・管理（手動で `/opt/models` に配置済み前提）
- Open WebUI との統合（別 issue で対応）
- vLLM の認証・API キー設定
- マルチ GPU / テンソル並列（96GB VRAM で単一 GPU 運用）
- AlertManager / 監視アラート設定

## 設計決定

| 項目 | 決定 | 理由 |
|------|------|------|
| デプロイ方式 | Kubernetes マニフェスト（template → kubectl apply） | vLLM に定番公式 Helm chart がなく、マニフェスト直接管理の方が安定 |
| GPU 指定 | `NVIDIA_VISIBLE_DEVICES=GPU-079e606a-926e-e5d4-dcd3-6322c089ef8a` | RTX Pro 6000 を UUID で明示指定し GTX 1650（Ollama 使用）との競合を確実に回避 |
| モデル管理 | 手動配置（`/opt/models` hostPath） | 数十〜数百GB のモデルを Ansible で管理すると playbook 実行時間が長大になるため |
| TLS | cert-manager `letsencrypt-prod` ClusterIssuer 再利用 | issue-18 で構築済みの ClusterIssuer をそのまま使える |
| アクセス方式 | Traefik Ingress + Cloudflare DNS → Tailscale IP | Prometheus と同じパターンで統一 |

## 変数定義

| 変数 | デフォルト値 | 説明 |
|------|-------------|------|
| `vllm_namespace` | `vllm` | k8s namespace |
| `vllm_image_tag` | `latest` | vllm/vllm-openai イメージタグ |
| `vllm_model` | `Qwen/Qwen3-30B-A3B` | サーブするモデルパス（`/opt/models` 以下の相対パス または HuggingFace ID） |
| `vllm_served_model_name` | `default` | OpenAI API での model 名 |
| `vllm_gpu_uuid` | `GPU-079e606a-926e-e5d4-dcd3-6322c089ef8a` | RTX Pro 6000 の GPU UUID |
| `vllm_models_host_path` | `/opt/models` | ホスト側モデルディレクトリ |
| `vllm_domain` | `vllm.{{ base_domain }}` | Ingress ホスト名 |
| `vllm_gpu_memory_utilization` | `0.90` | GPU メモリ使用率上限 |
| `vllm_port` | `8000` | コンテナ内 API ポート |

## 受け入れ基準

1. **AC-1**: `09-vllm.yml` を 2 回実行しても冪等である（2 回目は changed=0）
2. **AC-2**: `kubectl get pods -n vllm` で vLLM Pod が `Running` である
3. **AC-3**: Deployment に `NVIDIA_VISIBLE_DEVICES=GPU-079e606a-926e-e5d4-dcd3-6322c089ef8a` が設定されており、`nvidia.com/gpu: "1"` が割り当てられている
4. **AC-4**: Pod 内で `wget http://localhost:8000/v1/models` が HTTP 200 を返す
5. **AC-5**: `https://vllm.solvelio.com/v1/models` に HTTPS でアクセスでき応答する
6. **AC-6**: TLS 証明書が有効である（`kubectl get certificate vllm-tls -n vllm` で `Ready=True`）
7. **AC-7**: `ansible-lint` / `yamllint` が無エラーで通過する

## アーキテクチャ概要

```
Cloudflare DNS
  vllm.solvelio.com → 100.107.191.51 (Tailscale IP)
        ↓
   Traefik Ingress (k3s 標準)
        ↓
  ┌─────────────────────────────────┐
  │  k3s (vllm namespace)           │
  │  └── Deployment: vllm           │
  │        ├── image: vllm-openai   │
  │        ├── runtimeClass: nvidia │
  │        ├── GPU: RTX Pro 6000    │
  │        └── /opt/models (RO)     │
  └─────────────────────────────────┘
        ↑ GPU
  RTX Pro 6000 (96GB VRAM, UUID: GPU-079e606a-...)
```

## テスト方針

Molecule/本番ホストへの直接接続は不要。以下の確認で代替する:

- `ansible-lint roles/vllm/` — YAML / best-practices チェック
- `yamllint roles/vllm/ playbooks/09-vllm.yml` — YAML 構文チェック
- check モード (`--check`) での dry-run 実行
- `kubectl` / HTTP API による実環境での受け入れ基準確認（playbook 末尾の verify タスク）
