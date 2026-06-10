# Cloudflare Terraform

This directory manages Cloudflare-side DNS, Tunnel, and Access resources for `llm01`.
Terraform is the source of truth for Cloudflare resources after import/apply. Do not
change these resources in the Cloudflare UI after Terraform takes ownership.

## Managed Resources

- Cloudflare Tunnel: `cloudflare_zero_trust_tunnel_cloudflared.llm01`
- Cloudflare-managed Tunnel ingress config: `cloudflare_zero_trust_tunnel_cloudflared_config.llm01`
- DNS CNAME records for `open-webui`, `ssh`, `vllm`, and `ollama`
- Access applications for `open-webui`, `ssh`, `vllm`, and `ollama`
- Access policies for Google login and Service Auth
- Access Service Token for API clients

The Cloudflare account, zone, domain, and existing Google IdP are prerequisites.
They are not created here.

## State And Secrets

Terraform uses local state in this repository working tree. Treat
`terraform.tfstate` as a secret because it can contain Cloudflare Tunnel and
Access Service Token material.

Do not commit:

- `terraform.tfstate`
- `terraform.tfstate.backup`
- `.terraform/`
- `terraform.tfvars`
- `*.auto.tfvars`
- `*.tfplan`

Keep `.terraform.lock.hcl` committed after the first successful `terraform init`
so provider versions remain reproducible.

Pass the provider token through the environment:

```bash
export CLOUDFLARE_API_TOKEN="<temporary-token>"
```

Use the narrowest permissions possible. If you use a broad token for import or
bootstrap, revoke it or reduce permissions immediately after the work.

## Configure Variables

Create a local tfvars file:

```bash
cp infra/cloudflare/terraform.tfvars.example infra/cloudflare/terraform.tfvars
```

Edit `infra/cloudflare/terraform.tfvars`:

```hcl
cloudflare_account_id = "..."
cloudflare_zone_id    = "..."
domain                = "solvelio.com"
host_id               = "llm01"
allowed_email         = "user@example.com"
access_team_name      = "example-team"
```

For another domain, change `domain`, `host_id`, account, zone, and email values.

## Initialize

```bash
terraform -chdir=infra/cloudflare init
```

## Import Existing Resources

If Cloudflare resources already exist, import them before applying. Replace the
placeholder IDs with real Cloudflare IDs from API/CLI output or the dashboard in
read-only mode.

```bash
terraform -chdir=infra/cloudflare import cloudflare_zero_trust_tunnel_cloudflared.llm01 <account_id>/<tunnel_id>
terraform -chdir=infra/cloudflare import cloudflare_zero_trust_tunnel_cloudflared_config.llm01 <account_id>/<tunnel_id>

terraform -chdir=infra/cloudflare import 'cloudflare_dns_record.tunnel["open_webui"]' <zone_id>/<record_id>
terraform -chdir=infra/cloudflare import 'cloudflare_dns_record.tunnel["ssh"]' <zone_id>/<record_id>
terraform -chdir=infra/cloudflare import 'cloudflare_dns_record.tunnel["vllm"]' <zone_id>/<record_id>
terraform -chdir=infra/cloudflare import 'cloudflare_dns_record.tunnel["ollama"]' <zone_id>/<record_id>

terraform -chdir=infra/cloudflare import cloudflare_zero_trust_access_application.open_webui <account_id>/<application_id>
terraform -chdir=infra/cloudflare import cloudflare_zero_trust_access_application.ssh <account_id>/<application_id>
terraform -chdir=infra/cloudflare import cloudflare_zero_trust_access_application.vllm <account_id>/<application_id>
terraform -chdir=infra/cloudflare import cloudflare_zero_trust_access_application.ollama <account_id>/<application_id>

terraform -chdir=infra/cloudflare import cloudflare_zero_trust_access_service_token.api_clients <account_id>/<service_token_id>
```

Access policies are managed inline in each `cloudflare_zero_trust_access_application`
resource. After importing an application, run `terraform plan` and compare the
inline `policies` diff before applying.

After each import batch, inspect state:

```bash
terraform -chdir=infra/cloudflare state show cloudflare_zero_trust_tunnel_cloudflared.llm01
```

## Plan And Apply

For existing environments:

```bash
terraform -chdir=infra/cloudflare plan
```

If the plan shows unexpected destroy or replacement, stop and do not run
`terraform apply`. Fix the import/config mismatch first.

For new environments, or after imports are clean:

```bash
terraform -chdir=infra/cloudflare apply
```

## Verification

```bash
terraform fmt -check -recursive infra/cloudflare
terraform -chdir=infra/cloudflare init -backend=false
terraform -chdir=infra/cloudflare validate
```

## UI Policy

After import/apply, the Cloudflare UI is read-only for these resources. Make
changes through Terraform PRs only. If the account supports it, enable Cloudflare
Zero Trust dashboard read-only access for human users to prevent drift.
