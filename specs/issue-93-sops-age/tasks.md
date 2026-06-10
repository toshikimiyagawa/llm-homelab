# Tasks: issue-93 — SOPS+age によるシークレット管理整理

> 実装エージェントは `spec.md` とこの `tasks.md` を契約として扱う。実装中に secret 実値、age 秘密鍵、復号済みファイルを commit しないこと。spec が不足している場合は STOP して人間に確認する。

## Task 0: age recipient を確認する

対応 AC: AC-2, AC-7

- [ ] `~/.config/sops/age/keys.txt` が実行環境に存在するか確認する。

  Run:

  ```bash
  test -f ~/.config/sops/age/keys.txt
  ```

  Expected:

  - exit 0: 既存 key を使う。
  - exit non-zero: 実装を止め、人間に age public recipient を依頼する。秘密鍵をチャットやログへ出さない。

- [ ] age public recipient を取得する。

  Run:

  ```bash
  rg '^# public key: age1' ~/.config/sops/age/keys.txt
  ```

  Expected: `# public key: age1...` が 1 行出る。出ない場合は STOP。

## Task 1: SOPS policy と secrets ディレクトリを追加する

対応 AC: AC-2, AC-3, AC-7

Files:

- Create: `.sops.yaml`
- Create: `secrets/README.md`
- Create: `secrets/infra.sops.yml`

- [ ] `.sops.yaml` を作成する。`age:` には Task 0 で取得した実際の public recipient を入れる。

  Run:

  ```bash
  AGE_RECIPIENT="$(sed -n 's/^# public key: //p' ~/.config/sops/age/keys.txt | head -n1)"
  test -n "$AGE_RECIPIENT"
  printf '%s\n' '---' 'creation_rules:' '  - path_regex: ^secrets/.*\.sops\.ya?ml$' "    age: $AGE_RECIPIENT" > .sops.yaml
  ```

- [ ] `secrets/README.md` を作成する。

  Required content:

  ```markdown
  # Secrets

  This directory stores SOPS-encrypted project secrets.

  ## Key Material

  - Commit `*.sops.yml` encrypted files only.
  - Never commit `keys.txt`, `*.plain.yml`, `*.decrypted.yml`, or temporary decrypted files.
  - The age private key lives at `~/.config/sops/age/keys.txt`.
  - 1Password may store a backup item named `llm-homelab age private key` in the `LLM Server Infrastructure` vault.
  - 1Password is only a recovery location for the age private key; normal Ansible runs use the local age key directly.

  ## Editing

  ```bash
  sops secrets/infra.sops.yml
  ```

  ## Ansible

  Playbooks load encrypted variables with `community.sops.load_vars`; do not decrypt to a plaintext vars file.

  ## Temporary Cloudflare Tokens

  Broad Cloudflare tokens used for one-time Tunnel or Access setup must be passed through environment variables and revoked after use. Do not store them in SOPS, Ansible Vault, or the repository.
  ```

- [ ] `secrets/infra.sops.yml` を SOPS で作成する。

  The encrypted file must define these top-level keys:

  - `cloudflare_dns01_api_token`
  - `cloudflared_tunnel_credentials`

  Command:

  ```bash
  sops secrets/infra.sops.yml
  ```

  Expected:

  - file contains `sops:` metadata.
  - file does not contain real token plaintext.
  - if real secret values are not available yet, STOP and ask the human to populate the SOPS file. Do not commit sample plaintext.

## Task 2: Add SOPS Ansible dependency

対応 AC: AC-4

Files:

- Modify: `requirements.yml`

- [ ] Add `community.sops` to the collections list.

  Result:

  ```yaml
  ---
  collections:
    - name: ansible.posix
    - name: community.general
    - name: community.sops
  ```

## Task 3: Write static tests first

対応 AC: AC-1..AC-8

Files:

- Create: `tests/secrets/test_sops_policy.py`
- Modify: `tests/cloudflared/test_role.py`

- [ ] Create `tests/secrets/test_sops_policy.py`.

  ```python
  from pathlib import Path


  ROOT = Path(__file__).parents[2]
  SOPS_CONFIG = ROOT / ".sops.yaml"
  SECRETS_DIR = ROOT / "secrets"
  SECRETS_README = SECRETS_DIR / "README.md"
  INFRA_SECRETS = SECRETS_DIR / "infra.sops.yml"
  REQUIREMENTS = ROOT / "requirements.yml"
  SECURITY_DOC = ROOT / "docs" / "security-and-secrets.md"
  OPERATIONS_DOC = ROOT / "docs" / "operations.md"
  PROM_CLUSTER_ISSUER = (
      ROOT / "roles" / "prometheus" / "templates" / "cluster-issuer.yml.j2"
  )
  PROM_PLAYBOOK = ROOT / "playbooks" / "08-prometheus.yml"
  CLOUDFLARED_PLAYBOOK = ROOT / "playbooks" / "22-cloudflare-tunnel.yml"


  def test_sops_yaml_targets_secret_files():
      content = SOPS_CONFIG.read_text()
      assert "creation_rules:" in content
      assert "secrets/.*\\.sops" in content
      assert "age1" in content


  def test_secrets_readme_documents_key_handling():
      content = SECRETS_README.read_text()
      assert "keys.txt" in content
      assert "llm-homelab age private key" in content
      assert "1Password" in content
      assert "community.sops.load_vars" in content
      assert "revoke" in content.lower()


  def test_requirements_include_community_sops():
      assert "community.sops" in REQUIREMENTS.read_text()


  def test_security_docs_describe_sops_age_policy():
      content = SECURITY_DOC.read_text()
      for needle in [
          "SOPS",
          "age",
          "community.sops",
          "llm-homelab age private key",
          "cloudflare_dns01_api_token",
          "cloudflared_tunnel_credentials",
      ]:
          assert needle in content
      assert "revoke" in content.lower()


  def test_docs_describe_vault_migration_and_rotation():
      content = SECURITY_DOC.read_text() + "\n" + OPERATIONS_DOC.read_text()
      assert "cloudflare_api_token" in content
      assert "vault_cloudflared_tunnel_credentials" in content
      assert "rotate" in content.lower() or "rotation" in content.lower()


  def test_infra_sops_file_is_encrypted_and_has_required_keys():
      content = INFRA_SECRETS.read_text()
      assert "sops:" in content
      assert "cloudflare_dns01_api_token" in content
      assert "cloudflared_tunnel_credentials" in content


  def test_prometheus_uses_dns01_token_name():
      template = PROM_CLUSTER_ISSUER.read_text()
      assert "cloudflare_dns01_api_token" in template
      assert "cloudflare_api_token" not in template


  def test_prometheus_playbook_loads_sops_secrets():
      content = PROM_PLAYBOOK.read_text()
      assert "community.sops.load_vars" in content
      assert "secrets/infra.sops.yml" in content
      assert "cloudflare_dns01_api_token" in content
      assert "no_log: true" in content


  def test_cloudflared_playbook_loads_sops_credentials():
      content = CLOUDFLARED_PLAYBOOK.read_text()
      assert "community.sops.load_vars" in content
      assert "secrets/infra.sops.yml" in content
      assert "cloudflared_tunnel_credentials" in content
      assert "vault_cloudflared_tunnel_credentials" in content
      assert "no_log: true" in content


  def test_no_forbidden_secret_files_are_committed():
      forbidden_names = {"keys.txt"}
      forbidden_suffixes = (".plain.yml", ".plain.yaml", ".decrypted.yml", ".decrypted.yaml")
      for path in SECRETS_DIR.rglob("*"):
          assert path.name not in forbidden_names
          assert not path.name.endswith(forbidden_suffixes)
  ```

- [ ] Update `tests/cloudflared/test_role.py`.

  Change `test_credentials_no_log_and_mode` to accept the role input alias while requiring the playbook to source it from SOPS:

  ```python
  def test_credentials_no_log_and_mode():  # AC-4
      t = TASKS.read_text()
      p = PLAYBOOK.read_text()
      assert "no_log: true" in t
      assert "0600" in t
      assert "vault_cloudflared_tunnel_credentials" in t
      assert "cloudflared_tunnel_credentials" in p
      assert "community.sops.load_vars" in p
  ```

- [ ] Run tests and confirm they fail before implementation.

  Run:

  ```bash
  uvx pytest tests/secrets/test_sops_policy.py tests/cloudflared/test_role.py
  ```

  Expected: failures for missing `.sops.yaml`, `secrets/`, `community.sops`, and variable rename.

## Task 4: Load SOPS secrets in Prometheus playbook

対応 AC: AC-5

Files:

- Modify: `playbooks/08-prometheus.yml`
- Modify: `roles/prometheus/templates/cluster-issuer.yml.j2`

- [ ] Update `playbooks/08-prometheus.yml`.

  Result:

  ```yaml
  ---
  - name: Configure Prometheus monitoring stack
    hosts: llm_servers
    become: true
    gather_facts: true
    pre_tasks:
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
    roles:
      - prometheus
  ```

- [ ] Update `roles/prometheus/templates/cluster-issuer.yml.j2`.

  Change:

  ```yaml
  api-token: "{{ cloudflare_api_token }}"
  ```

  To:

  ```yaml
  api-token: "{{ cloudflare_dns01_api_token }}"
  ```

## Task 5: Load SOPS tunnel credentials in Cloudflare playbook

対応 AC: AC-6

Files:

- Modify: `playbooks/22-cloudflare-tunnel.yml`

- [ ] Update `playbooks/22-cloudflare-tunnel.yml`.

  Result:

  ```yaml
  ---
  - name: Configure Cloudflare Tunnel and SSH CA trust
    hosts: llm01
    become: true
    pre_tasks:
      - name: Load SOPS infrastructure secrets
        community.sops.load_vars:
          file: secrets/infra.sops.yml
        delegate_to: localhost
        run_once: true
        no_log: true

      - name: Cache cloudflared tunnel credentials
        ansible.builtin.set_fact:
          vault_cloudflared_tunnel_credentials: "{{ cloudflared_tunnel_credentials }}"
        no_log: true

      - name: Ensure cloudflared tunnel credentials are provided
        ansible.builtin.assert:
          that:
            - vault_cloudflared_tunnel_credentials is defined
            - vault_cloudflared_tunnel_credentials | length > 0
          fail_msg: >-
            cloudflared_tunnel_credentials が未設定です。
            secrets/infra.sops.yml に credentials JSON を格納してください
            (docs/operations.md 参照)。
        no_log: true
    roles:
      - cloudflared
  ```

## Task 6: Update docs

対応 AC: AC-1, AC-3, AC-8

Files:

- Modify: `docs/security-and-secrets.md`
- Modify: `docs/operations.md`

- [ ] Rewrite the 1Password / Ansible Vault sections in `docs/security-and-secrets.md` to explain:

  - SOPS+age is the default for Git-managed project secrets.
  - `~/.config/sops/age/keys.txt` is the local private key and must not be committed.
  - 1Password `LLM Server Infrastructure` may store `llm-homelab age private key` only as backup.
  - Ansible uses `community.sops.load_vars`.
  - `cloudflare_dns01_api_token` and `cloudflared_tunnel_credentials` live in `secrets/infra.sops.yml`.
  - old `cloudflare_api_token` and `vault_cloudflared_tunnel_credentials` in Ansible Vault must be removed after migration.
  - DNS01 token and tunnel credentials rotation remains a human operation after migration.
  - broad Cloudflare setup tokens are environment-only and must be revoked after use.

- [ ] Update `docs/operations.md` Cloudflare Tunnel setup:

  Change references from:

  ```text
  inventory/group_vars/all/vault.yml の vault_cloudflared_tunnel_credentials
  ```

  To:

  ```text
  secrets/infra.sops.yml の cloudflared_tunnel_credentials
  ```

  Also mention that `cloudflared_tunnel_id` remains non-secret in normal vars.

## Task 7: Run focused tests and lint

対応 AC: AC-9

- [ ] Run static tests.

  ```bash
  uvx pytest tests/secrets/test_sops_policy.py tests/cloudflared/test_role.py
  ```

  Expected: all tests pass.

- [ ] Run yamllint.

  ```bash
  yamllint .sops.yaml secrets/ docs/security-and-secrets.md docs/operations.md playbooks/08-prometheus.yml playbooks/22-cloudflare-tunnel.yml
  ```

  Expected: no errors.

- [ ] Run ansible-lint.

  ```bash
  ansible-lint playbooks/08-prometheus.yml playbooks/22-cloudflare-tunnel.yml roles/prometheus roles/cloudflared
  ```

  Expected: no new errors from changed files.

## Task 8: Update SDD state

対応 AC: process

- [ ] Set `.sdd/state.json` to verify phase.

  ```json
  {
    "feature": "issue-93-sops-age",
    "tier": 2,
    "phase": "verify",
    "spec": "specs/issue-93-sops-age/"
  }
  ```

- [ ] Commit implementation.

  ```bash
  git status --short
  git add .sops.yaml secrets/ requirements.yml docs/security-and-secrets.md docs/operations.md roles/prometheus/templates/cluster-issuer.yml.j2 playbooks/08-prometheus.yml playbooks/22-cloudflare-tunnel.yml tests/secrets/test_sops_policy.py tests/cloudflared/test_role.py .sdd/state.json
  git commit -m "feat(issue-93-sops-age): manage secrets with sops age"
  ```

## 受け入れ基準 → テスト対応

| AC | Test |
|----|------|
| AC-1 | `test_security_docs_describe_sops_age_policy` |
| AC-2 | `test_sops_yaml_targets_secret_files` |
| AC-3 | `test_secrets_readme_documents_key_handling` |
| AC-4 | `test_requirements_include_community_sops` |
| AC-5 | `test_prometheus_uses_dns01_token_name` |
| AC-6 | `test_cloudflared_playbook_loads_sops_credentials`, `test_credentials_no_log_and_mode` |
| AC-7 | `test_infra_sops_file_is_encrypted_and_has_required_keys`, `test_no_forbidden_secret_files_are_committed` |
| AC-8 | `test_docs_describe_vault_migration_and_rotation` |
| AC-9 | focused pytest, yamllint, ansible-lint |
