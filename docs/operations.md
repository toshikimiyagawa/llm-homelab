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

## 緊急対応

サーバーが応答しない場合:

1. Tailscale経由でSSH接続を試す。
2. ダメなら実家に物理アクセスを依頼する。
3. 復旧後、`ansible-playbook playbooks/site.yml`で再構築できる状態を維持する。
