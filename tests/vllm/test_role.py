"""
Static configuration tests for the vllm Ansible role.

Runtime acceptance criteria are verified by running the playbook against llm01.
These tests keep rollout and OpenAI-compatible server options checkable without
a live Kubernetes cluster.
"""
from pathlib import Path


ROLE_ROOT = Path(__file__).parents[2] / "roles" / "vllm"
DEPLOYMENT_TMPL = ROLE_ROOT / "templates" / "vllm-deployment.yml.j2"
TASKS = ROLE_ROOT / "tasks" / "main.yml"


def test_deployment_uses_recreate_strategy_for_fixed_gpu():
    content = DEPLOYMENT_TMPL.read_text()
    assert "strategy:" in content
    assert "type: Recreate" in content


def test_deployment_enables_tool_call_options():
    content = DEPLOYMENT_TMPL.read_text()
    assert '"--enable-auto-tool-choice"' in content
    assert '"--tool-call-parser"' in content
    assert '"hermes"' in content


def test_deployment_sets_max_model_len():
    content = DEPLOYMENT_TMPL.read_text()
    assert '"--max-model-len"' in content
    assert "vllm_max_model_len" in content


def test_default_max_model_len_is_81920():
    content = (ROLE_ROOT / "defaults" / "main.yml").read_text()
    assert "vllm_max_model_len: 81920" in content


def test_api_verification_uses_service_endpoint_not_pod_tools():
    content = TASKS.read_text()
    assert "curl -fsS" in content
    assert "get service vllm" in content
    assert "kubectl -n {{ vllm_namespace }} exec" not in content
    assert "-- wget" not in content
