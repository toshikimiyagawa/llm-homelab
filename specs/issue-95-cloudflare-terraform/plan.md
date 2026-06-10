# Plan: issue-95 - Cloudflare DNS/Tunnel/Access Terraform 管理

## アプローチ

Cloudflare 側の状態は Terraform を正本にする。`infra/cloudflare/` に単一 Terraform root を作り、Cloudflare account / zone は既存前提の variable として受け取り、Tunnel、Tunnel public hostname config、DNS CNAME、Access Application、Access Policy、Service Token を管理する。`terraform.tfvars.example` は `solvelio.com` / `llm01` の例を持つが、別利用者は `domain` / `host_id` / account / zone / email を差し替えるだけで同じ構成を作れる。

#88 では locally-managed tunnel config を Ansible の `roles/cloudflared/templates/config.yml.j2` に置いたが、#95 では最終的に Cloudflare 側を Terraform に寄せるため、Tunnel は `config_src = "cloudflare"` を前提にする。Ansible は `llm01` の host provisioning（cloudflared install、systemd、credentials/token 配置、SSH CA、sshd hardening）に残し、Cloudflare public hostname / ingress は Terraform の `cloudflare_zero_trust_tunnel_cloudflared_config` が管理する。

既存 Cloudflare リソースがある場合は `terraform import` を標準移行手順にする。未作成環境では同じ root で `terraform apply` する。Terraform state は local state のみで、Access Service Token secret や tunnel secret が入る可能性があるため secret として扱い、repo には commit しない。

## 影響範囲 / 主要ファイル

- `.gitignore` - Terraform local state、tfvars、plan file、`.terraform/` を除外する。`.terraform.lock.hcl` は除外しない。
- `infra/cloudflare/versions.tf` - Terraform / Cloudflare provider version constraint。
- `infra/cloudflare/providers.tf` - Cloudflare provider。token は `CLOUDFLARE_API_TOKEN` 環境変数を使い、tfvars に保存しない。
- `infra/cloudflare/variables.tf` - account / zone / domain / host / email / backend URL 変数。
- `infra/cloudflare/locals.tf` - hostname、backend、Access application map、Tunnel ingress map。
- `infra/cloudflare/tunnel.tf` - `cloudflare_zero_trust_tunnel_cloudflared` と `cloudflare_zero_trust_tunnel_cloudflared_config`。
- `infra/cloudflare/dns.tf` - 4 hostname の proxied CNAME record。
- `infra/cloudflare/access.tf` - 4 Access applications、Google login policies、Service Auth policies、Service Token。
- `infra/cloudflare/outputs.tf` - tunnel ID、hostnames、service token client ID、sensitive 指定した service token client secret output。
- `infra/cloudflare/terraform.tfvars.example` - `solvelio.com` / `llm01` の example。
- `infra/cloudflare/README.md` - init / import / plan / apply / state 取り扱い / Cloudflare UI 禁止運用。
- `roles/cloudflared/templates/config.yml.j2` - locally-managed ingress を削除し、Cloudflare-managed tunnel 起動用の最小 config に寄せる。
- `tests/cloudflare_terraform/test_config.py` - Terraform root と docs の静的契約テスト。
- `tests/cloudflared/test_role.py` - cloudflared config が重複 ingress を持たないことの既存テスト更新。
- `docs/operations.md` - Cloudflare UI 手順を Terraform 手順へ置換し、#91 の前提として参照。
- `docs/security-and-secrets.md` - Terraform state / Service Token secret / provider token の扱いを追記。

## Terraform 構成方針

Cloudflare provider は v5 系を前提にする。

```hcl
terraform {
  required_version = ">= 1.6.0"
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.19"
    }
  }
}

provider "cloudflare" {}
```

provider token は `CLOUDFLARE_API_TOKEN` 環境変数で渡す。`provider "cloudflare" { api_token = var... }` のような保存しやすい形は採用しない。

`locals.tf` は hostname/backend を 1 箇所に集約する。

```hcl
locals {
  hostnames = {
    open_webui = "open-webui-${var.host_id}.${var.domain}"
    ssh        = "ssh-${var.host_id}.${var.domain}"
    vllm       = "vllm-${var.host_id}.${var.domain}"
    ollama     = "ollama-${var.host_id}.${var.domain}"
  }

  tunnel_services = {
    open_webui = var.open_webui_backend_url
    ssh        = var.ssh_backend_url
    vllm       = var.vllm_backend_url
    ollama     = var.ollama_backend_url
  }
}
```

Tunnel config は Cloudflare-managed を採用する。

```hcl
resource "cloudflare_zero_trust_tunnel_cloudflared" "llm01" {
  account_id = var.cloudflare_account_id
  name       = var.host_id
  config_src = "cloudflare"
}
```

`cloudflare_zero_trust_tunnel_cloudflared_config` は 4 ingress と catch-all を持つ。実装時は provider v5 の schema に合わせて `config = { ingress = [...] }` 形式で書く。vLLM は `origin_request.origin_server_name = "vllm.${var.domain}"` を保持し、#88 の Traefik 経由設計を維持する。

DNS は tunnel の CNAME target に向ける。target は provider / resource の実際の attribute に合わせる。provider が tunnel CNAME target attribute を公開しない場合は Cloudflare Tunnel の標準 target 形式 `<tunnel-id>.cfargotunnel.com` を Terraform local で構成する。

Access はアプリケーションごとに分ける。Open WebUI / SSH は `allowed_email` の Google login policy、vLLM / Ollama は Service Token を include する Service Auth policy にする。Google IdP 自体は既存設定を前提とし、本 issue では作らない。

## 既存リソース移行

`infra/cloudflare/README.md` に import 手順を置く。import ID は Cloudflare provider v5 の実仕様に依存するため、README では resource address と取得すべき ID を明示し、実 ID は `cloudflare` CLI/API/UI read-only で確認して埋める形にする。

標準手順:

1. `cp terraform.tfvars.example terraform.tfvars`
2. `terraform -chdir=infra/cloudflare init`
3. `export CLOUDFLARE_API_TOKEN=...`
4. 既存リソースがある場合だけ `terraform import ...`
5. `terraform -chdir=infra/cloudflare plan`
6. destroy / replacement が出たら apply せず STOP
7. 差分が意図通りなら `terraform -chdir=infra/cloudflare apply`

## テスト戦略

Terraform apply は Cloudflare API と secret state を必要とするため CI では行わない。repo 内で確認するのは以下。

- `uvx pytest tests/cloudflare_terraform/`
  - Terraform root、provider、resources、variables、docs、`.gitignore` を静的検査。
  - 4 hostname/backend/catch-all が Terraform 側に存在することを検査。
  - Ansible cloudflared config が 4 hostname ingress を残していないことを検査。
- `uvx pytest tests/cloudflared/test_role.py`
  - #88/#90 の既存 host provisioning 契約が壊れていないことを検査。#95 で ingress 正本が移るため該当テストは更新する。
- Terraform CLI がある環境:
  - `terraform fmt -check -recursive infra/cloudflare`
  - `terraform -chdir=infra/cloudflare init -backend=false`
  - `terraform -chdir=infra/cloudflare validate`

## 検討した代替案とトレードオフ

- **Cloudflare ingress を Ansible に残す**
  - 不採用。#88 の locally-managed 方針とは整合するが、Cloudflare 側の routing が Terraform 正本にならず、UI/CLI 操作排除と別ドメイン再利用の一貫性が落ちる。
- **Terraform module + root に分割**
  - 不採用。現時点では `llm01` 1 台だけで、module 化は抽象化が先行する。将来複数ホスト化したら切り出す。
- **remote state / SOPS 前提**
  - 不採用。#93 が blocked のため、本 issue では local state を secret として扱う手動運用に限定する。
- **Cloudflare UI read-only を Terraform で強制**
  - 不採用。運用として推奨するが、権限設計の影響が大きく #95 の主目的から外れる。

## リスク / ロールバック

- **Terraform state 漏洩**: state に tunnel secret / Service Token secret が入る可能性がある。`.gitignore` と docs で commit 禁止を明示し、state を secret として扱う。
- **Access resource drift**: Cloudflare provider v5 の Zero Trust resources は drift や provider bug の影響を受ける可能性がある。初回 import/apply は `terraform plan` を人間が読み、destroy/replacement があれば STOP する。
- **#88 からの移行ミス**: Ansible ingress と Terraform ingress が二重正本になると混乱する。#95 で Ansible config は最小化し、静的テストで hostname ingress が残っていないことを確認する。
- **Service Token secret の出力**: output は sensitive にし、通常 docs では client secret を表示・保存しない。必要な場合だけ `terraform output -raw` を人間が実行する。
