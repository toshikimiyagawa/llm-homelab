# Spec: issue-94 — in-repo secret consumers を SOPS+age に寄せる

**Status**: draft
**Tier**: 2
**Issue**: #94

## 目的

この issue は、リポジトリ内の Ansible playbook / role が実際に消費する secret を SOPS+age へ寄せ、`inventory/group_vars/all/vault.yml` や 1Password lookup を in-repo の secret ソースとして使わない状態にする。

対象は **現在この repo で実際に消費されている secret** に限定する。

- `tailscale_auth_key`
- `grafana_admin_password`

外部 API key / PAT など、現時点でこの repo の active path から消費されていないものは本 issue の対象外とする。そうした secret は別 issue で段階移行する。

## スコープ

### 含む

- `playbooks/07-tailscale.yml` を SOPS 読み込みに対応させ、`tailscale_auth_key` を `secrets/infra.sops.yml` から渡す。
- `docs/security-and-secrets.md` に、in-repo secret の正本が SOPS+age であることを明記する。
- `docs/software-stack.md` の Tailscale auth key の保管説明を更新し、1Password を secret 本体の正本として扱わない。
- `secrets/README.md` に、`secrets/infra.sops.yml` が in-repo secret の保管場所であることを追記する。
- `tests/` に静的契約テストを追加し、Tailscale playbook が SOPS を読むこと、`tailscale_auth_key` が `no_log: true` のまま使われること、関連 docs が SOPS 前提に追従していることを検証する。
- 既存の `grafana_admin_password` が SOPS 管理であることを、docs とテストで明示する。

### 含まない

- Anthropic / Google / GitHub PAT などの外部サービス API key の段階移行。
- `k3s_token` の再設計や移行。現時点でこの repo の active path から消費されていないため、別 issue で扱う。
- #93 で既に完了した Cloudflare DNS01 token / Cloudflare Tunnel credentials の移行作業そのもの。
- `inventory/group_vars/all/vault.yml` の中身を全面的に解読して再暗号化し直すこと。

## 設計決定

| 項目 | 決定 | 理由 |
|------|------|------|
| secret の正本 | `secrets/infra.sops.yml` | 既に SOPS+age の基盤が入り、現行の in-repo secret 参照もここへ寄せられる |
| Tailscale auth key | SOPS 読み込み | 1Password lookup を廃止し、Ansible 実行を repo 内の暗号化 secret に寄せる |
| Grafana admin password | SOPS 維持 | 既に SOPS 管理なので、正本を明文化して drift を防ぐ |
| 1Password の位置づけ | age 秘密鍵の復旧用バックアップ | secret 本体の保管庫ではない |
| legacy Vault file | in-repo secret の正本にはしない | 今後の新規 in-repo secret は SOPS に統一する |

## 想定するデータフロー

1. 実行者はローカルの age 秘密鍵 `~/.config/sops/age/keys.txt` を持つ。
2. `playbooks/07-tailscale.yml` が `community.sops.load_vars` で `secrets/infra.sops.yml` を読み込む。
3. `tailscale_auth_key` を `no_log: true` の `set_fact` でキャッシュする。
4. `roles/tailscale` は従来どおり `tailscale_auth_key` を受け取って `tailscale up` を実行する。
5. `playbooks/08-prometheus.yml` は既存どおり SOPS 由来の `grafana_admin_password` を使う。

## 受け入れ基準

1. **AC-1**: `playbooks/07-tailscale.yml` が `community.sops.load_vars` で `secrets/infra.sops.yml` を読み込み、`tailscale_auth_key` を `no_log: true` で `set_fact` に渡している。
2. **AC-2**: `roles/tailscale/tasks/main.yml` は `tailscale_auth_key` を使っているが、1Password lookup や Vault 直接参照に依存していない。
3. **AC-3**: `docs/security-and-secrets.md` に `tailscale_auth_key` と `grafana_admin_password` が SOPS 管理であることが明記されている。
4. **AC-4**: `docs/software-stack.md` の Tailscale auth key の説明が 1Password 正本ではなく SOPS 正本に更新されている。
5. **AC-5**: `secrets/README.md` に in-repo secret の保管場所と編集方法が記載されている。
6. **AC-6**: 静的テストが `playbooks/07-tailscale.yml` の SOPS 読み込みと、Tailscale / Grafana の SOPS 前提を検証する。
7. **AC-7**: `yamllint` と `ansible-lint` が、今回変更したファイルについては新規エラーを出さない。

## テスト方針

- `tests/secrets/test_sops_policy.py`
  - `playbooks/07-tailscale.yml` が `community.sops.load_vars` と `secrets/infra.sops.yml` を参照すること。
  - `roles/tailscale/tasks/main.yml` が `tailscale_auth_key` を使い、`no_log: true` を維持していること。
  - `docs/security-and-secrets.md` と `docs/software-stack.md` が Tailscale auth key の SOPS 管理を説明していること。
  - `secrets/README.md` が in-repo SOPS secret の編集方法を説明していること。
- `uvx pytest tests/secrets/test_sops_policy.py`
- `yamllint docs/security-and-secrets.md docs/software-stack.md secrets/README.md playbooks/07-tailscale.yml`
- `ansible-lint playbooks/07-tailscale.yml roles/tailscale`

## リスク / 注意点

- `inventory/group_vars/all/vault.yml` の中身はこの作業では解読しない。もしそこに外部 API key / PAT / `k3s_token` が残っているなら、それは別 issue で扱う。
- `tailscale_auth_key` を SOPS に寄せても、Tailscale 側の token rotation は別途人間が実施する。
- `tests/` に新規ファイルを追加する場合は、既存の pytest import mismatch 問題を避けるため、`test_role.py` という basename を増やさない。
