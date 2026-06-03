"""Static configuration tests for the open_webui Ansible role."""
from pathlib import Path


ROOT = Path(__file__).parents[2]
ROLE_ROOT = ROOT / "roles" / "open_webui"
DEFAULTS = ROLE_ROOT / "defaults" / "main.yml"
TASKS = ROLE_ROOT / "tasks" / "main.yml"
DEPLOYMENT_TMPL = ROLE_ROOT / "templates" / "open-webui-deployment.yml.j2"
SOFTWARE_DOC = ROOT / "docs" / "software-stack.md"
OPS_DOC = ROOT / "docs" / "operations.md"


def test_defaults_define_global_model_params_max_tokens():
    content = DEFAULTS.read_text()
    assert "open_webui_default_model_params" in content
    assert "max_tokens: 8192" in content


def test_deployment_exports_default_model_params_to_container():
    content = DEPLOYMENT_TMPL.read_text()
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
