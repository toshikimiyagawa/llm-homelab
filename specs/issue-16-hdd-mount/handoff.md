# Handoff: issue-16-hdd-mount

## Context

- Tier: 2
- Goal: 14TB HDD（`/dev/sda`）を UUID 指定で永続マウントし、再起動後も再現可能にする

## Must Implement (from tasks.md)

1. inventory に HDD マウント変数追加（`/dev/sda` → `/mnt/archive`）
2. `roles/common` に mount/fstab 管理タスク追加（`ansible.posix.mount`, `state: mounted`）
3. `docs/storage.md` と `docs/operations.md` に反映・確認手順を追記

## Constraints

- 既存 mount（`/`, `/var/lib/rancher`, `/opt`）は変更しない
- HDD の再フォーマットや RAID 化は行わない
- `fstab` は UUID 指定で管理する

## Open Point for Human Approval (before freeze)

- マウントポイント初期案: `/mnt/archive`
