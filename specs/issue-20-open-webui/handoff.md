# Handoff: issue-20-open-webui

## Status

Design/tasks complete. Awaiting explicit implementation instruction.

## Scope

Deploy Open WebUI on k3s with persistent storage and connect it to both vLLM/Qwen3-32B and Ollama. Do not add RAG/Web Search/MCP/SSO in this issue.

## Files To Use

- `specs/issue-20-open-webui/spec.md`
- `specs/issue-20-open-webui/plan.md`
- `specs/issue-20-open-webui/tasks.md`

## Critical Note

Ollama currently runs as a host systemd service. Implementation must verify pod reachability to Ollama. If `http://llm01:11434` is not reachable from the Open WebUI pod, STOP and ask for a design decision rather than silently changing Ollama binding.
