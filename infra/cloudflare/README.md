# Cloudflare Terraform

This directory manages Cloudflare-side Tunnel and Cloudflare WARP private
network resources for `llm01`. Terraform is the source of truth for Cloudflare
resources after import/apply. Do not change these resources in the Cloudflare UI
after Terraform takes ownership.

## Managed Resources

- Cloudflare Tunnel: `cloudflare_zero_trust_tunnel_cloudflared.llm01`
- Cloudflare Tunnel token data source and sensitive `tunnel_token` output
- WARP private network route: `cloudflare_zero_trust_tunnel_cloudflared_route.llm01_lan`
- WARP device enrollment policy/application for `allowed_email`
- WARP device custom profile with Split Tunnel Include for `warp_private_network_cidr`

The Cloudflare account, Zero Trust team, and existing Google IdP are
prerequisites. They are not created here.

## State And Secrets

Terraform uses local state in this repository working tree. Treat
`terraform.tfstate` as a secret because it can contain Cloudflare Tunnel token
material and Cloudflare resource IDs.

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
cloudflare_account_id     = "..."
cloudflare_zone_id        = "..."
domain                    = "solvelio.com"
host_id                   = "llm01"
allowed_email             = "user@example.com"
access_team_name          = "example-team"
warp_private_network_cidr = "192.168.1.0/24"
```

For the `llm01` home LAN, the intended local value is:

```hcl
warp_private_network_cidr = "192.168.0.0/17"
```

That CIDR is intentionally kept in local `terraform.tfvars`, which is ignored by
git. If the WARP client is used from another network that overlaps this CIDR,
routes can conflict. In that case, narrow `warp_private_network_cidr` and apply
again.

## Initialize

```bash
terraform -chdir=infra/cloudflare init
```

## Import Existing Tunnel Resources

If the Cloudflare Tunnel already exists, use `terraform import` before applying.
Replace the placeholder IDs with real Cloudflare IDs from API/CLI output or the
dashboard in read-only mode.

```bash
terraform -chdir=infra/cloudflare import cloudflare_zero_trust_tunnel_cloudflared.llm01 <account_id>/<tunnel_id>
terraform -chdir=infra/cloudflare import cloudflare_zero_trust_tunnel_cloudflared_config.llm01 <account_id>/<tunnel_id>
```

After each import batch, inspect state:

```bash
terraform -chdir=infra/cloudflare state show cloudflare_zero_trust_tunnel_cloudflared.llm01
```

## Plan And Apply

For existing environments:

```bash
terraform -chdir=infra/cloudflare plan
```

Expected destructive changes are limited to the old public hostname Access path
when migrating from the previous configuration. If the plan shows unexpected
destroy or replacement outside that scope, stop and do not run `terraform apply`.
Fix the import/config mismatch first.

For new environments, or after imports are clean, use `terraform apply`:

```bash
terraform -chdir=infra/cloudflare apply
```

Device enrollment and device profile updates can take several minutes to
propagate to Cloudflare One client devices.

## WARP Client Verification

After apply, enroll a device with the Cloudflare One client using the
`allowed_email` identity and the Zero Trust team name. Verify the profile and
Split Tunnel configuration from the client:

```bash
warp-cli status
warp-cli settings
```

The client settings should show the WARP profile and a Split Tunnel Include for
`warp_private_network_cidr`.

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
