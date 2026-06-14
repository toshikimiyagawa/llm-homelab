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


def test_tunnel_is_cloudflare_managed_without_public_hostname_ingress():
    text = read_all_tf()
    assert "cloudflare_zero_trust_tunnel_cloudflared" in text
    assert 'config_src = "cloudflare"' in text
    assert "cloudflare_zero_trust_tunnel_cloudflared_config" not in text
    assert "ingress" not in (TF / "tunnel.tf").read_text()
    assert "origin_server_name" not in text
    assert "cfargotunnel.com" not in text


def test_warp_access_resources_exist():
    text = read_all_tf()
    assert "cloudflare_zero_trust_access_application" in text
    assert "policies = [{" in text
    assert re.search(r'type\s*=\s*"warp"', text)
    assert "allowed_email" in text
    assert "service_token" not in text
    assert re.search(r'decision\s*=\s*"allow"', text)


def test_tunnel_token_data_source_and_sensitive_output():
    tunnel = (TF / "tunnel.tf").read_text()
    outputs = (TF / "outputs.tf").read_text()
    assert 'data "cloudflare_zero_trust_tunnel_cloudflared_token" "llm01"' in tunnel
    assert "tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.llm01.id" in tunnel
    assert 'output "tunnel_token"' in outputs
    assert "data.cloudflare_zero_trust_tunnel_cloudflared_token.llm01.token" in outputs
    assert "sensitive   = true" in outputs


def test_warp_private_network_variable_is_portable():
    variables = (TF / "variables.tf").read_text()
    example = (TF / "terraform.tfvars.example").read_text()
    assert 'variable "warp_private_network_cidr"' in variables
    assert "Cloudflare WARP private network CIDR" in variables
    assert "warp_private_network_cidr" in example
    assert 'warp_private_network_cidr = "192.168.1.0/24"' in example
    assert '192.168.0.0/17' not in example


def test_warp_private_network_route_uses_existing_tunnel():
    text = read_all_tf()
    assert 'resource "cloudflare_zero_trust_tunnel_cloudflared_route" "llm01_lan"' in text
    assert "tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.llm01.id" in text
    assert "network    = var.warp_private_network_cidr" in text
    assert "comment" in text


def test_warp_enrollment_application_is_limited_to_allowed_email():
    text = read_all_tf()
    assert 'resource "cloudflare_zero_trust_access_policy" "warp_enrollment"' in text
    assert 'resource "cloudflare_zero_trust_access_application" "warp_enrollment"' in text
    assert re.search(r'type\s*=\s*"warp"', text)
    assert "cloudflare_zero_trust_access_policy.warp_enrollment.id" in text
    assert "allowed_email" in text


def test_warp_device_profile_includes_private_network_only():
    text = read_all_tf()
    assert 'resource "cloudflare_zero_trust_device_custom_profile" "llm01_warp"' in text
    assert "identity.email" in text
    assert "var.allowed_email" in text
    assert "service_mode_v2" in text
    assert 'mode = "warp"' in text
    assert "include = [{" in text
    assert "address     = var.warp_private_network_cidr" in text or "address = var.warp_private_network_cidr" in text
    for forbidden in ["10.42.0.0", "10.43.0.0", "cluster", "pod cidr", "service cidr"]:
        assert forbidden not in text.lower()


def test_public_hostname_access_resources_are_removed():
    text = read_all_tf()
    outputs = (TF / "outputs.tf").read_text()
    forbidden_resources = [
        'resource "cloudflare_dns_record" "tunnel"',
        'resource "cloudflare_zero_trust_access_application" "open_webui"',
        'resource "cloudflare_zero_trust_access_application" "ssh"',
        'resource "cloudflare_zero_trust_access_application" "vllm"',
        'resource "cloudflare_zero_trust_access_application" "ollama"',
        'resource "cloudflare_zero_trust_access_short_lived_certificate" "ssh"',
        'resource "cloudflare_zero_trust_access_service_token" "api_clients"',
    ]
    for resource in forbidden_resources:
        assert resource not in text
    for output_name in ["hostnames", "ssh_ca_public_key", "service_token_client_id", "service_token_client_secret"]:
        assert f'output "{output_name}"' not in outputs
    assert 'resource "cloudflare_zero_trust_access_application" "warp_enrollment"' in text


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


def test_docs_describe_warp_private_network_operations():
    docs = (TF / "README.md").read_text() + OPS_DOC.read_text() + (ROOT / "docs" / "software-stack.md").read_text()
    for term in [
        "Cloudflare WARP",
        "Cloudflare One client",
        "warp_private_network_cidr",
        "Split Tunnel",
        "Tailscale",
        "CIDR",
    ]:
        assert term in docs
    assert "CF-Access-Client-Id" not in docs
    assert "CF-Access-Client-Secret" not in docs
