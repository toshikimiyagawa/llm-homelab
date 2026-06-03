# Tasks: issue-46-dcgm-exporter-version

## Implementation Tasks

- [ ] T1: `dcgm_exporter_version` を NVIDIA 公式 Helm chart repository に存在する chart version に更新する。対応AC: AC1, AC3
- [ ] T2: DCGM Exporter HelmChart の repo/chart/version/targetNamespace/serviceMonitor 設定を静的テストで固定する。対応AC: AC1, AC2
- [ ] T3: `playbooks/08-prometheus.yml` を実機へ適用し、DaemonSet rollout と Prometheus scrape 検証まで通ることを確認する。対応AC: AC3

## Tests

- [ ] AC1, AC2 → `uvx pytest tests/prometheus/test_role.py`
- [ ] AC3 → `ansible-playbook playbooks/08-prometheus.yml --vault-password-file /home/ubuntu/.vault_pass --ssh-common-args='-o ControlPath=/tmp/ansible-ssh-%h-%p-%r'`

## Definition of Done

- [ ] AC1-AC3 が確認できる
- [ ] SDD traceability が PR に残る
