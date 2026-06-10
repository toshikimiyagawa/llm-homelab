# Handoff: issue-95 - Cloudflare DNS/Tunnel/Access Terraform 管理

## Status

- Tier: 2
- Phase: implement
- Spec status: frozen
- Issue: #95

## Required Reading

Implementation agents must read these files before editing code:

1. `AGENTS.md`
2. `vendor/ai-sdd-guide/rules/core.md`
3. `vendor/ai-sdd-guide/rules/workflow.md`
4. `vendor/ai-sdd-guide/orchestration/rules/orchestration.md`
5. `specs/issue-95-cloudflare-terraform/spec.md`
6. `specs/issue-95-cloudflare-terraform/plan.md`
7. `specs/issue-95-cloudflare-terraform/tasks.md`

## Implementation Contract

Implement exactly `specs/issue-95-cloudflare-terraform/tasks.md`.

Do not redesign during implementation. If Cloudflare provider v5 schema makes a required resource impossible as written, stop and report the blocker instead of changing the spec to fit the implementation.

## Scope Summary

Cloudflare-side DNS / Tunnel / Access state becomes Terraform-managed under `infra/cloudflare/`. Tunnel public hostname / ingress config moves to Terraform as the source of truth using a Cloudflare-managed tunnel config. Ansible remains responsible for `llm01` host provisioning: cloudflared package/service, credentials placement, SSH CA, and sshd hardening.

Terraform apply is not part of this implementation. The implementation must provide Terraform config, docs, import/apply procedures, static pytest coverage, and verification commands.

## Verification Required

Run these when implementation is complete:

```bash
uvx pytest tests/cloudflare_terraform/ tests/cloudflared/test_role.py
```

Run these if the tools are available:

```bash
yamllint roles/cloudflared/ playbooks/22-cloudflare-tunnel.yml playbooks/23-cloudflare-smoke-test.yml
ansible-lint roles/cloudflared playbooks/22-cloudflare-tunnel.yml playbooks/23-cloudflare-smoke-test.yml
terraform fmt -check -recursive infra/cloudflare
terraform -chdir=infra/cloudflare init -backend=false
terraform -chdir=infra/cloudflare validate
```

If Terraform CLI is unavailable, report that explicitly.

## Stop Conditions

Stop and ask the human if:

- Terraform provider v5 does not expose a way to manage Browser SSH without Cloudflare UI.
- Import/apply would require committing Terraform state, tfvars, API tokens, or Service Token secrets.
- A task requires changing #91 runtime behavior beyond Cloudflare-side management and the minimal Ansible config migration described in the frozen spec.
- Any acceptance criterion cannot be mapped to a passing test.
