# Spec: issue-120 - Terraform-managed Cloudflare Tunnel token

**Status**: frozen
**Tier**: 2
**Issue**: #120
**Created**: 2026-06-12

## 目的

#95 で Cloudflare Tunnel / DNS / Access の正本を Terraform に移した後も、
Ansible 側に locally-managed tunnel の credentials JSON 前提が残っている。
この不整合により #91 の実機適用が `cloudflared_tunnel_credentials` 空文字で停止している。

Cloudflare 側は Terraform の `config_src = "cloudflare"` を正本とし、llm01 側の
`cloudflared` は remotely-managed / Cloudflare-managed tunnel の token で起動する
構成へ寄せる。これにより、手元で `cloudflared tunnel create llm01` を実行して
`<TUNNEL_ID>.json` を作る運用を不要にし、#91 の実機適用を Terraform-created tunnel
前提で再開できるようにする。

## スコープ

### 含む

- Terraform に `cloudflare_zero_trust_tunnel_cloudflared_token` data source を追加する。
- Terraform output に sensitive な `tunnel_token` を追加する。
- `playbooks/22-cloudflare-tunnel.yml` が SOPS の `cloudflared_tunnel_token` を読み、role へ `vault_cloudflared_tunnel_token` として渡す。
- `roles/cloudflared` が tunnel token を root-only file に配置する。
- `cloudflared.service` が `cloudflared tunnel run --token-file <PATH>` で起動する。
- `roles/cloudflared/templates/config.yml.j2` から `credentials-file:` を外し、Cloudflare-managed tunnel token 起動と矛盾しない最小 config にする。
- SOPS / docs / tests の契約を `cloudflared_tunnel_credentials` JSON から `cloudflared_tunnel_token` へ更新する。
- `cloudflared_tunnel_id` は非機密 inventory 変数として維持し、config / docs / smoke-test の文脈で引き続き使えるようにする。
- secret を扱う Ansible task は `no_log: true` と file mode `0600` を維持する。

### 含まない

- #91 の実機適用そのもの。
- Terraform apply / import の実行。
- Cloudflare provider token、tunnel token、Terraform state、復号済み SOPS 内容の commit。
- Cloudflare Access SSH CA 公開鍵の実値差し替え。
- Service Token client secret の配布方式変更。
- Cloudflare UI で tunnel を手動作成する運用への回帰。

## 設計決定

| 項目 | 決定 | 理由 |
|------|------|------|
| tunnel 起動方式 | token file (`--token-file`) | Cloudflare-managed tunnel は token で connector を認証する。token を process args に出さず file mode 0600 で扱える |
| token 正本 | Terraform data source から取得し SOPS に手動格納 | Terraform が作る tunnel と同一の token を使い、repo に secret を置かない |
| SOPS key | `cloudflared_tunnel_token` | credentials JSON ではないことを明確にする |
| role 変数 | `vault_cloudflared_tunnel_token` | 既存の role-internal `vault_...` alias pattern を踏襲しつつ、SOPS を role に漏らさない |
| config.yml | `tunnel: {{ cloudflared_tunnel_id }}` のみ | ingress は Terraform-managed config が正本。credentials-file は token 起動と矛盾するため削除 |
| token file path | `/etc/cloudflared/tunnel-token` | credentials JSON と区別し、root-only secret file として扱う |
| legacy key | `cloudflared_tunnel_credentials` は docs/tests から外す | #91 の誤誘導をなくす。SOPS ファイルに空 key が残っていても runtime path は参照しない |

## Terraform token 取得手順

Terraform は tunnel 作成後に次を持つ。

```hcl
data "cloudflare_zero_trust_tunnel_cloudflared_token" "llm01" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.llm01.id
}

output "tunnel_token" {
  description = "Cloudflare Tunnel token for cloudflared on llm01. Treat as a secret."
  value       = data.cloudflare_zero_trust_tunnel_cloudflared_token.llm01.token
  sensitive   = true
}
```

人間は `terraform output -raw tunnel_token` で token を取得し、値を表示・commit せず
`sops secrets/infra.sops.yml` の `cloudflared_tunnel_token` に格納する。

## 受け入れ基準

各 AC は `tasks.md` で具体的なテストに対応させる。

1. **AC-1**: Terraform に `cloudflare_zero_trust_tunnel_cloudflared_token` data source があり、`tunnel_token` output は `sensitive = true` である。
2. **AC-2**: `playbooks/22-cloudflare-tunnel.yml` は `cloudflared_tunnel_token` を SOPS から読み、`vault_cloudflared_tunnel_token` に `no_log: true` で渡す。
3. **AC-3**: `roles/cloudflared` は tunnel token を root-owned mode `0600` の file に配置し、token 配置 task は `no_log: true` を持つ。
4. **AC-4**: `cloudflared.service` は token を command line に直接埋め込まず、`--token-file` で token file を参照する。
5. **AC-5**: Ansible の `config.yml.j2` は `credentials-file:` を含まず、Terraform-managed tunnel config と矛盾しない最小 config である。
6. **AC-6**: static tests は旧 `cloudflared_tunnel_credentials` runtime path が使われていないこと、`cloudflared_tunnel_token` runtime path が使われていることを検証する。
7. **AC-7**: docs は Terraform output から tunnel token を取得し、SOPS の `cloudflared_tunnel_token` に格納する手順を説明する。token / Terraform state / tfvars は commit 禁止であることも明記する。
8. **AC-8**: `docs/operations.md` の #91 手順は credentials JSON ではなく tunnel token 前提に更新される。
9. **AC-9**: `docs/security-and-secrets.md` と `secrets/README.md` は `cloudflared_tunnel_token` の扱い、rotation、age key との境界を説明する。
10. **AC-10**: `uvx pytest tests/cloudflare_terraform/ tests/cloudflared/test_role.py tests/secrets/test_sops_policy.py -q` が通る。
11. **AC-11**: `yamllint` と `ansible-lint` が変更対象で通る。
12. **AC-12**: secret 本体、tunnel token、Terraform state、復号済み一時ファイル、age 秘密鍵を commit しない。

## テスト方針

- **静的 pytest**
  - `tests/cloudflare_terraform/test_config.py`: Terraform token data source / sensitive output / docs contract。
  - `tests/cloudflared/test_role.py`: token file 配置、`--token-file`、`credentials-file:` 削除、`no_log` / `0600`。
  - `tests/secrets/test_sops_policy.py`: SOPS key / playbook mapping / docs contract。
- **lint**
  - `yamllint infra/cloudflare/ roles/cloudflared/ playbooks/22-cloudflare-tunnel.yml docs/operations.md docs/security-and-secrets.md secrets/README.md`
  - `ansible-lint roles/cloudflared playbooks/22-cloudflare-tunnel.yml`
- **Terraform CLI**
  - `terraform fmt -check -recursive infra/cloudflare`
  - `terraform -chdir=infra/cloudflare init -backend=false`
  - `terraform -chdir=infra/cloudflare validate`
- **手動**
  - `terraform output -raw tunnel_token` は人間が必要時のみ実行し、SOPS に格納する。
  - token 格納後に #91 の `ansible-playbook --check` へ進む。

## リスク / ロールバック

- **token 漏洩**: tunnel token は connector を起動できる secret。SOPS と root-only file mode 0600 で扱い、command line に載せない。
- **Terraform state 漏洩**: token data source / output により state に token が入る可能性がある。state は既存方針どおり secret として扱い commit しない。
- **token rotation**: Cloudflare token rotation 後は Terraform output から新 token を取得し、SOPS を更新し、Ansible 再適用で token file を更新する。
- **既存 llm01 への影響**: `cloudflared.service` が未導入の現状では移行影響は小さい。既に credentials-file 方式で稼働している環境があれば、token file 方式へ切り替える前に service restart が必要。
- **Cloudflare provider schema 差異**: provider v5 の token data source 名 / attribute が変わった場合は Terraform validate で検出する。
