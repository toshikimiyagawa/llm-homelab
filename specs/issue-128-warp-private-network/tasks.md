# Tasks: issue-128 - Cloudflare WARP private network for llm01

> 実装 agent は `spec.md` と `plan.md` を読み、この tasks を過不足なく実装する。`specs/` 配下は実装中に変更しない。

## Task 1: WARP Terraform contract tests を追加する

**Files**

- Modify: `tests/cloudflare_terraform/test_config.py`

**Steps**

- [ ] Add tests that assert `warp_private_network_cidr` exists in `variables.tf` and `terraform.tfvars.example`.

  ```python
  def test_warp_private_network_variable_is_portable():
      variables = (TF / "variables.tf").read_text()
      example = (TF / "terraform.tfvars.example").read_text()
      assert 'variable "warp_private_network_cidr"' in variables
      assert "Cloudflare WARP private network CIDR" in variables
      assert "warp_private_network_cidr" in example
      assert 'warp_private_network_cidr = "192.168.1.0/24"' in example
      assert '192.168.0.0/17' not in example
  ```

- [ ] Add tests that assert a tunnel private route uses the existing tunnel and CIDR variable.

  ```python
  def test_warp_private_network_route_uses_existing_tunnel():
      text = read_all_tf()
      assert 'resource "cloudflare_zero_trust_tunnel_cloudflared_route" "llm01_lan"' in text
      assert "tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.llm01.id" in text
      assert "network    = var.warp_private_network_cidr" in text
      assert "comment" in text
  ```

- [ ] Add tests that assert WARP enrollment is limited to `allowed_email`.

  ```python
  def test_warp_enrollment_application_is_limited_to_allowed_email():
      text = read_all_tf()
      assert 'resource "cloudflare_zero_trust_access_policy" "warp_enrollment"' in text
      assert 'resource "cloudflare_zero_trust_access_application" "warp_enrollment"' in text
      assert 'type                 = "warp"' in text or 'type             = "warp"' in text
      assert "cloudflare_zero_trust_access_policy.warp_enrollment.id" in text
      assert "allowed_email" in text
      assert "app_launcher_visible = false" in text
  ```

- [ ] Add tests that assert the custom device profile applies WARP mode and includes only `warp_private_network_cidr`.

  ```python
  def test_warp_device_profile_includes_private_network_only():
      text = read_all_tf()
      assert 'resource "cloudflare_zero_trust_device_custom_profile" "llm01_warp"' in text
      assert "identity.email" in text
      assert "var.allowed_email" in text
      assert "service_mode_v2" in text
      assert 'mode = "warp"' in text
      assert "include = [{" in text
      assert "address     = var.warp_private_network_cidr" in text or "address = var.warp_private_network_cidr" in text
      for forbidden in ["10.42.0.0", "10.43.0.0", "cluster", "pod cidr", "service cidr"]:
          assert forbidden not in text.lower()
  ```

- [ ] Add tests that assert old public-hostname resources and outputs are gone while WARP enrollment Access remains allowed.

  ```python
  def test_public_hostname_access_resources_are_removed():
      text = read_all_tf()
      outputs = (TF / "outputs.tf").read_text()
      forbidden_resources = [
          'resource "cloudflare_dns_record" "tunnel"',
          'resource "cloudflare_zero_trust_access_application" "open_webui"',
          'resource "cloudflare_zero_trust_access_application" "ssh"',
          'resource "cloudflare_zero_trust_access_application" "vllm"',
          'resource "cloudflare_zero_trust_access_application" "ollama"',
          'resource "cloudflare_zero_trust_access_short_lived_certificate" "ssh"',
          'resource "cloudflare_zero_trust_access_service_token" "api_clients"',
      ]
      for resource in forbidden_resources:
          assert resource not in text
      for output_name in ["hostnames", "ssh_ca_public_key", "service_token_client_id", "service_token_client_secret"]:
          assert f'output "{output_name}"' not in outputs
      assert 'resource "cloudflare_zero_trust_access_application" "warp_enrollment"' in text
  ```

**Expected RED**

```bash
uvx pytest tests/cloudflare_terraform/test_config.py -q
```

Expected: FAIL because Terraform still has public hostname resources and lacks WARP route/profile resources.

**Acceptance Criteria**

- AC-1
- AC-2
- AC-3
- AC-4
- AC-5
- AC-6

## Task 2: Terraform variables and route resources を実装する

**Files**

- Modify: `infra/cloudflare/variables.tf`
- Modify: `infra/cloudflare/terraform.tfvars.example`
- Modify: `infra/cloudflare/tunnel.tf`

**Steps**

- [ ] Add this variable to `infra/cloudflare/variables.tf`.

  ```hcl
  variable "warp_private_network_cidr" {
    description = "Cloudflare WARP private network CIDR routed to llm01 through the Cloudflare Tunnel."
    type        = string
  }
  ```

- [ ] Add this sample value to `infra/cloudflare/terraform.tfvars.example`.

  ```hcl
  warp_private_network_cidr = "192.168.1.0/24"
  ```

- [ ] Add this resource to `infra/cloudflare/tunnel.tf` after the token data source.

  ```hcl
  resource "cloudflare_zero_trust_tunnel_cloudflared_route" "llm01_lan" {
    account_id = var.cloudflare_account_id
    tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.llm01.id
    network    = var.warp_private_network_cidr
    comment    = "${var.host_id} LAN via WARP"
  }
  ```

- [ ] Run the focused tests.

  ```bash
  uvx pytest tests/cloudflare_terraform/test_config.py::test_warp_private_network_variable_is_portable tests/cloudflare_terraform/test_config.py::test_warp_private_network_route_uses_existing_tunnel -q
  ```

Expected: PASS for the two tests named above.

**Acceptance Criteria**

- AC-1
- AC-2

## Task 3: WARP enrollment と device profile を Terraform に追加する

**Files**

- Modify: `infra/cloudflare/access.tf`
- Modify: `infra/cloudflare/tunnel.tf` if `terraform validate` shows profile or route placement should move to another file.

**Steps**

- [ ] Replace the public-hostname Access resources in `infra/cloudflare/access.tf` with WARP enrollment resources.

  ```hcl
  resource "cloudflare_zero_trust_access_policy" "warp_enrollment" {
    account_id = var.cloudflare_account_id
    name       = "${var.host_id}-warp-enrollment"
    decision   = "allow"

    include = [{
      email = {
        email = var.allowed_email
      }
    }]
  }

  resource "cloudflare_zero_trust_access_application" "warp_enrollment" {
    account_id           = var.cloudflare_account_id
    name                 = "${var.host_id}-warp-enrollment"
    type                 = "warp"
    app_launcher_visible = false

    policies = [{
      id         = cloudflare_zero_trust_access_policy.warp_enrollment.id
      precedence = 1
    }]
  }

  resource "cloudflare_zero_trust_device_custom_profile" "llm01_warp" {
    account_id        = var.cloudflare_account_id
    name              = "${var.host_id}-warp-private-network"
    description       = "Route ${var.host_id} private network traffic through Cloudflare WARP."
    enabled           = true
    precedence        = 1
    match             = "identity.email == \"${var.allowed_email}\""
    allow_mode_switch = false
    allowed_to_leave  = false

    service_mode_v2 = {
      mode = "warp"
    }

    include = [{
      address     = var.warp_private_network_cidr
      description = "${var.host_id} private network"
    }]
  }
  ```

- [ ] Run Terraform formatting.

  ```bash
  terraform fmt -recursive infra/cloudflare
  ```

Expected: formats Terraform files in place.

- [ ] Run focused tests.

  ```bash
  uvx pytest tests/cloudflare_terraform/test_config.py::test_warp_enrollment_application_is_limited_to_allowed_email tests/cloudflare_terraform/test_config.py::test_warp_device_profile_includes_private_network_only -q
  ```

Expected: PASS for the two tests named above.

- [ ] Run Terraform validate.

  ```bash
  terraform -chdir=infra/cloudflare init -backend=false
  terraform -chdir=infra/cloudflare validate
  ```

Expected: PASS. If validate fails because the provider schema uses a different spelling for the WARP application or device profile fields, make the smallest schema-only correction that preserves the frozen spec. If provider v5.19 cannot express WARP enrollment or Split Tunnel Include, STOP and mark `.sdd/tasks.json` blocked.

**Acceptance Criteria**

- AC-3
- AC-4
- AC-5
- AC-11

## Task 4: 旧 public hostname / Access / DNS outputs を削除する

**Files**

- Modify: `infra/cloudflare/locals.tf`
- Modify: `infra/cloudflare/tunnel.tf`
- Modify: `infra/cloudflare/dns.tf`
- Modify: `infra/cloudflare/outputs.tf`
- Modify: `tests/cloudflare_terraform/test_config.py`

**Steps**

- [ ] In `infra/cloudflare/locals.tf`, remove `vllm_origin_hostname`, `hostnames`, and `tunnel_services` if they are no longer referenced after public hostname deletion.

- [ ] In `infra/cloudflare/tunnel.tf`, remove the `config.ingress` list that contains `hostname = local.hostnames.open_webui`, `hostname = local.hostnames.ollama`, `hostname = local.hostnames.vllm`, and `hostname = local.hostnames.ssh`.

- [ ] Keep `cloudflare_zero_trust_tunnel_cloudflared_config.llm01` only if Terraform validate accepts a private-routing-compatible minimal config. Start with:

  ```hcl
  resource "cloudflare_zero_trust_tunnel_cloudflared_config" "llm01" {
    account_id = var.cloudflare_account_id
    tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.llm01.id

    config = {}
  }
  ```

  If validate rejects empty config, try removing `cloudflare_zero_trust_tunnel_cloudflared_config.llm01` entirely. If both forms fail or imply a non-private-routing public ingress, STOP and mark `.sdd/tasks.json` blocked.

- [ ] Delete or empty `infra/cloudflare/dns.tf` so it no longer defines `cloudflare_dns_record.tunnel` or `tunnel_cname_target`. Prefer deleting the file if it becomes empty.

- [ ] In `infra/cloudflare/outputs.tf`, keep only:

  ```hcl
  output "tunnel_id" {
    description = "Cloudflare Tunnel ID."
    value       = cloudflare_zero_trust_tunnel_cloudflared.llm01.id
  }

  output "tunnel_token" {
    description = "Cloudflare Tunnel token for cloudflared on llm01. Treat as a secret."
    value       = data.cloudflare_zero_trust_tunnel_cloudflared_token.llm01.token
    sensitive   = true
  }
  ```

- [ ] Update or remove old tests in `tests/cloudflare_terraform/test_config.py` that asserted public DNS, public hostnames, Access Service Token, SSH CA, service-token outputs, or tunnel public ingress. Keep tests for provider version, tfvars portability, tunnel token, gitignore secret exclusions, docs, and WARP resources.

- [ ] Run tests.

  ```bash
  uvx pytest tests/cloudflare_terraform/test_config.py -q
  ```

Expected: PASS after removing obsolete expectations.

- [ ] Run Terraform validate.

  ```bash
  terraform fmt -recursive infra/cloudflare
  terraform -chdir=infra/cloudflare validate
  ```

Expected: PASS, or STOP if Cloudflare provider cannot represent a private-routing-only tunnel per the frozen spec.

**Acceptance Criteria**

- AC-5
- AC-6
- AC-10
- AC-11

## Task 5: cloudflared static tests を WARP-only Terraform shape に合わせる

**Files**

- Modify: `tests/cloudflared/test_role.py`

**Steps**

- [ ] Remove the `HOSTNAMES` constant if it is only used to assert old public hostnames.

- [ ] Replace `test_ansible_config_no_longer_contains_locally_managed_ingress` with a version that checks only the role template contract:

  ```python
  def test_ansible_config_no_longer_contains_locally_managed_ingress():
      text = CONFIG_TMPL.read_text()
      assert "tunnel:" in text
      assert "credentials-file:" not in text
      assert "ingress:" not in text
      assert "open-webui-llm01" not in text
      assert "ollama-llm01" not in text
      assert "vllm-llm01" not in text
      assert "ssh-llm01" not in text
  ```

- [ ] Replace `test_docs_document_hostnames_and_service_token` with a WARP docs contract:

  ```python
  def test_docs_document_warp_and_not_public_access_primary_path():
      ops = OPS_DOC.read_text()
      assert "Cloudflare WARP" in ops
      assert "Cloudflare One client" in ops
      assert "Service Token" not in ops or "旧" in ops
      assert "Browser SSH" not in ops or "旧" in ops
  ```

  If this assertion is too brittle after docs editing, keep the intent: WARP is documented, old Service Token / Browser SSH is not documented as the primary path.

- [ ] Run tests.

  ```bash
  uvx pytest tests/cloudflared/test_role.py -q
  ```

Expected: PASS.

**Acceptance Criteria**

- AC-6
- AC-7
- AC-10

## Task 6: Cloudflare Terraform docs を WARP private network に更新する

**Files**

- Modify: `infra/cloudflare/README.md`
- Modify: `tests/cloudflare_terraform/test_config.py`

**Steps**

- [ ] Add a docs test to `tests/cloudflare_terraform/test_config.py`.

  ```python
  def test_docs_describe_warp_private_network_operations():
      docs = (TF / "README.md").read_text() + OPS_DOC.read_text() + (ROOT / "docs" / "software-stack.md").read_text()
      for term in [
          "Cloudflare WARP",
          "Cloudflare One client",
          "warp_private_network_cidr",
          "Split Tunnel",
          "Tailscale",
          "CIDR",
      ]:
          assert term in docs
      assert "CF-Access-Client-Id" not in docs
      assert "CF-Access-Client-Secret" not in docs
  ```

- [ ] Rewrite `infra/cloudflare/README.md` managed resources list so it includes:

  ```markdown
  - Cloudflare Tunnel: `cloudflare_zero_trust_tunnel_cloudflared.llm01`
  - Cloudflare Tunnel token data source and sensitive `tunnel_token` output
  - WARP private network route: `cloudflare_zero_trust_tunnel_cloudflared_route.llm01_lan`
  - WARP device enrollment policy/application for `allowed_email`
  - WARP device custom profile with Split Tunnel Include for `warp_private_network_cidr`
  ```

- [ ] Remove instructions that import or manage old DNS CNAME records, old public-hostname Access applications, SSH short-lived certificate, and API service token.

- [ ] Add variable documentation:

  ```hcl
  warp_private_network_cidr = "192.168.1.0/24"
  ```

  Explain that real environments can set `192.168.0.0/17` in local `terraform.tfvars`, which is ignored by git.

- [ ] Add WARP apply and verification notes:

  ```bash
  terraform -chdir=infra/cloudflare plan
  terraform -chdir=infra/cloudflare apply
  warp-cli settings
  ```

  Include that device profile propagation can take several minutes.

- [ ] Run focused docs tests.

  ```bash
  uvx pytest tests/cloudflare_terraform/test_config.py::test_docs_describe_warp_private_network_operations -q
  ```

Expected: PASS.

**Acceptance Criteria**

- AC-7
- AC-8
- AC-12
- AC-13

## Task 7: Operations and software stack docs を WARP 主経路に更新する

**Files**

- Modify: `docs/operations.md`
- Modify: `docs/software-stack.md`
- Modify: `tests/cloudflare_terraform/test_config.py`
- Modify: `tests/cloudflared/test_role.py`

**Steps**

- [ ] In `docs/operations.md`, replace the "外部アクセス（Cloudflare Tunnel + Access）" section with "外部アクセス（Cloudflare WARP private network）".

- [ ] Include this operational shape:

  ```markdown
  - Cloudflare One client を端末に導入し、Zero Trust team に `allowed_email` で enroll する。
  - `warp_private_network_cidr` の traffic だけを Split Tunnel Include で WARP に流す。
  - SSH は Browser SSH ではなく標準 `ssh <user>@<llm01-lan-ip>` を使う。
  - vLLM / Ollama / Open WebUI は WARP 越しに LAN IP / port へ接続する。
  - Access Service Token header は WARP 経路では不要。
  - Tailscale は今回撤去せず当面併存する。
  - `192.168.0.0/17` は接続元 LAN と衝突しうるため、問題がある場合は `warp_private_network_cidr` を狭める。
  ```

- [ ] Add manual runtime checks:

  ```bash
  warp-cli status
  warp-cli settings
  ssh <user>@<llm01-lan-ip>
  curl http://<llm01-lan-ip>:11434/
  curl http://<llm01-lan-ip>:8080/health
  ```

  Use symbolic values such as `<llm01-lan-ip>` instead of committing real private IPs.

- [ ] In `docs/software-stack.md`, change the remote access summary so Cloudflare WARP is the primary path and Tailscale is the retained parallel path.

- [ ] Remove or rewrite old statements that say the Cloudflare public hostnames are the primary way to access Open WebUI, vLLM, Ollama, or SSH.

- [ ] Run tests.

  ```bash
  uvx pytest tests/cloudflare_terraform/test_config.py tests/cloudflared/test_role.py -q
  ```

Expected: PASS.

**Acceptance Criteria**

- AC-7
- AC-8
- AC-9
- AC-10
- AC-13

## Task 8: Full verification and secret hygiene

**Files**

- No source edits unless verification reveals an implementation bug inside the approved task scope.

**Steps**

- [ ] Run static tests.

  ```bash
  uvx pytest tests/cloudflare_terraform/test_config.py tests/cloudflared/test_role.py -q
  ```

Expected: PASS.

- [ ] Run Terraform formatting check and validation.

  ```bash
  terraform fmt -check -recursive infra/cloudflare
  terraform -chdir=infra/cloudflare init -backend=false
  terraform -chdir=infra/cloudflare validate
  ```

Expected: PASS.

- [ ] Run YAML lint on changed YAML/Markdown/Terraform-adjacent paths.

  ```bash
  yamllint infra/cloudflare/ docs/operations.md docs/software-stack.md
  ```

Expected: PASS, or document if yamllint is not installed.

- [ ] Confirm no forbidden secret artifacts are staged or untracked.

  ```bash
  git status --short
  git diff --name-only
  git diff --name-only --cached
  ```

Expected: no `terraform.tfstate`, `terraform.tfstate.*`, `terraform.tfvars`, `*.tfplan`, decrypted SOPS file, Cloudflare token, WARP device token, or private key is present.

**Acceptance Criteria**

- AC-10
- AC-11
- AC-12

## Task 9: SDD implementation handoff completion

**Files**

- Modify: `.sdd/tasks.json`

**Steps**

- [ ] After implementation and local verification complete, update the `issue-128-warp-private-network` entry in `.sdd/tasks.json`:

  ```json
  {
    "id": "issue-128-warp-private-network",
    "phase": "tasks",
    "assigned_agent": "codex",
    "status": "completed",
    "handoff": "specs/issue-128-warp-private-network/handoff.md",
    "blocked_reason": null
  }
  ```

- [ ] Run kanban display.

  ```bash
  bash vendor/ai-sdd-guide/orchestration/tools/kanban.sh
  ```

Expected: `issue-128-warp-private-network` is visible with completed status.

**Acceptance Criteria**

- SDD orchestration requirement.

## テスト対応表

- AC-1 -> `test_warp_private_network_variable_is_portable`
- AC-2 -> `test_warp_private_network_route_uses_existing_tunnel`
- AC-3 -> `test_warp_enrollment_application_is_limited_to_allowed_email`
- AC-4 -> `test_warp_device_profile_includes_private_network_only`
- AC-5 -> `test_warp_device_profile_includes_private_network_only`
- AC-6 -> `test_public_hostname_access_resources_are_removed`
- AC-7 -> `test_docs_describe_warp_private_network_operations`, `test_docs_document_warp_and_not_public_access_primary_path`
- AC-8 -> `test_docs_describe_warp_private_network_operations`
- AC-9 -> `test_docs_describe_warp_private_network_operations`
- AC-10 -> full pytest command in Task 8
- AC-11 -> Terraform commands in Task 8
- AC-12 -> secret hygiene command review in Task 8
- AC-13 -> docs checks in `test_docs_describe_warp_private_network_operations`

## 完了の定義

- [ ] All tasks above are complete.
- [ ] Every AC in `spec.md` has a passing test or documented manual runtime check.
- [ ] `uvx pytest tests/cloudflare_terraform/test_config.py tests/cloudflared/test_role.py -q` passes.
- [ ] `terraform fmt -check -recursive infra/cloudflare` passes.
- [ ] `terraform -chdir=infra/cloudflare validate` passes.
- [ ] No forbidden secret artifact is staged or untracked.
- [ ] `.sdd/tasks.json` entry is updated by the implementation agent.
