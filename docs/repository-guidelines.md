# Repository Guidelines

## 予定ディレクトリ構造

```text
llm-homelab/
├── AGENTS.md
├── README.md
├── LICENSE
├── ansible.cfg
├── requirements.yml
├── inventory/
│   ├── hosts.yml
│   └── group_vars/
│       └── all/
│           └── vars.yml
├── playbooks/
│   ├── site.yml
│   ├── 00-bootstrap.yml
│   ├── 01-system.yml
│   ├── 02-nvidia.yml
│   ├── 03-container.yml
│   ├── 04-k3s.yml
│   ├── 05-gpu-plugin.yml
│   ├── 06-monitoring.yml
│   ├── 07-tailscale.yml
│   ├── 08-workloads.yml
│   └── 09-flux-pro-display.yml
├── roles/
│   ├── common/
│   ├── nvidia/
│   ├── container/
│   ├── k3s/
│   ├── tailscale/
│   ├── monitoring/
│   ├── workloads/
│   └── flux_pro_display/
├── manifests/
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
│   ├── bootstrap.sh
│   ├── thermal-guard.sh
│   └── backup-openwebui.sh
└── .github/
    └── workflows/
        ├── lint.yml
        └── security.yml
```

## コーディング規約

- YAMLは2スペースインデント。
- yamllint準拠。
- Ansibleはansible-lint推奨ルール準拠。
- タスク名は動詞始まりで具体的にする。
- 全タスクを冪等にする。
- playbook/roleには適切な`tags:`を付与する。
- シークレットを含むタスクには`no_log: true`を付ける。

## コミットメッセージ

Conventional Commits形式を使う。

```text
feat: add vLLM deployment manifest
fix: correct GPU UUID for RTX Pro 6000
docs: update README with setup instructions
chore: bump ansible collections version
refactor: split nvidia role into driver and toolkit
```

## ブランチ戦略

- `main`: 常に動作する状態を維持する。
- 大きな変更はfeatureブランチで作業し、PRでマージする。
- 1台運用なのでCI/CD自動デプロイはしない。
- 本番適用は手動で`ansible-playbook`を実行する。

## エージェントへの依頼方針

- `AGENTS.md`を最初に読む。
- 設計判断を尊重する。
- シークレットをハードコードしない。
- `no_log: true`を忘れない。
- 冪等性を保つ。
- 可能な範囲でテストを書く。
- コミット前に`ansible-lint`、`yamllint`を実行する。
- 不明点は推測せず確認する。
