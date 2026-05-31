"""
Static configuration tests for the ollama Ansible role.
These tests validate role structure and config content without a running host.
Integration testing (AC1, AC3, AC5 runtime behaviour) is done by running
the playbook against llm01 and following docs/operations.md.
"""
import re
from pathlib import Path

ROLE_ROOT = Path(__file__).parents[2] / "roles" / "ollama"
DEFAULTS = ROLE_ROOT / "defaults" / "main.yml"
TASKS = ROLE_ROOT / "tasks" / "main.yml"
OVERRIDE_TMPL = ROLE_ROOT / "templates" / "override.conf.j2"
PLAYBOOK = Path(__file__).parents[2] / "playbooks" / "20-ollama.yml"
SITE_YML = Path(__file__).parents[2] / "playbooks" / "site.yml"
OPS_DOC = Path(__file__).parents[2] / "docs" / "operations.md"


# AC1: playbook and site.yml reference the role
def test_playbook_exists():
    assert PLAYBOOK.exists()


def test_site_yml_imports_ollama():
    content = SITE_YML.read_text()
    assert "20-ollama.yml" in content


def test_playbook_uses_ollama_role():
    content = PLAYBOOK.read_text()
    assert "ollama" in content


# AC2: models directory is set to /opt path
def test_models_dir_is_on_opt():
    content = DEFAULTS.read_text()
    assert "/opt/ollama/models" in content


def test_tasks_create_models_dir():
    content = TASKS.read_text()
    assert "ollama_models_dir" in content


# AC3: OLLAMA_HOST restricts to localhost
def test_override_binds_localhost():
    content = OVERRIDE_TMPL.read_text()
    assert "OLLAMA_HOST" in content
    assert "ollama_host" in content


def test_default_host_is_loopback():
    content = DEFAULTS.read_text()
    assert "127.0.0.1" in content


# AC4: CUDA_VISIBLE_DEVICES targets GTX 1650 (index 0)
def test_override_sets_cuda_device():
    content = OVERRIDE_TMPL.read_text()
    assert "CUDA_VISIBLE_DEVICES" in content


def test_default_cuda_device_is_zero():
    content = DEFAULTS.read_text()
    assert re.search(r'ollama_cuda_visible_devices:\s*"0"', content)


# AC5: service is enabled (auto-start on boot)
def test_tasks_enable_service():
    content = TASKS.read_text()
    assert "enabled: true" in content


# AC6: operations.md has Ollama section
def test_ops_doc_has_ollama_section():
    content = OPS_DOC.read_text()
    assert "## Ollama" in content


def test_ops_doc_has_health_check_command():
    content = OPS_DOC.read_text()
    assert "127.0.0.1:11434" in content
