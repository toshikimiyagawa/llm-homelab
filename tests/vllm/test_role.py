"""
Static configuration tests for the vllm Ansible role.

Runtime acceptance criteria are verified by running the playbook against llm01.
These tests keep rollout and OpenAI-compatible server options checkable without
a live Kubernetes cluster.
"""
from pathlib import Path


ROLE_ROOT = Path(__file__).parents[2] / "roles" / "vllm"
DEPLOYMENT_TMPL = ROLE_ROOT / "templates" / "vllm-deployment.yml.j2"


def test_deployment_uses_recreate_strategy_for_fixed_gpu():
    content = DEPLOYMENT_TMPL.read_text()
    assert "strategy:" in content
    assert "type: Recreate" in content


def test_deployment_enables_tool_call_options():
    content = DEPLOYMENT_TMPL.read_text()
    assert '"--enable-auto-tool-choice"' in content
    assert '"--tool-call-parser"' in content
    assert '"hermes"' in content
