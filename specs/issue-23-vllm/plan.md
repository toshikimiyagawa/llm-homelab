# vLLM デプロイ Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** RTX Pro 6000（96GB VRAM）を使った vLLM を k3s 上に構築し、`https://vllm.solvelio.com` で OpenAI 互換 API を公開する。

**Architecture:** Ansible テンプレート（Jinja2）で Namespace / Deployment / Service / Ingress を生成し `k3s kubectl apply` で適用する（issue-18 の ClusterIssuer/PV 適用パターンと同じ）。GPU は RTX Pro 6000 の UUID を `NVIDIA_VISIBLE_DEVICES` で明示指定。TLS は既存の `letsencrypt-prod` ClusterIssuer を再利用。

**Tech Stack:** Ansible, k3s kubectl, vllm/vllm-openai Docker image, Traefik Ingress, cert-manager

---

## Impacted Files

| ファイル | 操作 | 内容 |
|---------|------|------|
| `roles/vllm/defaults/main.yml` | 新規作成 | 全変数のデフォルト値 |
| `roles/vllm/tasks/main.yml` | 新規作成 | Namespace 作成・manifest apply・wait・verify |
| `roles/vllm/templates/vllm-deployment.yml.j2` | 新規作成 | vLLM Deployment（GPU指定・モデルマウント・readinessProbe） |
| `roles/vllm/templates/vllm-service.yml.j2` | 新規作成 | ClusterIP Service |
| `roles/vllm/templates/vllm-ingress.yml.j2` | 新規作成 | Traefik Ingress + TLS |
| `playbooks/09-vllm.yml` | 新規作成 | vllm role を呼ぶ playbook |
| `docs/software-stack.md` | 変更 | vLLM の設定方針・URL・適用コマンドを更新 |

## Alternatives and Tradeoffs

- **マニフェスト直接管理（採用）** vs **HelmChart addon**: vLLM に公式 Helm chart がないため、カスタムマニフェストが最も安定。prometheus role の ClusterIssuer/PV 適用と同一パターン。
- **UUID 直接指定（採用）** vs **nvidia.com/gpu リソース任せ**: Ollama は systemd で GTX 1650 を使用しており k8s resource management 外。UUID 指定で確実に RTX Pro 6000 を使う。
- **手動モデル配置（採用）** vs **init container でダウンロード**: 96GB モデルの playbook 内ダウンロードは非現実的。`/opt/models` に事前配置が前提。

## Risks / Rollback

- **リスク**: vLLM は大規模モデルのロードに 5〜15 分かかる。`rollout status` は長いタイムアウトと retries が必要。
- **リスク**: `NVIDIA_VISIBLE_DEVICES` を UUID で指定した場合でも `nvidia.com/gpu: "1"` リソースリクエストが必要（device plugin が GPU を割り当てる仕組みのため）。
- **ロールバック**: `k3s kubectl delete namespace vllm` で全リソースを削除。`/tmp` のテンプレートファイルは always で削除するため残留なし。
