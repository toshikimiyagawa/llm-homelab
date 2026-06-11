# Spec: issue-114 - SOPS load_vars の secrets パスを安定化する

## Intent

`community.sops.load_vars` が `secrets/infra.sops.yml` を playbook ファイル側の相対パスとして探索し、repo root の secret ファイルを読めない問題を修正する。

## Scope

- `playbooks/07-tailscale.yml`
- `playbooks/08-prometheus.yml`
- `playbooks/22-cloudflare-tunnel.yml`
- `tests/secrets/test_sops_policy.py`

## Acceptance Criteria

1. **AC-1**: 対象3 playbook の `community.sops.load_vars.file` は `{{ playbook_dir }}/../secrets/infra.sops.yml` を参照する。
2. **AC-2**: 対象3 playbook は引き続き `no_log: true` を維持する。
3. **AC-3**: 静的 pytest が AC-1 と AC-2 を検証する。
4. **AC-4**: `uvx pytest tests/secrets/test_sops_policy.py -q` が通る。

## Verification

```bash
uvx pytest tests/secrets/test_sops_policy.py -q
yamllint playbooks/07-tailscale.yml playbooks/08-prometheus.yml playbooks/22-cloudflare-tunnel.yml
git diff --check
```
