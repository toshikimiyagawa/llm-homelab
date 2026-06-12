from pathlib import Path
import re

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


def test_ssh_access_app_has_short_lived_certificate_ca():
    text = read_all_tf()
    outputs = (TF / "outputs.tf").read_text()
    assert "cloudflare_zero_trust_access_short_lived_certificate" in text
    assert "app_id     = cloudflare_zero_trust_access_application.ssh.id" in text
    output_block = re.search(r'output "ssh_ca_public_key" \{.*?\n\}', outputs, re.DOTALL)
    assert output_block
    assert "cloudflare_zero_trust_access_short_lived_certificate.ssh.public_key" in outputs
    assert "sensitive   = true" not in output_block.group(0)


def test_outputs_mark_service_token_secret_sensitive():
    text = (TF / "outputs.tf").read_text()
    assert "service_token_client_id" in text
    assert "service_token_client_secret" in text
    assert "sensitive   = true" in text


def test_tunnel_token_data_source_and_sensitive_output():
    tunnel = (TF / "tunnel.tf").read_text()
    outputs = (TF / "outputs.tf").read_text()
    assert 'data "cloudflare_zero_trust_tunnel_cloudflared_token" "llm01"' in tunnel
    assert "tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.llm01.id" in tunnel
    assert 'output "tunnel_token"' in outputs
    assert "data.cloudflare_zero_trust_tunnel_cloudflared_token.llm01.token" in outputs
    assert "sensitive   = true" in outputs


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
    assert "credentials-file:" not in text
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


def test_docs_describe_tunnel_token_not_credentials_json():
    docs = OPS_DOC.read_text() + SECURITY_DOC.read_text()
    assert "terraform output -raw tunnel_token" in docs
    assert "cloudflared_tunnel_token" in docs
    assert "cloudflared_tunnel_credentials" not in docs
    assert "credentials JSON" not in docs


def test_docs_describe_ssh_ca_public_key_output():
    docs = OPS_DOC.read_text()
    assert "terraform -chdir=infra/cloudflare output -raw ssh_ca_public_key" in docs
    assert "roles/cloudflared/files/cloudflare_ca.pub" in docs
