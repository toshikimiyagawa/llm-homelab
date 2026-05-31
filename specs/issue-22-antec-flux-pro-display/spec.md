# Spec: issue-22-antec-flux-pro-display

## Intent
Ubuntu 26.04 上で Antec Flux Pro の温度表示を CPU+GPU で運用可能にする。
公式 iUnity (Windows 専用) は使わず、Linux 向けコミュニティ実装を Ansible で再現可能に導入する。

## Acceptance Criteria
1. Ansible 実行により、Flux Pro 温度表示サービスが導入される。
2. サービスは `systemd` で起動時自動有効化され、再起動後も動作する。
3. 表示対象は CPU+GPU とし、実機確認手順が docs に記載されている。
4. 依存条件（USBデバイス認識、udev権限、NVML/NVIDIA前提）が docs に記載されている。
5. 失敗時の診断手順（service status / journal / lsusb）が docs に記載されている。

## Out of Scope
- Antec公式 iUnity の Linux 対応実装。
- ケース表示以外の監視基盤（Prometheus/Grafana）の新規導入。
- K8s ワークロード設計全体の見直し。

## Constraints / Assumptions
- 対象ホストは `llm01` (Ubuntu 26.04 LTS) で NVIDIA ドライバ導入済み。
- 使用候補実装は `nishtahir/antec-flux-pro-display` を第一候補とする。
- シークレットは不要だが、Ansible タスクは既存の冪等性ルールに従う。
