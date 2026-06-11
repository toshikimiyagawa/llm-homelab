# Handoff: issue-107-vault-to-sops

## Status

- Tier: 2
- Phase: implement
- Spec status: frozen
- Issue: #107

## Required Reading

Implementation agents must read these files before editing code:

1. `AGENTS.md`
2. `vendor/ai-sdd-guide/rules/core.md`
3. `vendor/ai-sdd-guide/rules/workflow.md`
4. `vendor/ai-sdd-guide/orchestration/rules/orchestration.md`
5. `specs/issue-107-vault-to-sops/spec.md`
6. `specs/issue-107-vault-to-sops/plan.md`
7. `specs/issue-107-vault-to-sops/tasks.md`

## Implementation Contract

Implement exactly `specs/issue-107-vault-to-sops/tasks.md`.

Do not decrypt `inventory/group_vars/all/vault.yml`. Do not migrate unknown secret values. If implementation discovers a current runtime consumer that still depends on a value only available from Ansible Vault, stop and report the blocker instead of expanding scope.

## Scope Summary

Remove the legacy Ansible Vault inventory dependency by deleting `inventory/group_vars/all/vault.yml`, updating current docs away from `--vault-password-file`, and adding static tests that keep in-repo operational secrets on SOPS+age.

Historical specs under `specs/issue-*` are not part of the current operational docs and should not be rewritten for this issue.

## Verification Required

Run these when implementation is complete:

```bash
uvx pytest tests/secrets/test_sops_policy.py -q
yamllint docs/security-and-secrets.md docs/software-stack.md secrets/README.md playbooks/07-tailscale.yml playbooks/08-prometheus.yml playbooks/22-cloudflare-tunnel.yml
ansible-inventory --list
git diff --check
```

`ansible-inventory --list` must be run without `--vault-password-file`.

## Stop Conditions

Stop and ask the human if:

- A task would require modifying `spec.md`, `plan.md`, or `tasks.md` to fit implementation.
- Any acceptance criterion cannot be mapped to a passing test.
- A current runtime consumer still needs a secret that is only present in the deleted Ansible Vault file.
- Any step would require committing plaintext secrets, an age private key, or decrypted SOPS output.
