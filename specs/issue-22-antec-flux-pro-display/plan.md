# Plan: issue-22-antec-flux-pro-display

## Approach
Ansible role `flux_pro_display` と playbook `10-flux-pro-display.yml` を追加し、
Linuxコミュニティ実装 (`af-pro-display`) の導入・有効化・起動確認を自動化する。
導入方式は upstream が提供する Debian package または release asset を優先し、
不可時のみ source build をフォールバックとして扱う。

## Impacted Files
- `playbooks/10-flux-pro-display.yml` — Flux Pro 表示設定専用 playbook 追加
- `playbooks/site.yml` — 新 playbook の取り込み
- `roles/flux_pro_display/defaults/main.yml` — バージョン・取得元・サービス名などの既定値
- `roles/flux_pro_display/tasks/main.yml` — 導入、udev、service enable/start、検証
- `docs/software-stack.md` — 温度表示実装方式の更新
- `docs/operations.md` — 運用/診断コマンドの追加
- `docs/repository-guidelines.md` — 予定構成との差分解消（存在前提の具体化）

## Alternatives and Tradeoffs
- 公式 iUnity を Wine で動かす案:
  - 短期導入の可能性はあるが、安定性・再現性・自動起動の運用コストが高い。
- Windows向け軽量実装 (`shroudedhorizon/*`) を流用する案:
  - .NET/Windows 依存が強く Ubuntu 対象外。
- Linuxネイティブ実装 (`nishtahir/*`) 案（採用）:
  - systemd/udev と整合し Ansible 化しやすい。

## Risks / Rollback
- リスク: ケース側USB認識不良、CPUセンサー選択不一致、GPU温度取得失敗。
- ロールバック: `af-pro-display` service 停止/無効化、関連パッケージ削除、role 適用前状態へ戻す。
