# Spec: issue-118 - devcontainer SOPS / age CLI

- Tier: 1
- Status: frozen
- Issue: #118

## Intent

#91 の Cloudflare Tunnel 実機適用で `playbooks/22-cloudflare-tunnel.yml`
を実行できるように、devcontainer 作成時に SOPS CLI と age CLI を
再現可能にインストールする。

このリポジトリでは Git 管理対象の operational secret を
`secrets/infra.sops.yml` に集約し、Ansible playbook は
`community.sops.load_vars` で復号する。`community.sops` collection だけでは
実行時に `sops` binary が必要なため、Terraform CLI と同じ project tooling
層で SOPS / age CLI を管理する。

## Scope

### In Scope

- `.devcontainer/project-tools.yml` に SOPS CLI の pinned install 手順を追加する。
- `.devcontainer/project-tools.yml` に age / age-keygen CLI の pinned install 手順を追加する。
- `tests/devcontainer/` に SOPS / age CLI が project tools で管理されていることを確認する regression test を追加する。
- `secrets/README.md` に、CLI は devcontainer tooling、age 秘密鍵は `~/.config/sops/age/keys.txt` でユーザー管理という境界を補足する。

### Out of Scope

- `secrets/infra.sops.yml` の復号済み内容を表示、保存、commit すること。
- age 秘密鍵 `~/.config/sops/age/keys.txt` を repository に追加すること。
- Cloudflare Tunnel の実機適用、Terraform apply、`cloudflared_tunnel_id` 設定、Cloudflare Access SSH CA 公開鍵差し替え。
- #91 の手動検証 M-1〜M-5。

## Acceptance Criteria

1. `.devcontainer/project-tools.yml` が SOPS CLI を固定 version でインストールする。
2. `.devcontainer/project-tools.yml` が age と age-keygen を固定 version でインストールする。
3. インストール先は devcontainer 内の通常 PATH から実行できる場所である。
4. `tests/devcontainer/` に SOPS / age CLI が project tools で管理されていることを確認する regression test がある。
5. docs または project tools 内コメントで、SOPS / age CLI は `community.sops.load_vars` による in-repo secret 復号の実行時依存であり、age 秘密鍵そのものは repository 管理外であることが分かる。
6. 実装後の環境で `sops --version`, `age --version`, `age-keygen --version` が実行できる。
7. secret 本体、age 秘密鍵、復号済み一時ファイルが追加されていない。

## Verification

```bash
uvx pytest tests/devcontainer/test_sops_age_cli_tooling.py -q
yamllint .devcontainer/project-tools.yml secrets/README.md
sops --version
age --version
age-keygen --version
```

#91 を再開する前に、age 秘密鍵をローカルの
`~/.config/sops/age/keys.txt` に配置したうえで次を実行する。

```bash
ANSIBLE_SSH_ARGS='-o ControlMaster=no -o ControlPersist=no' \
  ansible-playbook --check playbooks/22-cloudflare-tunnel.yml
```
