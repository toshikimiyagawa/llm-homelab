# Handoff: issue-128-warp-private-network

## Your scope

Implementation phase only. Do not touch `spec.md`, `plan.md`, or the verify phase.
If the spec needs changes, stop and escalate to a human.

## Done when

- [ ] All tasks in `specs/issue-128-warp-private-network/tasks.md` are complete
- [ ] Every acceptance criterion in `specs/issue-128-warp-private-network/spec.md` has a passing test or documented manual runtime check
- [ ] Test suite passes
- [ ] Terraform formatting and validation pass
- [ ] No secret artifacts are staged or untracked
- [ ] `.sdd/tasks.json` entry for `issue-128-warp-private-network` is completed

## Reference files

- spec:  `specs/issue-128-warp-private-network/spec.md`
- plan:  `specs/issue-128-warp-private-network/plan.md`
- tasks: `specs/issue-128-warp-private-network/tasks.md`

## If the spec is ambiguous or insufficient

1. Stop immediately.
2. Set `.sdd/tasks.json` status to `"blocked"`.
3. Fill in `blocked_reason`.
4. Wait for a human to escalate before resuming.

## Important constraints

- Do not modify files under `specs/` during implementation.
- Do not redesign WARP scope, Tailscale scope, or CIDR scope during implementation.
- Do not commit `terraform.tfstate`, `terraform.tfvars`, `*.tfplan`, decrypted SOPS files, Cloudflare API tokens, WARP device tokens, or private keys.
- If Terraform provider v5.19 cannot express WARP enrollment or private-routing-only tunnel config, stop and mark the task blocked.
