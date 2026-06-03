# Tasks: issue-45-prometheus-data-ownership

## Implementation Tasks
- [x] T1: `roles/prometheus/tasks/main.yml` の PV manifest 適用前に `/opt/prometheus-data` の owner/group/mode を設定する。対応AC: AC1, AC2, AC3

## Tests
- [x] AC1 → `stat -c '%u:%g %a' /opt/prometheus-data` が `1000:2000 755`
- [x] AC2 → `k3s kubectl -n monitoring get pod prometheus-kube-prometheus-stack-prometheus-0` が `2/2 Running`
- [x] AC3 → ownership 補正タスク相当の Ansible file module 再実行が `changed=false`

## Verification Notes
- `yamllint -s roles/prometheus/tasks/main.yml` は通過。
- `ansible-lint playbooks/08-prometheus.yml roles/prometheus` は既存の role 変数名規約違反で失敗。#45 追加タスク起因の新規違反ではない。
- `playbooks/08-prometheus.yml` 全体は DCGM Exporter chart version 不一致で後段失敗。この別問題は #46 で追跡。

## Definition of Done
- [x] AC1-AC3 が確認できる
- [x] #45 の SDD traceability が main に残る
