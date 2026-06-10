import re
from pathlib import Path

ROOT = Path(__file__).parents[2]
PROJECT_TOOLS = ROOT / ".devcontainer" / "project-tools.yml"


def _project_tools_text():
    return PROJECT_TOOLS.read_text()


def test_project_tools_installs_terraform_cli():
    text = _project_tools_text()
    assert "- name: install terraform cli" in text
    assert "releases.hashicorp.com/terraform/" in text
    assert "terraform_${TERRAFORM_VERSION}_linux_${ARCH}.zip" in text
    assert "/usr/local/bin/terraform" in text


def test_terraform_cli_version_is_pinned():
    text = _project_tools_text()
    match = re.search(r"TERRAFORM_VERSION=(?P<version>[0-9]+\.[0-9]+\.[0-9]+)", text)
    assert match is not None
    assert match.group("version") == "1.13.5"


def test_project_tools_documents_cloudflare_terraform_use():
    text = _project_tools_text()
    assert "Cloudflare Terraform" in text
    assert "infra/cloudflare" in text
