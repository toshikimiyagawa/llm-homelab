from pathlib import Path


ROOT = Path(__file__).parents[2]
SOPS_CONFIG = ROOT / ".sops.yaml"
SECRETS_DIR = ROOT / "secrets"
SECRETS_README = SECRETS_DIR / "README.md"
INFRA_SECRETS = SECRETS_DIR / "infra.sops.yml"
INVENTORY_DIR = ROOT / "inventory"
REQUIREMENTS = ROOT / "requirements.yml"
SECURITY_DOC = ROOT / "docs" / "security-and-secrets.md"
OPERATIONS_DOC = ROOT / "docs" / "operations.md"
PROM_CLUSTER_ISSUER = (
    ROOT / "roles" / "prometheus" / "templates" / "cluster-issuer.yml.j2"
)
PROM_PLAYBOOK = ROOT / "playbooks" / "08-prometheus.yml"
CLOUDFLARED_PLAYBOOK = ROOT / "playbooks" / "22-cloudflare-tunnel.yml"
TAILSCALE_PLAYBOOK = ROOT / "playbooks" / "07-tailscale.yml"
TAILSCALE_ROLE_TASKS = ROOT / "roles" / "tailscale" / "tasks" / "main.yml"
SOFTWARE_STACK_DOC = ROOT / "docs" / "software-stack.md"
REPO_ROOT_SOPS_PATH = "{{ playbook_dir }}/../secrets/infra.sops.yml"


def test_sops_yaml_targets_secret_files():
    content = SOPS_CONFIG.read_text()
    assert "creation_rules:" in content
    assert "secrets/.*\\.sops" in content
    assert "age1" in content


def test_secrets_readme_documents_key_handling():
    content = SECRETS_README.read_text()
    assert "keys.txt" in content
    assert "llm-homelab age private key" in content
    assert "1Password" in content
    assert "community.sops.load_vars" in content
    assert "revoke" in content.lower()


def test_requirements_include_community_sops():
    assert "community.sops" in REQUIREMENTS.read_text()


def test_security_docs_describe_sops_age_policy():
    content = SECURITY_DOC.read_text()
    for needle in [
        "SOPS",
        "age",
        "community.sops",
        "llm-homelab age private key",
        "tailscale_auth_key",
        "grafana_admin_password",
        "cloudflare_dns01_api_token",
        "cloudflared_tunnel_credentials",
    ]:
        assert needle in content
    assert "revoke" in content.lower()


def test_docs_describe_sops_migration_and_rotation():
    content = SECURITY_DOC.read_text() + "\n" + OPERATIONS_DOC.read_text()
    assert "cloudflare_dns01_api_token" in content
    assert "cloudflared_tunnel_credentials" in content
    assert "tailscale_auth_key" in content
    assert "SOPS" in content
    assert "rotate" in content.lower() or "rotation" in content.lower()


def test_infra_sops_file_is_encrypted_and_has_required_keys():
    content = INFRA_SECRETS.read_text()
    assert "sops:" in content
    assert "cloudflare_dns01_api_token" in content
    assert "cloudflared_tunnel_credentials" in content


def test_prometheus_uses_dns01_token_name():
    template = PROM_CLUSTER_ISSUER.read_text()
    assert "cloudflare_dns01_api_token" in template
    assert "cloudflare_api_token" not in template


def test_prometheus_playbook_loads_sops_secrets():
    content = PROM_PLAYBOOK.read_text()
    assert "community.sops.load_vars" in content
    assert REPO_ROOT_SOPS_PATH in content
    assert "cloudflare_dns01_api_token" in content
    assert "no_log: true" in content


def test_cloudflared_playbook_loads_sops_credentials():
    content = CLOUDFLARED_PLAYBOOK.read_text()
    assert "community.sops.load_vars" in content
    assert REPO_ROOT_SOPS_PATH in content
    assert "cloudflared_tunnel_credentials" in content
    assert "vault_cloudflared_tunnel_credentials" in content
    assert "no_log: true" in content


def test_tailscale_playbook_loads_sops_secrets():
    content = TAILSCALE_PLAYBOOK.read_text()
    assert "community.sops.load_vars" in content
    assert REPO_ROOT_SOPS_PATH in content
    assert "tailscale_auth_key" in content
    assert "no_log: true" in content


def test_tailscale_role_uses_auth_key_directly():
    content = TAILSCALE_ROLE_TASKS.read_text()
    assert "tailscale_auth_key" in content
    assert "community.general.onepassword" not in content
    assert "vault_" not in content


def test_docs_describe_tailscale_sops_source_of_truth():
    stack = SOFTWARE_STACK_DOC.read_text()
    assert "SOPS 管理の `secrets/infra.sops.yml`" in stack
    assert '1Password "LLM Server Infrastructure" > "Tailscale Auth Key"' not in stack


def test_secrets_readme_documents_sops_editing():
    content = SECRETS_README.read_text()
    assert "secrets/infra.sops.yml" in content
    assert "sops secrets/infra.sops.yml" in content
    assert "1Password is only a recovery location" in content


def test_inventory_has_no_ansible_vault_encrypted_files():
    for path in INVENTORY_DIR.rglob("*"):
        if path.is_file():
            assert not path.read_text(errors="ignore").startswith("$ANSIBLE_VAULT"), (
                f"{path.relative_to(ROOT)} must not be an Ansible Vault file; "
                "use secrets/infra.sops.yml for in-repo operational secrets"
            )


def test_current_docs_do_not_require_ansible_vault_password_file():
    docs = [
        SECURITY_DOC,
        SOFTWARE_STACK_DOC,
        SECRETS_README,
    ]
    for path in docs:
        content = path.read_text()
        assert "--vault-password-file" not in content
        assert "~/.vault_pass" not in content


def test_no_forbidden_secret_files_are_committed():
    forbidden_names = {"keys.txt"}
    forbidden_suffixes = (
        ".plain.yml",
        ".plain.yaml",
        ".decrypted.yml",
        ".decrypted.yaml",
    )
    for path in SECRETS_DIR.rglob("*"):
        assert path.name not in forbidden_names
        assert not path.name.endswith(forbidden_suffixes)
