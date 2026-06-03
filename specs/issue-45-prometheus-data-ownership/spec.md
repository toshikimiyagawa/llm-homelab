# Spec: issue-45-prometheus-data-ownership

## Intent

Prometheus hostPath PV の実体である `/opt/prometheus-data` を、Prometheus Pod が書き込める所有者に Ansible で設定する。

## Acceptance Criteria

1. `playbooks/08-prometheus.yml` 適用時に `/opt/prometheus-data` が `1000:2000` / `0755` で管理される。
2. 手動 `chown` なしで Prometheus Pod が `Running` になる。
3. `playbooks/08-prometheus.yml` 再実行で所有者補正タスクが冪等に動作する。
