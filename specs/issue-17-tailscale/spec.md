# Spec: issue-17 — Tailscale 導入

**Status**: draft  
**Tier**: 2  
**Issue**: #17

## 目的

Ansible で `llm01` に Tailscale クライアントを導入し、再現可能・冪等なリモートアクセス経路を整える。

## スコープ

### 含む

- `roles/tailscale/` Ansible role の新規作成
- `07-tailscale.yml` playbook の新規追加
- Tailscale APT リポジトリの追加とパッケージインストール
- `tailscaled.service` の enable/start
- 1Password 連携による auth key 取得と `tailscale up` 実行（接続済みなら skip）
- `docs/software-stack.md` への Tailscale 設定方針の追記

### 含まない

- ACL ポリシー設定（Tailscale admin console で管理）
- サブネットルーティング・exit node 設定
- Tailscale SSH（`--ssh` フラグ）
- `site.yml` への自動組み込み（手動でplaybook実行）

## 設計決定

| 項目 | 決定 | 理由 |
|------|------|------|
| インストール方法 | 公式 APT リポジトリ | 公式推奨、バージョン管理が容易 |
| auth key 種別 | Reusable | 冪等な Ansible 実行に対応、1Password に一度登録すれば再利用可 |
| Tailscale SSH | 無効 | シンプルさ優先、通常の sshd を使い続ける |
| シークレット取得 | 1Password lookup (`community.general.onepassword`) | `docs/security-and-secrets.md` の既定方針 |
| 冪等性確保 | `tailscale status --json` で接続確認 → 未接続時のみ `tailscale up` | 再実行安全性 |

## 受け入れ基準

1. **AC-1**: `07-tailscale.yml` を 2 回実行しても冪等である（2 回目は changed=0）
2. **AC-2**: `tailscaled.service` が enabled かつ running である
3. **AC-3**: `tailscale status` が `llm01` の接続状態を返す
4. **AC-4**: `llm01` の再起動後も Tailscale が自動復帰する（systemd enable で保証）
5. **AC-5**: auth key がログに平文で出力されない（`no_log: true`）
6. **AC-6**: `ansible-lint` / `yamllint` が無エラーで通過する

## シークレット管理

```yaml
- name: Fetch Tailscale auth key from 1Password
  ansible.builtin.set_fact:
    tailscale_auth_key: "{{ lookup('community.general.onepassword',
                                   'Tailscale Auth Key',
                                   vault='LLM Server Infrastructure') }}"
  no_log: true
  delegate_to: localhost
  run_once: true
```

auth key は 1Password Vault "LLM Server Infrastructure" > "Tailscale Auth Key" に格納する。

## テスト方針

Molecule/本番ホストへの直接接続は不要。以下の確認で代替する:

- `ansible-lint roles/tailscale/` — YAML / best-practices チェック
- `yamllint roles/tailscale/ playbooks/07-tailscale.yml` — YAML 構文チェック
- check モード (`--check`) での dry-run 実行
