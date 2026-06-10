# Tasks: issue-95 - Cloudflare DNS/Tunnel/Access Terraform 管理

> 実装エージェントはこの tasks を上から順に実行する。Cloudflare API への実 apply はしない。Terraform と pytest による静的検証、docs、import/apply 手順の整備までを行う。

## Task 1: Terraform local state を commit しない `.gitignore`

**Files:**
- Modify: `.gitignore`
- Test: `tests/cloudflare_terraform/test_config.py`

1. `.gitignore` に以下を追加する。

   ```gitignore
   # Terraform local working files and secret state
   **/.terraform/
   **/terraform.tfstate
   **/terraform.tfstate.*
   **/terraform.tfvars
   **/*.auto.tfvars
   **/*.tfplan
   ```

2. `.terraform.lock.hcl` は ignore しない。
3. `tests/cloudflare_terraform/test_config.py::test_gitignore_excludes_terraform_secrets_not_lockfile` で、上記 ignore と lockfile 非除外を検査する。

## Task 2: Terraform root scaffold

**Files:**
- Create: `infra/cloudflare/versions.tf`
- Create: `infra/cloudflare/providers.tf`
- Create: `infra/cloudflare/variables.tf`
- Create: `infra/cloudflare/locals.tf`
- Create: `infra/cloudflare/terraform.tfvars.example`
- Test: `tests/cloudflare_terraform/test_config.py`

1. `versions.tf` を作成する。

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
   ```

2. `providers.tf` を作成する。token は `CLOUDFLARE_API_TOKEN` 環境変数で渡すため、provider block に `api_token` を書かない。

   ```hcl
   provider "cloudflare" {}
   ```

3. `variables.tf` に以下の変数を定義する。

   ```hcl
   variable "cloudflare_account_id" {
     description = "Cloudflare account ID that owns the Zero Trust resources."
     type        = string
   }

   variable "cloudflare_zone_id" {
     description = "Cloudflare zone ID for domain."
     type        = string
   }

   variable "domain" {
     description = "Base DNS zone, for example solvelio.com."
     type        = string
   }

   variable "host_id" {
     description = "Host identifier used in public hostnames."
     type        = string
     default     = "llm01"
   }

   variable "allowed_email" {
     description = "Google account email allowed to access browser applications."
     type        = string
   }

   variable "access_team_name" {
     description = "Cloudflare Zero Trust team name."
     type        = string
   }

   variable "open_webui_backend_url" {
     description = "Origin URL for Open WebUI through the tunnel."
     type        = string
     default     = "http://localhost:8080"
   }

   variable "ollama_backend_url" {
     description = "Origin URL for Ollama through the tunnel."
     type        = string
     default     = "http://localhost:11434"
   }

   variable "vllm_backend_url" {
     description = "Origin URL for vLLM through Traefik."
     type        = string
     default     = null
   }

   variable "ssh_backend_url" {
     description = "Origin URL for Browser SSH through the tunnel."
     type        = string
     default     = "ssh://localhost:22"
   }

   variable "tunnel_catch_all_service" {
     description = "Final catch-all tunnel service."
     type        = string
     default     = "http_status:404"
   }
   ```

4. `locals.tf` に hostname/backend locals を定義する。

   ```hcl
   locals {
     vllm_origin_hostname = "vllm.${var.domain}"

     hostnames = {
       open_webui = "open-webui-${var.host_id}.${var.domain}"
       ollama     = "ollama-${var.host_id}.${var.domain}"
       vllm       = "vllm-${var.host_id}.${var.domain}"
       ssh        = "ssh-${var.host_id}.${var.domain}"
     }

     tunnel_services = {
       open_webui = var.open_webui_backend_url
       ollama     = var.ollama_backend_url
       vllm       = coalesce(var.vllm_backend_url, "https://${local.vllm_origin_hostname}")
       ssh        = var.ssh_backend_url
     }
   }
   ```

5. `terraform.tfvars.example` を作成する。

   ```hcl
   cloudflare_account_id = "00000000000000000000000000000000"
   cloudflare_zone_id    = "00000000000000000000000000000000"
   domain                = "solvelio.com"
   host_id               = "llm01"
   allowed_email         = "user@example.com"
   access_team_name      = "example-team"
   ```

6. `tests/cloudflare_terraform/test_config.py` で AC-1 / AC-2 を検査する。

## Task 3: Tunnel and Cloudflare-managed ingress

**Files:**
- Create: `infra/cloudflare/tunnel.tf`
- Test: `tests/cloudflare_terraform/test_config.py`

1. `cloudflare_zero_trust_tunnel_cloudflared.llm01` を作成する。

   ```hcl
   resource "cloudflare_zero_trust_tunnel_cloudflared" "llm01" {
     account_id = var.cloudflare_account_id
     name       = var.host_id
     config_src = "cloudflare"
   }
   ```

2. `cloudflare_zero_trust_tunnel_cloudflared_config.llm01` を作成する。provider v5 schema に合わせ、以下の意味を持つ config にする。

   ```hcl
   resource "cloudflare_zero_trust_tunnel_cloudflared_config" "llm01" {
     account_id = var.cloudflare_account_id
     tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.llm01.id

     config = {
       ingress = [
         {
           hostname = local.hostnames.open_webui
           service  = local.tunnel_services.open_webui
         },
         {
           hostname = local.hostnames.ollama
           service  = local.tunnel_services.ollama
         },
         {
           hostname = local.hostnames.vllm
           service  = local.tunnel_services.vllm
           origin_request = {
             origin_server_name = local.vllm_origin_hostname
           }
         },
         {
           hostname = local.hostnames.ssh
           service  = local.tunnel_services.ssh
         },
         {
           service = var.tunnel_catch_all_service
         }
       ]
     }
   }
   ```

3. `tests/cloudflare_terraform/test_config.py` で以下を検査する。
   - tunnel resource がある。
   - `config_src = "cloudflare"` がある。
   - 4 hostname local と 4 backend default がある。
   - catch-all `http_status:404` がある。
   - vLLM の `origin_server_name` がある。

## Task 4: DNS CNAME records

**Files:**
- Create: `infra/cloudflare/dns.tf`
- Test: `tests/cloudflare_terraform/test_config.py`

1. Tunnel CNAME target を local に追加する。

   ```hcl
   locals {
     tunnel_cname_target = "${cloudflare_zero_trust_tunnel_cloudflared.llm01.id}.cfargotunnel.com"
   }
   ```

   既存 `locals.tf` に追記するか、`dns.tf` の `locals` block として追加する。

2. 4 hostname の DNS CNAME を `for_each` で作る。

   ```hcl
   resource "cloudflare_dns_record" "tunnel" {
     for_each = local.hostnames

     zone_id = var.cloudflare_zone_id
     name    = each.value
     type    = "CNAME"
     content = local.tunnel_cname_target
     proxied = true
     ttl     = 1
   }
   ```

3. static test で `cloudflare_dns_record`, `CNAME`, `proxied = true`, `ttl = 1`, `cfargotunnel.com` を検査する。

## Task 5: Access applications, policies, and service token

**Files:**
- Create: `infra/cloudflare/access.tf`
- Test: `tests/cloudflare_terraform/test_config.py`

1. `cloudflare_zero_trust_access_service_token.api_clients` を作る。

   ```hcl
   resource "cloudflare_zero_trust_access_service_token" "api_clients" {
     account_id = var.cloudflare_account_id
     name       = "${var.host_id}-api-clients"
   }
   ```

2. 4 Access applications を作る。Google IdP は既存 Cloudflare 設定を使うため、本 task では新規 identity provider resource を作らない。

   ```hcl
   resource "cloudflare_zero_trust_access_application" "open_webui" {
     account_id       = var.cloudflare_account_id
     name             = "${var.host_id}-open-webui"
     domain           = local.hostnames.open_webui
     type             = "self_hosted"
     session_duration = "24h"
   }

   resource "cloudflare_zero_trust_access_application" "ssh" {
     account_id       = var.cloudflare_account_id
     name             = "${var.host_id}-ssh"
     domain           = local.hostnames.ssh
     type             = "self_hosted"
     session_duration = "24h"
   }

   resource "cloudflare_zero_trust_access_application" "vllm" {
     account_id       = var.cloudflare_account_id
     name             = "${var.host_id}-vllm"
     domain           = local.hostnames.vllm
     type             = "self_hosted"
     session_duration = "24h"
   }

   resource "cloudflare_zero_trust_access_application" "ollama" {
     account_id       = var.cloudflare_account_id
     name             = "${var.host_id}-ollama"
     domain           = local.hostnames.ollama
     type             = "self_hosted"
     session_duration = "24h"
   }
   ```

   Browser SSH を有効化する provider attribute が Terraform validate で確認できる場合は `cloudflare_zero_trust_access_application.ssh` に追加する。provider v5 で Browser SSH attribute が公開されていない場合は、実装を止めて人間に報告する。Cloudflare UI で補完しない。

3. Google login policy を Open WebUI / SSH に設定する。

   ```hcl
   resource "cloudflare_zero_trust_access_policy" "open_webui_google" {
     account_id     = var.cloudflare_account_id
     application_id = cloudflare_zero_trust_access_application.open_webui.id
     name           = "${var.host_id}-open-webui-google"
     decision       = "allow"
     precedence     = 1

     include = [{
       email = {
         email = var.allowed_email
       }
     }]
   }
   ```

   SSH 用も明示的に作る。

   ```hcl
   resource "cloudflare_zero_trust_access_policy" "ssh_google" {
     account_id     = var.cloudflare_account_id
     application_id = cloudflare_zero_trust_access_application.ssh.id
     name           = "${var.host_id}-ssh-google"
     decision       = "allow"
     precedence     = 1

     include = [{
       email = {
         email = var.allowed_email
       }
     }]
   }
   ```

4. Service Auth policy を vLLM / Ollama に設定する。

   ```hcl
   resource "cloudflare_zero_trust_access_policy" "vllm_service_auth" {
     account_id     = var.cloudflare_account_id
     application_id = cloudflare_zero_trust_access_application.vllm.id
     name           = "${var.host_id}-vllm-service-auth"
     decision       = "non_identity"
     precedence     = 1

     include = [{
       service_token = {
         token_id = cloudflare_zero_trust_access_service_token.api_clients.id
       }
     }]
   }
   ```

   Ollama 用も明示的に作る。

   ```hcl
   resource "cloudflare_zero_trust_access_policy" "ollama_service_auth" {
     account_id     = var.cloudflare_account_id
     application_id = cloudflare_zero_trust_access_application.ollama.id
     name           = "${var.host_id}-ollama-service-auth"
     decision       = "non_identity"
     precedence     = 1

     include = [{
       service_token = {
         token_id = cloudflare_zero_trust_access_service_token.api_clients.id
       }
     }]
   }
   ```

5. static test で以下を検査する。
   - `cloudflare_zero_trust_access_application` がある。
   - `cloudflare_zero_trust_access_policy` がある。
   - `cloudflare_zero_trust_access_service_token` がある。
   - `allowed_email` が参照される。
   - `service_token` が参照される。
   - `decision = "non_identity"` がある。

## Task 6: Outputs

**Files:**
- Create: `infra/cloudflare/outputs.tf`
- Test: `tests/cloudflare_terraform/test_config.py`

1. 非 secret output を作る。

   ```hcl
   output "tunnel_id" {
     description = "Cloudflare Tunnel ID."
     value       = cloudflare_zero_trust_tunnel_cloudflared.llm01.id
   }

   output "hostnames" {
     description = "Public hostnames managed by Terraform."
     value       = local.hostnames
   }

   output "service_token_client_id" {
     description = "Cloudflare Access Service Token client ID for API clients."
     value       = cloudflare_zero_trust_access_service_token.api_clients.client_id
   }
   ```

2. client secret output が必要な場合は sensitive にする。

   ```hcl
   output "service_token_client_secret" {
     description = "Cloudflare Access Service Token client secret. Treat as a secret."
     value       = cloudflare_zero_trust_access_service_token.api_clients.client_secret
     sensitive   = true
   }
   ```

3. static test で `sensitive = true` を検査する。

## Task 7: Ansible cloudflared config を最小化

**Files:**
- Modify: `roles/cloudflared/templates/config.yml.j2`
- Modify: `tests/cloudflared/test_role.py`
- Test: `tests/cloudflared/test_role.py`
- Test: `tests/cloudflare_terraform/test_config.py`

1. `roles/cloudflared/templates/config.yml.j2` から `ingress:` 以下の 4 hostname/backend/catch-all を削除する。
2. Cloudflare-managed tunnel の origin 起動に必要な最小 config へ寄せる。

   ```yaml
   {{ ansible_managed | comment }}
   # cloudflared Cloudflare-managed tunnel config (issue #95)
   tunnel: {{ cloudflared_tunnel_id }}
   credentials-file: {{ cloudflared_credentials_path }}
   ```

3. `tests/cloudflared/test_role.py::test_config_has_all_hostnames` を、hostnames が Ansible config ではなく Terraform config に存在する契約へ変更する。cloudflared role のテストでは config が tunnel / credentials-file を持つこと、`ingress:` を持たないことを検査する。
4. `tests/cloudflare_terraform/test_config.py` で Terraform 側に 4 hostname/backend/catch-all があることを検査する。

## Task 8: Terraform docs

**Files:**
- Create: `infra/cloudflare/README.md`
- Modify: `docs/operations.md`
- Modify: `docs/security-and-secrets.md`
- Test: `tests/cloudflare_terraform/test_config.py`

1. `infra/cloudflare/README.md` に以下を書く。
   - `terraform.tfvars.example` から `terraform.tfvars` を作る手順。
   - `CLOUDFLARE_API_TOKEN` を環境変数で渡すこと。
   - token は保存せず、作業後に revoke または権限縮小すること。
   - 既存リソースがある場合の `terraform import` resource address 一覧。
   - 未作成環境での `terraform apply` 手順。
   - `terraform plan` で destroy/replacement が出たら STOP すること。
   - state は secret であり commit しないこと。
   - Cloudflare UI は import/apply 後に変更しないこと。必要なら Zero Trust dashboard read-only を有効化すること。
2. `docs/operations.md` の「一度きりの手動セットアップ（Cloudflare 側）」を Terraform 手順へ置換する。Cloudflare UI で DNS/Access/Tunnel を作る手順は残さない。
3. `docs/security-and-secrets.md` に Terraform state と Access Service Token secret の扱いを追記する。
4. static test で docs に `terraform import`, `terraform apply`, `CLOUDFLARE_API_TOKEN`, `terraform.tfstate`, `read-only`, `revoke` が含まれることを検査する。

## Task 9: Terraform static contract tests

**Files:**
- Create: `tests/cloudflare_terraform/test_config.py`
- Test: `tests/cloudflare_terraform/test_config.py`

1. pathlib ベースで repository files を読む test を作る。
2. 最低限、以下の test を実装する。

   ```python
   from pathlib import Path

   ROOT = Path(__file__).parents[2]
   TF = ROOT / "infra" / "cloudflare"
   GITIGNORE = ROOT / ".gitignore"
   CLOUDFLARED_CONFIG = ROOT / "roles" / "cloudflared" / "templates" / "config.yml.j2"
   OPS_DOC = ROOT / "docs" / "operations.md"
   SECURITY_DOC = ROOT / "docs" / "security-and-secrets.md"


   def read_all_tf() -> str:
       return "\n".join(path.read_text() for path in sorted(TF.glob("*.tf")))


   def test_provider_version_and_env_token_contract():
       text = (TF / "versions.tf").read_text() + (TF / "providers.tf").read_text()
       assert 'source  = "cloudflare/cloudflare"' in text
       assert 'version = "~> 5.19"' in text
       assert 'provider "cloudflare" {}' in text
       assert "api_token" not in (TF / "providers.tf").read_text()


   def test_tfvars_example_is_domain_portable():
       text = (TF / "terraform.tfvars.example").read_text()
       for key in [
           "cloudflare_account_id",
           "cloudflare_zone_id",
           "domain",
           "host_id",
           "allowed_email",
           "access_team_name",
       ]:
           assert key in text
       assert 'domain                = "solvelio.com"' in text


   def test_tunnel_is_cloudflare_managed_and_has_ingress_contract():
       text = read_all_tf()
       assert "cloudflare_zero_trust_tunnel_cloudflared" in text
       assert 'config_src = "cloudflare"' in text
       for key in ["open_webui", "ollama", "vllm", "ssh"]:
           assert key in text
       for service in [
           "http://localhost:8080",
           "http://localhost:11434",
           "ssh://localhost:22",
           "http_status:404",
       ]:
           assert service in text
       assert "origin_server_name" in text


   def test_dns_records_point_to_tunnel():
       text = read_all_tf()
       assert "cloudflare_dns_record" in text
       assert '"CNAME"' in text
       assert "proxied = true" in text
       assert "ttl     = 1" in text
       assert "cfargotunnel.com" in text


   def test_access_resources_exist():
       text = read_all_tf()
       assert "cloudflare_zero_trust_access_application" in text
       assert "cloudflare_zero_trust_access_policy" in text
       assert "cloudflare_zero_trust_access_service_token" in text
       assert "allowed_email" in text
       assert "service_token" in text
       assert 'decision       = "non_identity"' in text


   def test_outputs_mark_service_token_secret_sensitive():
       text = (TF / "outputs.tf").read_text()
       assert "service_token_client_id" in text
       assert "service_token_client_secret" in text
       assert "sensitive   = true" in text


   def test_gitignore_excludes_terraform_secrets_not_lockfile():
       text = GITIGNORE.read_text()
       for pattern in [
           "**/.terraform/",
           "**/terraform.tfstate",
           "**/terraform.tfstate.*",
           "**/terraform.tfvars",
           "**/*.auto.tfvars",
           "**/*.tfplan",
       ]:
           assert pattern in text
       assert ".terraform.lock.hcl" not in text


   def test_ansible_config_no_longer_contains_locally_managed_ingress():
       text = CLOUDFLARED_CONFIG.read_text()
       assert "credentials-file:" in text
       assert "ingress:" not in text
       for hostname in [
           "open-webui-llm01.solvelio.com",
           "ollama-llm01.solvelio.com",
           "vllm-llm01.solvelio.com",
           "ssh-llm01.solvelio.com",
       ]:
           assert hostname not in text


   def test_docs_cover_import_apply_state_and_ui_policy():
       docs = (TF / "README.md").read_text() + OPS_DOC.read_text() + SECURITY_DOC.read_text()
       for term in [
           "terraform import",
           "terraform apply",
           "CLOUDFLARE_API_TOKEN",
           "terraform.tfstate",
           "read-only",
           "revoke",
       ]:
           assert term in docs
   ```

3. Run: `uvx pytest tests/cloudflare_terraform/ -q`
4. Expected: tests fail before implementation, pass after Tasks 1-8.

## Task 10: Terraform fmt / validate commands

**Files:**
- Modify: `infra/cloudflare/README.md`
- Test: manual command when Terraform CLI is available

1. README に以下の検証コマンドを明記する。

   ```bash
   terraform fmt -check -recursive infra/cloudflare
   terraform -chdir=infra/cloudflare init -backend=false
   terraform -chdir=infra/cloudflare validate
   ```

2. 実装環境に Terraform CLI がある場合は実行する。CLI がない場合は「未実行: terraform CLI not installed」と実装完了報告に明記する。

## Task 11: Verification

**Files:**
- All files above

1. Run static tests:

   ```bash
   uvx pytest tests/cloudflare_terraform/ tests/cloudflared/test_role.py
   ```

2. Run repository linters for touched YAML/docs if available:

   ```bash
   yamllint roles/cloudflared/ playbooks/22-cloudflare-tunnel.yml playbooks/23-cloudflare-smoke-test.yml
   ansible-lint roles/cloudflared playbooks/22-cloudflare-tunnel.yml playbooks/23-cloudflare-smoke-test.yml
   ```

3. Run Terraform checks if CLI exists:

   ```bash
   terraform fmt -check -recursive infra/cloudflare
   terraform -chdir=infra/cloudflare init -backend=false
   terraform -chdir=infra/cloudflare validate
   ```

4. Confirm AC mapping:

   | AC | Test |
   |----|------|
   | AC-1 | `test_provider_version_and_env_token_contract` |
   | AC-2 | `test_tfvars_example_is_domain_portable` |
   | AC-3 | `test_tunnel_is_cloudflare_managed_and_has_ingress_contract`, `test_dns_records_point_to_tunnel`, `test_access_resources_exist` |
   | AC-4 | `test_tunnel_is_cloudflare_managed_and_has_ingress_contract` |
   | AC-5 | `test_docs_cover_import_apply_state_and_ui_policy` |
   | AC-6 | `test_docs_cover_import_apply_state_and_ui_policy`, `test_gitignore_excludes_terraform_secrets_not_lockfile`, `test_outputs_mark_service_token_secret_sensitive` |
   | AC-7 | `test_gitignore_excludes_terraform_secrets_not_lockfile` |
   | AC-8 | `test_docs_cover_import_apply_state_and_ui_policy` |
   | AC-9 | `test_ansible_config_no_longer_contains_locally_managed_ingress` |
   | AC-10 | Task 10 commands |
   | AC-11 | `uvx pytest tests/cloudflare_terraform/` |
