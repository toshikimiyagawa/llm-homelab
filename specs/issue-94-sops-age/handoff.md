# Handoff: issue-94-sops-age-inrepo

## Status

- Tier: 2
- Phase: verify
- Spec status: frozen
- Issue: #94

## Required Reading

Implementation agents must read these files before editing code:

1. `AGENTS.md`
2. `vendor/ai-sdd-guide/rules/core.md`
3. `vendor/ai-sdd-guide/rules/workflow.md`
4. `vendor/ai-sdd-guide/orchestration/rules/orchestration.md`
5. `specs/issue-94-sops-age/spec.md`
6. `specs/issue-94-sops-age/plan.md`
7. `specs/issue-94-sops-age/tasks.md`

## Implementation Contract

Implement exactly `specs/issue-94-sops-age/tasks.md`.

Do not redesign during implementation. If the Tailscale role or docs require a broader secret migration than the frozen spec allows, stop and report the blocker instead of expanding scope.

## Scope Summary

`playbooks/07-tailscale.yml` loads `tailscale_auth_key` from `secrets/infra.sops.yml` using `community.sops.load_vars`, and the docs / static tests describe `secrets/infra.sops.yml` as the source of truth for in-repo secrets. `roles/tailscale` continues to consume `tailscale_auth_key` normally. External API keys / PATs are excluded and tracked in #102.

## Verification Required

Run these when implementation is complete:

```bash
uvx pytest tests/secrets/test_sops_policy.py
yamllint docs/security-and-secrets.md docs/software-stack.md secrets/README.md playbooks/07-tailscale.yml roles/tailscale/tasks/main.yml
ansible-lint playbooks/07-tailscale.yml roles/tailscale
```

## Stop Conditions

Stop and ask the human if:

- A task would require modifying `spec.md`, `plan.md`, or `tasks.md` to fit implementation.
- Any acceptance criterion cannot be mapped to a passing test.
- The Tailscale auth key can no longer be sourced from `secrets/infra.sops.yml` without broadening scope beyond #94.
