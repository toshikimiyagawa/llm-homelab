# Spec: issue-90 — cloudflared プレースホルダ CA 適用ガード

**Status**: frozen
**Tier**: 1
**Issue**: #90
**関連**: #88 / PR #89

## 目的

`roles/cloudflared/files/cloudflare_ca.pub` は PR #89 でプレースホルダとして commit されており、実値は Cloudflare Access ダッシュボードから手動取得して差し替える運用になっている。プレースホルダのまま `playbooks/22-cloudflare-tunnel.yml` を適用すると、sshd が**ダミーの SSH CA** を `TrustedUserCAKeys` で信頼し、同時に `PasswordAuthentication no` が適用される footgun になる。コード側に fail-fast ガードを追加し、差し替え忘れを適用前に明示エラーで止める。

## スコープ

### 含む

- `roles/cloudflared` に、CA 公開鍵がプレースホルダのままなら `ansible.builtin.assert` で **fail-fast** するガードタスクを追加する。
- ガードは CA 公開鍵配置（`Deploy Cloudflare Access SSH CA public key`）および sshd 再設定タスクより**前**に実行する。
- プレースホルダ判定マーカーを `roles/cloudflared/defaults/main.yml` に role-prefix 付き変数で定義する。
- `tests/cloudflared/test_role.py` にガードの静的契約テストを追加する。

### 含まない

- issue-88 凍結済み spec (`specs/issue-88-cloudflare-tunnel/`) の変更。
- 実 CA 公開鍵の投入自体（手動運用のまま、docs/operations.md 記載）。
- Vault 化など CA 公開鍵の管理方式変更（公開鍵のため非機密）。

## 設計決定

| 項目 | 決定 | 理由 |
|------|------|------|
| 検出方式 | `lookup('ansible.builtin.file', 'cloudflare_ca.pub')` の内容にプレースホルダマーカーが含まれるかを `assert` で検査 | role の files/ を読むだけで冪等・副作用なし |
| 失敗のさせ方 | skip ではなく fail-fast（明示エラー） | 「Browser SSH が無言で機能しない + PasswordAuthentication no だけ効く」中途半端な状態を作らない |
| 実行位置 | CA 配置・sshd 設定タスクより前 | 危険な変更を一切適用する前に止める |

## 受け入れ基準（自動検証）

1. **AC-1**: `roles/cloudflared/tasks/main.yml` に `ansible.builtin.assert` を使ったガードタスクが存在し、プレースホルダマーカーを含む場合に fail する。
2. **AC-2**: ガードタスクは `Deploy Cloudflare Access SSH CA public key` および sshd 設定タスクより前に位置する。
3. **AC-3**: プレースホルダ判定マーカーは `roles/cloudflared/defaults/main.yml` に role-prefix 付き変数（`cloudflared_ssh_ca_placeholder_marker`）として定義される。
4. **AC-4**: `tests/cloudflared/test_role.py` が AC-1〜AC-3 を静的にアサートする。
5. **AC-5**: `ansible-lint` / `yamllint` が `roles/cloudflared` で無エラー。

## テスト方針

- **静的**: `uvx pytest tests/cloudflared/test_role.py`（issue #75 に従い `uvx pytest` を正準とする）。
- **lint**: `yamllint roles/cloudflared/` / `ansible-lint roles/cloudflared`。
- **運用確認（手動）**: プレースホルダのまま `playbooks/22-cloudflare-tunnel.yml --check` を実行すると assert で停止することを目視確認（docs/operations.md の既存手順に追従）。
