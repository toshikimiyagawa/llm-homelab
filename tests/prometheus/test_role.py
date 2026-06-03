"""Static configuration tests for the prometheus Ansible role."""
from pathlib import Path


ROOT = Path(__file__).parents[2]
ROLE_ROOT = ROOT / "roles" / "prometheus"
DEFAULTS = ROLE_ROOT / "defaults" / "main.yml"
TASKS = ROLE_ROOT / "tasks" / "main.yml"


def test_dcgm_exporter_uses_existing_chart_version():
    content = DEFAULTS.read_text()
    assert 'dcgm_exporter_version: "4.8.2"' in content
    assert 'dcgm_exporter_version: "3.3.9"' not in content


def test_dcgm_exporter_helmchart_uses_role_defaults():
    content = TASKS.read_text()
    assert "repo: https://nvidia.github.io/dcgm-exporter/helm-charts" in content
    assert "chart: dcgm-exporter" in content
    assert 'version: "{{ dcgm_exporter_version }}"' in content
    assert 'targetNamespace: "{{ prometheus_namespace }}"' in content
    assert "serviceMonitor:" in content
    assert "enabled: true" in content


def test_dcgm_exporter_rollout_and_scrape_are_verified():
    content = TASKS.read_text()
    assert "rollout status daemonset/dcgm-exporter" in content
    assert 'query=up%7Bjob%3D%22dcgm-exporter%22%7D' in content
