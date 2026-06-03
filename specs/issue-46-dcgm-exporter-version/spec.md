# Spec: issue-46-dcgm-exporter-version

## Intent

`playbooks/08-prometheus.yml` が DCGM Exporter HelmChart まで完了するように、`dcgm_exporter_version` を NVIDIA 公式 Helm chart repository に存在する chart version に更新する。

## Acceptance Criteria

1. `roles/prometheus/defaults/main.yml` の `dcgm_exporter_version` は NVIDIA 公式 DCGM Exporter Helm chart repository に存在する chart version を指す。
2. `roles/prometheus/tasks/main.yml` の DCGM Exporter HelmChart は `dcgm_exporter_version` を使い、`monitoring` namespace に DaemonSet を作成する設定を維持する。
3. `playbooks/08-prometheus.yml` が DCGM Exporter DaemonSet rollout と Prometheus scrape 検証まで完了する。
