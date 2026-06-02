# Tasks: issue-17 — Tailscale 導入

## Task 1: defaults/main.yml を作成する

`roles/tailscale/defaults/main.yml` を作成する。

変数:
- `tailscale_package`: `tailscale`
- `tailscale_service_name`: `tailscaled`
- `tailscale_apt_repo_url`: Tailscale 公式 APT リポジトリ URL（stable）
- `tailscale_up_flags`: `""` （追加フラグ用、デフォルト空）

**テスト**: yamllint でエラーなし

---

## Task 2: handlers/main.yml を作成する

`roles/tailscale/handlers/main.yml` を作成する。

ハンドラ:
- `restart tailscaled` — `ansible.builtin.systemd` で tailscaled を restart

**テスト**: yamllint でエラーなし

---

## Task 3: tasks/main.yml を作成する（コア実装）

`roles/tailscale/tasks/main.yml` を作成する。タスク順:

1. **Tailscale APT 署名鍵の追加** — `ansible.builtin.get_url` で keyring に配置
2. **Tailscale APT リポジトリの追加** — `ansible.builtin.apt_repository`
3. **tailscale パッケージのインストール** — `ansible.builtin.apt`
4. **tailscaled サービスの enable/start** — `ansible.builtin.systemd`
5. **接続状態の確認** — `ansible.builtin.command: tailscale status --json`、`register: tailscale_status`、`changed_when: false`、`failed_when: false`
6. **tailscale up の実行** — `ansible.builtin.command: tailscale up --auth-key={{ tailscale_auth_key }}` の実行、`no_log: true`、`when: tailscale_status.rc != 0 or 'Running' not in tailscale_status.stdout`

全タスクに `tags: [tailscale]` を付ける。

**テスト (AC-1)**: 2 回実行で changed=0  
**テスト (AC-5)**: `no_log: true` が tailscale up タスクに付いていること（コードレビューで確認）

---

## Task 4: playbooks/07-tailscale.yml を作成する

```yaml
---
- name: Configure Tailscale
  hosts: llm01
  become: true
  vars:
    tailscale_auth_key: "{{ lookup('community.general.onepassword',
                                   'Tailscale Auth Key',
                                   vault='LLM Server Infrastructure') }}"
  pre_tasks:
    - name: Set tailscale_auth_key fact
      ansible.builtin.set_fact:
        tailscale_auth_key: "{{ tailscale_auth_key }}"
      no_log: true
  roles:
    - tailscale
```

**テスト (AC-5)**: `no_log: true` が set_fact タスクに付いていること

---

## Task 5: docs/software-stack.md に Tailscale セクションを追記する

「周辺サービス」セクションの Tailscale 項目に以下の情報を追記:

- インストール方法（APT）
- auth key 種別（Reusable、1Password管理）
- 接続確認コマンド
- ACL は admin console で管理する旨

---

## Task 6: lint を実行して全件グリーンを確認する

```bash
yamllint roles/tailscale/ playbooks/07-tailscale.yml
ansible-lint roles/tailscale/ playbooks/07-tailscale.yml
```

**テスト (AC-6)**: エラー 0 件

---

## Task 7: .sdd/state.json を更新する

```json
{
  "feature": "issue-17-tailscale",
  "tier": 2,
  "phase": "implement"
}
```

---

## 受け入れ基準 → タスクマッピング

| AC | タスク |
|----|--------|
| AC-1 冪等性 | Task 3 (条件付き tailscale up) |
| AC-2 サービス running | Task 3 (systemd enable/start) |
| AC-3 tailscale status | Task 3 (status チェック) |
| AC-4 再起動後自動復帰 | Task 3 (systemd enabled=true) |
| AC-5 no_log | Task 3, 4 |
| AC-6 lint グリーン | Task 6 |
