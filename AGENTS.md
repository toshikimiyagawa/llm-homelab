# AGENTS.md

このリポジトリは、自宅に設置するLLM推論サーバーをAnsibleで自動構築するためのものです。Claude Code / Codex CLI / Gemini CLI 等のエージェントが作業しやすいよう、設計判断・前提・運用ポリシーをまとめています。

エージェントは**実装を進める前に必ずこのファイルを読んで**、設計判断を尊重してください。判断を変更する場合はユーザーに確認を取ること。

---

## プロジェクト目的

自宅実家に設置するLLM推論サーバーを、再現可能な形で構築・運用する。

- **メインワークロード**: 大型LLM推論（vLLM、Qwen3.6-35B等）
- **サブワークロード**: 軽量モデル推論（Ollama）、Web UI、検索エージェント
- **運用形態**: 24時間稼働、リモートからアクセス
- **管理方針**: 全てコード化（Infrastructure as Code）、再構築可能

---

## ハードウェア構成（確定・実機確認状況）

確認日: 2026-05-28（llm01 / Ubuntu上で確認）

| 区分 | 内容 |
|------|------|
| **ホスト名** | llm01 |
| **CPU** | AMD Ryzen 9 3950X（16C32T、TDP 105W、PPT 142W）※`lscpu`で確認 |
| **マザーボード** | ASUS ROG Strix X570-E Gaming ※DMIで確認 |
| **BIOS** | American Megatrends Inc. 5031（2025-01-13）※DMIで確認 |
| **RAM** | 128GB DDR4（32GB × 4、G.Skill F4-3200C16-32GVK、現在2666 MT/s動作）※DMIで確認 |
| **GPU 1（推論メイン）** | NVIDIA RTX Pro 6000 Blackwell Workstation Edition（**600Wフル版**、96GB VRAM）※2026-05-29または2026-05-30装着予定 |
| **GPU 2（軽量推論）** | NVIDIA GeForce GTX 1650（4GB VRAM）※PCIe上で確認、現在nouveauドライバ |
| **ストレージ** | NVMe SSD 1TB × 2（CSSD-M2B1TPG3VNF系、M.2_1/M.2_2）※`lsblk`で確認 |
| **ケース** | Antec Flux Pro（無印、通常版） |
| **電源** | Seasonic PRIME TX-1600（通常版、80+ Titanium、ATX 3.1、12V-2x6、12年保証） |
| **CPUクーラー** | Noctua NH-D15（空冷、初代 or D15S） |

### 現在の実機状態

- **OS**: Ubuntu 26.04 LTS
- **カーネル**: Linux 7.0.0-15-generic
- **Secure Boot**: Disabled（`mokutil --sb-state`で確認）
- **IOMMU**: IOMMUグループ作成あり（`/sys/kernel/iommu_groups`で確認）
- **NVIDIAドライバ**: 未導入（`nvidia-smi`なし、GTX 1650はnouveau使用中）
- **RTX Pro 6000**: 未装着。装着後に`lspci`、`nvidia-smi`、GPU UUID、PCIeリンク幅を確認してinventoryへ反映する。
- **Re-Size BAR / Above 4G Decoding**: BIOS設定で有効化必須。RTX Pro 6000装着後にOS側で再確認する。

### GPU配置（重要）

```
PCIe x16_1 (CPU直結 x16) ──→ RTX Pro 6000  ← フルレーン維持
PCIe x16_2 (CPU直結 x8)  ──→ 空（GPU間スペース確保、熱干渉回避）
PCIe x16_3 (チップセット x4) ─→ GTX 1650
```

理由：

- RTX Pro 6000は x16 フルレーン維持
- GTX 1650は軽量推論用途で x4 で十分
- GPU間に空きスロットを設け、熱干渉を回避

### サイズ・クリアランス確認済み

| 項目 | サイズ | ケース対応 | 余裕 |
|------|--------|----------|------|
| CPUクーラー高さ | 165mm | 170mm | 5mm |
| PSU長さ | 210mm | 300mm（HDDケージ撤去時） | 90mm |
| GPU長さ | 304mm | 455mm | 151mm |

すべて余裕を持って収まる。

### ストレージ設計

```
/dev/nvme0n1 (1TB NVMe) → システム用
   ├── /boot/efi              (1GB, vfat)
   ├── /boot                  (2GB, ext4)
   └── ubuntu-vg (LVM)
       ├── /                  (100GB, ext4) - OS、ホームディレクトリ
       ├── /var/lib/rancher   (300GB, ext4) - k3sデータ、コンテナイメージ
       └── 空き               (約528GB) - 拡張余地

/dev/nvme1n1 (1TB NVMe) → モデル・データ用
   └── /opt                   (約916GB, ext4)
       ├── /opt/models             - LLMモデル本体
       ├── /opt/huggingface-cache  - HFキャッシュ
       └── /opt/prometheus-data    - メトリクス
```

**RAIDは使わない**（役割分担で管理シンプル化）。当初はLVMなしを想定していたが、Ubuntuインストーラ既定のLVM構成を活かす方針に変更済み。理由は、既存の正常なOSインストールを維持しつつ、k3sの肥大化しやすいデータだけ`/var/lib/rancher`へ分離できるため。

実機の永続マウント設定:

- `/`: `/dev/mapper/ubuntu--vg-ubuntu--lv`
- `/var/lib/rancher`: `/dev/mapper/ubuntu--vg-rancher`
- `/opt`: `/dev/nvme1n1p1`

### ケース設定

- **HDDケージ**: 撤去（TX-1600 210mm 搭載のため必須）
- **ボトムファン**: 追加可能スペースあり（必要に応じて）
- **3.5"HDD**: 内蔵不可、外付け（USB 3.0ドック）またはNAS化で対応

### 設置環境（重要な制約）

- **実家の空き部屋に設置**（リモート運用）
- **エアコンなし**（夏場の室温35℃想定）
- **24時間稼働**
- 隣の部屋まで爆音でなければ静音性は妥協可
- メンテのための物理アクセスは年数回程度

→ 冷却最優先、信頼性最優先、メンテ頻度最小化の設計。

### 電源 (TX-1600) 運用方針

- **負荷率**: 平常運用で38〜57%（最高効率ゾーン）
- **セミファンレスモード**: OFF設定（コンデンサ寿命のため常時回転）
- **12V-2x6コネクタ**: 純正ケーブル使用、急角度の曲げ禁止
- **保証**: 12年（24時間稼働でも安心）

---

## ソフトウェアスタック

### OS / ベースシステム

- **OS**: Ubuntu 26.04 LTS（Resolute Raccoon、2026年4月リリース）
- **カーネル**: Linux 7.0
- **サポート**: 2031年4月まで

### コンテナ・オーケストレーション

- **k3s**（軽量Kubernetes、シングルノード運用）
- **containerd**（k3sのデフォルトランタイム）
- **NVIDIA Container Toolkit**
- **NVIDIA Device Plugin for Kubernetes**

### NVIDIA関連

- **ドライバ**: 575系（オープンソースカーネルモジュール必須、Blackwell世代の制約）
- **CUDA**: 12.9以降

### 推論エンジン

| エンジン | GPU割り当て | 用途 |
|---------|------------|------|
| **vLLM** | RTX Pro 6000 | メイン推論、並列処理、OpenAI互換API |
| **Ollama** | GTX 1650 | 軽量モデル、ホットスワップ、4GB VRAM向け |

### 周辺サービス

- **Open WebUI**: ChatGPT風UI、Web検索機能内蔵
- **SearXNG**: セルフホスト検索エンジン（プライバシー保護）
- **Prometheus + Grafana + node-exporter**: 温度・リソース監視
- **Tailscale**: リモートアクセス（VPN）
- **Antec Flux Pro温度ディスプレイ**: Linux対応OSS実装（Reikooters/antec-flux-pro-display）

### 外部AI連携（将来）

オーケストレーション構成。ローカルLLMがメインで、必要時のみクラウドAPIを呼ぶ：

```
[ローカルLLM (Qwen3.6 on RTX Pro 6000)]  ← メインエージェント
    ├── ローカルで完結する処理 → 無料
    ├── Web検索 → Gemini API（Flash無料枠）
    └── 複雑な推論 → Anthropic API（Pro $20プログラム枠 or 従量）
```

---

## 設計判断と禁止事項

### Anthropic API 利用ポリシー（重要）

- ✅ **Anthropic APIキー使用OK**（合法、従量課金）
- ✅ Claude Pro契約の**$20プログラム枠**（2026年6月15日〜）
- ✅ **`claude` コマンドを人間が起動して使う**は完全合法
- ⚠️ ローカルLLMから`claude`コマンドを自動で叩く ← 規約違反リスク
- ❌ Claude Pro/Maxの**OAuthトークンを第三者ツールに埋め込む** ← 規約違反
- ❌ サブスク経由でのプログラム的大量利用 ← 禁止

実装時は**APIキー利用を基本**とし、サブスクの自動化利用は避ける。

### コンテンツ・ライセンス

- リポジトリは **Public**（GitHub）
- 個人利用、参考目的の公開
- ライセンスはMIT等を予定

### 安全性・信頼性

- **水冷は使わない**（24時間稼働でポンプ故障リスク回避）
- **AIO水冷も避ける**（同上）
- **空冷一択**（Noctua NH-D15）
- BIOS設定で **Above 4G Decoding / Re-Size BAR / IOMMU** 有効化必須
- Secure Boot は無効化（Blackwellドライバの制約）

### 電源・GPU運用

夏場のGPUパワーリミット運用も視野に：

```bash
sudo nvidia-smi -i 1 -pl 450  # 夏場450W制限
sudo nvidia-smi -i 1 -pl 600  # 通常600W
```

### バックアップ戦略

| 対象 | 重要度 | 戦略 |
|------|-------|------|
| **Ansible Playbook** | ★★★★★ | GitHub（自動バックアップ） |
| **Open WebUI 会話履歴** | ★★★★ | 定期エクスポート、外付けHDDへ |
| **モデル設定** | ★★★★ | GitHub管理 |
| **シークレット** | ★★★★★ | 1Password |
| **Prometheusデータ** | ★★ | 喪失OK（再収集可能） |
| **LLMモデル本体** | ★ | 再ダウンロード可能 |

**LLMモデル本体はバックアップ不要**（HuggingFaceから再ダウンロード）。

---

## リポジトリ運用ルール

### ディレクトリ構造（予定）

```
llm-homelab/
├── AGENTS.md                    # このファイル
├── README.md                    # 公開向け説明
├── LICENSE
├── ansible.cfg
├── requirements.yml             # Ansibleコレクション/ロール
├── inventory/
│   ├── hosts.yml
│   └── group_vars/
│       └── all/
│           └── vars.yml         # 1Password lookup経由でシークレット参照
├── playbooks/
│   ├── site.yml                 # 全部実行
│   ├── 00-bootstrap.yml         # 初期セットアップ
│   ├── 01-system.yml            # OS基本設定
│   ├── 02-nvidia.yml            # NVIDIAドライバ
│   ├── 03-container.yml         # Docker + Container Toolkit
│   ├── 04-k3s.yml               # k3sインストール
│   ├── 05-gpu-plugin.yml        # NVIDIA Device Plugin
│   ├── 06-monitoring.yml        # Prometheus + Grafana
│   ├── 07-tailscale.yml         # Tailscale設定
│   ├── 08-workloads.yml         # vLLM, Ollama等のデプロイ
│   └── 09-flux-pro-display.yml  # ケース温度ディスプレイ
├── roles/
│   ├── common/
│   ├── nvidia/
│   ├── container/
│   ├── k3s/
│   ├── tailscale/
│   ├── monitoring/
│   ├── workloads/
│   └── flux_pro_display/
├── manifests/                   # k3s用のKubernetesマニフェスト
│   ├── namespace.yaml
│   ├── storage/
│   │   └── local-pv.yaml
│   ├── nvidia-device-plugin.yaml
│   ├── vllm-deployment.yaml
│   ├── ollama-deployment.yaml
│   ├── open-webui-deployment.yaml
│   ├── searxng-deployment.yaml
│   ├── prometheus-stack.yaml
│   └── ingress.yaml
├── scripts/
│   ├── bootstrap.sh             # SSH接続後の最初の手動セットアップ
│   ├── thermal-guard.sh         # 温度監視・自動停止
│   └── backup-openwebui.sh      # 定期バックアップ
└── .github/
    └── workflows/
        ├── lint.yml             # ansible-lint + yamllint
        └── security.yml         # シークレット漏洩検知
```

### コーディング規約

- **YAML**: 2スペースインデント、yamllint準拠
- **Ansible**: ansible-lint推奨ルール準拠
- **タスク名**: 動詞始まりで具体的に（`Install NVIDIA driver` ◯、`nvidia` ✗）
- **冪等性**: 全タスクが何度実行しても安全であること
- **タグ**: 各playbookに適切な `tags:` を付与（部分実行可能に）
- **no_log**: シークレットを含むタスクは必ず `no_log: true`

### コミットメッセージ

Conventional Commits 形式：

```
feat: add vLLM deployment manifest
fix: correct GPU UUID for RTX Pro 6000
docs: update README with setup instructions
chore: bump ansible collections version
refactor: split nvidia role into driver and toolkit
```

### ブランチ戦略

- `main`: 常に動作する状態を維持
- 大きな変更は feature ブランチで作業 → PR → マージ
- 1台運用なので CI/CD自動デプロイは**しない**（手動で `ansible-playbook` 実行）

---

## シークレット管理（1Password Service Account）

### 方針

**1Password Service Account を使用**。理由：

- 既に1Password利用中
- 環境変数のみで動作、Touch ID不要
- エージェントが完全非対話で実行可能
- 個人プランで利用可能

### Vault構成

専用Vault: `LLM Server Infrastructure`

格納するシークレット：

- Tailscale Auth Key
- Anthropic API Key
- Google AI API Key (Gemini)
- k3s Token
- GitHub Personal Access Token (CI用)
- 必要に応じて追加

### 環境変数設定

```bash
# ~/.zshrc
export OP_SERVICE_ACCOUNT_TOKEN="$(security find-generic-password \
  -s 'op-service-account-llm' -w)"
```

トークン自体はMacのKeychainに保存。**リポジトリには絶対にコミットしない**。

### Ansibleでの使用例

```yaml
- name: Cache secrets at start
  set_fact:
    secrets:
      tailscale: "{{ lookup('community.general.onepassword',
                            'Tailscale Auth Key',
                            vault='LLM Server Infrastructure') }}"
      anthropic: "{{ lookup('community.general.onepassword',
                            'Anthropic API Key',
                            vault='LLM Server Infrastructure') }}"
  no_log: true
  delegate_to: localhost
  run_once: true
```

レート制限対策として、**playbook開始時に1回だけ取得してキャッシュ**する。

### 禁止事項

- ❌ シークレットを平文で commit
- ❌ ログにシークレットを出力（no_log忘れ）
- ❌ Service Accountトークンをコードに記述
- ❌ Private Vault に格納（Service Accountからアクセス不可）

---

## 構築フロー

### Phase 0: 手動セットアップ（人間が実施）

1. Ubuntu 26.04 LTS をインストール
2. ユーザー作成、sudoers設定
3. `sudo apt update && sudo apt install -y openssh-server`
4. Macから接続できるよう SSH公開鍵を `~/.ssh/authorized_keys` に登録
5. ホストの固定IP設定（または Tailscale 経由前提）
6. BIOS設定確認:
   - Secure Boot: Disabled
   - Above 4G Decoding: Enabled
   - Re-Size BAR Support: Enabled
   - IOMMU: Enabled

ここまで完了したら、Macから `ansible all -m ping` で疎通確認。

### Phase 1: Ansible自動構築（GTX 1650のみで動作）

RTX Pro 6000装着前、GTX 1650だけで実行可能な範囲：

```bash
# Mac上で実行
ansible-playbook playbooks/site.yml --skip-tags vllm
```

実施内容：

- システム初期設定（タイムゾーン、ロケール、不要パッケージ削除）
- ストレージ設定（nvme1n1 を /opt にマウント）
- NVIDIAドライバ575系インストール（オープンソースモジュール）
- Docker + NVIDIA Container Toolkit
- k3s インストール（containerd経由）
- NVIDIA Device Plugin デプロイ
- Tailscale設定
- Prometheus + Grafana + node-exporter
- Ollama Pod デプロイ（GTX 1650）
- Open WebUI、SearXNG デプロイ
- Antec Flux Pro温度ディスプレイ設定

### Phase 2: RTX Pro 6000 追加（物理装着後）

2026-05-29または2026-05-30に装着予定。

1. シャットダウン → RTX Pro 6000 物理装着 → 起動
2. `nvidia-smi` で両GPU認識確認
3. GPU UUID を取得して inventory に記録
4. vLLM デプロイ:

   ```bash
   ansible-playbook playbooks/site.yml --tags vllm
   ```

### Phase 3: 運用

- 監視ダッシュボード: `http://100.x.x.x:3001`（Tailscale経由）
- Open WebUI: `http://100.x.x.x:3000`
- vLLM API: `http://100.x.x.x:8000/v1`
- Ollama API: `http://100.x.x.x:11434`

---

## 動作確認・監視

### 温度監視（重要）

エアコンなし環境のため、以下の閾値で運用：

```yaml
alerts:
  gpu_temp_warning: 80℃
  gpu_temp_critical: 85℃   # ここで自動的にワークロード停止
  cpu_temp_warning: 80℃
  cpu_temp_critical: 88℃   # ここで vLLM を pause
  case_temp_warning: 50℃   # ケース内温度
  nvme_temp_warning: 65℃
  nvme_temp_critical: 75℃   # サーマルスロットリング前
```

自動停止スクリプトを `scripts/thermal-guard.sh` に配置、systemd timer で定期実行。

### ディスク監視

```yaml
disk_alerts:
  usage_warning: 75%
  usage_critical: 90%
  nvme_lifetime_warning: 80%  # SMART寿命使用率
```

### ヘルスチェック

各Podに liveness/readiness probe を設定：

- vLLM: `GET /health`
- Ollama: `GET /`
- Open WebUI: `GET /health`

異常時は k3s が自動再起動。

---

## エージェントへの依頼方針

### Claude Code / Codex CLI 使用時の注意

1. **このAGENTS.mdを最初に読む**
2. **設計判断を尊重**（変更前に確認）
3. **シークレットを絶対にハードコードしない**
4. **`no_log: true` を忘れない**
5. **冪等性を保つ**（複数回実行しても安全）
6. **テストを書く**（可能な範囲で）
7. **コミット前に `ansible-lint`、`yamllint` を実行**
8. **不明点は推測せず確認する**

### 推奨ワークフロー

```
1. Issue または タスクで作業範囲を明確化
2. featureブランチを作成
3. 実装・テスト
4. ansible-lint、yamllint パス
5. PR作成、ユーザーレビュー
6. main にマージ
7. 本番（実家サーバー）に手動でplaybook適用
```

### 緊急対応

サーバーが応答しない場合：

1. Tailscale で SSH 接続試行
2. ダメなら実家に物理アクセス依頼
3. 復旧手順: `ansible-playbook playbooks/site.yml` で再構築可能な状態を維持

---

## 参考リソース

### NVIDIA関連

- [NVIDIA Driver Downloads](https://www.nvidia.com/Download/index.aspx)
- [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-container-toolkit)
- [NVIDIA Device Plugin for Kubernetes](https://github.com/NVIDIA/k8s-device-plugin)

### k3s関連

- [k3s 公式ドキュメント](https://docs.k3s.io/)
- [k3s + GPU セットアップ](https://docs.k3s.io/advanced#nvidia-container-runtime-support)

### 推論エンジン

- [vLLM](https://github.com/vllm-project/vllm)
- [Ollama](https://ollama.com/)
- [Open WebUI](https://github.com/open-webui/open-webui)

### Antec Flux Pro温度ディスプレイ

- [Reikooters/antec-flux-pro-display](https://github.com/Reikooters/antec-flux-pro-display)
- [nishtahir/antec-flux-pro-display](https://github.com/nishtahir/antec-flux-pro-display)

### Ubuntu 26.04 + RTX Pro 6000の参考事例

- [Qiita記事: Ubuntu-26.04 + RTX PRO 6000 Blackwell環境構築](https://qiita.com/matsudai/items/b0142958ae0e897c7757)
  - Max-Q版（300W）での事例だが、初期構築は共通
  - Secure Boot 無効化手順、ドライバインストール手順が詳細

### 1Password

- [Service Accounts](https://developer.1password.com/docs/service-accounts/)
- [Ansible 1Password lookup](https://docs.ansible.com/ansible/latest/collections/community/general/onepassword_lookup.html)

---

## 変更履歴

| 日付 | 内容 |
|------|------|
| 2026-05-27 | 初版作成 |
| 2026-05-27 | ハードウェア確定（PSU通常版、ケース通常版、Noctua NH-D15）、ストレージ設計追加 |
| 2026-05-28 | llm01実機確認結果を反映。現行LVM構成、/var/lib/rancher、/optマウント、RTX Pro 6000装着予定を追記 |

---

## 連絡先・運営

このリポジトリは個人プロジェクトです。Issueは歓迎しますが、サポートは保証しません。
