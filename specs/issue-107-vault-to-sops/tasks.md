# Tasks: issue-107 - legacy Ansible Vault inventory dependency を SOPS+age へ寄せる

> 実装エージェントは `spec.md` とこの `tasks.md` を契約として扱う。旧 `inventory/group_vars/all/vault.yml` は復号しない。未知の secret 移行はこの issue の範囲外。

## Task 1: Static tests for removing the inventory Vault dependency

対応 AC: AC-2, AC-3, AC-5, AC-7

Files:

- Modify: `tests/secrets/test_sops_policy.py`

- [ ] Add constants near the existing path constants.

  ```python
  INVENTORY_DIR = ROOT / "inventory"
  ```

- [ ] Add a test that rejects committed Ansible Vault files under `inventory/`.

  ```python
  def test_inventory_has_no_ansible_vault_encrypted_files():
      for path in INVENTORY_DIR.rglob("*"):
          if path.is_file():
              assert not path.read_text(errors="ignore").startswith("$ANSIBLE_VAULT"), (
                  f"{path.relative_to(ROOT)} must not be an Ansible Vault file; "
                  "use secrets/infra.sops.yml for in-repo operational secrets"
              )
  ```

- [ ] Add a test that current operational docs do not require a vault password file.

  ```python
  def test_current_docs_do_not_require_ansible_vault_password_file():
      docs = [
          SECURITY_DOC,
          SOFTWARE_STACK_DOC,
          SECRETS_README,
      ]
      for path in docs:
          content = path.read_text()
          assert "--vault-password-file" not in content
          assert "~/.vault_pass" not in content
  ```

- [ ] Update the existing Vault migration documentation test so it no longer requires the old Vault variable names as current documentation.

  Replace `test_docs_describe_vault_migration_and_rotation` with:

  ```python
  def test_docs_describe_sops_migration_and_rotation():
      content = SECURITY_DOC.read_text() + "\n" + OPERATIONS_DOC.read_text()
      assert "cloudflare_dns01_api_token" in content
      assert "cloudflared_tunnel_credentials" in content
      assert "tailscale_auth_key" in content
      assert "SOPS" in content
      assert "rotate" in content.lower() or "rotation" in content.lower()
  ```

- [ ] Run the focused test before implementation changes to confirm the new inventory Vault guard fails while `inventory/group_vars/all/vault.yml` still exists.

  ```bash
  uvx pytest tests/secrets/test_sops_policy.py -q
  ```

  Expected: fail on `test_inventory_has_no_ansible_vault_encrypted_files` until Task 2 removes the Vault file.

## Task 2: Remove the legacy Ansible Vault inventory file

対応 AC: AC-1, AC-2, AC-5

Files:

- Delete: `inventory/group_vars/all/vault.yml`

- [ ] Delete the legacy encrypted inventory file.

  ```bash
  git rm inventory/group_vars/all/vault.yml
  ```

- [ ] Confirm it is no longer tracked.

  ```bash
  git ls-files inventory/group_vars/all/vault.yml
  ```

  Expected: no output.

- [ ] Run inventory loading without a vault password file.

  ```bash
  ansible-inventory --list
  ```

  Expected: command succeeds and does not print `Attempting to decrypt but no vault secrets found`.

## Task 3: Update current operations and secret docs

対応 AC: AC-3, AC-4

Files:

- Modify: `docs/security-and-secrets.md`
- Modify: `docs/software-stack.md`
- Modify: `secrets/README.md`

- [ ] In `docs/security-and-secrets.md`, update the SOPS section to explicitly state that `inventory/group_vars/all/vault.yml` is not part of the normal runtime path.

  Required wording:

  ```markdown
  Ansible Vault is no longer used for normal in-repo operational secrets. Do not add
  `inventory/group_vars/all/vault.yml`; inventory must load without a vault password file.
  ```

- [ ] In `docs/software-stack.md`, remove `--vault-password-file ~/.vault_pass` from current Ansible commands.

  Replace commands like:

  ```bash
  ansible-playbook playbooks/09-vllm.yml --vault-password-file ~/.vault_pass
  ```

  with:

  ```bash
  ansible-playbook playbooks/09-vllm.yml
  ```

  Apply the same replacement to current commands for `playbooks/21-open-webui.yml` and `playbooks/08-prometheus.yml`.

- [ ] In `secrets/README.md`, add a note under the Ansible section.

  Required wording:

  ```markdown
  Do not add Ansible Vault files under `inventory/`; inventory loading must not require
  `--vault-password-file`.
  ```

## Task 4: Verify SOPS playbook contracts still pass

対応 AC: AC-4, AC-6, AC-7

Files:

- Check: `playbooks/07-tailscale.yml`
- Check: `playbooks/08-prometheus.yml`
- Check: `playbooks/22-cloudflare-tunnel.yml`
- Check: `tests/secrets/test_sops_policy.py`

- [ ] Run the SOPS static contract tests.

  ```bash
  uvx pytest tests/secrets/test_sops_policy.py -q
  ```

  Expected: all tests pass.

- [ ] Run YAML lint for changed docs and playbooks.

  ```bash
  yamllint docs/security-and-secrets.md docs/software-stack.md secrets/README.md playbooks/07-tailscale.yml playbooks/08-prometheus.yml playbooks/22-cloudflare-tunnel.yml
  ```

  Expected: no lint errors.

- [ ] Run inventory load without a vault password file.

  ```bash
  ansible-inventory --list
  ```

  Expected: command succeeds and emits JSON/YAML inventory data. It must not fail with an Ansible Vault decrypt error.

- [ ] Check whitespace.

  ```bash
  git diff --check
  ```

  Expected: no output.

## Task 5: Mark SDD task complete and commit

対応 AC: AC-1 through AC-7

Files:

- Modify: `.sdd/tasks.json`

- [ ] Update `.sdd/tasks.json` entry `issue-107-vault-to-sops` to `status: "completed"` after all verification commands pass.

- [ ] Confirm the final diff contains only #107 files.

  ```bash
  git status --short
  git diff --stat
  ```

- [ ] Commit the implementation.

  ```bash
  git add inventory/group_vars/all/vault.yml tests/secrets/test_sops_policy.py docs/security-and-secrets.md docs/software-stack.md secrets/README.md .sdd/tasks.json
  git commit -m "feat(issue-107-vault-to-sops): remove legacy ansible vault dependency"
  ```

## Acceptance Criteria to Tests

| AC | Test / Command |
|----|----------------|
| AC-1 | `git ls-files inventory/group_vars/all/vault.yml`; `test_inventory_has_no_ansible_vault_encrypted_files` |
| AC-2 | `ansible-inventory --list` without vault password file |
| AC-3 | `test_current_docs_do_not_require_ansible_vault_password_file` |
| AC-4 | `test_security_docs_describe_sops_age_policy`; `test_secrets_readme_documents_sops_editing` |
| AC-5 | `test_inventory_has_no_ansible_vault_encrypted_files` |
| AC-6 | `test_tailscale_playbook_loads_sops_secrets`; `test_prometheus_playbook_loads_sops_secrets`; `test_cloudflared_playbook_loads_sops_credentials` |
| AC-7 | `test_no_forbidden_secret_files_are_committed`; `git diff --check` |
