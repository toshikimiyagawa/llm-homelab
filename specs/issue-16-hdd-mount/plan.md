# Plan: issue-16-hdd-mount

## Approach

既存の `common` role に HDD 永続マウント設定を追加し、inventory 変数でマウント対象を定義する。
`ansible.posix.mount` を使って `state: mounted` で適用し、UUID ベースで `fstab` を管理する。

## Impacted Files

- `inventory/group_vars/all/vars.yml`
  - HDD マウント用の変数（デバイス、UUID、マウントポイント、fstype、mount options）を追加
- `roles/common/defaults/main.yml`
  - HDD マウント管理の enable/disable フラグ既定値を追加
- `roles/common/tasks/main.yml`
  - UUID 解決、ディレクトリ作成、mount/fstab 適用タスクを追加
- `docs/storage.md`
  - 14TB HDD を「未マウント」から運用マウント後の記述へ更新
- `docs/operations.md`
  - 検証/診断コマンド（`findmnt`, `lsblk -f`, `mount -a`）を追記

## Alternatives and Tradeoffs

- `/opt/archive` 配下にマウントする案:
  - 既存 `/opt`（NVMe）と混在しやすく、物理デバイス境界が見えにくくなる。
- `/mnt/archive` 案（採用）:
  - Linux運用上の慣例に沿い、独立ボリュームであることが明確。

## Risks / Rollback

- リスク: 誤デバイスを mount 対象にすると運用データ競合の可能性。
- 対策: UUID 固定、事前に `lsblk -f` で ext4/UUID を確認するタスクを入れる。
- ロールバック: mount state を `absent` へ戻し、`fstab` エントリを削除。
