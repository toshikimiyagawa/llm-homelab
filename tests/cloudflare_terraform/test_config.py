from pathlib import Path

ROOT = Path(__file__).parents[2]
TF = ROOT / "infra" / "cloudflare"
GITIGNORE = ROOT / ".gitignore"
CLOUDFLARED_CONFIG = ROOT / "roles" / "cloudflared" / "templates" / "config.yml.j2"
OPS_DOC = ROOT / "docs" / "operations.md"
SECURITY_DOC = ROOT / "docs" / "security-and-secrets.md"


def read_all_tf() -> str:
    return "\n".join(path.read_text() for path in sorted(TF.glob("*.tf")))


def test_provider_version_and_env_token_contract():
    text = (TF / "versions.tf").read_text() + (TF / "providers.tf").read_text()
    assert 'source  = "cloudflare/cloudflare"' in text
    assert 'version = "~> 5.19"' in text
    assert 'provider "cloudflare" {}' in text
    assert "api_token" not in (TF / "providers.tf").read_text()


def test_tfvars_example_is_domain_portable():
    text = (TF / "terraform.tfvars.example").read_text()
    for key in [
        "cloudflare_account_id",
        "cloudflare_zone_id",
        "domain",
        "host_id",
        "allowed_email",
        "access_team_name",
    ]:
        assert key in text
    assert 'domain                = "solvelio.com"' in text


def test_tunnel_is_cloudflare_managed_and_has_ingress_contract():
    text = read_all_tf()
    assert "cloudflare_zero_trust_tunnel_cloudflared" in text
    assert 'config_src = "cloudflare"' in text
    for key in ["open_webui", "ollama", "vllm", "ssh"]:
        assert key in text
    for service in [
        "http://localhost:8080",
        "http://localhost:11434",
        "ssh://localhost:22",
        "http_status:404",
    ]:
        assert service in text
    assert "origin_server_name" in text


def test_dns_records_point_to_tunnel():
    text = read_all_tf()
    assert "cloudflare_dns_record" in text
    assert '"CNAME"' in text
    assert "proxied = true" in text
    assert "ttl     = 1" in text
    assert "cfargotunnel.com" in text


def test_access_resources_exist():
    text = read_all_tf()
    assert "cloudflare_zero_trust_access_application" in text
    assert "policies = [{" in text
    assert "cloudflare_zero_trust_access_service_token" in text
    assert 'type             = "ssh"' in text
    assert "allowed_email" in text
    assert "service_token" in text
    assert 'decision   = "non_identity"' in text


def test_outputs_mark_service_token_secret_sensitive():
    text = (TF / "outputs.tf").read_text()
    assert "service_token_client_id" in text
    assert "service_token_client_secret" in text
    assert "sensitive   = true" in text


def test_gitignore_excludes_terraform_secrets_not_lockfile():
    text = GITIGNORE.read_text()
    for pattern in [
        "**/.terraform/",
        "**/terraform.tfstate",
        "**/terraform.tfstate.*",
        "**/terraform.tfvars",
        "**/*.auto.tfvars",
        "**/*.tfplan",
    ]:
        assert pattern in text
    assert ".terraform.lock.hcl" not in text


def test_ansible_config_no_longer_contains_locally_managed_ingress():
    text = CLOUDFLARED_CONFIG.read_text()
    assert "credentials-file:" in text
    assert "ingress:" not in text
    for hostname in [
        "open-webui-llm01.solvelio.com",
        "ollama-llm01.solvelio.com",
        "vllm-llm01.solvelio.com",
        "ssh-llm01.solvelio.com",
    ]:
        assert hostname not in text


def test_docs_cover_import_apply_state_and_ui_policy():
    docs = (TF / "README.md").read_text() + OPS_DOC.read_text() + SECURITY_DOC.read_text()
    for term in [
        "terraform import",
        "terraform apply",
        "CLOUDFLARE_API_TOKEN",
        "terraform.tfstate",
        "read-only",
        "revoke",
    ]:
        assert term in docs
