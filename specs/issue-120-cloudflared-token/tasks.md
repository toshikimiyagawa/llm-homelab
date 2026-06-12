# Tasks: issue-120 - Terraform-managed Cloudflare Tunnel token

> 実装 agent は `spec.md` と `plan.md` を読み、この tasks を過不足なく実装する。`specs/` 配下は実装中に変更しない。

## Task 1: Terraform token data source のテストを追加する

**Files**

- Modify: `tests/cloudflare_terraform/test_config.py`

**Steps**

1. `tests/cloudflare_terraform/test_config.py` に、`infra/cloudflare/tunnel.tf` が `cloudflare_zero_trust_tunnel_cloudflared_token` data source を持つことを確認する test を追加する。
2. `infra/cloudflare/outputs.tf` が `output "tunnel_token"` を持ち、`sensitive = true` と `.token` 参照を含むことを確認する test を追加する。
3. 旧 credentials JSON ではなく token を docs が説明することを確認する test を追加する。

**Expected RED**

```bash
uvx pytest tests/cloudflare_terraform/test_config.py -q
```

追加 test が失敗する。

**Acceptance Criteria**

- AC-1
- AC-7

## Task 2: Terraform token data source / output を実装する

**Files**

- Modify: `infra/cloudflare/tunnel.tf`
- Modify: `infra/cloudflare/outputs.tf`

**Steps**

1. `infra/cloudflare/tunnel.tf` に以下を追加する。

   ```hcl
   data "cloudflare_zero_trust_tunnel_cloudflared_token" "llm01" {
     account_id = var.cloudflare_account_id
     tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.llm01.id
   }
   ```

2. `infra/cloudflare/outputs.tf` に以下を追加する。

   ```hcl
   output "tunnel_token" {
     description = "Cloudflare Tunnel token for cloudflared on llm01. Treat as a secret."
     value       = data.cloudflare_zero_trust_tunnel_cloudflared_token.llm01.token
     sensitive   = true
   }
   ```

3. Test を実行する。

   ```bash
   uvx pytest tests/cloudflare_terraform/test_config.py -q
   ```

**Acceptance Criteria**

- AC-1

## Task 3: cloudflared role の token 契約テストを追加/更新する

**Files**

- Modify: `tests/cloudflared/test_role.py`

**Steps**

1. `test_config_is_minimal_for_cloudflare_managed_tunnel` を更新し、`credentials-file:` が存在しないことを assert する。
2. `test_credentials_no_log_and_mode` を token 前提へ置換する。期待内容:
   - `vault_cloudflared_tunnel_token` が tasks にある。
   - `cloudflared_tunnel_token` が playbook にある。
   - `cloudflared_tunnel_credentials` が playbook にない。
   - `no_log: true` と `0600` が維持される。
3. systemd unit が `--token-file` を使い、token literal を ExecStart に埋め込まないことを確認する test を追加する。
4. defaults が `cloudflared_token_path` を持ち、旧 `cloudflared_credentials_path` に依存しないことを確認する test を追加/更新する。

**Expected RED**

```bash
uvx pytest tests/cloudflared/test_role.py -q
```

追加/更新 test が失敗する。

**Acceptance Criteria**

- AC-2
- AC-3
- AC-4
- AC-5
- AC-6

## Task 4: playbook と role を token 方式へ移行する

**Files**

- Modify: `playbooks/22-cloudflare-tunnel.yml`
- Modify: `roles/cloudflared/defaults/main.yml`
- Modify: `roles/cloudflared/tasks/main.yml`
- Modify: `roles/cloudflared/templates/config.yml.j2`
- Modify: `roles/cloudflared/templates/cloudflared.service.j2`

**Steps**

1. `playbooks/22-cloudflare-tunnel.yml` の secret mapping を `cloudflared_tunnel_token` -> `vault_cloudflared_tunnel_token` に変更する。
2. assert 名と fail message を tunnel token 前提に変更する。
3. `roles/cloudflared/defaults/main.yml` に `cloudflared_token_path: /etc/cloudflared/tunnel-token` を追加し、`cloudflared_credentials_path` は削除または未使用化する。
4. `roles/cloudflared/tasks/main.yml` の credentials JSON 配置 task を token file 配置 task に変更する。
   - `content: "{{ vault_cloudflared_tunnel_token }}"`
   - `dest: "{{ cloudflared_token_path }}"`
   - mode `0600`
   - `no_log: true`
   - notify `Restart cloudflared`
5. `roles/cloudflared/templates/config.yml.j2` から `credentials-file:` を削除する。
6. `roles/cloudflared/templates/cloudflared.service.j2` の ExecStart を `--token-file {{ cloudflared_token_path }}` 方式へ変更する。
7. Test を実行する。

   ```bash
   uvx pytest tests/cloudflared/test_role.py -q
   ```

**Acceptance Criteria**

- AC-2
- AC-3
- AC-4
- AC-5
- AC-6

## Task 5: SOPS policy tests を token key へ更新する

**Files**

- Modify: `tests/secrets/test_sops_policy.py`

**Steps**

1. `cloudflared_tunnel_credentials` 期待を `cloudflared_tunnel_token` へ変更する。
2. playbook contract test を `cloudflared_tunnel_token` / `vault_cloudflared_tunnel_token` 期待に変更する。
3. 旧 key が runtime path に残っていないことを assert する。

**Expected RED**

```bash
uvx pytest tests/secrets/test_sops_policy.py -q
```

実装前は失敗し、Task 6 後に pass する。

**Acceptance Criteria**

- AC-2
- AC-6
- AC-9
- AC-12

## Task 6: SOPS file と docs を token 前提へ更新する

**Files**

- Modify: `secrets/infra.sops.yml`
- Modify: `docs/operations.md`
- Modify: `docs/security-and-secrets.md`
- Modify: `secrets/README.md`

**Steps**

1. `secrets/infra.sops.yml` の top-level key を `cloudflared_tunnel_token` にする。実 token 値は commit しない。既存の `cloudflared_tunnel_credentials: ""` は削除するか、runtime path から外す。空文字 placeholder を置く場合も key 名は `cloudflared_tunnel_token` とする。
2. `docs/operations.md` の #91 手順を更新する。
   - `terraform output -raw tunnel_id` を `cloudflared_tunnel_id` に反映。
   - `terraform output -raw tunnel_token` を `sops secrets/infra.sops.yml` の `cloudflared_tunnel_token` に入れる。
   - credentials JSON を探す/格納する記述を削除。
3. `docs/security-and-secrets.md` を更新する。
   - `cloudflared_tunnel_token` の用途、SOPS 格納、root-only file mode 0600、rotation を説明。
   - Terraform state に token が入る可能性と commit 禁止を維持。
4. `secrets/README.md` を更新する。
   - in-repo secret key として `cloudflared_tunnel_token` を記載。
5. Test を実行する。

   ```bash
   uvx pytest tests/secrets/test_sops_policy.py tests/cloudflared/test_role.py tests/cloudflare_terraform/test_config.py -q
   ```

**Acceptance Criteria**

- AC-6
- AC-7
- AC-8
- AC-9
- AC-12

## Task 7: Verification

**Files**

- No source edits unless a verification failure reveals an implementation bug.

**Steps**

1. Run static tests.

   ```bash
   uvx pytest tests/cloudflare_terraform/ tests/cloudflared/test_role.py tests/secrets/test_sops_policy.py -q
   ```

2. Run yaml lint.

   ```bash
   yamllint infra/cloudflare/ roles/cloudflared/ playbooks/22-cloudflare-tunnel.yml docs/operations.md docs/security-and-secrets.md secrets/README.md
   ```

3. Run ansible lint.

   ```bash
   ansible-lint roles/cloudflared playbooks/22-cloudflare-tunnel.yml
   ```

4. Run Terraform formatting and validation.

   ```bash
   terraform fmt -check -recursive infra/cloudflare
   terraform -chdir=infra/cloudflare init -backend=false
   terraform -chdir=infra/cloudflare validate
   ```

5. Scan staged/uncommitted files for forbidden secret artifacts.

   ```bash
   git status --short
   git diff --name-only
   ```

   Confirm no `terraform.tfstate`, `*.tfvars`, `*.tfplan`, `keys.txt`, decrypted files, or token plaintext are present.

**Acceptance Criteria**

- AC-10
- AC-11
- AC-12

## Task 8: Handoff state

**Files**

- Modify: `.sdd/state.json`
- Modify: `.sdd/tasks.json`

**Steps**

1. After implementation verification passes, set `.sdd/state.json` to:

   ```json
   {
     "feature": "issue-120-cloudflared-token",
     "tier": 2,
     "phase": "verify",
     "spec": "specs/issue-120-cloudflared-token/"
   }
   ```

2. Update `.sdd/tasks.json` entry for `issue-120-cloudflared-token` to `status: "completed"` after implementation tasks pass.
3. Run kanban.

   ```bash
   bash vendor/ai-sdd-guide/orchestration/tools/kanban.sh
   ```

4. Stop. Do not run verify/sdd-reviewer in the same implementation phase unless explicitly instructed.

**Acceptance Criteria**

- SDD workflow compliance.
