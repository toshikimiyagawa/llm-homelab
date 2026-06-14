# Spec: issue-128 - Cloudflare WARP private network for llm01

**Status**: frozen
**Tier**: 2
**Issue**: #128
**Created**: 2026-06-14

## 目的

`llm01` への通常運用経路を Cloudflare WARP / Cloudflare One client に移し、OS レベルの VPN 的な接続で SSH と推論系サービスへ到達できるようにする。

既存の Cloudflare Tunnel + Access 構成は、公開 hostname ごとに Access 認証を挟むモデルである。このモデルでは API クライアントが `CF-Access-Client-Id` / `CF-Access-Client-Secret` ヘッダを持つ必要があり、SSH も Browser SSH / 短命証明書経由になる。会社 Mac でも Cloudflare One client を導入できる前提に変わったため、公開 hostname + Access 経路を最終状態から外し、WARP private network を主経路にする。

Tailscale は今回撤去しない。WARP 移行後も当面の併存経路として残す。

## スコープ

### 含む

- 既存 `llm01` Cloudflare Tunnel を WARP private network の経路として使う。
- `infra/cloudflare/` Terraform root に WARP private network route を追加する。
- private network CIDR は `warp_private_network_cidr` 変数で定義し、実環境では `192.168.0.0/17` を使う。
- `terraform.tfvars.example` には実値固定ではなくサンプル CIDR を置く。
- WARP device profile を Terraform 管理にし、`allowed_email` の identity に一致する端末へ WARP mode と Split Tunnel Include を適用する。
- WARP device enrollment permissions を Terraform 管理にし、`allowed_email` の identity だけが Cloudflare One client を enroll できるようにする。
- WARP enroll 済み端末から LAN IP / port で SSH、vLLM、Ollama、Open WebUI へ到達する運用手順を docs に追加する。
- Terraform から旧公開 hostname 経路を削除する。
  - `open-webui-llm01.<domain>`
  - `ssh-llm01.<domain>`
  - `vllm-llm01.<domain>`
  - `ollama-llm01.<domain>`
- Terraform から上記 hostname の DNS CNAME、public-hostname Access applications、public-hostname Access policies、Access Service Token を削除する。
- 旧 service token / Browser SSH 手順が主経路として残らないよう docs と静的テストを更新する。
- Terraform / docs / tests によって、Cloudflare 側は UI ではなく Terraform を正本にする方針を維持する。

### 含まない

- Tailscale の撤去、Tailscale ACL 変更、Tailscale auth key rotation。
- ルーターの inbound port 開放。
- k3s Service CIDR / Pod CIDR / ClusterIP への直接アクセス経路追加。
- Cloudflare Gateway network policy による細粒度 L4 制御。必要なら後続 issue とする。
- Cloudflare One client のインストール自動化。
- Terraform apply の CI/CD 自動化。
- Cloudflare provider token、Terraform state、tfvars、復号済み SOPS、WARP device token などの secret commit。
- Open WebUI / vLLM / Ollama の認証モデル変更。

## 設計決定

| 項目 | 決定 | 理由 |
|------|------|------|
| 主経路 | Cloudflare WARP private network | OS レベルで SSH と API に到達でき、Access service token header や Browser SSH を不要にできる |
| Tailscale | 当面併存 | WARP 移行と Tailscale 撤去を分け、切り戻し経路を残す |
| ルーティング対象 | LAN CIDR `192.168.0.0/17` | `llm01` だけでなく LAN 内の運用対象を WARP から到達可能にする |
| CIDR 管理 | `warp_private_network_cidr` 変数 | Public repo に実値を散らさず、別環境でも差し替え可能にする |
| Tunnel | 既存 `cloudflare_zero_trust_tunnel_cloudflared.llm01` を再利用 | すでに llm01 上の `cloudflared` と Terraform-managed tunnel がある |
| Tunnel route | `cloudflare_zero_trust_tunnel_cloudflared_route` | provider v5.19.1 の schema で private network CIDR を tunnel に紐付けられる |
| Device profile | Terraform-managed custom profile | Split Tunnel Include を Terraform 正本にし、UI drift を避ける |
| Device enrollment | Terraform-managed WARP Access application + allow policy | Cloudflare One client の enroll 許可を `allowed_email` に限定する |
| Profile 対象 | `identity.email == var.allowed_email` | 既存 Access と同じ allowed identity を使い、個人利用の最小構成にする |
| Split Tunnel | Include mode で `warp_private_network_cidr` のみ流す | 全通信を WARP に流さず、LAN 到達に必要な CIDR だけを対象にする |
| 旧公開 hostname | 最終状態では削除 | 会社 Mac でも Cloudflare One client が使えるため、Access 公開経路を残す必要がない |
| Service Token | 削除 | API は WARP 越しの LAN 到達を主経路にし、Access header 前提をなくす |

## Terraform 変数

`terraform.tfvars.example` には次の変数を追加する。

```hcl
warp_private_network_cidr = "192.168.1.0/24"
```

実環境の `terraform.tfvars` では次を設定する。

```hcl
warp_private_network_cidr = "192.168.0.0/17"
```

`192.168.0.0/17` は広い RFC1918 範囲であり、WARP 接続元のローカル LAN と重複すると経路衝突が起きうる。docs には、接続元ネットワークが同一または包含関係にある場合は到達検証で問題を確認し、必要なら CIDR を縮小することを明記する。

## Cloudflare Terraform 構成

Terraform は次の状態へ移行する。

- 維持:
  - `cloudflare_zero_trust_tunnel_cloudflared.llm01`
  - `cloudflare_zero_trust_tunnel_cloudflared_config.llm01`
  - `data.cloudflare_zero_trust_tunnel_cloudflared_token.llm01`
  - tunnel token output
- 追加:
  - `cloudflare_zero_trust_tunnel_cloudflared_route.llm01_lan`
  - `cloudflare_zero_trust_access_policy.warp_enrollment`
  - `cloudflare_zero_trust_access_application.warp_enrollment`
  - `cloudflare_zero_trust_device_custom_profile.llm01_warp`
- 削除:
  - `cloudflare_dns_record.tunnel`
  - `cloudflare_zero_trust_access_application.open_webui`
  - `cloudflare_zero_trust_access_application.ssh`
  - `cloudflare_zero_trust_access_application.vllm`
  - `cloudflare_zero_trust_access_application.ollama`
  - `cloudflare_zero_trust_access_short_lived_certificate.ssh`
  - `cloudflare_zero_trust_access_service_token.api_clients`
  - service token outputs
  - public hostname locals / outputs that exist only for the deleted Access path

WARP enrollment permissions は `cloudflare_zero_trust_access_application` の `type = "warp"` で表現し、`cloudflare_zero_trust_access_policy.warp_enrollment` を紐付ける。policy は `include.email.email = var.allowed_email` の allow decision にする。既存 Google IdP は引き続き Cloudflare 側の前提リソースとし、この spec では新規 identity provider を作らない。provider schema / validate が WARP enrollment application を表現できない場合は STOP して人間に報告する。

`cloudflare_zero_trust_tunnel_cloudflared_config.llm01` は public hostname ingress を持たない private routing 用 tunnel config へ寄せる。provider が空 ingress を許容しない場合は、実装時に Terraform validate の結果を確認し、Cloudflare-managed tunnel connector と private network route に必要な最小 config にする。provider schema / validate がこの構成を表現できない場合は STOP して人間に報告する。

## 運用手順

docs は次を説明する。

1. Terraform で WARP private network route と device profile を apply する。
2. Cloudflare One client を端末にインストールする。
3. Zero Trust team へ `allowed_email` identity で enroll する。`allowed_email` 以外の identity は enrollment policy で拒否される。
4. WARP 接続後、LAN IP / port で `llm01` へ接続する。
5. SSH は標準 `ssh <user>@<llm01 LAN IP>` を使う。
6. vLLM / Ollama / Open WebUI は認証 header なしで LAN IP / port または既存 LAN 向け hostname へ接続する。
7. 旧 `open-webui-llm01` / `ssh-llm01` / `vllm-llm01` / `ollama-llm01` の公開 Access 経路は廃止済みとして扱う。

docs では具体的な private IP や個人情報を固定値として増やさない。必要な値は `<llm01-lan-ip>` や `warp_private_network_cidr` として表現する。

## 受け入れ基準

各 AC は `tasks.md` で具体的なテストに対応させる。

1. **AC-1**: `infra/cloudflare/variables.tf` と `terraform.tfvars.example` が `warp_private_network_cidr` を定義し、example はサンプル CIDR に留まる。
2. **AC-2**: Terraform に `cloudflare_zero_trust_tunnel_cloudflared_route` があり、`network = var.warp_private_network_cidr` と既存 `llm01` tunnel を参照する。
3. **AC-3**: Terraform に WARP enrollment 用の Access policy と `type = "warp"` の Access application があり、`allowed_email` の identity だけが device enrollment できる。
4. **AC-4**: Terraform に WARP device custom profile があり、`allowed_email` の identity に一致する端末へ WARP mode と Split Tunnel Include を適用する。
5. **AC-5**: Split Tunnel Include は `warp_private_network_cidr` を参照し、全通信や k3s Service CIDR / Pod CIDR を WARP に流す設定を追加しない。
6. **AC-6**: Terraform から旧公開 hostname の DNS CNAME、public-hostname Access applications、Access short-lived SSH certificate、Access Service Token、service token outputs が削除される。ただし WARP enrollment 用 Access application は残る。
7. **AC-7**: `infra/cloudflare/README.md` と `docs/operations.md` は WARP enrollment、Split Tunnel、SSH、vLLM、Ollama、Open WebUI の接続手順を説明し、旧 service token / Browser SSH を主経路として案内しない。
8. **AC-8**: docs は Tailscale が今回撤去対象外で当面併存すること、WARP と CIDR が接続元 LAN と重複すると経路衝突しうることを明記する。
9. **AC-9**: `docs/software-stack.md` はリモートアクセスの主経路を Cloudflare WARP として説明し、Tailscale は併存経路として残す。
10. **AC-10**: static tests は AC-1 から AC-9 を検証する。
11. **AC-11**: `terraform fmt -check -recursive infra/cloudflare` と `terraform -chdir=infra/cloudflare validate` が可能な環境で pass する。
12. **AC-12**: secret 本体、Terraform state、tfvars、plan file、Cloudflare API token、復号済みファイルを commit しない。
13. **AC-13**: 手動 runtime 検証手順として、WARP enroll 済み端末から標準 SSH と vLLM / Ollama / Open WebUI へ認証 header なしで到達する確認項目が docs にある。

## テスト方針

- **静的 pytest**
  - `tests/cloudflare_terraform/test_config.py`
    - `warp_private_network_cidr` variable / example。
    - `cloudflare_zero_trust_tunnel_cloudflared_route` の tunnel と CIDR 参照。
    - WARP enrollment 用 Access policy / `type = "warp"` Access application / `allowed_email` 制限。
    - `cloudflare_zero_trust_device_custom_profile` の identity match / WARP mode / include。
    - 旧 DNS / Access / Service Token resource と outputs の削除。
    - docs の WARP 接続手順、Tailscale 併存、CIDR 衝突注意。
  - `tests/cloudflared/test_role.py`
    - cloudflared role が public hostname ingress を持たないことを引き続き検査する。
- **Terraform CLI**
  - `terraform fmt -check -recursive infra/cloudflare`
  - `terraform -chdir=infra/cloudflare init -backend=false`
  - `terraform -chdir=infra/cloudflare validate`
- **lint**
  - 変更対象に応じて `yamllint` / `ansible-lint` を実行する。Ansible ファイルを変更しない場合は `ansible-lint` の対象外としてよい。
- **手動 runtime**
  - Terraform apply 前に plan で意図しない destroy / replacement が旧公開経路削除以外にないことを人間が確認する。
  - Cloudflare One client を `allowed_email` で enroll する。
  - WARP 接続状態で `ssh <user>@<llm01-lan-ip>` が標準 SSH で接続できる。
  - WARP 接続状態で vLLM / Ollama / Open WebUI へ LAN 経由で接続でき、Access service token header を不要にする。
  - Tailscale は削除されていないことを確認する。

## リスク / ロールバック

- **CIDR 衝突**: `192.168.0.0/17` は接続元の自宅 / 会社 LAN と重複しやすい。衝突した場合は `warp_private_network_cidr` をより狭い CIDR へ変更し、route / Split Tunnel を再 apply する。
- **公開経路削除による切り戻し困難化**: 旧 hostname / Access / Service Token を Terraform から削除するため、WARP が使えない端末からの Cloudflare Access 経路はなくなる。切り戻す場合はこの spec の PR を revert するか、旧 Access 構成を復元する後続 spec を作る。
- **Terraform provider schema 差異**: provider v5.19.1 の device profile / tunnel route schema に合わせる。validate で表現できない場合は実装を止める。
- **Cloudflare UI drift**: WARP route / device profile を UI で変更すると Terraform と乖離する。変更は Terraform PR 経由にする。
- **Access 認証層の削除**: service token / Access policy が消えるため、WARP enrollment と LAN 側サービスの露出範囲が重要になる。必要なら後続 issue で Gateway network policy やサービス側認証を追加する。
- **Tailscale 併存の混乱**: WARP と Tailscale の両方が使える期間は、docs で主経路と併存経路を明確に分ける。

## 参考

- GitHub issue #128
- `infra/cloudflare/` Terraform root
- Cloudflare provider v5.19.1 local schema
