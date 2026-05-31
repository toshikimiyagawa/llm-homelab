# Spec: issue-16-hdd-mount

- Tier: 2
- Status: draft
- Feature slug: issue-16-hdd-mount

## 背景 / 意図

`/dev/sda`（14TB HDD, ext4 既フォーマット）を運用用途に合わせて永続マウントし、
再起動後も再現可能な状態を Ansible 管理下に置く。

`/`、`/var/lib/rancher`、`/opt`（NVMe）の既存構成は維持し、既存設計判断（RAIDなし・LVM維持）を変えない。

## 受入条件

- [ ] AC1: 14TB HDD のマウントポイントが明示され、ドキュメントに反映されている
- [ ] AC2: `/etc/fstab` が UUID 指定で管理され、該当 HDD が永続マウントされる
- [ ] AC3: `ansible-playbook` の再実行で設定がドリフトせず冪等に適用できる
- [ ] AC4: 既存マウント（`/`、`/var/lib/rancher`、`/opt`）を壊さない
- [ ] AC5: 再起動後の確認手順（`findmnt` / `lsblk` / `mount -a` 等）が `docs/operations.md` に記載される

## スコープ外

- HDD の再パーティション/再フォーマット
- RAID/ZFS/LVM-on-HDD への構成変更
- バックアップジョブそのものの実装（別 issue）

## 制約 / 前提

- 対象ホスト: `llm01`（Ubuntu 26.04 LTS）
- HDD デバイス: `/dev/sda`（ext4 既フォーマット済み）
- マウントポイント案は `/mnt/archive` を初期案とする（freeze 前に人間承認）
- mount 設定は Ansible で冪等に管理し、`fstab` は UUID を使う
