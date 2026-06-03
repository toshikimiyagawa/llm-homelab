# Spec: issue-20-open-webui

## Intent

Open WebUI を k3s 上に Ansible で導入し、既存の vLLM/Qwen3-32B と Ollama をブラウザから利用できる主要 UI として提供する。

## Scope

### Include

- `open-webui` namespace の作成
- Open WebUI Deployment / Service / Ingress の Ansible 管理
- Open WebUI データ永続化用 hostPath `/opt/open-webui-data` の作成
- `https://open-webui.solvelio.com` での HTTPS アクセス
- vLLM OpenAI-compatible API (`https://vllm.solvelio.com/v1`) の初期接続設定
- Ollama API の初期接続設定
- `docs/software-stack.md` への Open WebUI 運用情報追記
- `.gitignore` に `.DS_Store` と `.worktrees/` を追加する既存ローカル変更の取り込み

### Exclude

- SearXNG / Web Search 連携
- Knowledge / RAG 用の vector DB や外部 document pipeline
- MCP / OpenAPI tools / pipelines の追加
- Open WebUI の外部 OAuth / SSO 連携
- vLLM / Ollama 自体の構成変更

## Design Decisions

| Item | Decision | Reason |
|------|----------|--------|
| Deployment method | Kubernetes manifests rendered by Ansible templates | Existing vLLM role uses this pattern; keeps repo conventions consistent |
| Namespace | `open-webui` | Isolates UI resources from inference backends |
| Image | `ghcr.io/open-webui/open-webui:main` | Official container image and common deployment path |
| Persistence | hostPath `/opt/open-webui-data` mounted at `/app/backend/data` | Keeps user/database state under `/opt` data disk and survives pod recreation |
| Exposure | Traefik Ingress + cert-manager TLS | Same pattern as vLLM/Grafana/Prometheus |
| Domain | `open-webui.solvelio.com` | Predictable service hostname under existing base domain |
| vLLM backend | OpenAI-compatible API base URL `https://vllm.solvelio.com/v1` | Matches current working external endpoint and avoids cluster DNS coupling |
| Ollama backend | `http://llm01:11434` if reachable from pod; otherwise STOP for a design decision | Ollama currently runs as host systemd service bound to 127.0.0.1, so reachability must be verified explicitly |
| Auth | Open WebUI built-in auth/signup defaults | Avoids adding SSO/secrets in this issue |

## Acceptance Criteria

1. `playbooks/21-open-webui.yml` exists and applies an `open_webui` role.
2. The role creates `/opt/open-webui-data` with stable ownership/mode before applying Kubernetes resources.
3. Open WebUI Deployment, Service, and Ingress manifests are rendered from templates and applied idempotently.
4. `k3s kubectl -n open-webui get pod -l app=open-webui` reports `Running`.
5. `https://open-webui.solvelio.com` returns an HTTP success response through Traefik TLS.
6. Open WebUI is configured with both backends: vLLM/Qwen via OpenAI-compatible API and Ollama via Ollama API.
7. Restarting the Open WebUI pod does not delete user/application state stored under `/opt/open-webui-data`.
8. `docs/software-stack.md` documents the Open WebUI URL, persistence path, and backend connections.
9. `.gitignore` ignores `.DS_Store` at any path and `.worktrees/`.
10. Targeted `yamllint` and `ansible-lint` checks for changed files pass, or failures are documented as pre-existing unrelated debt.

## Test Mapping

| AC | Verification |
|----|--------------|
| AC1 | `test -f playbooks/21-open-webui.yml` and role invocation inspection |
| AC2 | `ssh llm01 "stat -c '%U:%G %a' /opt/open-webui-data"` |
| AC3 | first and second `ansible-playbook playbooks/21-open-webui.yml --vault-password-file ~/.vault_pass`; second run should not report unnecessary manifest changes |
| AC4 | `ssh llm01 "sudo k3s kubectl -n open-webui get pod -l app=open-webui"` |
| AC5 | `curl -kI https://open-webui.solvelio.com` from an environment with Tailscale/DNS access |
| AC6 | inspect Deployment env and verify UI/API model list after deployment |
| AC7 | create a marker file or inspect persistent database path before/after pod restart |
| AC8 | `rg -n "Open WebUI|open-webui.solvelio.com|/opt/open-webui-data" docs/software-stack.md` |
| AC9 | `git check-ignore -v vendor/.DS_Store .DS_Store .worktrees/example` |
| AC10 | `yamllint -s` and `ansible-lint` on changed role/playbook |
