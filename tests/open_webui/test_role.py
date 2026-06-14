"""
Static configuration tests for the open_webui Ansible role.

Runtime acceptance criteria are verified by running the playbook against llm01.
These tests keep the repository contract for manifests, persistence, backends,
and documentation checkable without a live Kubernetes cluster.
"""
from pathlib import Path


ROOT = Path(__file__).parents[2]
ROLE_ROOT = ROOT / "roles" / "open_webui"
DEFAULTS = ROLE_ROOT / "defaults" / "main.yml"
TASKS = ROLE_ROOT / "tasks" / "main.yml"
DEPLOYMENT_TMPL = ROLE_ROOT / "templates" / "open-webui-deployment.yml.j2"
SERVICE_TMPL = ROLE_ROOT / "templates" / "open-webui-service.yml.j2"
INGRESS_TMPL = ROLE_ROOT / "templates" / "open-webui-ingress.yml.j2"
PLAYBOOK = ROOT / "playbooks" / "21-open-webui.yml"
SITE_YML = ROOT / "playbooks" / "site.yml"
SOFTWARE_DOC = ROOT / "docs" / "software-stack.md"
OPS_DOC = ROOT / "docs" / "operations.md"
GITIGNORE = ROOT / ".gitignore"


def test_playbook_exists():
    assert PLAYBOOK.exists()


def test_playbook_uses_open_webui_role():
    assert "open_webui" in PLAYBOOK.read_text()


def test_site_yml_imports_open_webui_after_ollama():
    content = SITE_YML.read_text()
    assert "20-ollama.yml" in content
    assert "21-open-webui.yml" in content
    assert content.index("20-ollama.yml") < content.index("21-open-webui.yml")


def test_defaults_define_persistence_and_backends():
    content = DEFAULTS.read_text()
    assert "/opt/open-webui-data" in content
    assert "https://vllm.solvelio.com/v1" in content
    assert "http://llm01:11434" in content


def test_tasks_create_data_directory_and_apply_manifests():
    content = TASKS.read_text()
    assert "open_webui_data_path" in content
    assert "k3s kubectl apply" in content
    assert "open_webui_app_name: open-webui" in DEFAULTS.read_text()
    assert "rollout status deployment/{{ open_webui_app_name }}" in content


def test_deployment_mounts_persistent_data_and_sets_backends():
    content = DEPLOYMENT_TMPL.read_text()
    assert "mountPath: /app/backend/data" in content
    assert "hostPath:" in content
    assert "OPENAI_API_BASE_URLS" in content
    assert "OLLAMA_BASE_URLS" in content


def test_service_exposes_port_80_to_8080():
    defaults = DEFAULTS.read_text()
    content = SERVICE_TMPL.read_text()
    assert "open_webui_service_port: 80" in defaults
    assert "open_webui_container_port: 8080" in defaults
    assert "port: {{ open_webui_service_port }}" in content
    assert "targetPort: {{ open_webui_container_port }}" in content


def test_ingress_uses_open_webui_domain_and_tls():
    content = INGRESS_TMPL.read_text()
    assert "open_webui_domain" in content
    assert "cert-manager.io/cluster-issuer: letsencrypt-prod" in content
    assert "open-webui-tls" in content


def test_software_stack_documents_open_webui():
    content = SOFTWARE_DOC.read_text()
    assert "Open WebUI" in content
    assert "http://<llm01-lan-ip>:8080" in content
    assert "Cloudflare WARP" in content
    assert "/opt/open-webui-data" in content


def test_gitignore_ignores_ds_store_and_worktrees():
    content = GITIGNORE.read_text()
    assert ".DS_Store" in content
    assert ".worktrees/" in content


def test_deployment_uses_host_network_for_loopback_ollama():
    defaults = DEFAULTS.read_text()
    content = DEPLOYMENT_TMPL.read_text()
    assert "open_webui_host_network: true" in defaults
    assert "open_webui_ollama_host_alias_ip: 127.0.0.1" in defaults
    assert "hostNetwork: {{ open_webui_host_network | bool | lower }}" in content
    assert "dnsPolicy: ClusterFirstWithHostNet" in content
    assert "hostAliases:" in content
    assert "- llm01" in content


def test_defaults_define_global_model_params_max_tokens():
    content = DEFAULTS.read_text()
    assert "open_webui_default_model_params" in content
    assert "max_tokens: 8192" in content


def test_deployment_exports_default_model_params_to_container():
    content = DEPLOYMENT_TMPL.read_text()
    assert "strategy:\n    type: Recreate" in content
    assert "DEFAULT_MODEL_PARAMS" in content
    assert "open_webui_default_model_params" in content


def test_docs_explain_long_conversation_limit_and_workaround():
    software = SOFTWARE_DOC.read_text()
    ops = OPS_DOC.read_text()
    assert "max_tokens" in software
    assert "40960" in software
    assert "vllm.exceptions.VLLMValidationError" in ops
    assert "max_tokens" in ops
    assert "長い会話" in ops or "長い会話" in software
