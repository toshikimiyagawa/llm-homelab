# Spec: issue-128 - Multiple WARP enrollment identities

**Status**: frozen
**Tier**: 1
**Issue**: #128 follow-up
**Created**: 2026-06-14

## 目的

Cloudflare WARP enrollment を単一の `allowed_email` だけでなく、ユーザーが明示した複数の exact email identity から許可できるようにする。

Cloudflare Access logs では WARP enrollment app へのログインが `allowed = false` で拒否されており、拒否された identity は Terraform の `allowed_email` と一致していなかった。会社 Mac と個人端末の両方で WARP を使えるよう、許可 identity を local `terraform.tfvars` で増やせる形にする。

## スコープ

### 含む

- `infra/cloudflare/` Terraform root に複数 email identity 用の変数を追加する。
- WARP enrollment Access policy の `include` を複数 email に対応させる。
- WARP device custom profile の `match` を複数 email に対応させる。
- 既存 `allowed_email` は後方互換のため残す。
- `terraform.tfvars.example` はサンプル email のみを含める。
- 実メールは local `terraform.tfvars` にのみ設定し、commit しない。
- static tests で複数 email 対応と実メール非混入を検証する。

### 含まない

- email domain 全体の許可。
- Cloudflare IdP の追加・変更。
- Gateway network policy の追加。
- Cloudflare One client の自動 enroll。

## 設計

新しい変数 `allowed_emails` を `list(string)` として追加する。default は `[]` とし、実効許可リストは `distinct(concat([var.allowed_email], var.allowed_emails))` で作る。これにより既存環境は `allowed_email` だけで動き続け、必要な環境だけ `allowed_emails` を local `terraform.tfvars` で追加できる。

Access policy は dynamic `include` block で各 email を許可する。Device profile の `match` は Cloudflare の expression として `identity.email in {"a@example.com" "b@example.com"}` 形式を生成する。

## 受け入れ基準

1. `allowed_emails` 変数があり、`terraform.tfvars.example` はサンプル値だけを含む。
2. WARP enrollment policy は `allowed_email` と `allowed_emails` の両方を許可対象にできる。
3. WARP device custom profile の `match` は複数 email identity に対応する。
4. ユーザーが指定した実メールアドレスは commit されない。
5. `terraform fmt -check -recursive infra/cloudflare` と `terraform -chdir=infra/cloudflare validate` が pass する。
6. `terraform plan -var 'warp_private_network_cidr=192.168.0.0/17'` が実環境で no changes または WARP identity policy/profile の期待差分のみになる。

## テスト方針

- `tests/cloudflare_terraform/test_config.py`
  - `allowed_emails` variable / example。
  - `locals.allowed_warp_emails` が `allowed_email` と `allowed_emails` を結合すること。
  - Access policy が dynamic include で複数 email を許可すること。
  - Device profile match が複数 email 用 local を参照すること。
  - 実メールが tracked files に含まれないこと。
- Terraform CLI
  - `terraform fmt -check -recursive infra/cloudflare`
  - `terraform -chdir=infra/cloudflare validate`
