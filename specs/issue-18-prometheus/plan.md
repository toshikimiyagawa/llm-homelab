# Plan: issue-18-prometheus

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** k3s HelmChart addon で cert-manager / kube-prometheus-stack / DCGM Exporter を導入し、Grafana・Prometheus を HTTPS + Cloudflare DNS で公開する。

**Architecture:** `/var/lib/rancher/k3s/server/manifests/` に HelmChart YAML を配置し k3s Helm Controller に管理させる（nvidia-device-plugin と同パターン）。ClusterIssuer・PersistentVolume など Helm Controller 外のリソースは `k3s kubectl apply` で適用する。シークレットは Ansible Vault（`inventory/group_vars/all/vault.yml`）で管理する。

**Tech Stack:** Ansible, k3s HelmChart addon, cert-manager v1.16.x, kube-prometheus-stack v68.x, DCGM Exporter v3.3.x, Traefik Ingress, Let's Encrypt DNS01 / Cloudflare

---

## Impacted Files

| ファイル | 操作 | 内容 |
|---------|------|------|
| `roles/prometheus/defaults/main.yml` | 新規作成 | chart バージョン・namespace・ドメイン変数 |
| `roles/prometheus/tasks/main.yml` | 新規作成 | 全タスク（cert-manager / PV / kube-prometheus-stack / DCGM / verify） |
| `roles/prometheus/templates/cluster-issuer.yml.j2` | 新規作成 | Cloudflare Secret + ClusterIssuer |
| `roles/prometheus/templates/prometheus-pv.yml.j2` | 新規作成 | Prometheus hostPath PersistentVolume |
| `playbooks/08-prometheus.yml` | 新規作成 | prometheus role を呼ぶ playbook |
| `inventory/group_vars/all/vars.yml` | 変更 | `base_domain` 追加 |
| `inventory/group_vars/all/vault.yml` | 変更 | `cloudflare_api_token` / `grafana_admin_password` 追加 |
| `docs/software-stack.md` | 変更 | 監視基盤セクション追記 |

## Alternatives and Tradeoffs

- **HelmChart addon（採用）** vs **Ansible kubernetes.core.helm**: HelmChart addon は nvidia-device-plugin と同パターンで一貫性があり、k3s ネイティブ。helm CLI をコントロールマシンに要求しない。
- **hostPath PV（採用）** vs **local-path-provisioner（k3s 標準）**: local-path-provisioner は動的プロビジョニングだが PV のパスが自動生成され既存の `/opt/prometheus-data` を使えない。hostPath PV を静的定義して `volumeName` で直接バインドする。
- **kube-prometheus-stack（採用）** vs **個別 chart**: 一括管理できメンテコスト低。AlertManager は無効化してシンプルに保つ。

## Risks / Rollback

- **リスク**: cert-manager が Ready になる前に ClusterIssuer を apply すると CRD not found エラー。対策: CRD 確立を待つリトライタスクを挟む。
- **リスク**: kube-prometheus-stack の values に `grafana_admin_password` が含まれるため `no_log: true` 必須。
- **ロールバック**: `k3s kubectl delete -f <manifest>` でリソース削除 + `/var/lib/rancher/k3s/server/manifests/` から YAML を削除すれば k3s Helm Controller が chart をアンインストールする。
