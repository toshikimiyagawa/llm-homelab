# Tasks: issue-20-open-webui

## Implementation Tasks

- [ ] T1: Add `.DS_Store` and `.worktrees/` to `.gitignore`. 対応AC: AC9
- [ ] T2: Create `roles/open_webui/defaults/main.yml` with namespace, image, domain, persistence path, service port, vLLM URL, Ollama URL, and resource defaults. 対応AC: AC2, AC6
- [ ] T3: Create Deployment template with persistent `/app/backend/data` mount and vLLM/Ollama environment variables. 対応AC: AC3, AC6, AC7
- [ ] T4: Create Service template exposing Open WebUI port 8080 as ClusterIP port 80. 対応AC: AC3
- [ ] T5: Create Ingress template for `open-webui.solvelio.com` with `letsencrypt-prod` TLS. 対応AC: AC3, AC5
- [ ] T6: Create `roles/open_webui/tasks/main.yml` to create namespace, data directory, apply manifests, wait for rollout, and verify pod phase. 対応AC: AC2, AC3, AC4
- [ ] T7: Add `playbooks/21-open-webui.yml` and include it from `playbooks/site.yml` after Ollama/vLLM dependencies. 対応AC: AC1
- [ ] T8: Document Open WebUI in `docs/software-stack.md`. 対応AC: AC8
- [ ] T9: Verify Ollama reachability from the Open WebUI pod; if `http://llm01:11434` is not reachable, STOP and report the required design decision instead of changing Ollama binding silently. 対応AC: AC6
- [ ] T10: Run targeted lint and implementation verification commands. 対応AC: AC1-AC10
- [ ] T11: Update `.sdd/tasks.json` with issue-20 status and run kanban display. 対応AC: process

## Tests

- [ ] AC1 -> `test -f playbooks/21-open-webui.yml` and inspect role invocation.
- [ ] AC2 -> `ssh llm01 "stat -c '%U:%G %a' /opt/open-webui-data"`.
- [ ] AC3 -> Run `ansible-playbook playbooks/21-open-webui.yml --vault-password-file ~/.vault_pass` twice and inspect changed summary.
- [ ] AC4 -> `ssh llm01 "sudo k3s kubectl -n open-webui get pod -l app=open-webui"` reports Running.
- [ ] AC5 -> `curl -kI https://open-webui.solvelio.com` returns HTTP success/redirect.
- [ ] AC6 -> Inspect Deployment env and confirm vLLM/Ollama models are visible from Open WebUI after deployment.
- [ ] AC7 -> Restart pod and confirm `/opt/open-webui-data` contents persist.
- [ ] AC8 -> `rg -n "Open WebUI|open-webui.solvelio.com|/opt/open-webui-data" docs/software-stack.md`.
- [ ] AC9 -> `git check-ignore -v vendor/.DS_Store .DS_Store .worktrees/example`.
- [ ] AC10 -> `yamllint -s` and `ansible-lint` for changed files.

## Definition of Done

- [ ] All AC tests pass or any blocker is documented and escalated.
- [ ] sdd-reviewer passes against the frozen spec.
- [ ] PR carries `sdd:tier-2` label and Japanese description.
