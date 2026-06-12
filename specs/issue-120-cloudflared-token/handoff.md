# Handoff: issue-120-cloudflared-token

## Your scope

Implementation phase only. Do not touch `spec.md`, `plan.md`, or the verify phase.
If the spec needs changes, stop and escalate to a human.

## Done when

- [ ] All tasks in `specs/issue-120-cloudflared-token/tasks.md` are complete
- [ ] Every acceptance criterion in `specs/issue-120-cloudflared-token/spec.md` has a passing test
- [ ] Test suite and lint commands in Task 7 pass, or any blocker is documented
- [ ] `.sdd/state.json` is moved to verify phase
- [ ] `.sdd/tasks.json` entry for `issue-120-cloudflared-token` is completed

## Reference files

- spec:  `specs/issue-120-cloudflared-token/spec.md`
- plan:  `specs/issue-120-cloudflared-token/plan.md`
- tasks: `specs/issue-120-cloudflared-token/tasks.md`

## Context

#95 moved Cloudflare Tunnel / DNS / Access to Terraform with `config_src = "cloudflare"`.
The current Ansible role still expects locally-managed credentials JSON. This issue
migrates the host-side connector to a Terraform-managed tunnel token flow.

## If the spec is ambiguous or insufficient

1. Stop immediately.
2. Set `.sdd/tasks.json` status to `"blocked"`.
3. Fill in `blocked_reason`.
4. Wait for a human before resuming.
