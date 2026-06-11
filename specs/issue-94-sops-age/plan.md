# issue-94-sops-age Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the repo's remaining in-repo secret consumers to SOPS+age by sourcing Tailscale auth key from `secrets/infra.sops.yml` and documenting SOPS as the in-repo secret source of truth.

**Architecture:** Keep the secret source centralized in `secrets/infra.sops.yml`, load it at playbook start with `community.sops.load_vars`, and keep roles consuming ordinary variables. Update the docs so the in-repo secret model is explicit, while leaving external API keys / PATs for a separate issue.

**Tech Stack:** Ansible, `community.sops`, SOPS, age, pytest static contract tests, yamllint, ansible-lint.

---

## File Structure

| Path | Responsibility |
|------|----------------|
| `playbooks/07-tailscale.yml` | Load SOPS secrets and pass `tailscale_auth_key` to the Tailscale role. |
| `docs/security-and-secrets.md` | Explain that in-repo secret consumers use SOPS+age, including Tailscale auth key and Grafana admin password. |
| `docs/software-stack.md` | Update the Tailscale section to point at SOPS rather than 1Password as the secret source. |
| `secrets/README.md` | Document `secrets/infra.sops.yml` as the editable in-repo secret bundle and how to edit it. |
| `tests/secrets/test_sops_policy.py` | Static contract tests for Tailscale/Grafana SOPS usage and docs consistency. |

## Approach

Use the existing `secrets/infra.sops.yml` file as the single in-repo secret bundle. `playbooks/07-tailscale.yml` should load that file at playbook start, then copy the decrypted `tailscale_auth_key` into an Ansible fact with `no_log: true` before calling `roles/tailscale`.

`roles/tailscale` should remain unchanged unless the tests reveal an actual contract mismatch. The role already accepts `tailscale_auth_key`; the work here is to change the source of that value and document the source of truth.

The docs should be explicit that in-repo operational secrets are stored in SOPS and that 1Password is only a recovery location for the age private key. External API keys / PATs stay out of scope and are tracked separately in #102.

## Tradeoffs

- `community.sops.load_vars` over shelling out to `sops -d`: avoids plaintext temporary files and keeps the playbook flow consistent with the existing Cloudflare SOPS pattern.
- Keep the Tailscale role unchanged: minimizes churn and isolates the change to the secret source.
- Treat external API keys / PATs as a separate issue: prevents this work from becoming a broad secret migration with mixed ownership and rotation rules.

## Verification

- `uvx pytest tests/secrets/test_sops_policy.py`
- `yamllint docs/security-and-secrets.md docs/software-stack.md secrets/README.md playbooks/07-tailscale.yml`
- `ansible-lint playbooks/07-tailscale.yml roles/tailscale`

## Acceptance Criteria Mapping

| AC | Implementation / Test |
|----|------------------------|
| AC-1 Tailscale playbook loads SOPS | `playbooks/07-tailscale.yml`; `test_tailscale_playbook_loads_sops_secrets` |
| AC-2 role consumes auth key directly | `roles/tailscale/tasks/main.yml`; `test_tailscale_role_uses_auth_key_directly` |
| AC-3 security docs updated | `docs/security-and-secrets.md`; `test_docs_describe_in_repo_sops_secrets` |
| AC-4 software stack docs updated | `docs/software-stack.md`; `test_docs_describe_tailscale_sops_source_of_truth` |
| AC-5 secrets README updated | `secrets/README.md`; `test_secrets_readme_documents_sops_editing` |
| AC-6 static tests added | `tests/secrets/test_sops_policy.py` |
| AC-7 lint stays green for changed files | verification commands above |

## Task 1: Load SOPS secrets in the Tailscale playbook

対応 AC: AC-1, AC-2

Files:

- Modify: `playbooks/07-tailscale.yml`

- [ ] Update `playbooks/07-tailscale.yml` so it loads `secrets/infra.sops.yml` before the Tailscale role runs.

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

- [ ] Run the playbook-focused static contract test before implementing the file change, to confirm it fails against the old version.

  Run:

  ```bash
  uvx pytest tests/secrets/test_sops_policy.py -q
  ```

  Expected: the new Tailscale assertions fail until the playbook is updated.

## Task 2: Update the secret-management docs

対応 AC: AC-3, AC-4, AC-5

Files:

- Modify: `docs/security-and-secrets.md`
- Modify: `docs/software-stack.md`
- Modify: `secrets/README.md`

- [ ] Update `docs/security-and-secrets.md` to describe `tailscale_auth_key` and `grafana_admin_password` as SOPS-managed in-repo secrets.

  Required outcomes:

  - The SOPS+age section explicitly names `tailscale_auth_key` as an in-repo secret source of truth.
  - The docs continue to say `grafana_admin_password` is SOPS-managed.
  - 1Password is described as age private key backup only, not as the normal in-repo secret source.

- [ ] Update `docs/software-stack.md` Tailscale section so the auth key is described as coming from `secrets/infra.sops.yml`, not from 1Password.

  Replace the old guidance:

  ```text
  auth key 種別 | Reusable（1Password "LLM Server Infrastructure" > "Tailscale Auth Key"）
  ```

  with wording that points to the SOPS-managed source of truth:

  ```text
  auth key 種別 | Reusable（SOPS 管理の `secrets/infra.sops.yml` に保存）
  ```

- [ ] Update `secrets/README.md` to explain that `secrets/infra.sops.yml` is the editable SOPS bundle for in-repo secret consumers.

  Required content:

  ```markdown
  ## In-repo Secrets

  - `secrets/infra.sops.yml` is the SOPS-encrypted bundle for project secrets consumed by Ansible playbooks.
  - Edit it with `sops secrets/infra.sops.yml`.
  - Do not commit plaintext secret files or decrypted temporary outputs.
  - 1Password is only a recovery location for the age private key.
  ```

## Task 3: Add static contract tests for the new secret source of truth

対応 AC: AC-1, AC-2, AC-3, AC-4, AC-5, AC-6

Files:

- Modify: `tests/secrets/test_sops_policy.py`

- [ ] Extend `tests/secrets/test_sops_policy.py` with Tailscale-specific assertions.

  Add imports/constants:

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

- [ ] Run the focused test file against the current tree before editing, to confirm the new coverage fails on the old Tailscale playbook/docs.

  Run:

  ```bash
  uvx pytest tests/secrets/test_sops_policy.py -q
  ```

  Expected: the new Tailscale assertions fail until Tasks 1 and 2 are implemented.

## Task 4: Run lint and finalize

対応 AC: AC-7

- [ ] Run the focused verification commands after implementation.

  ```bash
  uvx pytest tests/secrets/test_sops_policy.py
  yamllint docs/security-and-secrets.md docs/software-stack.md secrets/README.md playbooks/07-tailscale.yml
  ansible-lint playbooks/07-tailscale.yml roles/tailscale
  ```

  Expected:

  - `pytest` passes.
  - `yamllint` passes.
  - `ansible-lint` passes for the changed files.

- [ ] Commit the #94 implementation once verification passes.

  ```bash
  git status --short
  git add playbooks/07-tailscale.yml docs/security-and-secrets.md docs/software-stack.md secrets/README.md tests/secrets/test_sops_policy.py .sdd/state.json .sdd/tasks.json
  git commit -m "feat(issue-94-sops-age-inrepo): move tailscale auth key to sops"
  ```

## Acceptance Criteria → Test Matrix

| AC | Test |
|----|------|
| AC-1 | `test_tailscale_playbook_loads_sops_secrets` |
| AC-2 | `test_tailscale_role_uses_auth_key_directly` |
| AC-3 | `test_docs_describe_in_repo_sops_secrets` |
| AC-4 | `test_docs_describe_tailscale_sops_source_of_truth` |
| AC-5 | `test_secrets_readme_documents_sops_editing` |
| AC-6 | All tests in `tests/secrets/test_sops_policy.py` |
| AC-7 | `yamllint` / `ansible-lint` commands above |
