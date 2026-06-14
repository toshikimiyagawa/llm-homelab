# Operations

## 現在の進捗

2026-05-28時点:

- Ubuntu 26.04 LTSインストール済み。
- SSHログイン可能。
- ホスト名は`llm01`に設定済み。
- `/var/lib/rancher`と`/opt`のストレージ分離は設定済み。
- GTX 1650のみ装着済み。
- Ansible inventory、preflight、基本OS設定roleは作成済み。
- 基本OS設定playbookは適用済み。timezone、ベースパッケージ、`/opt`配下のデータディレクトリをAnsible管理している。
- NVIDIA 575 open driver roleは作成済み、適用済み。Ubuntu 26.04では実ドライバ580.159.03として導入されている。
- NVIDIA Container Toolkit 1.19.1は導入済み。
- k3s v1.35.5+k3s1は導入済み。`llm01`はReady。
- k3s containerd設定で`nvidia-container-runtime`検出済み。
- NVIDIA Device Plugin 0.17.1は導入済み。`llm01`は`nvidia.com/gpu: 1`を公開している。
- Kubernetes上の一時Jobで`runtimeClassName: nvidia`と`nvidia.com/gpu: 1`を指定し、Pod内`nvidia-smi`実行確認済み。
- Tailscale、監視、ワークロードは未構築。
- RTX Pro 6000は未装着。2026-05-29または2026-05-30に装着予定。
- 初期構築用に`toshiki ALL=(ALL) NOPASSWD: ALL`を一時設定中。構築完了後に削除または限定化する。

## 構築フロー

### Phase 0: 手動セットアップ

人間が実施する。

1. Ubuntu 26.04 LTSをインストールする。
2. ユーザー作成、sudoers設定を行う。
3. OpenSSH Serverをインストールする。
4. Macから接続できるようSSH公開鍵を登録する。
5. 固定IPまたはTailscale前提のネットワークを設定する。
6. BIOS設定を確認する。

BIOS必須設定:

- Secure Boot: Disabled
- Above 4G Decoding: Enabled
- Re-Size BAR Support: Enabled
- IOMMU: Enabled

### 構築前プリフライト

Ansibleを流す前に、Mac側から以下を確認する。

```bash
ssh llm01 hostnamectl
ssh llm01 findmnt /var/lib/rancher
ssh llm01 findmnt /opt
ssh llm01 mokutil --sb-state
ssh llm01 'find /sys/kernel/iommu_groups -maxdepth 1 -type d | wc -l'
ansible all -m ping
```

期待値:

- ホスト名が`llm01`。
- `/var/lib/rancher`と`/opt`が別ファイルシステムとしてマウント済み。
- Secure Bootがdisabled。
- IOMMUグループが作成されている。
- Ansible pingが成功する。

現在のAnsible実行入口:

```bash
ansible-playbook playbooks/00-bootstrap.yml
ansible-playbook playbooks/01-system.yml
ansible-playbook playbooks/02-nvidia.yml
ansible-playbook playbooks/03-container.yml
ansible-playbook playbooks/04-k3s.yml
ansible-playbook playbooks/05-gpu-plugin.yml
ansible-playbook playbooks/10-flux-pro-display.yml
ansible-playbook playbooks/20-ollama.yml
ansible-playbook playbooks/site.yml
```

GPU Pod動作確認は通常構築とは分け、必要時だけ一時Jobとして実行する。

```bash
ansible-playbook playbooks/06-gpu-smoke-test.yml
```

### Phase 1: GTX 1650のみで構築

RTX Pro 6000装着前に実行できる範囲。

```bash
ansible-playbook playbooks/site.yml --skip-tags vllm
```

実施内容:

- OS基本設定
- ストレージ設定
- NVIDIAドライバ575系
- containerd / k3s
- NVIDIA Device Plugin
- Tailscale
- Prometheus / Grafana / node-exporter
- Ollama
- Open WebUI
- SearXNG
- Antec Flux Pro温度ディスプレイ

### Phase 2: RTX Pro 6000追加

2026-05-29または2026-05-30に装着予定。

1. シャットダウンする。
2. 電源ケーブルを抜き、残留電荷を抜く。
3. RTX Pro 6000をPCIe x16_1に装着する。
4. GTX 1650がチップセット側スロットにあることを確認する。
5. 12V-2x6純正ケーブルを挿し込み、急角度で曲がっていないことを確認する。
6. 起動する。
7. BIOSでSecure Boot、Above 4G Decoding、Re-Size BAR、IOMMUを再確認する。
8. OS起動後に`lspci`と`nvidia-smi`で両GPU認識を確認する。
9. GPU UUIDとPCIeリンク幅を取得してinventoryに記録する。
10. vLLMをデプロイする。

装着後の確認コマンド:

```bash
lspci -nn | grep -Ei 'vga|3d|display|nvidia'
nvidia-smi
nvidia-smi -L
sudo lspci -vv -s <RTX_BUS_ID> | grep -E 'LnkCap|LnkSta'
```

```bash
ansible-playbook playbooks/site.yml --tags vllm
```

### Phase 3: 運用

- Grafana: `http://100.x.x.x:3001`
- Open WebUI: `http://100.x.x.x:3000`
- vLLM API: `http://100.x.x.x:8000/v1`
- Ollama API: `http://100.x.x.x:11434`

## 温度監視

## Flux Pro温度表示（Linux代替実装）

Antec公式 `iUnity` は Windows 向けのため、Ubuntu では
`af-pro-display`（`nishtahir/antec-flux-pro-display`）を使って
ケース表示を CPU+GPU 温度で運用する。

前提条件:

- NVIDIA ドライバ導入済み（GPU温度取得に NVML が必要）
- Flux Pro 表示デバイスが USB 接続され、`lsusb` で `2022:0522` が見える
- `udev` ルールでサービス実行ユーザーがデバイスにアクセス可能

導入:

```bash
ansible-playbook playbooks/10-flux-pro-display.yml
```

動作確認（CPU+GPU表示）:

```bash
systemctl is-enabled af-pro-display
systemctl is-active af-pro-display
journalctl -u af-pro-display -n 50 --no-pager
lsusb | grep '2022:0522'
```

期待値:

- `is-enabled` が `enabled`
- `is-active` が `active`
- ケースの温度表示が CPU/GPU の更新に追従する

障害時診断:

```bash
systemctl status af-pro-display
journalctl -u af-pro-display -n 100 --no-pager
lsusb | grep '2022:0522'
udevadm info --name=/dev/bus/usb/$(lsusb | grep '2022:0522' | awk '{print $2 "/" substr($4,1,3)}')
```

エアコンなし環境のため、温度閾値は保守的にする。

```yaml
alerts:
  gpu_temp_warning: 80
  gpu_temp_critical: 85
  cpu_temp_warning: 80
  cpu_temp_critical: 88
  case_temp_warning: 50
  nvme_temp_warning: 65
  nvme_temp_critical: 75
```

`scripts/thermal-guard.sh`を配置し、systemd timerで定期実行する。

## Ollama（GTX 1650 軽量推論）

GTX 1650（4GB VRAM）上で軽量モデルを提供する。`127.0.0.1:11434` のみにバインドし、外部に認証なしで露出しない。

導入:

```bash
ansible-playbook playbooks/20-ollama.yml
```

動作確認:

```bash
# サービス状態
systemctl is-enabled ollama
systemctl is-active ollama

# ログ
journalctl -u ollama -f

# API ヘルスチェック（モデル一覧が返れば正常）
curl http://127.0.0.1:11434/api/tags

# モデル一覧
ollama list

# GTX 1650 の GPU 使用率確認（推論中に上昇することを確認）
nvidia-smi -i 0
```

モデル取得例（GTX 1650 の 4GB VRAM に収まる量子化モデル推奨）:

```bash
ollama pull qwen2.5:0.5b
ollama pull gemma3:1b
```

障害時診断:

```bash
systemctl status ollama
journalctl -u ollama -n 100 --no-pager
cat /etc/systemd/system/ollama.service.d/override.conf
```

## GPUパワーリミット

夏場はRTX Pro 6000を450W制限で運用する可能性がある。

```bash
sudo nvidia-smi -i 1 -pl 450
sudo nvidia-smi -i 1 -pl 600
```

GPU indexは装着後に必ず確認する。固定値を安易に信用しない。

## 初期構築後の後始末

初期構築が安定したら、広すぎるpasswordless sudoを削除または限定化する。

```bash
sudo rm /etc/sudoers.d/codex
sudo visudo -c
```

エージェントによる継続運用が必要な場合は、`NOPASSWD: ALL`ではなく、必要なコマンドだけに限定したsudoersへ置き換える。

## 14TB HDDマウント確認

`/dev/sda` は `/mnt/archive` に UUID 指定で永続マウントする。

```bash
ansible-playbook playbooks/01-system.yml
```

適用後確認:

```bash
findmnt /mnt/archive
lsblk -f | grep -E 'sda|archive'
sudo mount -a
```

期待値:

- `/mnt/archive` が `UUID=...` に対応する ext4 としてマウントされている
- `mount -a` でエラーが発生しない
- 再起動後も `findmnt /mnt/archive` で同じマウントが確認できる

## ヘルスチェック

各Podにliveness/readiness probeを設定する。

| サービス | Probe |
|----------|-------|
| vLLM | `GET /health` |
| Ollama | `GET /` |
| Open WebUI | `GET /health` |

## バックアップ

| 対象 | 重要度 | 戦略 |
|------|--------|------|
| Ansible Playbook | 高 | GitHub |
| Open WebUI会話履歴 | 高 | 定期エクスポート、外付けHDD |
| モデル設定 | 高 | GitHub |
| シークレット | 高 | 1Password |
| Prometheusデータ | 低 | 喪失許容 |
| LLMモデル本体 | 低 | 再ダウンロード |

## Open WebUI の長文対策

Open WebUI から vLLM の Qwen を使う場合、`max_tokens=32000` のような大きい出力上限を長い会話履歴に対して使うと、`vllm.exceptions.VLLMValidationError` で失敗する。

回避策:

1. Open WebUI の `DEFAULT_MODEL_PARAMS` で `max_tokens` を `8192` に保つ。
2. 長い会話では、新しいチャットを開始するか、履歴を要約してから続ける。
3. モデルごとに出力上限を変えたい場合は、Open WebUI のモデル設定で上書きする。

## 外部アクセス（Cloudflare WARP private network）

`llm01` への主な外部アクセス経路は Cloudflare WARP private network とする（issue #128）。端末に Cloudflare One client を導入し、Zero Trust team に `allowed_email` で enroll する。`warp_private_network_cidr` の traffic だけを Split Tunnel Include で WARP に流し、ルーターのインバウンド開放は行わない。

Tailscale は今回撤去しない。当面は併存経路として残し、WARP 側の切り戻しや緊急対応で利用できる状態を維持する。

### Cloudflare 側 Terraform 適用

Cloudflare 側の Tunnel / WARP route / device enrollment / device profile は `infra/cloudflare/` の Terraform を正本にする。Cloudflare UI で作成・変更しない。

前提:

- Cloudflare account / Zero Trust team は存在している
- Zero Trust の Google IdP は設定済み
- `CLOUDFLARE_API_TOKEN` は環境変数で一時的に渡す
- `infra/cloudflare/terraform.tfstate` は secret として扱い commit しない

```bash
cp infra/cloudflare/terraform.tfvars.example infra/cloudflare/terraform.tfvars
export CLOUDFLARE_API_TOKEN="<temporary-token>"
terraform -chdir=infra/cloudflare init
```

`infra/cloudflare/terraform.tfvars` に account ID / zone ID / domain / host ID / allowed email / WARP private network CIDR を設定する。`llm01` の実環境では次の CIDR を使う。

```hcl
warp_private_network_cidr = "192.168.0.0/17"
```

`192.168.0.0/17` は接続元 LAN と衝突しうる。WARP 接続中にローカルネットワークや `llm01` への到達に問題がある場合は、`warp_private_network_cidr` をより狭い範囲に変更して再適用する。

既存 Tunnel がある場合は import する。

```bash
terraform -chdir=infra/cloudflare import cloudflare_zero_trust_tunnel_cloudflared.llm01 <account_id>/<tunnel_id>
terraform -chdir=infra/cloudflare import cloudflare_zero_trust_tunnel_cloudflared_config.llm01 <account_id>/<tunnel_id>
```

import 後または未作成環境では plan を確認する。

```bash
terraform -chdir=infra/cloudflare plan
```

旧公開 hostname 経路から移行する場合、旧 DNS / public-hostname Access resources の destroy は意図した差分である。それ以外の意図しない destroy / replacement が出たら `terraform apply` せず STOP する。差分が意図通りなら適用する。

```bash
terraform -chdir=infra/cloudflare apply
```

作業後、広い権限の `CLOUDFLARE_API_TOKEN` は revoke するか権限を縮小する。Terraform import/apply 後、Cloudflare UI は read-only 扱いにし、変更は Terraform PR 経由で行う。必要なら Zero Trust dashboard read-only 権限を有効化する。

Ansible 用には Terraform output を次のように反映する。

```bash
terraform -chdir=infra/cloudflare output -raw tunnel_id
terraform -chdir=infra/cloudflare output -raw tunnel_token
sops secrets/infra.sops.yml
```

`infra/cloudflare` ディレクトリ内で実行している場合は `terraform output -raw tunnel_token` で同じ値を取得できる。

- `tunnel_id`: `cloudflared_tunnel_id`（非機密）へ反映する。
- `tunnel_token`: `secrets/infra.sops.yml` の `cloudflared_tunnel_token` に格納する。token は機密として扱い、平文ファイルや shell history に残さない。

### Ansible 適用（llm01 側・再現可能）

```bash
ansible-playbook playbooks/22-cloudflare-tunnel.yml
```

`roles/cloudflared` が cloudflared install / `config.yml` / systemd 常駐 / tunnel token 配置 / sshd hardening を冪等に適用する。Cloudflare 側の private network route は Terraform が管理する。

### Cloudflare One client 接続

端末に Cloudflare One client を導入し、Zero Trust team に `allowed_email` で enroll する。device profile の変更は反映まで数分かかることがある。

```bash
warp-cli status
warp-cli settings
```

`warp-cli settings` で WARP profile と `warp_private_network_cidr` の Split Tunnel Include が反映されていることを確認する。

### 接続方法

SSH は標準 ssh で LAN IP に接続する。

```bash
ssh <user>@<llm01-lan-ip>
```

vLLM / Ollama / Open WebUI は WARP 越しに LAN IP / port へ接続する。WARP 経路では追加の Access header は不要。

```bash
curl http://<llm01-lan-ip>:11434/
curl http://<llm01-lan-ip>:8080/health
```

vLLM は環境の公開方法に合わせ、WARP 越しに LAN IP / port または LAN 内向け reverse proxy へ接続する。

```bash
curl http://<llm01-lan-ip>:<vllm-port>/v1/chat/completions \
  -H "Authorization: Bearer dummy" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.6-35b-a3b","stream":true,"messages":[{"role":"user","content":"hi"}]}'
```

Hermes agent などから検索 tool を使わせる場合、vLLM Deployment は
`--enable-auto-tool-choice`、`--reasoning-parser qwen3`、
`--tool-call-parser qwen3_coder`、
`--default-chat-template-kwargs '{"enable_thinking": false}'` で起動している
必要がある。実機確認では `enable_thinking=false` なしだと `tool_choice:auto`
は受理されても `tool_calls: []` になり、reasoning のみが返った。検索が
必要な質問で tool が呼ばれない場合は、まず Deployment args と vLLM Pod の
rollout 後ログを確認する。

OpenAI-compatible API で tool choice が受理されるかは、WARP 接続後に
次のように確認する。レスポンスが 400 で
`auto tool choice requires --enable-auto-tool-choice` を返す場合、Pod が
新しい args で再起動していない。

```bash
curl http://<llm01-lan-ip>:<vllm-port>/v1/chat/completions \
  -H "Authorization: Bearer dummy" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.6-35b-a3b","tool_choice":"auto","tools":[{"type":"function","function":{"name":"web_search","description":"Search the web for current information.","parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}}],"messages":[{"role":"user","content":"今日のニュースを検索して要約して"}]}'
```

### 運用検証チェックリスト

- [ ] W-1: Cloudflare One client が `allowed_email` で enroll できる
- [ ] W-2: `warp-cli status` が接続状態を示す
- [ ] W-3: `warp-cli settings` に `warp_private_network_cidr` の Split Tunnel Include がある
- [ ] W-4: WARP 接続状態で `ssh <user>@<llm01-lan-ip>` に標準 ssh でログインできる
- [ ] W-5: WARP 接続状態で Ollama / Open WebUI へ LAN 経由で到達できる
- [ ] W-6: vLLM へ WARP 経由で到達できる
- [ ] W-7: ルーターのインバウンド開放がゼロ
- [ ] W-8: Tailscale が削除されておらず、併存経路として残っている

### ランタイムスモークテスト（llm01 側）

```bash
ansible-playbook playbooks/23-cloudflare-smoke-test.yml
```

`cloudflared.service` の active/enabled、sshd の `PasswordAuthentication no` と `TrustedUserCAKeys` をアサートする。

## 緊急対応

サーバーが応答しない場合:

1. Tailscale経由でSSH接続を試す。
2. ダメなら実家に物理アクセスを依頼する。
3. 復旧後、`ansible-playbook playbooks/site.yml`で再構築できる状態を維持する。
