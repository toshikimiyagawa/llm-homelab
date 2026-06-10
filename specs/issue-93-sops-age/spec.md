# Spec: issue-93 — SOPS+age によるシークレット管理整理

**Status**: frozen
**Tier**: 2
**Issue**: #93

## 目的

1Password Service Account と Ansible Vault に分散しているシークレット管理を、SOPS+age を中心にした方式へ整理する。Git 上には暗号化済み secret だけを置き、復号鍵は Git に置かない。Ansible は `community.sops` collection を使って SOPS ファイルを直接復号し、復号済み一時 vars ファイルを作らない。

これにより、1Password への製品依存を「age 秘密鍵のバックアップ」に限定し、日常の Ansible 実行はローカルの age 秘密鍵とリポジトリ内の暗号化 secret だけで再現できるようにする。

## スコープ

### 含む

- SOPS+age の導入方針を `docs/security-and-secrets.md` に明記する。
- `.sops.yaml` を追加し、`secrets/*.sops.yml` を age 公開鍵で暗号化するルールを定義する。
- `secrets/README.md` を追加し、age 秘密鍵、1Password バックアップ、復号方法、一時 Cloudflare token の扱いを記載する。
- `secrets/infra.sops.yml` を追加し、初期 secret キーを SOPS 管理下に置く。
- `requirements.yml` に `community.sops` collection を追加する。
- cert-manager DNS01 用 Cloudflare token の変数名を `cloudflare_dns01_api_token` に寄せる。
- Prometheus / cert-manager DNS01 が SOPS 由来の `cloudflare_dns01_api_token` を参照するようにする。
- Cloudflare Tunnel credentials JSON を SOPS 管理の `cloudflared_tunnel_credentials` へ寄せ、既存 role が使う値へ安全に渡す。
- 平文 secret、age 秘密鍵、復号済み一時ファイルを commit しないための静的テストを追加する。

### 含まない

- issue #91 の Cloudflare Tunnel 実機適用そのもの。
- Cloudflare Access Service Token の Client Secret をリポジトリへ保存する変更。
- 1Password Service Account の完全廃止。
- age 秘密鍵 `keys.txt` をリポジトリへ保存すること。
- 既存の全 secret（Tailscale Auth Key、k3s token、API keys を含む）を一度に SOPS へ移行すること。

## 設計決定

| 項目 | 決定 | 理由 |
|------|------|------|
| secret 管理の中心 | SOPS+age | vendor lock-in を下げつつ、Git 管理と暗号化を両立できる |
| Ansible 連携 | `community.sops` で直接復号 | 復号済み一時 vars ファイルを作らず、Ansible の中で完結できる |
| age 秘密鍵 | ローカル `~/.config/sops/age/keys.txt` | Ansible 実行時の復号鍵。Git には置かない |
| age 秘密鍵バックアップ | 1Password `LLM Server Infrastructure` | 1Password は secret 本体の正本ではなく、復旧用保管庫として使う |
| Cloudflare DNS01 token | `cloudflare_dns01_api_token` | 用途を明確化し、Tunnel / Access 管理用 token との誤用を避ける |
| Cloudflare Tunnel credentials | `cloudflared_tunnel_credentials` in SOPS | 対象ホストへ配布する構成 secret だが、今後の統一方針として SOPS に寄せる |
| 広権限 Cloudflare token | 保存しない | 初期構築用の一時 token は環境変数で使い、作業後 revoke する |

## シークレット分類

### SOPS 管理

- `cloudflare_dns01_api_token`: cert-manager DNS01 用 Cloudflare token。
- `cloudflared_tunnel_credentials`: locally-managed Cloudflare Tunnel credentials JSON。

### 通常 Git 管理

- `cloudflared_tunnel_id`: 非機密の tunnel ID。
- `roles/cloudflared/files/cloudflare_ca.pub`: Cloudflare Access SSH CA 公開鍵。

### 1Password バックアップ

- `llm-homelab age private key`: `~/.config/sops/age/keys.txt` のバックアップ。通常の Ansible 実行時には 1Password lookup を使わない。

### 保存しない

- Cloudflare Tunnel / Access 初期構築用の広権限 API token。
- Cloudflare Access Service Token の Client Secret。ただし将来、特定クライアントへ配布する必要が出た場合は別 issue で扱う。

## 想定ファイル構成

```text
.sops.yaml
secrets/
  README.md
  infra.sops.yml
requirements.yml
docs/security-and-secrets.md
roles/prometheus/templates/cluster-issuer.yml.j2
playbooks/08-prometheus.yml
playbooks/22-cloudflare-tunnel.yml
tests/secrets/test_sops_policy.py
```

`secrets/infra.sops.yml` は暗号化済みファイルとして commit する。平文例は docs に最小限のキー名だけ記載し、実値は書かない。

## Ansible データフロー

1. 実行者はローカルに age 秘密鍵 `~/.config/sops/age/keys.txt` を持つ。
2. Ansible 実行時に `community.sops` が `secrets/infra.sops.yml` を復号する。
3. playbook は復号した値を `no_log: true` の `set_fact` でキャッシュする。
4. `roles/prometheus` は `cloudflare_dns01_api_token` を Kubernetes Secret manifest に埋め込む。
5. `roles/cloudflared` は `cloudflared_tunnel_credentials` を既存の credentials 配置タスクへ渡す。
6. secret を含む manifest / temporary file は mode `0600` で作成し、使用後に削除する。

## 受け入れ基準

1. **AC-1**: `docs/security-and-secrets.md` に SOPS+age を中心とする方針、age 秘密鍵の扱い、1Password のバックアップ用途、一時 Cloudflare token の revoke 方針が明記されている。
2. **AC-2**: `.sops.yaml` が存在し、`secrets/*.sops.yml` を age 公開鍵で暗号化する creation rule を持つ。
3. **AC-3**: `secrets/README.md` が存在し、`keys.txt` を commit しないこと、1Password からの復旧位置づけ、`community.sops` での Ansible 復号方針を説明している。
4. **AC-4**: `requirements.yml` に `community.sops` collection が含まれる。
5. **AC-5**: Prometheus / cert-manager DNS01 は `cloudflare_api_token` ではなく `cloudflare_dns01_api_token` を参照する。
6. **AC-6**: Cloudflare Tunnel credentials は SOPS 由来の `cloudflared_tunnel_credentials` として読み込まれ、既存 role へ渡される。credentials を扱うタスクは `no_log: true` を維持する。
7. **AC-7**: SOPS 管理対象として `secrets/infra.sops.yml` が存在し、平文 secret の実値、age 秘密鍵、復号済み一時ファイルを commit しない guard/test がある。
8. **AC-8**: 既存 Ansible Vault の `cloudflare_api_token` / `vault_cloudflared_tunnel_credentials` から SOPS への移行手順と、移行後の token rotation 方針が docs に記載されている。
9. **AC-9**: 関連する静的テスト、`yamllint`、`ansible-lint` が通る。

## テスト方針

- `tests/secrets/test_sops_policy.py`
  - `.sops.yaml` の creation rule が `secrets/*.sops.yml` を対象にしていること。
  - `requirements.yml` に `community.sops` が含まれること。
  - `docs/security-and-secrets.md` と `secrets/README.md` に SOPS / age / `keys.txt` / 1Password backup / temporary Cloudflare token revoke が記載されていること。
  - `roles/prometheus/templates/cluster-issuer.yml.j2` が `cloudflare_dns01_api_token` を参照し、`cloudflare_api_token` を参照しないこと。
  - `playbooks/22-cloudflare-tunnel.yml` が SOPS 由来の `cloudflared_tunnel_credentials` を既存 role に渡すこと。
  - `secrets/` 配下に `keys.txt` や復号済みを示す `*.plain.yml` / `*.decrypted.yml` が存在しないこと。
- `uvx pytest tests/secrets/test_sops_policy.py`
- `yamllint .sops.yaml secrets/ docs/security-and-secrets.md playbooks/08-prometheus.yml playbooks/22-cloudflare-tunnel.yml`
- `ansible-lint playbooks/08-prometheus.yml playbooks/22-cloudflare-tunnel.yml roles/prometheus roles/cloudflared`

## 移行方針

1. 新しい SOPS 管理を導入する。
2. `cloudflare_dns01_api_token` と `cloudflared_tunnel_credentials` を `secrets/infra.sops.yml` へ移す。
3. Ansible 側を SOPS 読み込みへ切り替える。
4. 動作確認後、Ansible Vault 内の旧 `cloudflare_api_token` / `vault_cloudflared_tunnel_credentials` を削除する。
5. Cloudflare DNS01 token と Tunnel credentials の rotation 手順を docs に記載し、実 rotation は人間が実施する運用タスクとして残す。

## リスク / 注意点

- age 秘密鍵を失うと SOPS secret を復号できない。1Password バックアップを復旧手順として docs に明記する。
- age 秘密鍵が漏れると Git 履歴上の SOPS secret も読める。漏洩時は全 SOPS 管理 secret を rotate する。
- `community.sops` / `sops` / `age` が実行環境に必要になる。devcontainer / docs に導入方法を明記する。
- 移行中に Vault と SOPS の二重管理期間が発生する場合は、期限と正本を docs に明記する。
