# Tasks: issue-46-dcgm-exporter-version

## Implementation Tasks

- [x] T1: `dcgm_exporter_version` を NVIDIA 公式 Helm chart repository に存在する chart version に更新する。対応AC: AC1, AC3
- [x] T2: DCGM Exporter HelmChart の repo/chart/version/targetNamespace/serviceMonitor 設定を静的テストで固定する。対応AC: AC1, AC2
- [x] T3: `playbooks/08-prometheus.yml` を実機へ適用し、DaemonSet rollout と Prometheus scrape 検証まで通ることを確認する。対応AC: AC3

## Tests

- [x] AC1, AC2 → `uvx pytest tests/prometheus/test_role.py`
- [x] AC3 → `ansible-playbook playbooks/08-prometheus.yml --vault-password-file /home/ubuntu/.vault_pass --ssh-common-args='-o ControlPath=/tmp/ansible-ssh-%h-%p-%r'`

## Verification Notes

- NVIDIA 公式 Helm chart index `https://nvidia.github.io/dcgm-exporter/helm-charts/index.yaml` で `dcgm-exporter` chart version `4.8.2` が存在することを確認。
- RED: `uvx pytest tests/prometheus/test_role.py -q` は `dcgm_exporter_version: "3.3.9"` のまま `test_dcgm_exporter_uses_existing_chart_version` が失敗。
- GREEN: `uvx pytest tests/prometheus/test_role.py -q` は `3 passed`。
- `yamllint -s roles/prometheus/defaults/main.yml roles/prometheus/tasks/main.yml` は通過。
- `ansible-lint playbooks/08-prometheus.yml roles/prometheus` は既存の Prometheus role 変数 prefix 違反で失敗。今回変更した version 行起因の新規違反ではない。
- 実機 `playbooks/08-prometheus.yml` は `ok=24 changed=8 failed=0` で完了。
- 実機 DCGM Exporter DaemonSet は `READY 1/1`、Pod は `Running`、HelmChart spec version は `4.8.2`。

## Definition of Done

- [x] AC1-AC3 が確認できる
- [x] SDD traceability が PR に残る
