# Spec: issue-107 - legacy Ansible Vault inventory dependency を SOPS+age へ寄せる

## Background

#93 と #94 で Git 管理対象の operational secret は `secrets/infra.sops.yml` を正本に寄せた。
しかし `inventory/group_vars/all/vault.yml` が Ansible Vault 暗号化ファイルとして残っており、Ansible inventory 読み込み時に vault password file を要求する。

このため、Cloudflare Tunnel credentials 自体は SOPS 管理へ移行済みでも、#91 の `ansible-playbook playbooks/22-cloudflare-tunnel.yml` は `inventory/group_vars/all/vault.yml` の復号で止まる。

## Goal

通常の Ansible 実行経路から legacy Ansible Vault 依存を外し、vault password file なしで inventory を読める状態にする。
in-repo secret の正本は SOPS+age の `secrets/infra.sops.yml` とし、旧 `inventory/group_vars/all/vault.yml` は repository から削除する。

## Non-Goals

- 旧 Ansible Vault の中身を復号して棚卸しすること。
- 外部 API key / PAT の移行を完了すること。これは #102 で扱う。
- Cloudflare Tunnel 実機適用そのもの。これは #91 で扱う。
- Terraform state の長期保管を決めること。これは #101 で扱う。
- SOPS age 秘密鍵や実 secret 値を repository に追加すること。

## Current State

- `secrets/infra.sops.yml` は SOPS encrypted file として存在する。
- `secrets/infra.sops.yml` には以下の in-repo operational secret key がある。
  - `tailscale_auth_key`
  - `grafana_admin_password`
  - `cloudflare_dns01_api_token`
  - `cloudflared_tunnel_credentials`
- `playbooks/07-tailscale.yml`, `playbooks/08-prometheus.yml`, `playbooks/22-cloudflare-tunnel.yml` は `community.sops.load_vars` を使う。
- `inventory/group_vars/all/vault.yml` は Ansible Vault encrypted file として残っており、inventory load 時に vault password を要求する。

## Design

### Source of Truth

Git 管理対象の operational secret は `secrets/infra.sops.yml` を正本にする。
`inventory/group_vars/all/vault.yml` は runtime inventory から削除し、Ansible Vault password file を通常実行手順の前提にしない。

旧 Vault の中身はこの issue では復号しない。
既に SOPS へ移行済みの key を正本とし、もし旧 Vault に未移行の外部 API key / PAT / `k3s_token` が残っていた場合は #102 または別 issue で扱う。

### Ansible Runtime

Ansible inventory は `inventory/group_vars/all/vars.yml` の非機密値と、各 playbook の `community.sops.load_vars` による secret 読み込みに分離する。

通常実行では以下を満たす。

- inventory load は vault password file を要求しない。
- secret が必要な playbook は `community.sops.load_vars` で `secrets/infra.sops.yml` を読む。
- secret を扱う `set_fact` / role task は `no_log: true` を維持する。

### Documentation

docs では、通常の Ansible 実行に `--vault-password-file ~/.vault_pass` を付けない形へ更新する。
SOPS の age 秘密鍵が必要であること、旧 Ansible Vault は repository の通常経路から外れたことを明記する。

historical specs under `specs/issue-*` は過去の設計記録なので、この issue では書き換えない。

## Acceptance Criteria

1. **AC-1**: `inventory/group_vars/all/vault.yml` が repository から削除されている。
2. **AC-2**: `ansible-inventory --list` が vault password file なしで Ansible Vault 復号エラーを出さない。
3. **AC-3**: 通常運用 docs から `--vault-password-file ~/.vault_pass` を前提にした現行手順が削除または SOPS 前提へ更新されている。
4. **AC-4**: `docs/security-and-secrets.md` と `secrets/README.md` が、in-repo operational secret の正本を SOPS+age と説明している。
5. **AC-5**: `tests/secrets/test_sops_policy.py` などの静的テストが、inventory 配下に Ansible Vault encrypted file を置かないことを検証する。
6. **AC-6**: `playbooks/07-tailscale.yml`, `playbooks/08-prometheus.yml`, `playbooks/22-cloudflare-tunnel.yml` が SOPS 由来の secret を読み続けることをテストで検証する。
7. **AC-7**: 平文 secret、age 秘密鍵、復号済み一時ファイルを commit しない既存 guard が維持されている。

## Verification

- `uvx pytest tests/secrets/test_sops_policy.py -q`
- `yamllint docs/security-and-secrets.md docs/software-stack.md secrets/README.md playbooks/07-tailscale.yml playbooks/08-prometheus.yml playbooks/22-cloudflare-tunnel.yml`
- `ansible-inventory --list`
- `git diff --check`

`ansible-inventory --list` は vault password file を指定しない。
SOPS secret の実復号が必要な playbook runtime は #91 / #104 で扱い、この issue では inventory-level の Vault dependency removal を検証する。

## Risks

- 旧 `inventory/group_vars/all/vault.yml` に未移行 secret が残っていた場合、この issue では復号しないため中身を確認できない。
  ただし現在の runtime code が参照している in-repo operational secret は SOPS 側に移行済みであり、未移行候補は #102 側で扱う。
- docs の過去 spec には Ansible Vault 前提の記述が残る。
  historical record として残し、現行運用 docs と tests を正本にする。
