import re
from pathlib import Path

ROOT = Path(__file__).parents[2]
PROJECT_TOOLS = ROOT / ".devcontainer" / "project-tools.yml"
SECRETS_README = ROOT / "secrets" / "README.md"


def _project_tools_text():
    return PROJECT_TOOLS.read_text()


def test_project_tools_installs_sops_cli():
    text = _project_tools_text()
    assert "- name: install sops cli" in text
    assert "SOPS_VERSION=" in text
    assert "github.com/getsops/sops/releases/download/" in text
    assert 'sops_asset="sops-${SOPS_VERSION}.linux.${ARCH}"' in text
    assert "sops-${SOPS_VERSION}.linux.${ARCH}" in text
    assert "/usr/local/bin/sops" in text
    assert "sops --version" in text


def test_sops_cli_version_is_pinned():
    text = _project_tools_text()
    match = re.search(r"SOPS_VERSION=v(?P<version>[0-9]+\.[0-9]+\.[0-9]+)", text)
    assert match is not None
    assert match.group("version") == "3.13.1"


def test_project_tools_installs_age_cli():
    text = _project_tools_text()
    assert "- name: install age cli" in text
    assert "AGE_VERSION=" in text
    assert "github.com/FiloSottile/age/releases/download/" in text
    assert "age-v${AGE_VERSION}-linux-${ARCH}.tar.gz" in text
    assert "/usr/local/bin/age" in text
    assert "/usr/local/bin/age-keygen" in text
    assert "age --version" in text
    assert "age-keygen --version" in text


def test_age_cli_version_is_pinned():
    text = _project_tools_text()
    match = re.search(r"AGE_VERSION=(?P<version>[0-9]+\.[0-9]+\.[0-9]+)", text)
    assert match is not None
    assert match.group("version") == "1.3.1"


def test_project_tools_documents_sops_runtime_dependency():
    text = _project_tools_text()
    assert "community.sops.load_vars" in text
    assert "secrets/infra.sops.yml" in text
    assert "age private key is not installed by project tooling" in text


def test_project_tools_verifies_sops_release_checksum():
    text = _project_tools_text()
    assert "sops-${SOPS_VERSION}.checksums.txt" in text
    assert 'grep "sops-${SOPS_VERSION}.linux.${ARCH}$"' in text
    assert "sha256sum -c -" in text


def test_secrets_readme_separates_cli_tooling_from_age_private_key():
    text = SECRETS_README.read_text()
    assert "SOPS / age CLI" in text
    assert ".devcontainer/project-tools.yml" in text
    assert "~/.config/sops/age/keys.txt" in text
    assert "repository に commit しない" in text
