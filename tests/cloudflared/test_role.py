"""
Static configuration tests for the cloudflared Ansible role (issue #88).

Runtime acceptance criteria (cloudflared.service state, sshd effective config)
are verified by playbooks/23-cloudflare-smoke-test.yml against llm01.
Cloudflare-edge behaviours (M-1..M-5) are verified manually per docs/operations.md.
These tests keep the repository contract checkable without a live host.
"""
from pathlib import Path

ROOT = Path(__file__).parents[2]
ROLE = ROOT / "roles" / "cloudflared"
DEFAULTS = ROLE / "defaults" / "main.yml"
TASKS = ROLE / "tasks" / "main.yml"
CONFIG_TMPL = ROLE / "templates" / "config.yml.j2"
SERVICE_TMPL = ROLE / "templates" / "cloudflared.service.j2"
SSHD_TMPL = ROLE / "templates" / "sshd-cloudflare.conf.j2"
CA_PUB = ROLE / "files" / "cloudflare_ca.pub"
PLAYBOOK = ROOT / "playbooks" / "22-cloudflare-tunnel.yml"
SMOKE = ROOT / "playbooks" / "23-cloudflare-smoke-test.yml"
SITE = ROOT / "playbooks" / "site.yml"
OPS_DOC = ROOT / "docs" / "operations.md"
SECURITY_DOC = ROOT / "docs" / "security-and-secrets.md"

HOSTNAMES = [
    "open-webui-llm01.solvelio.com",
    "ollama-llm01.solvelio.com",
    "vllm-llm01.solvelio.com",
    "ssh-llm01.solvelio.com",
]


def test_apt_install_present():  # AC-1
    t = TASKS.read_text()
    assert "apt_repository" in t
    assert "cloudflared" in t


def test_config_is_minimal_for_cloudflare_managed_tunnel():  # issue #95
    c = CONFIG_TMPL.read_text()
    for h in HOSTNAMES:
        assert h not in c
    assert "tunnel:" in c
    assert "credentials-file:" not in c
    assert "ingress:" not in c


def test_service_enabled():  # AC-3
    assert "enabled: true" in TASKS.read_text()


def test_tunnel_token_no_log_and_mode():  # AC-4
    t = TASKS.read_text()
    p = PLAYBOOK.read_text()
    assert "no_log: true" in t
    assert "0600" in t
    assert "vault_cloudflared_tunnel_token" in t
    assert "cloudflared_tunnel_token" in p
    assert "cloudflared_tunnel_credentials" not in p
    assert "community.sops.load_vars" in p


def test_systemd_uses_token_file_without_literal_token():  # issue #120
    unit = SERVICE_TMPL.read_text()
    assert "--token-file {{ cloudflared_token_path }}" in unit
    assert "vault_cloudflared_tunnel_token" not in unit
    assert "cloudflared_tunnel_token" not in unit


def test_sshd_ca_trust():  # AC-5
    assert "TrustedUserCAKeys" in SSHD_TMPL.read_text()
    assert CA_PUB.exists()
    head = CA_PUB.read_text().strip()
    assert head.startswith(("ssh-rsa ", "ssh-ed25519 ", "ecdsa-"))


def test_sshd_password_auth_off():  # AC-6
    assert "PasswordAuthentication no" in SSHD_TMPL.read_text()
    assert "validate:" in TASKS.read_text()


def test_ca_placeholder_guard():  # issue #90 footgun guard
    t = TASKS.read_text()
    assert "ansible.builtin.assert" in t
    assert "cloudflared_ssh_ca_placeholder_marker" in DEFAULTS.read_text()
    # ガードは CA 配置 / sshd 設定より前に走らなければ意味がない
    guard_pos = t.index("ansible.builtin.assert")
    deploy_pos = t.index("Deploy Cloudflare Access SSH CA public key")
    sshd_pos = t.index("Configure sshd to trust Cloudflare SSH CA")
    assert guard_pos < deploy_pos < sshd_pos


def test_role_vars_use_prefix():  # AC-7 (var-naming[no-role-prefix] 回避)
    d = DEFAULTS.read_text()
    assert "cloudflared_config_path" in d
    assert "cloudflared_token_path" in d
    assert "cloudflared_credentials_path" not in d


def test_playbook_uses_role():  # AC-9 連動
    assert PLAYBOOK.exists()
    assert "cloudflared" in PLAYBOOK.read_text()


def test_site_imports_playbook():  # AC-9
    assert "22-cloudflare-tunnel.yml" in SITE.read_text()


def test_smoke_asserts_runtime():  # AC-10
    s = SMOKE.read_text().lower()
    assert "passwordauthentication no" in s
    assert "trustedusercakeys" in s
    assert "cloudflared" in s


def test_docs_document_hostnames_and_service_token():  # M-1..M-5 docs
    ops = OPS_DOC.read_text()
    for h in HOSTNAMES:
        assert h in ops
    assert "Service Token" in ops
    assert "cloudflared_tunnel_token" in SECURITY_DOC.read_text()
    assert "vault_cloudflared_tunnel_credentials" not in SECURITY_DOC.read_text()
