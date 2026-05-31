# Plan: issue-17 — Tailscale 導入

## アプローチ

既存 role（ollama 等）と同じ構造で `roles/tailscale/` を作る。  
シークレット取得は `docs/security-and-secrets.md` の 1Password lookup パターンを踏襲する。

## 影響ファイル

| ファイル | 変更内容 |
|----------|----------|
| `roles/tailscale/defaults/main.yml` | 新規: デフォルト変数 |
| `roles/tailscale/tasks/main.yml` | 新規: インストール・設定タスク |
| `roles/tailscale/handlers/main.yml` | 新規: tailscaled restart ハンドラ |
| `playbooks/07-tailscale.yml` | 新規: Tailscale playbook |
| `docs/software-stack.md` | 追記: Tailscale セクション |
| `.sdd/state.json` | 更新: feature=issue-17-tailscale, phase |

## タスク順序

1. `roles/tailscale/defaults/main.yml` — 変数定義
2. `roles/tailscale/handlers/main.yml` — ハンドラ定義
3. `roles/tailscale/tasks/main.yml` — メインタスク群
4. `playbooks/07-tailscale.yml` — playbook
5. `docs/software-stack.md` 更新
6. lint 実行・確認
7. `.sdd/state.json` 更新

## トレードオフ・代替案

### APT リポジトリ vs snap

- APT を選択: 既存のパッケージ管理と統一、snap は別デーモンが必要で運用が複雑
- デメリット: リポジトリ追加タスクが必要

### auth key の冪等性

- `tailscale status --json | jq '.BackendState'` が `"Running"` なら `tailscale up` をスキップ
- Reusable key なら再実行しても問題ないが、不要な API コールを避けるためスキップする

### `site.yml` への組み込み

- 今回は組み込まない: Tailscale は他ロールに依存せず、単独で実行できる
- 将来的に `site.yml` に追加するかはユーザー判断
