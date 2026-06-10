# Spec: issue-95 - Cloudflare DNS/Tunnel/Access Terraform 管理

**Status**: draft
**Tier**: 2
**Issue**: #95
**Created**: 2026-06-11

## 目的

Cloudflare 側の DNS / Tunnel / Access 操作を Terraform 管理へ移行し、Cloudflare UI を人が変更する運用をやめる。既存の `solvelio.com` 環境を Terraform state に取り込めるようにしつつ、別の利用者が別ドメインで同じ構成を作る場合は設定ファイルを書き換えるだけで再利用できる構成にする。

#91 の Cloudflare Tunnel 実機適用は、Cloudflare 側の前提リソースが Terraform 管理へ移行された後に進める。#93 の SOPS+age 基盤は blocked のため、本 spec では Terraform state と provider token をローカル手動運用で扱う。

## スコープ

### 含む

- `infra/cloudflare/` Terraform root の新規作成。
- Cloudflare provider v5 系を前提にした provider / variables / locals / resources / outputs の定義。
- `terraform.tfvars.example` による domain/account/zone/host/user 設定の外部化。
- 既存 Cloudflare account / zone / domain を前提リソースとして参照する設計。
- `llm01` 用 Cloudflare Tunnel の Terraform 管理。
- `open-webui-llm01`, `ssh-llm01`, `vllm-llm01`, `ollama-llm01` の DNS CNAME 管理。
- Open WebUI / Browser SSH 用の Access Application と Google ログイン許可ポリシー管理。
- vLLM / Ollama 用の Access Application、Service Token、Service Auth ポリシー管理。
- Tunnel ingress config の Terraform 管理。`roles/cloudflared/templates/config.yml.j2` と同じ 4 backend / catch-all を表現する。
- 既存リソースを `terraform import` で state に取り込む手順と、未作成環境で `terraform apply` する手順の docs 化。
- Terraform state / tfvars / provider token / generated secret を commit しない `.gitignore` と docs。
- Terraform 構成を静的検証する pytest。

### 含まない

- #91 の実機適用そのもの。
- #93 の SOPS+age 導入、secret 本体の SOPS 移行、remote state 暗号化。
- Terraform apply の CI/CD 自動化。
- Cloudflare UI read-only 設定の実適用。docs には推奨運用として記載してよい。
- Google OAuth client / IdP 元情報の新規発行。必要な ID / secret は tfvars または既存 Cloudflare 設定の import 前提とする。
- 既存 Tailscale 経路（`open-webui.solvelio.com`, `vllm.solvelio.com` など）の変更。
- Ansible role の cloudflared install / systemd / sshd hardening の置き換え。

## 設計決定

| 項目 | 決定 | 理由 |
|------|------|------|
| Terraform 配置 | `infra/cloudflare/` を単一 root にする | 現状は単一ホスト `llm01` が対象で、module 分割は過剰 |
| 再利用単位 | `terraform.tfvars` で domain/account/zone/host/user を差し替える | `solvelio.com` 固定を避け、別ドメインで再利用できる |
| account / zone | 既存前提として variable または data 参照 | Cloudflare domain 自体は既に存在し、他ユーザーも既存 zone を使う可能性が高い |
| 既存リソース | `terraform import` を標準移行手順にする | 既に作成済みの domain/DNS/Access を Terraform 管理へ取り込める |
| 未作成環境 | 同じ root で `terraform apply` 新規作成を可能にする | 他ユーザーの bootstrap 手順を単純にする |
| state | local state のみ、commit 禁止、secret として扱う | #93 が blocked のため remote/SOPS 前提にしない。Service Token secret や tunnel secret が state に入る可能性を明示する |
| provider token | `CLOUDFLARE_API_TOKEN` 環境変数で渡す | API token を tfvars や repo に保存しない |
| Cloudflare UI | apply/import 後は UI 変更禁止、必要なら read-only 推奨 | drift を防ぎ Terraform を正本にする |
| Tunnel config | Terraform managed config を正本にする | Cloudflare 側の public hostname / ingress を UI から排除する |

## Terraform 変数

`terraform.tfvars.example` は少なくとも以下を含む。

```hcl
cloudflare_account_id = "00000000000000000000000000000000"
cloudflare_zone_id    = "00000000000000000000000000000000"
domain                = "solvelio.com"
host_id               = "llm01"
allowed_email         = "user@example.com"
access_team_name      = "example-team"
```

backend URL は以下の変数で上書きできるようにする。default は issue #88 の凍結 spec と同じ値にする。

- `open_webui_backend_url`: `http://localhost:8080`
- `ollama_backend_url`: `http://localhost:11434`
- `vllm_backend_url`: `https://vllm.${domain}`
- `ssh_backend_url`: `ssh://localhost:22`
- `tunnel_catch_all_service`: `http_status:404`

## 管理対象リソース

Terraform は次の Cloudflare リソースを管理する。

- `cloudflare_zero_trust_tunnel_cloudflared` for `llm01`
- `cloudflare_zero_trust_tunnel_cloudflared_config` for 4 ingress rules and catch-all
- DNS CNAME records for:
  - `open-webui-llm01.<domain>`
  - `ssh-llm01.<domain>`
  - `vllm-llm01.<domain>`
  - `ollama-llm01.<domain>`
- Access applications for the same 4 hostnames
- Access policies:
  - Open WebUI: allow `allowed_email` through Google login
  - SSH: allow `allowed_email` through Google login and Browser SSH
  - vLLM: service auth only
  - Ollama: service auth only
- Access Service Token for API clients

Terraform resource names must be stable and descriptive, for example `cloudflare_zero_trust_access_application.open_webui`, so import commands remain understandable.

## 既存リソース移行

既存 Cloudflare リソースがある環境では、初回に `terraform import` で state へ取り込む。docs には次を含める。

- `terraform init`
- `CLOUDFLARE_API_TOKEN` の一時 export。token は保存せず、作業後に revoke または権限縮小する。
- account ID / zone ID / domain / allowed email を `terraform.tfvars` に書く。
- Tunnel / DNS records / Access applications / policies / service token の import コマンド雛形。
- `terraform plan` で差分を確認し、意図しない destroy / replacement がある場合は apply しないこと。
- import せず新規作成する環境では同じ tfvars で `terraform apply` すること。

## シークレットと state 管理

以下は repo に commit しない。

- `infra/cloudflare/terraform.tfstate`
- `infra/cloudflare/terraform.tfstate.backup`
- `infra/cloudflare/.terraform/`
- `infra/cloudflare/.terraform.lock.hcl` は provider reproducibility のため commit 対象にする。
- `infra/cloudflare/terraform.tfvars`
- `infra/cloudflare/*.auto.tfvars`
- `infra/cloudflare/*.tfplan`
- Cloudflare API token
- Terraform output に現れる可能性がある Access Service Token secret

Terraform state は secret として扱う。#93 完了後に SOPS+age または別の安全な state 保管へ移す余地を docs に残す。

## Ansible との境界

`roles/cloudflared` は引き続き origin host 側を管理する。#95 は Cloudflare 側を Terraform 管理へ移すだけで、Ansible role の責務を削らない。

ただし Terraform が Tunnel config を管理する場合、`roles/cloudflared/templates/config.yml.j2` の ingress と Terraform の ingress は drift しない必要がある。実装 plan では、静的テストで両者の hostname/backend/catch-all が一致することを検証する。

Cloudflare Tunnel credentials JSON を Ansible Vault に置く issue #88 の方針は本 spec では変更しない。#93 が完了するまでは Vault 方針を維持する。

## 受け入れ基準

各 AC は `tasks.md` で具体的なテストに対応させる。

1. **AC-1**: `infra/cloudflare/` に Terraform root が存在し、Cloudflare provider v5 系、required Terraform version、provider token の環境変数利用方針が定義されている。
2. **AC-2**: `terraform.tfvars.example` で `domain`, `host_id`, `cloudflare_account_id`, `cloudflare_zone_id`, `allowed_email`, `access_team_name` を差し替え可能で、`solvelio.com` は example 値に留まる。
3. **AC-3**: Terraform が `llm01` Tunnel、4 DNS CNAME、4 Access applications、Google login policy、Service Auth policy、Service Token、Tunnel ingress config を管理する定義を持つ。
4. **AC-4**: Tunnel ingress config は issue #88 と同じ 4 hostname/backend と catch-all を持ち、別 `domain` / `host_id` に展開できる。
5. **AC-5**: docs に既存リソースの `terraform import` 手順と未作成環境の `terraform apply` 手順がある。
6. **AC-6**: docs に Terraform state / tfvars / provider token / Service Token secret を commit しないこと、state を secret として扱うこと、作業後に広権限 token を revoke または権限縮小することが明記されている。
7. **AC-7**: `.gitignore` が Terraform local state, `.terraform/`, tfvars, plan files を除外し、`.terraform.lock.hcl` を除外しない。
8. **AC-8**: Cloudflare UI は Terraform import/apply 後に変更しない運用であること、必要なら Cloudflare Zero Trust dashboard read-only を有効化することが docs に明記されている。
9. **AC-9**: `roles/cloudflared/templates/config.yml.j2` と Terraform Tunnel ingress の hostname/backend/catch-all が静的テストで一致する。
10. **AC-10**: `terraform fmt -check -recursive infra/cloudflare` と `terraform validate` の実行手順が tasks/docs にあり、可能な環境では pass する。
11. **AC-11**: `uvx pytest tests/cloudflare_terraform/` が AC-1〜AC-9 を静的に検証する。

## テスト方針

Terraform は Cloudflare API と local state を必要とするため、CI で実 apply しない。以下を主検証にする。

- **静的 pytest**: `tests/cloudflare_terraform/test_config.py`
  - Terraform root / provider / resources / variables / outputs / docs / `.gitignore` を検査する。
  - 4 hostname/backend/catch-all が Ansible cloudflared config と Terraform locals/resources で一致することを検査する。
- **Terraform CLI**:
  - `terraform fmt -check -recursive infra/cloudflare`
  - `terraform -chdir=infra/cloudflare init -backend=false`
  - `terraform -chdir=infra/cloudflare validate`
- **手動**:
  - 既存環境では import 後に `terraform plan` を実行し、意図しない destroy/replacement がないことを人間が確認する。
  - 未作成環境では `terraform apply` 後、#91 の M-1〜M-5 へ進める。

## リスク / ロールバック

- **state 漏洩**: Access Service Token secret や tunnel secret が state に入る可能性がある。state は commit せず secret として扱う。
- **import ID 誤り**: 誤った Cloudflare リソースを state に取り込むと plan が危険になる。docs に `terraform state show` と `terraform plan` 確認を明記する。
- **既存リソース置換**: import 後に provider schema と実リソース差分で replacement が出る可能性がある。初回 plan で destroy/replacement が出たら apply せず STOP する。
- **UI drift**: import/apply 後に UI 変更すると Terraform と乖離する。UI は閲覧のみ、変更は Terraform PR 経由とする。
- **#93 未完了**: SOPS+age が未整備のため state/secret の長期保管は未完成。#95 は local manual state の安全運用に限定する。

## 参考

- Cloudflare Docs: API and Terraform
- Cloudflare Docs: Deploy Tunnels with Terraform
- Terraform Registry: Cloudflare provider
