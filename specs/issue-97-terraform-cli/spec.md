# Spec: issue-97 - devcontainer Terraform CLI

- Tier: 1
- Status: frozen
- Issue: #97

## Intent

devcontainer 作成時に Terraform CLI をインストールし、#95 の Cloudflare Terraform 構成をローカルで `terraform fmt/init/validate` できるようにする。OpenTofu ではなく Terraform CLI を採用する。#95 の docs と検証コマンドが `terraform` 前提であり、別名 CLI だけでは #95 の未検証状態を解消できないため。

## Acceptance Criteria

1. `.devcontainer/project-tools.yml` が Terraform CLI を reproducible な固定 version でインストールする。
2. Terraform は `/usr/local/bin/terraform` として実行できる。
3. `tests/devcontainer/` に Terraform CLI が project tools で管理されていることを確認する regression test がある。
4. docs または project tools 内コメントで、Cloudflare Terraform 検証用 CLI であることが分かる。
5. 現在の作業環境でも `terraform version` が実行できる。

## Verification

```bash
uvx pytest tests/devcontainer/test_terraform_cli_tooling.py
terraform version
```

After #95 is present in the same environment, run:

```bash
terraform fmt -check -recursive infra/cloudflare
terraform -chdir=infra/cloudflare init -backend=false
terraform -chdir=infra/cloudflare validate
```
