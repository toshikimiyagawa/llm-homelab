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

## 1Password Service Account

専用Vault:

```text
LLM Server Infrastructure
```

格納するシークレット:

- Tailscale Auth Key
- Anthropic API Key
- Google AI API Key
- k3s Token
- GitHub Personal Access Token

環境変数例:

```bash
export OP_SERVICE_ACCOUNT_TOKEN="$(security find-generic-password \
  -s 'op-service-account-llm' -w)"
```

Service AccountトークンはMacのKeychainに保存し、リポジトリには書かない。

## Ansibleでの取得方針

playbook開始時に1回だけ取得してキャッシュする。レート制限とログ漏洩を避けるため、シークレットを含むタスクは必ず`no_log: true`を付ける。

```yaml
- name: Cache secrets at start
  ansible.builtin.set_fact:
    secrets:
      tailscale: "{{ lookup('community.general.onepassword',
                            'Tailscale Auth Key',
                            vault='LLM Server Infrastructure') }}"
      anthropic: "{{ lookup('community.general.onepassword',
                            'Anthropic API Key',
                            vault='LLM Server Infrastructure') }}"
  no_log: true
  delegate_to: localhost
  run_once: true
```

## 禁止事項

- シークレットを平文でcommitしない。
- シークレットをログに出さない。
- Service Accountトークンをコードに記述しない。
- Service AccountからアクセスできないPrivate Vaultを参照しない。
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
