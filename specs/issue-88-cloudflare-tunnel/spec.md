# Spec: issue-88 — Cloudflare Tunnel + Access による外部アクセス基盤

**Status**: frozen
**Tier**: 2
**Issue**: #88

## 目的

会社管理の Mac（追加ソフト導入不可・ブラウザと標準 `ssh` のみ・外出先では outbound 443 のみのことがある）から、自宅 `llm01` の SSH / Open WebUI / vLLM / Ollama へ安全にアクセスできるようにする。ルーターのインバウンド開放は行わず、`cloudflared` が `llm01` から外向き（443/QUIC）にトンネルを張る方式を、Ansible で再現可能・冪等に構築する。

## スコープ

### 含む

- `roles/cloudflared/` Ansible role の新規作成（apt install / `config.yml`(ingress) / systemd / credentials 配置）
- locally-managed tunnel の `config.yml`（4 ホスト名 ingress）テンプレート
- tunnel credentials JSON を Ansible Vault（`inventory/group_vars/all/vault.yml`）で管理し、`no_log: true` でホストへ配置
- sshd ドロップイン: Cloudflare SSH CA 信頼（`TrustedUserCAKeys`）+ ハードニング（`PasswordAuthentication no`）+ `validate`/`sshd -t` 検証 → reload handler
- `playbooks/22-cloudflare-tunnel.yml` 新規 + `playbooks/site.yml` への追記
- `playbooks/23-cloudflare-smoke-test.yml`（`llm01` 側ランタイム AC の自動アサート）
- `tests/cloudflared/test_role.py` 静的設定テスト
- `docs/operations.md`（手動セットアップ手順 + 運用検証チェックリスト）/ `docs/security-and-secrets.md`（tunnel credentials のシークレット方針）への追記

### 含まない

- Cloudflare ダッシュボード側の作成操作の自動化（tunnel 作成 / DNS ルート / Access Application / Service Token 発行 / Google IdP 設定）= 一度きりの手動操作とし、出力を docs に記録（Terraform 化は将来 issue）
- vLLM / Ollama 自体への api-key 付与（多層防御の層B）= 今回は層A（Cloudflare Access Service Token）のみ
- 既存 `vllm.solvelio.com` / `open-webui.solvelio.com`（DNS-only → Tailscale 経路）の変更
- ルーターのインバウンドポート開放
- Ollama / Open WebUI の bind 変更（現状維持）

## 設計決定

| 項目 | 決定 | 理由 |
|------|------|------|
| 接続方式 | Cloudflare Tunnel（outbound）+ Cloudflare Access | インバウンド開放不要・全経路 443 で貫通（outbound 22 ブロック環境でも可） |
| tunnel 種別 | locally-managed（credentials-file 方式） | ingress を `config.yml` として版管理＝OS 再インストール時の再現性 |
| ホスト名 | `<svc>-llm01.solvelio.com`（1 階層） | 無料 Universal SSL `*.solvelio.com` でカバー（2 階層は ACM 課金が必要なため回避） |
| Web UI backend | `http://localhost:8080` | hostNetwork 直バインド、Traefik 不要で最小構成 |
| Ollama backend | `http://localhost:11434` | loopback 直結（cloudflared は同ホスト）。bind は変更しない |
| vLLM backend | 既存 Traefik ingress 経由 | vLLM は k8s ClusterIP のためホスト直ポートが無い |
| ブラウザ認証 | Access: Google ログイン | 本人のみ許可、Zero Trust に Google を IdP 設定 |
| API 認証 | Access: Service Token（層A のみ） | プログラムクライアント向け。エッジで未認証を遮断（GPU を露出させない） |
| SSH | Browser-rendered SSH + Cloudflare 短命 SSH 証明書 | クライアントにソフト不要・outbound 22 ブロック対応 |
| シークレット | Ansible Vault `inventory/group_vars/all/vault.yml` | 既存 `cloudflare_api_token` と同方針 |

## 受け入れ基準（自動検証）

各 AC は `tasks.md` でテスト（静的 pytest / smoke-test playbook / lint）に対応させる。

1. **AC-1**: `roles/cloudflared` が Cloudflare 公式 apt リポジトリを追加し、`cloudflared` パッケージをインストールする。
2. **AC-2**: `config.yml` テンプレートが 4 ホスト名 → backend の ingress を定義する。`open-webui-llm01.solvelio.com`→`http://localhost:8080`、`ollama-llm01.solvelio.com`→`http://localhost:11434`、`vllm-llm01.solvelio.com`→Traefik 経由、`ssh-llm01.solvelio.com`→`ssh://localhost:22`、末尾に catch-all（`http_status:404`）を持つ。
3. **AC-3**: `cloudflared` が systemd サービスとして enable され、再起動後も自動起動する（systemd enabled）。
4. **AC-4**: tunnel credentials を扱うタスクに `no_log: true` が付き、credentials は Vault キー参照で平文を含まない。配置先ファイルは mode `0600`。
5. **AC-5**: sshd ドロップインが `TrustedUserCAKeys` で Cloudflare SSH CA 公開鍵を信頼する。
6. **AC-6**: sshd ドロップインが `PasswordAuthentication no` を設定し、適用は `validate`（`sshd -t`）検証 → reload handler 経由で行う。
7. **AC-7**: `ansible-lint` と `yamllint` が `roles/cloudflared` および新規 playbook で無エラー。
8. **AC-8**: 冪等性 — `playbooks/22-cloudflare-tunnel.yml` を 2 回実行して 2 回目が changed=0。
9. **AC-9**: `playbooks/site.yml` が `22-cloudflare-tunnel.yml` を含む。
10. **AC-10**: `playbooks/23-cloudflare-smoke-test.yml` が、`cloudflared.service` の active/enabled、`sshd -T` の `passwordauthentication no`、`trustedusercakeys` 設定をアサートする。

## 受け入れ基準（手動・運用検証）

Cloudflare エッジ／外部クライアント挙動に依存し自動化できないため、`docs/operations.md` の検証チェックリストとして人手で確認する（完了条件）。

- **M-1**: 外出先 Mac のブラウザ（outbound 443 のみ）から Access(Google) 認証経由で `open-webui-llm01.solvelio.com` が開ける。
- **M-2**: 同 Mac のブラウザから Browser SSH（`ssh-llm01.solvelio.com`）で `llm01` にログインできる（outbound 22 ブロックでも可）。
- **M-3**: Service Token を付けた API クライアントから `vllm-llm01` / `ollama-llm01` が応答し、トークン無しは 403。
- **M-4**: ルーターのインバウンド開放はゼロ。
- **M-5**: OS 再インストール後、`ansible-playbook` 再実行のみで M-1〜M-3 が復活する。

## シークレット管理

`cloudflared tunnel create` が生成する credentials JSON（tunnel 秘密鍵を含む）を Ansible Vault に格納し、ホストへ mode `0600` で配置する。tunnel ID（非機密）は通常変数で持つ。

```yaml
# inventory/group_vars/all/vault.yml（Ansible Vault 暗号化）
vault_cloudflared_tunnel_credentials: |
  { "AccountTag": "...", "TunnelID": "...", "TunnelSecret": "..." }
```

```yaml
# roles/cloudflared/tasks/main.yml（抜粋）
- name: Deploy cloudflared tunnel credentials
  ansible.builtin.copy:
    content: "{{ vault_cloudflared_tunnel_credentials }}"
    dest: "{{ cloudflared_credentials_path }}"
    owner: root
    group: root
    mode: "0600"
  no_log: true
```

Cloudflare SSH CA 公開鍵（非機密）は `cloudflared` の Access SSH 設定から取得して `roles/cloudflared/files/cloudflare_ca.pub` に置く（公開鍵のため Vault 不要）。

## テスト方針

Molecule / 本番ホストへの直接接続は必須としない。以下で代替・補完する。

- **静的**: `tests/cloudflared/test_role.py` を `uvx pytest tests/cloudflared/test_role.py` で実行（環境に合わせ `uvx pytest` を正準とする。issue #75 参照）。role ファイルの契約（apt repo / 4 ホスト名 ingress / systemd / no_log / sshd ドロップイン / playbook・site.yml・docs）をアサート。
- **ランタイム（llm01 側）**: `playbooks/23-cloudflare-smoke-test.yml` を `ansible-playbook` で実行し AC-10 を自動アサート。
- **lint**: `yamllint roles/cloudflared/ playbooks/22-cloudflare-tunnel.yml` / `ansible-lint roles/cloudflared playbooks/22-cloudflare-tunnel.yml`。
- **手動**: `docs/operations.md` のチェックリスト（M-1〜M-5）。
