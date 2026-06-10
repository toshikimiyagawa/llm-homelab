# Security and Secrets

## Anthropic API利用ポリシー

許可:

- Anthropic APIキーの利用
- Claude Pro契約のプログラム枠の正規利用
- 人間が`claude`コマンドを起動して使うこと

禁止:

- Claude Pro/MaxのOAuthトークンを第三者ツールに埋め込むこと
- サブスク経由のプログラム的大量利用
- ローカルLLMから`claude`コマンドを自動実行すること

実装ではAPIキー利用を基本にする。

## SOPS + age

このリポジトリの Git 管理対象 secret は、SOPS + age を基本にする。
Git には暗号化済みの `secrets/*.sops.yml` だけを置き、復号鍵は置かない。
Ansible は `community.sops.load_vars` で SOPS ファイルを直接復号し、復号済みの一時 vars ファイルを作らない。

age 秘密鍵:

```text
~/.config/sops/age/keys.txt
```

この `keys.txt` は全 SOPS secret を復号できる強い鍵なので、リポジトリに commit しない。
復旧用バックアップとして、1Password の `LLM Server Infrastructure` vault に
`llm-homelab age private key` という item で保存してよい。
この場合の 1Password は secret 本体の正本ではなく、age 秘密鍵の復旧用保管庫として扱う。

SOPS 管理対象:

- `cloudflare_dns01_api_token`: cert-manager DNS01 用 Cloudflare token
- `cloudflared_tunnel_credentials`: locally-managed Cloudflare Tunnel credentials JSON

通常の Ansible 実行では、ローカルの age 秘密鍵と `secrets/infra.sops.yml` を使う。
1Password lookup は通常経路では使わない。

## 1Password Service Account

1Password Service Account は既存 secret の保管や age 秘密鍵バックアップに使えるが、
新規の Git 管理対象 secret の正本にはしない。
Service Account トークンを使う場合は Mac の Keychain などローカルの安全な場所に保存し、リポジトリには書かない。

## Ansibleでの取得方針

playbook 開始時に `community.sops.load_vars` で `secrets/infra.sops.yml` を読み込み、
必要な値を `no_log: true` の `set_fact` でキャッシュする。
シークレットを含むタスクは必ず `no_log: true` を付ける。

```yaml
- name: Load SOPS infrastructure secrets
  community.sops.load_vars:
    file: secrets/infra.sops.yml
  delegate_to: localhost
  run_once: true
  no_log: true

- name: Cache Cloudflare DNS01 token
  ansible.builtin.set_fact:
    cloudflare_dns01_api_token: "{{ cloudflare_dns01_api_token }}"
  no_log: true
```

## Cloudflare DNS01 API Token

cert-manager の DNS01 チャレンジ用に Cloudflare API Token を使用する。

**最新のトークン形式（2026年時点）:**

| プレフィックス | 種別 |
|--------------|------|
| `cfat_` | Account API Token（新形式） |
| `cfut_` | User API Token |

新規発行したトークンは `cfat_` または `cfut_` プレフィックスを持つ scannable format になる。
`/v4/user/tokens/verify` は account token（`cfat_`）では `Invalid API Token` を返すが、
これはエンドポイントの制約であり、トークン自体が無効なわけではない。
実際の権限確認は `/v4/zones` へのアクセスで行う。

発行方法: Cloudflare ダッシュボード → My Profile → API Tokens → Create Token → **Edit zone DNS** テンプレート

格納場所: `secrets/infra.sops.yml`（SOPS 暗号化）のキー名 `cloudflare_dns01_api_token`

旧方式では `inventory/group_vars/all/vault.yml` の `cloudflare_api_token` に格納していた。
SOPS 移行後は Vault 内の旧 `cloudflare_api_token` を削除し、Cloudflare 側で token rotation を人間が実施する。

## Cloudflare Tunnel credentials

`cloudflared` の locally-managed tunnel（issue #88）が使う credentials JSON（`TunnelSecret` を含む）は機密。

- 格納場所: `secrets/infra.sops.yml`（SOPS 暗号化）のキー名 `cloudflared_tunnel_credentials`
- `roles/cloudflared` が `no_log: true` でホストへ配置し、配置先 `/etc/cloudflared/credentials.json` は mode `0600`
- tunnel ID（`cloudflared_tunnel_id`）と SSH CA 公開鍵（`cloudflare_ca.pub`）は非機密のため通常変数 / `files/` で管理する
- Service Token の `Client Secret` はクライアント側で保持し、リポジトリには置かない。

旧方式では `inventory/group_vars/all/vault.yml` の `vault_cloudflared_tunnel_credentials` に格納していた。
SOPS 移行後は Vault 内の旧 `vault_cloudflared_tunnel_credentials` を削除する。
Tunnel credentials の rotation は Cloudflare Tunnel 再作成を伴うため、人間が運用タスクとして実施する。

## 一時 Cloudflare token

Cloudflare Tunnel / Access 初期構築のための広権限 token は恒久保存しない。
必要な作業中だけ環境変数で渡し、作業後に Cloudflare 側で revoke する。
この token は SOPS、Ansible Vault、リポジトリ、docs のいずれにも保存しない。

## Cloudflare Terraform state

issue #95 以降、Cloudflare 側の DNS / Tunnel / Access は `infra/cloudflare/` の Terraform で管理する。

Terraform provider token は `CLOUDFLARE_API_TOKEN` 環境変数で一時的に渡し、`terraform.tfvars` や `.tf` ファイルには保存しない。import/bootstrap で広い権限の token を使った場合は、作業後に revoke するか権限を縮小する。

`infra/cloudflare/terraform.tfstate` は Cloudflare Tunnel secret や Access Service Token の `Client Secret` を含む可能性があるため secret として扱う。以下は commit しない。

- `infra/cloudflare/terraform.tfstate`
- `infra/cloudflare/terraform.tfstate.backup`
- `infra/cloudflare/.terraform/`
- `infra/cloudflare/terraform.tfvars`
- `infra/cloudflare/*.auto.tfvars`
- `infra/cloudflare/*.tfplan`

`.terraform.lock.hcl` は provider version 固定のため commit してよい。#93 の SOPS+age 基盤が完了した後、Terraform state の長期保管方法は再検討する。

## 禁止事項

- シークレットを平文でcommitしない。
- シークレットをログに出さない。
- age 秘密鍵 `keys.txt` を commit しない。
- 復号済みの `*.plain.yml` / `*.decrypted.yml` / 一時 vars ファイルを commit しない。
- Service Account トークンをコードに記述しない。
- Publicリポジトリに内部情報を不用意に載せない。

## 一時的なsudo運用

初期構築中はCodex/Ansibleが非対話で作業できるよう、`llm01`に以下の広いsudoersを一時設定している。

```sudoers
toshiki ALL=(ALL) NOPASSWD: ALL
```

これは恒久運用には強すぎる。構築が安定したら削除するか、必要なコマンドだけに限定する。

削除する場合:

```bash
sudo rm /etc/sudoers.d/codex
sudo visudo -c
```

限定化する場合の例:

```sudoers
toshiki ALL=(ALL) NOPASSWD: /usr/bin/systemctl, /usr/bin/apt, /usr/bin/install, /usr/bin/mkdir, /usr/bin/chown, /usr/bin/chmod
```

Ansible専用ユーザーを作る場合も、同じく必要範囲だけに限定する。
