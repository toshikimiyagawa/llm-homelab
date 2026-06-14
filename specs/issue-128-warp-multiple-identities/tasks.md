# Tasks: issue-128 - Multiple WARP enrollment identities

> 実装 agent は `spec.md` を読み、この tasks を過不足なく実装する。`specs/` 配下は実装中に変更しない。

## Task 1: Terraform tests を複数 email 対応に更新する

**Files**

- Modify: `tests/cloudflare_terraform/test_config.py`

**Steps**

- [ ] Add assertions that `allowed_emails` exists in `variables.tf` and `terraform.tfvars.example`.
- [ ] Add assertions that Terraform builds `local.allowed_warp_emails` from both `var.allowed_email` and `var.allowed_emails`.
- [ ] Add assertions that WARP enrollment policy uses dynamic include over `local.allowed_warp_emails`.
- [ ] Add assertions that WARP device profile match uses `local.allowed_warp_email_match`.
- [ ] Add assertions that real user emails are not present in tracked Terraform files.
- [ ] Run `uvx pytest tests/cloudflare_terraform/test_config.py -q`.

**Acceptance Criteria**

- AC-1
- AC-2
- AC-3
- AC-4

## Task 2: Terraform を複数 email 対応にする

**Files**

- Modify: `infra/cloudflare/variables.tf`
- Modify: `infra/cloudflare/locals.tf`
- Modify: `infra/cloudflare/access.tf`
- Modify: `infra/cloudflare/terraform.tfvars.example`

**Steps**

- [ ] Add `allowed_emails` as `list(string)` with default `[]`.
- [ ] Add sample `allowed_emails` to `terraform.tfvars.example`.
- [ ] Add locals:
  - `allowed_warp_emails = distinct(concat([var.allowed_email], var.allowed_emails))`
  - `allowed_warp_email_match = join(" ", [for email in local.allowed_warp_emails : "\"${email}\""])`
- [ ] Change WARP enrollment policy to generate one `include` block per `local.allowed_warp_emails`.
- [ ] Change WARP device profile `match` to `identity.email in {${local.allowed_warp_email_match}}`.
- [ ] Run `terraform fmt -recursive infra/cloudflare`.
- [ ] Run `uvx pytest tests/cloudflare_terraform/test_config.py tests/cloudflared/test_role.py -q`.
- [ ] Run `terraform -chdir=infra/cloudflare validate`.

**Acceptance Criteria**

- AC-1
- AC-2
- AC-3
- AC-5

## Task 3: local tfvars を実環境 email で更新して apply する

**Files**

- Modify untracked/ignored: `infra/cloudflare/terraform.tfvars`

**Steps**

- [ ] Add the exact user emails to local `allowed_emails`.
- [ ] Run `terraform -chdir=infra/cloudflare plan -var 'warp_private_network_cidr=192.168.0.0/17'`.
- [ ] Confirm the plan only updates WARP enrollment policy and device profile identity conditions.
- [ ] Run `terraform -chdir=infra/cloudflare apply -var 'warp_private_network_cidr=192.168.0.0/17'`.
- [ ] Confirm the follow-up plan has no changes.
- [ ] Check Cloudflare Access logs after the user retries enrollment.

**Acceptance Criteria**

- AC-4
- AC-6

