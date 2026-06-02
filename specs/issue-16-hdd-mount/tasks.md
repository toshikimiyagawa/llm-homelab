# Tasks: issue-16-hdd-mount

## 実装タスク（順序付き）

- [x] T1: `inventory/group_vars/all/vars.yml` に HDD マウント変数を追加する。少なくとも以下を定義する。対応AC: AC1, AC2
  - `archive_hdd_device: /dev/sda`
  - `archive_hdd_mount_path: /mnt/archive`
  - `archive_hdd_fstype: ext4`
  - `archive_hdd_mount_opts: defaults,nofail`

- [x] T2: `roles/common/defaults/main.yml` に HDD マウント管理フラグを追加する。対応AC: AC3
  - `common_manage_archive_hdd_mount: true`

- [x] T3: `roles/common/tasks/main.yml` に HDD マウント用タスクを追加する。対応AC: AC2, AC3, AC4
  1. `/dev/sda` の UUID を取得（`blkid -s UUID -o value`）
  2. マウントポイント `/mnt/archive` を作成
  3. `ansible.posix.mount` で `src: UUID=<取得UUID>`, `path`, `fstype`, `opts`, `state: mounted` を適用
  4. 既存の `/`, `/var/lib/rancher`, `/opt` mount を変更しない

- [x] T4: `docs/storage.md` を更新し、14TB HDD を運用マウント後の状態へ反映する。対応AC: AC1

- [x] T5: `docs/operations.md` に検証/診断手順を追記する。対応AC: AC5
  - `findmnt /mnt/archive`
  - `lsblk -f | grep -E 'sda|archive'`
  - `sudo mount -a`（エラーが出ないこと）

## テスト（受入条件との対応）

- [x] AC1 → `docs/storage.md` にマウントポイント記載がある
- [x] AC2 → `findmnt /mnt/archive` で `/dev/sda`（UUID ベース）がマウントされる
- [x] AC3 → `ansible-playbook playbooks/01-system.yml` 再実行で不要変更が発生しない
- [x] AC4 → `findmnt / /var/lib/rancher /opt` が従来どおりである
- [x] AC5 → `docs/operations.md` に再起動後確認手順がある

## 完了の定義

- [x] 全 AC 対応の確認手順が docs と実行結果で追跡できる
- [x] `ansible-lint`（変更対象）を実行した結果を提示できる
- [x] `yamllint`（変更対象）を実行した結果を提示できる
- [x] verify フェーズで sdd-reviewer を実行して合格する
