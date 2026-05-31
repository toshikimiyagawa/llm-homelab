# Tasks: issue-22-antec-flux-pro-display

## Implementation Tasks
- [x] T1: `roles/flux_pro_display/defaults/main.yml` を新規作成し、導入ソース、サービス名、期待USB ID、更新間隔など既定値を定義する。対応AC: AC1, AC4
- [x] T2: `roles/flux_pro_display/tasks/main.yml` を新規作成し、依存パッケージ導入、`af-pro-display` 導入、udev ルール配備、systemd enable/start を実装する。対応AC: AC1, AC2
- [x] T3: `playbooks/10-flux-pro-display.yml` を新規作成し、`flux_pro_display` role を呼び出す。対応AC: AC1, AC2
- [x] T4: `playbooks/site.yml` に `10-flux-pro-display.yml` の実行導線を追加する。対応AC: AC1
- [x] T5: `docs/software-stack.md` / `docs/operations.md` に Linux代替実装、CPU+GPU表示方針、前提条件、診断手順を追記する。対応AC: AC3, AC4, AC5
- [x] T6: `docs/repository-guidelines.md` の予定構成と実態を整合させる。対応AC: AC3

## Tests (AC mapping)
- [x] AC1 → `ansible-playbook playbooks/10-flux-pro-display.yml --check` が構文/参照エラーなし
- [x] AC2 → `systemctl is-enabled af-pro-display` が `enabled`、`systemctl is-active af-pro-display` が `active`
- [x] AC3 → ケース表示が CPU+GPU で更新されることを手順どおりに確認できる
- [x] AC4 → `docs/operations.md` に USB ID 確認・udev・NVML前提が記載される
- [x] AC5 → `journalctl -u af-pro-display` / `lsusb | grep 2022:0522` / `systemctl status` の診断手順が docs に記載される

## Definition of Done
- [x] 全ACに対応するテスト/確認手順が存在する
- [ ] `yamllint -s .` と `ansible-lint` が実行される
- [x] verify フェーズで sdd-reviewer の確認を通過する
