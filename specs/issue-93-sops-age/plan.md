# issue-93-sops-age Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move Cloudflare-related infrastructure secrets from ad-hoc Ansible Vault naming toward SOPS+age, with Ansible reading encrypted variables through `community.sops`.

**Architecture:** Add SOPS policy files and docs, then load `secrets/infra.sops.yml` in the playbooks that need Cloudflare secrets. Keep roles focused: roles consume ordinary variables, while playbooks load and cache decrypted values with `no_log: true`.

**Tech Stack:** Ansible, `community.sops`, SOPS, age, pytest static contract tests, yamllint, ansible-lint.

---

## File Structure

| Path | Responsibility |
|------|----------------|
| `.sops.yaml` | SOPS creation rules for `secrets/*.sops.yml` using the local age recipient. |
| `secrets/README.md` | Operator documentation for age keys, 1Password backup, SOPS editing, and temporary Cloudflare token handling. |
| `secrets/infra.sops.yml` | Encrypted SOPS file containing `cloudflare_dns01_api_token` and `cloudflared_tunnel_credentials`. |
| `requirements.yml` | Adds `community.sops` collection dependency. |
| `docs/security-and-secrets.md` | Updates project secret-management policy from 1Password/Vault split to SOPS+age centered model. |
| `docs/operations.md` | Updates Cloudflare Tunnel setup instructions to place credentials in SOPS instead of Ansible Vault. |
| `roles/prometheus/templates/cluster-issuer.yml.j2` | Reads `cloudflare_dns01_api_token` instead of `cloudflare_api_token`. |
| `playbooks/08-prometheus.yml` | Loads SOPS secrets with `community.sops.load_vars` and caches `cloudflare_dns01_api_token` under `no_log`. |
| `playbooks/22-cloudflare-tunnel.yml` | Loads SOPS secrets and maps `cloudflared_tunnel_credentials` into the existing role variable expected by `roles/cloudflared`. |
| `tests/secrets/test_sops_policy.py` | Static tests mapping the spec acceptance criteria to checkable repository contracts. |
| `tests/cloudflared/test_role.py` | Updates existing cloudflared expectation from Vault variable naming to SOPS variable naming. |

## Approach

Use `community.sops.load_vars` in playbook `pre_tasks` rather than a SOPS vars plugin. The official Ansible docs describe `community.sops.load_vars` as loading SOPS-encrypted YAML/JSON variables dynamically during task runtime, with `sops` required on the executing host. This keeps decrypted values in Ansible memory and avoids creating a plaintext temporary vars file.

Roles should remain unaware of SOPS. `roles/prometheus` receives `cloudflare_dns01_api_token`; `roles/cloudflared` can keep its existing internal variable name for the copy task if the playbook maps `cloudflared_tunnel_credentials` to `vault_cloudflared_tunnel_credentials` under `no_log`. This preserves scope and reduces role churn while moving the secret source to SOPS.

The implementation must not commit real secret plaintext. If a real age recipient is unavailable, stop and ask for it. Do not create sample encrypted material that cannot be decrypted by the operator.

## Tradeoffs

- `community.sops.load_vars` over `sops -d -e @file`: avoids plaintext temporary files and fits Ansible execution better.
- SOPS over Ansible Vault for Cloudflare secrets: lowers 1Password product dependence and makes encrypted Git-managed secrets the normal path.
- Keep `vault_cloudflared_tunnel_credentials` as a role input alias for now: avoids broad changes to the frozen Cloudflare role behavior while documenting that SOPS is the source.

## Verification

- `uvx pytest tests/secrets/test_sops_policy.py tests/cloudflared/test_role.py`
- `yamllint .sops.yaml secrets/ docs/security-and-secrets.md docs/operations.md playbooks/08-prometheus.yml playbooks/22-cloudflare-tunnel.yml`
- `ansible-lint playbooks/08-prometheus.yml playbooks/22-cloudflare-tunnel.yml roles/prometheus roles/cloudflared`

## Acceptance Criteria Mapping

| AC | Implementation / Test |
|----|------------------------|
| AC-1 docs policy | `docs/security-and-secrets.md`; `test_security_docs_describe_sops_age_policy` |
| AC-2 `.sops.yaml` | `.sops.yaml`; `test_sops_yaml_targets_secret_files` |
| AC-3 `secrets/README.md` | `secrets/README.md`; `test_secrets_readme_documents_key_handling` |
| AC-4 `community.sops` dependency | `requirements.yml`; `test_requirements_include_community_sops` |
| AC-5 DNS01 variable rename | `cluster-issuer.yml.j2`; `test_prometheus_uses_dns01_token_name` |
| AC-6 tunnel credentials from SOPS | `playbooks/22-cloudflare-tunnel.yml`; `test_cloudflared_playbook_loads_sops_credentials` |
| AC-7 guard/test for plaintext/key files | `tests/secrets/test_sops_policy.py`; `test_no_forbidden_secret_files_are_committed` |
| AC-8 migration/rotation docs | `docs/security-and-secrets.md`, `docs/operations.md`; `test_docs_describe_vault_migration_and_rotation` |
| AC-9 lint/tests | Verification commands above |
