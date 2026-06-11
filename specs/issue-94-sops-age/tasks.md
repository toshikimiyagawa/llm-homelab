# Tasks: issue-94 — in-repo secret consumers を SOPS+age に寄せる

> 実装エージェントは `spec.md` とこの `tasks.md` を契約として扱う。`inventory/group_vars/all/vault.yml` はこの issue で解読しない。外部 API key / PAT は #102 に回す。

## Task 1: Tailscale playbook を SOPS 読み込みに切り替える

対応 AC: AC-1, AC-2

Files:

- Modify: `playbooks/07-tailscale.yml`

- [ ] `playbooks/07-tailscale.yml` に SOPS ロードと `tailscale_auth_key` のキャッシュを追加する。

  Result:

  ```yaml
  ---
  - name: Configure Tailscale
    hosts: llm01
    become: true
    pre_tasks:
      - name: Load SOPS infrastructure secrets
        community.sops.load_vars:
          file: secrets/infra.sops.yml
        delegate_to: localhost
        run_once: true
        no_log: true

      - name: Cache Tailscale auth key
        ansible.builtin.set_fact:
          tailscale_auth_key: "{{ tailscale_auth_key }}"
        no_log: true
    roles:
      - tailscale
  ```

- [ ] 変更前後の差分を確認する。

  Run:

  ```bash
  sed -n '1,120p' playbooks/07-tailscale.yml
  ```

  Expected:

  - `community.sops.load_vars` がある
  - `secrets/infra.sops.yml` がある
  - `tailscale_auth_key` を `set_fact` で受け直している
  - `no_log: true` がある

## Task 2: in-repo secret の docs を更新する

対応 AC: AC-3, AC-4, AC-5

Files:

- Modify: `docs/security-and-secrets.md`
- Modify: `docs/software-stack.md`
- Modify: `secrets/README.md`

- [ ] `docs/security-and-secrets.md` に `tailscale_auth_key` を SOPS 管理対象として追記する。

  Required changes:

  - `tailscale_auth_key` が `secrets/infra.sops.yml` の in-repo secret であることを明記する。
  - `grafana_admin_password` が SOPS 管理であることを継続して明記する。
  - 1Password は age 秘密鍵のバックアップであって、通常の in-repo secret の正本ではないことを維持する。

- [ ] `docs/software-stack.md` の Tailscale section を更新する。

  Change:

  ```text
  auth key 種別 | Reusable（1Password "LLM Server Infrastructure" > "Tailscale Auth Key"）
  ```

  To:

  ```text
  auth key 種別 | Reusable（SOPS 管理の `secrets/infra.sops.yml` に保存）
  ```

- [ ] `secrets/README.md` に in-repo secret bundle の説明を追記する。

  Required content:

  ```markdown
  ## In-repo Secrets

  - `secrets/infra.sops.yml` is the SOPS-encrypted bundle for project secrets consumed by Ansible playbooks.
  - Edit it with `sops secrets/infra.sops.yml`.
  - Do not commit plaintext secret files or decrypted temporary outputs.
  - 1Password is only a recovery location for the age private key.
  ```

## Task 3: Static contract tests を Tailscale 対応に拡張する

対応 AC: AC-1, AC-2, AC-3, AC-4, AC-5, AC-6

Files:

- Modify: `tests/secrets/test_sops_policy.py`

- [ ] `tests/secrets/test_sops_policy.py` に Tailscale 用の定数とテストを追加する。

  Add constants:

  ```python
  TAILSCALE_PLAYBOOK = ROOT / "playbooks" / "07-tailscale.yml"
  TAILSCALE_ROLE_TASKS = ROOT / "roles" / "tailscale" / "tasks" / "main.yml"
  SOFTWARE_STACK_DOC = ROOT / "docs" / "software-stack.md"
  ```

  Add tests:

  ```python
  def test_tailscale_playbook_loads_sops_secrets():
      content = TAILSCALE_PLAYBOOK.read_text()
      assert "community.sops.load_vars" in content
      assert "secrets/infra.sops.yml" in content
      assert "tailscale_auth_key" in content
      assert "no_log: true" in content


  def test_tailscale_role_uses_auth_key_directly():
      content = TAILSCALE_ROLE_TASKS.read_text()
      assert "tailscale_auth_key" in content
      assert "community.general.onepassword" not in content
      assert "vault_" not in content


  def test_docs_describe_in_repo_sops_secrets():
      security = SECURITY_DOC.read_text()
      assert "tailscale_auth_key" in security
      assert "grafana_admin_password" in security
      assert "SOPS + age" in security
      assert "1Password" in security


  def test_docs_describe_tailscale_sops_source_of_truth():
      stack = SOFTWARE_STACK_DOC.read_text()
      assert "SOPS 管理の `secrets/infra.sops.yml`" in stack
      assert '1Password "LLM Server Infrastructure" > "Tailscale Auth Key"' not in stack


  def test_secrets_readme_documents_sops_editing():
      content = SECRETS_README.read_text()
      assert "secrets/infra.sops.yml" in content
      assert "sops secrets/infra.sops.yml" in content
      assert "1Password is only a recovery location" in content
  ```

- [ ] Run the focused pytest target before applying the code changes, to confirm the new assertions fail on the current tree.

  Run:

  ```bash
  uvx pytest tests/secrets/test_sops_policy.py -q
  ```

  Expected: fail until Task 1 and Task 2 are implemented.

## Task 4: Verify, lint, and commit

対応 AC: AC-7

- [ ] Run the exact verification commands.

  ```bash
  uvx pytest tests/secrets/test_sops_policy.py
  yamllint docs/security-and-secrets.md docs/software-stack.md secrets/README.md playbooks/07-tailscale.yml
  ansible-lint playbooks/07-tailscale.yml roles/tailscale
  ```

  Expected:

  - `pytest` passes.
  - `yamllint` passes.
  - `ansible-lint` passes for the changed files.

- [ ] Commit the implementation.

  ```bash
  git status --short
  git add playbooks/07-tailscale.yml docs/security-and-secrets.md docs/software-stack.md secrets/README.md tests/secrets/test_sops_policy.py .sdd/state.json .sdd/tasks.json
  git commit -m "feat(issue-94-sops-age-inrepo): move tailscale auth key to sops"
  ```

## 受け入れ基準 → テスト対応

| AC | Test |
|----|------|
| AC-1 | `test_tailscale_playbook_loads_sops_secrets` |
| AC-2 | `test_tailscale_role_uses_auth_key_directly` |
| AC-3 | `test_docs_describe_in_repo_sops_secrets` |
| AC-4 | `test_docs_describe_tailscale_sops_source_of_truth` |
| AC-5 | `test_secrets_readme_documents_sops_editing` |
| AC-6 | `tests/secrets/test_sops_policy.py` 全体 |
| AC-7 | `yamllint` / `ansible-lint` コマンド |
