# issue-20-open-webui Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy Open WebUI on k3s with persistent state and connect it to both vLLM/Qwen3-32B and Ollama.

**Architecture:** Add a new Ansible role `open_webui` following the existing `vllm` manifest-template pattern. The role creates a hostPath data directory, renders Deployment/Service/Ingress manifests to `/tmp`, applies them with `k3s kubectl apply`, waits for rollout, and verifies the web endpoint and backend configuration.

**Tech Stack:** Ansible, k3s kubectl, Kubernetes Deployment/Service/Ingress, Traefik, cert-manager, Open WebUI container image, vLLM OpenAI-compatible API, Ollama API.

---

## Files

| Path | Action | Purpose |
|------|--------|---------|
| `.gitignore` | Modify | Ignore `.DS_Store` globally and `.worktrees/` |
| `roles/open_webui/defaults/main.yml` | Create | Open WebUI variables |
| `roles/open_webui/tasks/main.yml` | Create | Directory setup, manifest apply, rollout, verification |
| `roles/open_webui/templates/open-webui-deployment.yml.j2` | Create | Deployment with env and persistent volume mount |
| `roles/open_webui/templates/open-webui-service.yml.j2` | Create | ClusterIP Service |
| `roles/open_webui/templates/open-webui-ingress.yml.j2` | Create | Traefik Ingress + TLS |
| `playbooks/21-open-webui.yml` | Create | Role entrypoint |
| `playbooks/site.yml` | Modify | Include Open WebUI in site run after Ollama/vLLM dependencies |
| `docs/software-stack.md` | Modify | Document URL, persistence, backends |
| `.sdd/tasks.json` | Modify | Track issue-20 implementation status |

## Key Implementation Notes

- Use `open_webui` as Ansible role name to satisfy ansible-lint role variable prefix expectations.
- Use Kubernetes resource name `open-webui` to match project naming style.
- Start with one replica because SQLite/default local state is mounted on a single hostPath.
- Configure vLLM through OpenAI-compatible env variables.
- Configure Ollama only after confirming pod reachability to the host service. If `http://llm01:11434` is not reachable from a pod, STOP and report the required design decision instead of changing Ollama binding silently.
- Do not add Web Search, RAG, tools, MCP, or SSO in this issue.
