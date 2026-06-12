# Plan: issue-120 - Terraform-managed Cloudflare Tunnel token

## アプローチ

#95 で Cloudflare 側の Tunnel / ingress config を Terraform 正本にしたため、Ansible 側を locally-managed credentials JSON から remotely-managed token connector へ寄せる。Cloudflare Tunnel 自体は `cloudflare_zero_trust_tunnel_cloudflared.llm01` が作成し、Terraform data source で tunnel token を取得する。token は Terraform state / output では sensitive とし、人間が `terraform output -raw tunnel_token` で取得して `secrets/infra.sops.yml` の `cloudflared_tunnel_token` に入れる。

Ansible は SOPS から `cloudflared_tunnel_token` を読み、role へ `vault_cloudflared_tunnel_token` として渡す。role は `/etc/cloudflared/tunnel-token` を mode `0600` で配置し、systemd unit は `cloudflared tunnel run --token-file /etc/cloudflared/tunnel-token` を実行する。token は process args に直接出さない。`config.yml.j2` から `credentials-file:` を削除し、Cloudflare-managed ingress と矛盾しない最小 config にする。

docs/tests は `cloudflared_tunnel_credentials` ではなく `cloudflared_tunnel_token` を正本として扱う。旧 key は runtime path で参照しない。

## 影響範囲 / 主要ファイル

- `infra/cloudflare/tunnel.tf` — tunnel token data source を追加。
- `infra/cloudflare/outputs.tf` — sensitive output `tunnel_token` を追加。
- `roles/cloudflared/defaults/main.yml` — `cloudflared_token_path` など token file path を追加し、credentials path は削除または未使用化。
- `roles/cloudflared/tasks/main.yml` — credentials JSON 配置 task を token file 配置 task に置換。
- `roles/cloudflared/templates/config.yml.j2` — `credentials-file:` を削除。
- `roles/cloudflared/templates/cloudflared.service.j2` — `--token-file {{ cloudflared_token_path }}` を使う。
- `playbooks/22-cloudflare-tunnel.yml` — `cloudflared_tunnel_token` を `vault_cloudflared_tunnel_token` に map し、assert/fail_msg を token 前提へ更新。
- `tests/cloudflare_terraform/test_config.py` — token data source / sensitive output / docs contract test を追加。
- `tests/cloudflared/test_role.py` — token file / `--token-file` / no credentials-file contract へ更新。
- `tests/secrets/test_sops_policy.py` — SOPS/playbook/docs key を `cloudflared_tunnel_token` へ更新。
- `docs/operations.md` — #91 前提手順を tunnel token / SOPS key に更新。
- `docs/security-and-secrets.md` — tunnel token secret 方針と rotation を更新。
- `secrets/README.md` — `cloudflared_tunnel_token` を in-repo encrypted secret として説明。
- `secrets/infra.sops.yml` — key 名を `cloudflared_tunnel_token` に更新。ただし実 token 値はこの実装で commit しない。空 placeholder が必要な場合も token 本体は入れない。

## 設計詳細

### Terraform

`infra/cloudflare/tunnel.tf` に data source を追加する。

```hcl
data "cloudflare_zero_trust_tunnel_cloudflared_token" "llm01" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.llm01.id
}
```

`infra/cloudflare/outputs.tf` に sensitive output を追加する。

```hcl
output "tunnel_token" {
  description = "Cloudflare Tunnel token for cloudflared on llm01. Treat as a secret."
  value       = data.cloudflare_zero_trust_tunnel_cloudflared_token.llm01.token
  sensitive   = true
}
```

### Ansible

`playbooks/22-cloudflare-tunnel.yml` は SOPS 読み込み後に以下の mapping を行う。

```yaml
- name: Cache cloudflared tunnel token
  ansible.builtin.set_fact:
    vault_cloudflared_tunnel_token: "{{ cloudflared_tunnel_token }}"
  no_log: true
```

role defaults は token path を定義する。

```yaml
cloudflared_token_path: /etc/cloudflared/tunnel-token
```

role task は token file を配置する。

```yaml
- name: Deploy cloudflared tunnel token
  ansible.builtin.copy:
    content: "{{ vault_cloudflared_tunnel_token }}"
    dest: "{{ cloudflared_token_path }}"
    owner: root
    group: root
    mode: "0600"
  no_log: true
  notify: Restart cloudflared
  tags: [cloudflared]
```

systemd unit は token file を参照する。

```ini
ExecStart=/usr/bin/cloudflared --no-autoupdate tunnel run --token-file {{ cloudflared_token_path }}
```

### Docs

`docs/operations.md` には次の流れを書く。

1. `terraform -chdir=infra/cloudflare apply`
2. `terraform -chdir=infra/cloudflare output -raw tunnel_id` を `cloudflared_tunnel_id` へ反映
3. `terraform -chdir=infra/cloudflare output -raw tunnel_token` を人間が取得
4. `sops secrets/infra.sops.yml` で `cloudflared_tunnel_token` に格納
5. 値を表示せずに key 存在だけ検証
6. #91 の Ansible check/apply へ進む

## 検討した代替案とトレードオフ

- **credentials JSON を探して SOPS に入れる**
  - 不採用。Terraform が tunnel を作る前提では `cloudflared tunnel create` による locally-managed credentials file は生成されない。#95 の `config_src = "cloudflare"` と逆向き。
- **token を systemd ExecStart に直接埋め込む**
  - 不採用。process args / systemctl status / journal 等に token が出るリスクがある。`--token-file` を使う。
- **Ansible が Cloudflare API から token を取得する**
  - 不採用。Cloudflare provider token を llm01/Ansible 実行時に渡す必要があり、責務が Terraform と重複する。Terraform output -> SOPS -> Ansible の境界が明確。
- **Terraform が SOPS ファイルを直接更新する**
  - 不採用。secret tooling と Terraform state の責務が混ざり、事故時の blast radius が大きい。人間が明示的に SOPS に格納する。

## 検証コマンド

```bash
uvx pytest tests/cloudflare_terraform/ tests/cloudflared/test_role.py tests/secrets/test_sops_policy.py -q
yamllint infra/cloudflare/ roles/cloudflared/ playbooks/22-cloudflare-tunnel.yml docs/operations.md docs/security-and-secrets.md secrets/README.md
ansible-lint roles/cloudflared playbooks/22-cloudflare-tunnel.yml
terraform fmt -check -recursive infra/cloudflare
terraform -chdir=infra/cloudflare init -backend=false
terraform -chdir=infra/cloudflare validate
```

## リスク / ロールバック

- token file 方式で `cloudflared` が起動しない場合は、`systemctl status cloudflared` と journal を確認する。Cloudflare 側 token が stale なら Terraform output から再取得し SOPS を更新する。
- Terraform state に token が入るため、state を secret として扱う既存方針を徹底する。
- rollback は PR revert で credentials-file 方式へ戻せるが、#95 の Terraform-managed tunnel 方針とは再び不整合になるため、原則として token 方式の不具合を修正する。
