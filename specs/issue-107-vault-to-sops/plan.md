# issue-107 Vault-to-SOPS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the remaining Ansible Vault inventory dependency so normal Ansible inventory loading no longer requires a vault password file.

**Architecture:** Keep non-secret inventory in `inventory/group_vars/all/vars.yml` and keep Git-managed operational secrets in `secrets/infra.sops.yml`. Remove `inventory/group_vars/all/vault.yml` from the runtime inventory path, update current operations docs away from `--vault-password-file`, and add static tests that prevent encrypted Ansible Vault files from returning under `inventory/`.

**Tech Stack:** Ansible, SOPS + age, `community.sops`, pytest static contract tests, yamllint.

---

## Affected Files

| File | Change |
|------|--------|
| `inventory/group_vars/all/vault.yml` | Delete the legacy Ansible Vault file from the repository. |
| `tests/secrets/test_sops_policy.py` | Add tests that inventory has no Ansible Vault encrypted file, current docs do not require `--vault-password-file`, and SOPS playbook contracts remain intact. |
| `docs/security-and-secrets.md` | Clarify that Ansible Vault is no longer part of normal in-repo secret handling. |
| `docs/software-stack.md` | Remove current runbook commands that still require `--vault-password-file ~/.vault_pass`. |
| `secrets/README.md` | Clarify that SOPS is the normal in-repo secret source and Ansible Vault files must not be added under inventory. |
| `.sdd/tasks.json` | Mark #107 completed after implementation. |

Historical files under `specs/issue-*` are not modified. They describe previous decisions and are not current operational runbooks.

## Approach

The implementation should treat the existing encrypted `inventory/group_vars/all/vault.yml` as a legacy artifact that is no longer a runtime dependency. Do not try to decrypt it and do not move unknown values from it into SOPS. The runtime code already reads the known in-repo operational secrets from `secrets/infra.sops.yml`, so the safe change is to remove the file that forces Ansible Vault decryption during inventory load.

The tests should prove the behavior that matters:

- no committed file under `inventory/` starts with `$ANSIBLE_VAULT`
- current docs no longer tell operators to pass `--vault-password-file ~/.vault_pass`
- `ansible-inventory --list` can run without a vault password file
- existing SOPS playbooks still load `secrets/infra.sops.yml`

## Acceptance Criteria Mapping

| AC | Proof |
|----|-------|
| AC-1 | `git ls-files inventory/group_vars/all/vault.yml` returns no tracked file; static test checks no Ansible Vault file under `inventory/`. |
| AC-2 | `ansible-inventory --list` succeeds without `--vault-password-file`. |
| AC-3 | `test_current_docs_do_not_require_ansible_vault_password_file` checks current docs. |
| AC-4 | existing and updated SOPS docs tests check `docs/security-and-secrets.md` and `secrets/README.md`. |
| AC-5 | `test_inventory_has_no_ansible_vault_encrypted_files`. |
| AC-6 | existing playbook SOPS tests remain and continue passing. |
| AC-7 | existing forbidden secret file guard remains and is extended to catch inventory Vault files. |

## Verification Commands

Run these from the repository root:

```bash
uvx pytest tests/secrets/test_sops_policy.py -q
yamllint docs/security-and-secrets.md docs/software-stack.md secrets/README.md playbooks/07-tailscale.yml playbooks/08-prometheus.yml playbooks/22-cloudflare-tunnel.yml
ansible-inventory --list
git diff --check
```

`ansible-inventory --list` must be run without `--vault-password-file`.

## Tradeoffs

Deleting the legacy Vault file means this issue does not preserve unknown encrypted values that may still be inside it. That is deliberate: this environment cannot decrypt the file, current runtime consumers already use SOPS, and guessing secret contents would be unsafe. If a removed value is later discovered to matter, it should be added through SOPS under a separate scoped issue, usually #102 for external API keys / PATs.
