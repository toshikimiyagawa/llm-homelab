# Handoff: issue-93-sops-age

## Your scope

Implementation phase only. Implement exactly `specs/issue-93-sops-age/tasks.md`.
Do not modify `spec.md`, `plan.md`, or `tasks.md` to fit implementation.

## Done when

- [ ] All tasks in `specs/issue-93-sops-age/tasks.md` are complete
- [ ] Every acceptance criterion in `specs/issue-93-sops-age/spec.md` has a passing test
- [ ] `uvx pytest tests/secrets/test_sops_policy.py tests/cloudflared/test_role.py` passes
- [ ] `yamllint .sops.yaml secrets/ docs/security-and-secrets.md docs/operations.md playbooks/08-prometheus.yml playbooks/22-cloudflare-tunnel.yml` passes
- [ ] `ansible-lint playbooks/08-prometheus.yml playbooks/22-cloudflare-tunnel.yml roles/prometheus roles/cloudflared` passes or any pre-existing unrelated failures are documented

## Reference files

- spec: `specs/issue-93-sops-age/spec.md`
- plan: `specs/issue-93-sops-age/plan.md`
- tasks: `specs/issue-93-sops-age/tasks.md`

## Critical notes

- Do not commit age private keys, plaintext secret files, decrypted SOPS output, or real secret plaintext.
- If a usable age public recipient is unavailable, stop and ask the human. Do not create fake encrypted material.
- Ansible must use `community.sops.load_vars`; do not implement the `sops -d > /tmp/file` approach.
- Broad Cloudflare setup tokens remain environment-only and must not be saved in SOPS, Vault, or the repository.

## If the spec is ambiguous or insufficient

1. Stop immediately.
2. Set `.sdd/tasks.json` status to `"blocked"`.
3. Fill in `blocked_reason`.
4. Wait for a human decision before resuming.
