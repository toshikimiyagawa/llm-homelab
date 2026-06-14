# Cloudflare WARP Private Network Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the public Cloudflare Access hostname path for `llm01` with Terraform-managed Cloudflare WARP private network routing while leaving Tailscale installed as a parallel fallback path.

**Architecture:** Reuse the existing Terraform-managed `llm01` Cloudflare Tunnel as the WARP private network connector. Add a tunnel route for `warp_private_network_cidr`, add a WARP enrollment Access application plus allow policy for `allowed_email`, add a custom device profile with Split Tunnel Include for the same CIDR, and remove Terraform resources that only served the old public hostname + Access path. Update tests and docs so WARP is the documented primary remote access path.

**Tech Stack:** Terraform `cloudflare/cloudflare` provider `~> 5.19`, pytest static contract tests, Markdown docs, existing SDD workflow.

---

## File Structure

- `tests/cloudflare_terraform/test_config.py` - primary static contract tests for Terraform resources, removed resources, docs, and secret hygiene.
- `infra/cloudflare/variables.tf` - add `warp_private_network_cidr`.
- `infra/cloudflare/terraform.tfvars.example` - add sample CIDR only.
- `infra/cloudflare/locals.tf` - remove public hostname/backend locals that are no longer used.
- `infra/cloudflare/tunnel.tf` - keep the tunnel and token data source, remove public hostname ingress, add private network route.
- `infra/cloudflare/access.tf` - replace public-hostname Access resources with WARP enrollment policy/application.
- `infra/cloudflare/dns.tf` - remove DNS CNAME resources for old public hostnames.
- `infra/cloudflare/outputs.tf` - remove hostnames, SSH CA, and service token outputs; keep tunnel outputs.
- `infra/cloudflare/README.md` - document WARP Terraform resources and enrollment/apply workflow.
- `docs/operations.md` - replace Cloudflare public Access operations with WARP private network operations and manual runtime verification.
- `docs/software-stack.md` - describe WARP as the primary remote access path and Tailscale as retained parallel path.
- `tests/cloudflared/test_role.py` - update assertions that currently expect old public hostnames to be absent in cloudflared config but may still hard-code them as a list.
- `.sdd/tasks.json` - SDD orchestration entry only; implementation agents update status after implementation.

## Implementation Approach

Use test-first static contract updates. The first task updates pytest expectations so the current repository fails because it still contains public Access resources and lacks WARP route/profile resources. Subsequent tasks update Terraform and docs until tests pass. Terraform validate is a required guard because the Cloudflare provider schema is the source of truth for WARP enrollment and device profile syntax.

The implementation must stop instead of redesigning if either of these conditions occurs:

- `terraform -chdir=infra/cloudflare validate` proves provider v5.19 cannot represent a private-routing-only tunnel config.
- `terraform -chdir=infra/cloudflare validate` proves provider v5.19 cannot represent WARP enrollment with `cloudflare_zero_trust_access_application` `type = "warp"`.

## Key Terraform Shape

Use the existing tunnel:

```hcl
resource "cloudflare_zero_trust_tunnel_cloudflared" "llm01" {
  account_id = var.cloudflare_account_id
  name       = var.host_id
  config_src = "cloudflare"
}
```

Add the route:

```hcl
resource "cloudflare_zero_trust_tunnel_cloudflared_route" "llm01_lan" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.llm01.id
  network    = var.warp_private_network_cidr
  comment    = "${var.host_id} LAN via WARP"
}
```

Add enrollment policy and WARP application:

```hcl
resource "cloudflare_zero_trust_access_policy" "warp_enrollment" {
  account_id = var.cloudflare_account_id
  name       = "${var.host_id}-warp-enrollment"
  decision   = "allow"

  include = [{
    email = {
      email = var.allowed_email
    }
  }]
}

resource "cloudflare_zero_trust_access_application" "warp_enrollment" {
  account_id           = var.cloudflare_account_id
  name                 = "${var.host_id}-warp-enrollment"
  type                 = "warp"
  app_launcher_visible = false
  policies = [{
    id         = cloudflare_zero_trust_access_policy.warp_enrollment.id
    precedence = 1
  }]
}
```

Add device profile, adjusting only if `terraform validate` requires a minor schema correction:

```hcl
resource "cloudflare_zero_trust_device_custom_profile" "llm01_warp" {
  account_id        = var.cloudflare_account_id
  name              = "${var.host_id}-warp-private-network"
  description       = "Route ${var.host_id} private network traffic through Cloudflare WARP."
  enabled           = true
  precedence        = 1
  match             = "identity.email == \"${var.allowed_email}\""
  allow_mode_switch = false
  allowed_to_leave  = false

  service_mode_v2 = {
    mode = "warp"
  }

  include = [{
    address     = var.warp_private_network_cidr
    description = "${var.host_id} private network"
  }]
}
```

## Verification Commands

```bash
uvx pytest tests/cloudflare_terraform/test_config.py tests/cloudflared/test_role.py -q
terraform fmt -check -recursive infra/cloudflare
terraform -chdir=infra/cloudflare init -backend=false
terraform -chdir=infra/cloudflare validate
yamllint infra/cloudflare/ docs/operations.md docs/software-stack.md
git status --short
```

Confirm no forbidden secret artifacts are staged or untracked:

```bash
git status --short
git diff --name-only --cached
```

Forbidden examples: `terraform.tfstate`, `terraform.tfstate.*`, `terraform.tfvars`, `*.tfplan`, decrypted SOPS files, Cloudflare API tokens, WARP device tokens.

## Risk And Rollback

- CIDR conflict risk is explicit because `192.168.0.0/17` can overlap with client-side LANs. Rollback is changing `warp_private_network_cidr` to a narrower route and re-applying Terraform.
- Removing old public Access resources removes Browser SSH and service token API paths. Rollback is a PR revert that restores `dns.tf`, the old Access resources, public hostname locals, and old docs.
- WARP device profile changes can take time to propagate to clients. Runtime docs must tell operators to allow propagation time before declaring failure.
- Terraform state remains secret. This plan does not introduce remote state or commit local state.

## Implementation Sequence

Follow `specs/issue-128-warp-private-network/tasks.md` exactly. Do not edit files under `specs/` during implementation. If a task reveals the frozen spec is wrong or insufficient, stop and mark `.sdd/tasks.json` blocked with a concrete reason.
