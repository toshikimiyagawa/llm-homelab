"""Static tests for common role systemd-resolved domain routing."""
from pathlib import Path


ROOT = Path(__file__).parents[2]
DEFAULTS = ROOT / "roles" / "common" / "defaults" / "main.yml"
TASKS = ROOT / "roles" / "common" / "tasks" / "main.yml"
HANDLERS = ROOT / "roles" / "common" / "handlers" / "main.yml"


def test_defaults_enable_solvelio_resolved_route():
    content = DEFAULTS.read_text()
    assert "common_manage_resolved_domain_dns: true" in content
    assert "common_resolved_domain: solvelio.com" in content
    assert "1.1.1.1" in content
    assert "8.8.8.8" in content


def test_tasks_manage_resolved_drop_in():
    defaults = DEFAULTS.read_text()
    content = TASKS.read_text()
    assert "/etc/systemd/resolved.conf.d" in defaults
    assert "solvelio.conf" in defaults
    assert "common_resolved_dropin_dir" in content
    assert "common_resolved_dropin_path" in content
    assert "Domains=~{{ common_resolved_domain }}" in content
    assert "DNS={{ common_resolved_dns_servers | join(' ') }}" in content


def test_handler_restarts_systemd_resolved():
    content = HANDLERS.read_text()
    assert "Restart systemd-resolved" in content
    assert "systemd-resolved" in content
