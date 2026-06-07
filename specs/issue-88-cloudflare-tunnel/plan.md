# Plan: issue-88 — Cloudflare Tunnel + Access による外部アクセス基盤

## アプローチ

`tailscale` role と同じパターンで `roles/cloudflared` を新設する。`cloudflared` を Cloudflare 公式 apt リポジトリから導入し、**locally-managed tunnel**（credentials JSON + リポジトリ管理の `config.yml`）として systemd 常駐させる。`config.yml` の ingress で 4 ホスト名をローカル backend へ振り分ける。SSH の Browser-rendered SSH を成立させるため、同 role で sshd に Cloudflare SSH CA 信頼のドロップインを追加し、併せて `PasswordAuthentication no` のハードニングを `validate` 付きで適用する。

Cloudflare ダッシュボード側（tunnel 作成・DNS ルート・Access Application・Service Token・Google IdP）は一度きりの手動操作とし、その出力（tunnel ID / credentials / SSH CA 公開鍵 / Service Token）を Vault と `docs/operations.md` に記録して再現可能にする。OS 再インストール時はクラウド状態が残るため、`ansible-playbook` 再実行のみで復旧する。

ingress backend はサービスごとに異なる:
- Open WebUI → `http://localhost:8080`（hostNetwork 直バインド）
- Ollama → `http://localhost:11434`（loopback、cloudflared は同ホストなので到達可）
- SSH → `ssh://localhost:22`
- vLLM → 既存 Traefik ingress 経由（ClusterIP のため直ポート無し）。`service: https://vllm.solvelio.com` + `originRequest.originServerName: vllm.solvelio.com`（`vllm.solvelio.com` は host 自身の Tailscale IP に解決し Traefik へ届く）

## 影響範囲 / 主要ファイル

- `roles/cloudflared/defaults/main.yml` — 変数（apt repo、tunnel 名/ID、ホスト名、backend、credentials/​config パス、sshd ドロップインパス）
- `roles/cloudflared/handlers/main.yml` — `restart cloudflared` / `reload sshd`（validate 付き）
- `roles/cloudflared/files/cloudflare_ca.pub` — Cloudflare SSH CA 公開鍵（非機密）
- `roles/cloudflared/templates/config.yml.j2` — tunnel ingress 定義（4 ホスト + catch-all）
- `roles/cloudflared/templates/cloudflared.service.j2` または apt 同梱 unit + drop-in — systemd 常駐
- `roles/cloudflared/templates/sshd-cloudflare.conf.j2` — `/etc/ssh/sshd_config.d/10-cloudflare.conf`（`TrustedUserCAKeys` + `PasswordAuthentication no`）
- `roles/cloudflared/tasks/main.yml` — apt 鍵/repo、install、credentials 配置(no_log)、config 配置、systemd enable/start、CA pub 配置、sshd ドロップイン + validate reload
- `playbooks/22-cloudflare-tunnel.yml` — `hosts: llm01` / `become: true` / `roles: [cloudflared]`、Vault から credentials を取得
- `playbooks/23-cloudflare-smoke-test.yml` — ランタイム AC-10 アサート
- `playbooks/site.yml` — `22-cloudflare-tunnel.yml` を追記
- `tests/cloudflared/test_role.py` — 静的契約テスト
- `inventory/group_vars/all/vault.yml` — `vault_cloudflared_tunnel_credentials`（Vault 暗号化）
- `inventory/group_vars/all/vars.yml` — 非機密の tunnel ID / ホスト名変数（必要なら）
- `docs/operations.md` — Cloudflare 手動セットアップ手順 + 運用検証チェックリスト（M-1〜M-5）
- `docs/security-and-secrets.md` — tunnel credentials の格納方針追記

## config.yml.j2 の形（参考）

```yaml
tunnel: {{ cloudflared_tunnel_id }}
credentials-file: {{ cloudflared_credentials_path }}
ingress:
  - hostname: open-webui-llm01.solvelio.com
    service: http://localhost:8080
  - hostname: ollama-llm01.solvelio.com
    service: http://localhost:11434
  - hostname: vllm-llm01.solvelio.com
    service: https://vllm.solvelio.com
    originRequest:
      originServerName: vllm.solvelio.com
  - hostname: ssh-llm01.solvelio.com
    service: ssh://localhost:22
  - service: http_status:404
```

## sshd ドロップインの形（参考）

```text
# /etc/ssh/sshd_config.d/10-cloudflare.conf
TrustedUserCAKeys /etc/ssh/cloudflare_ca.pub
PasswordAuthentication no
```

handler は `sshd -t`（または copy/template の `validate: "sshd -t -f %s"` 相当）で構文検証してから reload する。

## 検討した代替案とトレードオフ

- **tunnel 種別: locally-managed vs remotely-managed(token)**
  - 採用: locally-managed。ingress 定義が `config.yml` としてリポジトリに残り、OS 再インストール再現性・監査性が高い。
  - 不採用: remotely-managed は token 1 本で簡単だが、ingress がダッシュボード側に存在し「config as code」にならない。
- **ホスト名: `<svc>-llm01`（1 階層）vs `<svc>.llm01`（2 階層）**
  - 採用: 1 階層。無料 Universal SSL `*.solvelio.com` でカバーされ追加課金不要。
  - 不採用: 2 階層は見た目のグルーピングは良いが ACM（約 $10/月）が必要。
- **vLLM backend: Traefik 経由 vs ホスト直ポート**
  - 採用: Traefik 経由。vLLM は ClusterIP のためホスト直ポートが無く、既存 TLS/ingress を再利用できる。
  - 不採用: 直ポート公開は Deployment/Service 変更が必要で既存設計を崩す。
- **API 認証: Service Token（層A）のみ vs 層A+B（vLLM api-key 併用）**
  - 採用: 層A のみ。既存 Tailscale 経路（opencode / Open WebUI が `vllm.solvelio.com` を内部利用）の挙動を変えない。
  - 不採用: 層B は最強だが既存クライアント設定変更が必要（別 issue 候補）。
- **sshd 管理: 本 role に含める vs 別 role**
  - 採用: 本 role に含める。CA 信頼は Browser SSH 成立に必須で本機能と密結合。
  - トレードオフ: 将来 sshd 設定が増えるなら `common` 等への切り出しを検討。

## リスク / ロールバック

- **SSH ロックアウト**: `PasswordAuthentication no` 適用で締め出しの懸念。→ 鍵認証が稼働中であることを確認済み（本セッションで鍵 SSH 成功）。適用は `sshd -t` 検証 → reload（restart でなく reload）で行い、既存接続は切らない。ロールバック: ドロップイン削除 → reload。
- **GPU の無認証露出**: vLLM/Ollama は native auth が無い。→ 公開ホスト名には必ず Service Token ポリシーを付与（手順は docs に明記、付与前は DNS ルートを作らない運用）。
- **credentials 漏洩**: → Vault 暗号化 + `no_log: true` + ファイル mode 0600。Public リポジトリに平文を置かない。
- **冪等性崩れ**: apt repo / credentials / config の各タスクを宣言的に。手動の `cloudflared tunnel login` は role 外（一度きり）。
- **ロールバック全体**: `playbooks/22-cloudflare-tunnel.yml` の対象を停止する場合、`cloudflared.service` を stop/disable + sshd ドロップイン削除 + reload。Cloudflare 側は DNS ルート / Access を無効化（手動）。
