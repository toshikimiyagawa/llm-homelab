# Tasks: issue-88 — Cloudflare Tunnel + Access による外部アクセス基盤

> 他 agent が設計コンテキスト無しで実装できるよう、各タスクはファイルパス・内容・テストを具体的に書く。`spec.md`（frozen）の受け入れ基準を過不足なく満たすこと。

## 前提（実装前に人手で一度だけ・docs 記録）

実装に必要な以下は Cloudflare ダッシュボード／`cloudflared` CLI で取得し、出力を所定の場所へ:

- `cloudflared tunnel login` → `cloudflared tunnel create llm01` で **tunnel ID** と **credentials JSON** を生成。
- credentials JSON → `inventory/group_vars/all/vault.yml` の `vault_cloudflared_tunnel_credentials`（Vault 暗号化）。
- DNS ルート: `cloudflared tunnel route dns llm01 <host>` を 4 ホスト分（`open-webui-llm01` / `ollama-llm01` / `vllm-llm01` / `ssh-llm01`.solvelio.com）。
- Zero Trust → Access：Google を IdP 設定、`open-webui-llm01`/`ssh-llm01` に Google ポリシー（ssh は Browser SSH 有効）、`vllm-llm01`/`ollama-llm01` に Service Token ポリシー、Service Token 発行。
- Access SSH の **SSH CA 公開鍵** → `roles/cloudflared/files/cloudflare_ca.pub`。

これらの手順と発行値の所在は Task 12 で `docs/operations.md` に記録する。

---

## Task 1: `roles/cloudflared/defaults/main.yml`

変数を定義:

- `cloudflared_apt_keyring_path`: `/usr/share/keyrings/cloudflare-main.gpg`
- `cloudflared_apt_key_url`: Cloudflare pkg 署名鍵 URL
- `cloudflared_apt_repo`: Cloudflare apt リポジトリ（`https://pkg.cloudflare.com/cloudflared` jammy/noble main 相当）
- `cloudflared_config_dir`: `/etc/cloudflared`
- `cloudflared_config_path`: `/etc/cloudflared/config.yml`
- `cloudflared_credentials_path`: `/etc/cloudflared/credentials.json`
- `cloudflared_tunnel_id`: `""`（実環境値は vars/vault で上書き、非機密）
- `cloudflared_service_name`: `cloudflared`
- `cloudflared_sshd_dropin_path`: `/etc/ssh/sshd_config.d/10-cloudflare.conf`
- `cloudflared_ssh_ca_path`: `/etc/ssh/cloudflare_ca.pub`
- `cloudflared_hostnames`: 4 ホスト名と backend の辞書（open-webui→`http://localhost:8080` / ollama→`http://localhost:11434` / vllm→`https://vllm.solvelio.com`(originServerName) / ssh→`ssh://localhost:22`）

**テスト**: yamllint 無エラー。`tests/cloudflared/test_role.py` が backend 文字列を検出。

---

## Task 2: `roles/cloudflared/handlers/main.yml`

ハンドラ:

- `restart cloudflared` — `ansible.builtin.systemd`（`name: cloudflared`, `state: restarted`）
- `reload sshd` — `ansible.builtin.service`（`name: ssh`, `state: reloaded`）。設定検証はドロップイン配置タスクの `validate` で担保する。

**テスト**: yamllint 無エラー。

---

## Task 3: `roles/cloudflared/files/cloudflare_ca.pub`

Cloudflare Access が発行する SSH CA 公開鍵（非機密）を 1 行で配置する。値は前提セクションの手動取得で得る。

**テスト**: ファイルが存在し、`ssh-rsa ` または `ecdsa-`/`ssh-ed25519 ` で始まる（`tests/cloudflared/test_role.py`）。

---

## Task 4: `roles/cloudflared/templates/config.yml.j2`

```yaml
tunnel: {{ cloudflared_tunnel_id }}
credentials-file: {{ cloudflared_credentials_path }}
ingress:
  - hostname: open-webui-llm01.solvelio.com
    service: http://localhost:8080
  - hostname: ollama-llm01.solvelio.com
    service: http://localhost:11434
  - hostname: vllm-llm01.solvelio.com
    service: https://vllm.solvelio.com
    originRequest:
      originServerName: vllm.solvelio.com
  - hostname: ssh-llm01.solvelio.com
    service: ssh://localhost:22
  - service: http_status:404
```

**テスト (AC-2)**: テンプレートに 4 ホスト名・各 backend・`http_status:404` が含まれる。

---

## Task 5: `roles/cloudflared/templates/sshd-cloudflare.conf.j2`

```text
# Managed by Ansible (roles/cloudflared) — issue #88
TrustedUserCAKeys {{ cloudflared_ssh_ca_path }}
PasswordAuthentication no
```

**テスト (AC-5, AC-6)**: テンプレートに `TrustedUserCAKeys` と `PasswordAuthentication no` が含まれる。

---

## Task 6: `roles/cloudflared/tasks/main.yml`（コア実装）

タスク順:

1. **apt 署名鍵の配置** — `ansible.builtin.get_url` で `cloudflared_apt_keyring_path` に配置。
2. **apt リポジトリ追加** — `ansible.builtin.apt_repository`（`signed-by` 指定）。
3. **cloudflared インストール** — `ansible.builtin.apt`（`name: cloudflared`, `update_cache: true`）。**(AC-1)**
4. **config ディレクトリ作成** — `ansible.builtin.file`（`/etc/cloudflared`, mode 0755）。
5. **credentials 配置** — `ansible.builtin.copy`（`content: "{{ vault_cloudflared_tunnel_credentials }}"`, `dest: {{ cloudflared_credentials_path }}`, mode `0600`）、`no_log: true`。**(AC-4)**
6. **config.yml 配置** — `ansible.builtin.template`（`config.yml.j2` → `cloudflared_config_path`）、notify `restart cloudflared`。**(AC-2)**
7. **cloudflared service enable/start** — `ansible.builtin.systemd`（`enabled: true`, `state: started`）。**(AC-3)**
8. **SSH CA 公開鍵配置** — `ansible.builtin.copy`（`files/cloudflare_ca.pub` → `cloudflared_ssh_ca_path`, mode 0644）。**(AC-5)**
9. **sshd ドロップイン配置** — `ansible.builtin.template`（`sshd-cloudflare.conf.j2` → `cloudflared_sshd_dropin_path`, mode 0644, `validate: "/usr/sbin/sshd -t -f %s"`）、notify `reload sshd`。**(AC-6)**

全タスクに `tags: [cloudflared]` を付ける。

**テスト (AC-4)**: `no_log: true` が credentials タスクに付く。**(AC-8)** 2 回実行で changed=0（手動 idempotency 確認、smoke 環境）。

---

## Task 7: `playbooks/22-cloudflare-tunnel.yml`

```yaml
---
- name: Configure Cloudflare Tunnel and SSH CA trust
  hosts: llm01
  become: true
  pre_tasks:
    - name: Cache cloudflared tunnel credentials
      ansible.builtin.set_fact:
        vault_cloudflared_tunnel_credentials: "{{ vault_cloudflared_tunnel_credentials }}"
      no_log: true
  roles:
    - cloudflared
```

**テスト (AC-9 連動)**: playbook が存在し `cloudflared` role を使う。

---

## Task 8: `playbooks/site.yml` に追記

`21-open-webui.yml` の後に `import_playbook: 22-cloudflare-tunnel.yml` を追加。

**テスト (AC-9)**: `site.yml` に `22-cloudflare-tunnel.yml` が含まれる。

---

## Task 9: `playbooks/23-cloudflare-smoke-test.yml`

`06-gpu-smoke-test.yml` と同じパターンで、`llm01` に対し以下をアサート:

- `cloudflared.service` が active かつ enabled（`ansible.builtin.systemd`/`service_facts`）。
- `sshd -T` の出力に `passwordauthentication no` が含まれる（`command: sshd -T`, `changed_when: false` → `assert`）。
- `sshd -T` の出力に `trustedusercakeys` が含まれる。

**テスト (AC-10)**: smoke-test playbook が上記 3 点を assert する。

---

## Task 10: `tests/cloudflared/test_role.py`（静的契約テスト）

`tests/open_webui/test_role.py` と同じ pathlib 方式。最低限のアサート:

```python
from pathlib import Path

ROOT = Path(__file__).parents[2]
ROLE = ROOT / "roles" / "cloudflared"
DEFAULTS = ROLE / "defaults" / "main.yml"
TASKS = ROLE / "tasks" / "main.yml"
CONFIG_TMPL = ROLE / "templates" / "config.yml.j2"
SSHD_TMPL = ROLE / "templates" / "sshd-cloudflare.conf.j2"
CA_PUB = ROLE / "files" / "cloudflare_ca.pub"
PLAYBOOK = ROOT / "playbooks" / "22-cloudflare-tunnel.yml"
SMOKE = ROOT / "playbooks" / "23-cloudflare-smoke-test.yml"
SITE = ROOT / "playbooks" / "site.yml"
OPS_DOC = ROOT / "docs" / "operations.md"


def test_apt_install_present():          # AC-1
    t = TASKS.read_text()
    assert "apt_repository" in t and "cloudflared" in t

def test_config_has_all_hostnames():     # AC-2
    c = CONFIG_TMPL.read_text()
    for h in ["open-webui-llm01.solvelio.com", "ollama-llm01.solvelio.com",
              "vllm-llm01.solvelio.com", "ssh-llm01.solvelio.com"]:
        assert h in c
    assert "http://localhost:8080" in c
    assert "http://localhost:11434" in c
    assert "ssh://localhost:22" in c
    assert "http_status:404" in c

def test_service_enabled():              # AC-3
    assert "enabled: true" in TASKS.read_text()

def test_credentials_no_log_and_mode():  # AC-4
    t = TASKS.read_text()
    assert "no_log: true" in t
    assert "0600" in t

def test_sshd_ca_trust():                # AC-5
    assert "TrustedUserCAKeys" in SSHD_TMPL.read_text()
    assert CA_PUB.exists()

def test_sshd_password_auth_off():       # AC-6
    assert "PasswordAuthentication no" in SSHD_TMPL.read_text()
    assert "validate:" in TASKS.read_text()

def test_site_imports_playbook():        # AC-9
    assert "22-cloudflare-tunnel.yml" in SITE.read_text()

def test_smoke_asserts_runtime():        # AC-10
    s = SMOKE.read_text()
    assert "passwordauthentication no" in s.lower()
    assert "trustedusercakeys" in s.lower()
    assert "cloudflared" in s
```

**テスト**: `uvx pytest tests/cloudflared/test_role.py` が全件 green。

---

## Task 11: docs 追記

- `docs/operations.md`: 前提セクションの手動セットアップ手順（tunnel 作成 / DNS / Access / Service Token / Google IdP）と、運用検証チェックリスト **M-1〜M-5**、Service Token を使う API クライアント例（`CF-Access-Client-Id`/`CF-Access-Client-Secret` ヘッダ）。
- `docs/security-and-secrets.md`: `vault_cloudflared_tunnel_credentials` の格納方針（Vault 暗号化 / `no_log` / mode 0600）を追記。

**テスト**: `tests/cloudflared/test_role.py` で `docs/operations.md` に各ホスト名と "Service Token" が含まれることをアサート（任意で追加）。

---

## Task 12: lint

```bash
yamllint roles/cloudflared/ playbooks/22-cloudflare-tunnel.yml playbooks/23-cloudflare-smoke-test.yml
ansible-lint roles/cloudflared playbooks/22-cloudflare-tunnel.yml playbooks/23-cloudflare-smoke-test.yml
```

**テスト (AC-7)**: エラー 0 件。`var-naming[no-role-prefix]` を避けるため role 変数は `cloudflared_` prefix にする。

---

## Task 13: `.sdd/state.json` を verify に更新

実装完了後:

```json
{ "feature": "issue-88-cloudflare-tunnel", "tier": 2, "phase": "verify", "spec": "specs/issue-88-cloudflare-tunnel/" }
```

その後 `sdd-reviewer` を diff に対して実行する。

---

## 受け入れ基準 → テストマッピング

| AC | テスト |
|----|--------|
| AC-1 apt install | `test_apt_install_present` |
| AC-2 ingress 4 ホスト | `test_config_has_all_hostnames` |
| AC-3 systemd enabled | `test_service_enabled` + smoke-test |
| AC-4 no_log / 0600 | `test_credentials_no_log_and_mode` |
| AC-5 SSH CA 信頼 | `test_sshd_ca_trust` + smoke-test |
| AC-6 PasswordAuthentication no | `test_sshd_password_auth_off` + smoke-test |
| AC-7 lint green | Task 12 |
| AC-8 冪等性 | Task 6（2 回実行 changed=0） |
| AC-9 site.yml | `test_site_imports_playbook` |
| AC-10 smoke runtime | `test_smoke_asserts_runtime` + `23-cloudflare-smoke-test.yml` |
| M-1〜M-5 手動 | `docs/operations.md` チェックリスト |

## 完了の定義

- [ ] 全 AC（自動）対応テストが green（`uvx pytest tests/cloudflared/`）
- [ ] `ansible-lint` / `yamllint` green
- [ ] `23-cloudflare-smoke-test.yml` が llm01 で pass
- [ ] M-1〜M-5 を手動確認し `docs/operations.md` に記録
- [ ] CI green
- [ ] `sdd-reviewer` 合格
