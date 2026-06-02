# Spec: issue-18 — Prometheus / Grafana / node-exporter 構築

**Status**: implement  
**Tier**: 2  
**Issue**: #18

## 目的

Ansible で `llm01` に監視基盤（Prometheus / Grafana / node-exporter / DCGM Exporter）を k3s 上に構築し、再現可能・冪等な運用を実現する。

## スコープ

### 含む

- `roles/prometheus/` Ansible role の新規作成
- `08-prometheus.yml` playbook の新規追加
- cert-manager（HelmChart addon）の導入と Cloudflare DNS01 ClusterIssuer の設定
- kube-prometheus-stack（HelmChart addon）の導入
  - Prometheus（メトリクス収集・保存）
  - Grafana（ダッシュボード）
  - node-exporter（ホストメトリクス）
  - AlertManager 無効化
- DCGM Exporter（HelmChart addon）の導入（GPU メトリクス）
- Traefik Ingress による `grafana.<domain>` / `prometheus.<domain>` の公開
- TLS 証明書の自動取得（Let's Encrypt + Cloudflare DNS チャレンジ）
- Prometheus 用 PersistentVolume（hostPath: `/opt/prometheus-data`）
- シークレット管理（`cloudflare_api_token`・`grafana_admin_password`）を Ansible Vault で管理
- `docs/software-stack.md` への監視基盤設定方針の追記

### 含まない

- AlertManager のアラートルール設定
- Grafana カスタムダッシュボードの作成（kube-prometheus-stack 同梱のデフォルトダッシュボードを使用）
- Cloudflare DNS レコードの自動作成（ユーザーが管理画面で手動設定）
- Grafana / Prometheus のインターネット公開（Tailscale 経由のみ）
- vLLM / Ollama のメトリクス収集（別 issue で対応）

## 設計決定

| 項目 | 決定 | 理由 |
|------|------|------|
| デプロイ方式 | k3s HelmChart addon | nvidia-device-plugin と同パターンで一貫性がある |
| 監視スタック | kube-prometheus-stack | Prometheus + Grafana + node-exporter を一括管理できる |
| GPU メトリクス | DCGM Exporter | RTX Pro 6000 のVRAM・温度・利用率を取得するため |
| TLS | cert-manager + Let's Encrypt DNS01 | Cloudflare DNS チャレンジで Tailscale IP（非公開）でも証明書取得可能 |
| アクセス方式 | Traefik Ingress + Cloudflare DNS → Tailscale IP | Tailscale 経由のみでセキュア、Ingress で URL アクセス可能 |
| ストレージ | hostPath PV（`/opt/prometheus-data`） | vars.yml に定義済みのディレクトリを活用 |
| データ保持期間 | 30 日 | 24 時間稼働のホームサーバーとして十分 |
| シークレット管理 | Ansible Vault | 1Password 依存なし、`~/.vault_pass` で CI 対応 |

## 受け入れ基準

1. **AC-1**: `08-prometheus.yml` を 2 回実行しても冪等である（2 回目は changed=0 または HelmChart 管理タスクのみ）
2. **AC-2**: `kubectl get pods -n monitoring` で Prometheus / Grafana / node-exporter / DCGM Exporter の Pod が `Running` である
3. **AC-3**: `https://grafana.<domain>` に HTTPS でアクセスでき、Grafana ログイン画面が表示される
4. **AC-4**: Prometheus API で `up{job="node-exporter"}==1` が返る
5. **AC-5**: Prometheus API で `up{job="dcgm-exporter"}==1` が返る
6. **AC-6**: TLS 証明書が有効である（`kubectl get certificate -n monitoring` で `Ready=True`）
7. **AC-7**: `cloudflare_api_token` / `grafana_admin_password` がログに平文で出力されない（`no_log: true`）
8. **AC-8**: `ansible-lint` / `yamllint` が無エラーで通過する

## シークレット管理

以下を `inventory/group_vars/all/vault.yml`（Ansible Vault 暗号化）に格納する:

```yaml
cloudflare_api_token: "<Cloudflare API Token（DNS 編集権限）>"
grafana_admin_password: "<Grafana 管理者パスワード>"
```

cert-manager は上記トークンを k8s Secret として参照する。

## アーキテクチャ概要

```
Cloudflare DNS
  grafana.<domain>     → 100.107.191.51 (Tailscale IP)
  prometheus.<domain>  → 100.107.191.51 (Tailscale IP)
        ↓
   Traefik Ingress (k3s 標準)
        ↓
  ┌─────────────────────────────┐
  │  k3s (monitoring namespace) │
  │  ├── Prometheus             │
  │  ├── Grafana                │
  │  ├── node-exporter          │
  │  └── DCGM Exporter          │
  └─────────────────────────────┘
        ↑ scrape
  ┌─────────────────────┐
  │  llm01 ホスト       │
  │  ├── CPU/RAM/Disk   │  ← node-exporter
  │  └── RTX Pro 6000   │  ← DCGM Exporter
  └─────────────────────┘
```

## テスト方針

Molecule/本番ホストへの直接接続は不要。以下の確認で代替する:

- `ansible-lint roles/prometheus/` — YAML / best-practices チェック
- `yamllint roles/prometheus/ playbooks/08-prometheus.yml` — YAML 構文チェック
- check モード (`--check`) での dry-run 実行
- `kubectl` / Prometheus API による実環境での受け入れ基準確認（playbook 末尾の verify タスク）
