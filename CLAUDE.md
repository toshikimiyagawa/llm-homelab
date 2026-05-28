# Project Guidelines (Claude Code)

このプロジェクトは Spec-Driven Development (SDD) に従う。正本は submodule にある。
作業前に必ず以下を読むこと:

@vendor/ai-sdd-guide/rules/core.md
@vendor/ai-sdd-guide/rules/workflow.md
@vendor/ai-sdd-guide/rules/subagents.md
@vendor/ai-sdd-guide/rules/conventions.md

- 設計フェーズ (spec/plan/tasks/verify) は Claude のみ。superpowers と subagent を使う。
- 実装は他agentでも可。`specs/<feature>/` を契約として厳守する。
- 人間向け解説: `vendor/ai-sdd-guide/docs/` ／ 雛形: `vendor/ai-sdd-guide/templates/`

---

# プロジェクト固有ルール

このリポジトリは、自宅実家に設置するLLM推論サーバーをAnsibleで再現可能に構築・運用するためのものです。

エージェントは作業前にこのファイルを読み、ここに書かれた設計判断と運用ルールを尊重してください。判断を変更する場合はユーザーに確認を取ること。

## 必ず守ること

- シークレットを平文でコミットしない。
- シークレットをログに出さない。Ansibleで扱うタスクは必ず`no_log: true`を付ける。
- 既存の設計判断を変える前にユーザーに確認する。
- タスクは冪等にする。何度実行しても安全なAnsible/スクリプトにする。
- コミット前に可能な範囲で`ansible-lint`、`yamllint`、該当テストを実行する。
- Publicリポジトリ前提で、個人情報・トークン・秘密鍵・内部URLを不用意に書かない。

## 重要な設計判断

- 24時間稼働、エアコンなし、夏場35度想定。冷却と信頼性を優先する。
- 水冷/AIO水冷は使わない。空冷前提。
- Secure Bootは無効化する。Blackwell世代NVIDIAドライバの制約を優先する。
- RAIDは使わない。2本のNVMeを役割分担する。
- Ubuntuインストーラ由来のLVMは維持する。`/var/lib/rancher`を別LVに分離済み。
- Anthropic連携はAPIキー利用を基本にする。Claude Pro/MaxのOAuthトークンを第三者ツールに埋め込まない。
- ローカルLLMから`claude`コマンドを自動実行しない。規約違反リスクがある。

## 実機状態の要点

- ホスト名: `llm01`
- OS: Ubuntu 26.04 LTS
- CPU: AMD Ryzen 9 3950X
- RAM: 128GB DDR4
- GPU: 現在GTX 1650のみ。RTX Pro 6000 Blackwell 600W版は2026-05-29または2026-05-30装着予定。
- ストレージ:
  - `/`: 100GB ext4 on LVM
  - `/var/lib/rancher`: 300GB ext4 on LVM
  - `/opt`: 約916GB ext4 on `/dev/nvme1n1p1`

詳細は以下を参照してください。

- [README.md](README.md): 公開向けの概要と構築フェーズ
- [docs/hardware.md](docs/hardware.md): ハードウェア構成、実機確認状況、GPU配置
- [docs/storage.md](docs/storage.md): ディスク/パーティション/マウント設計
- [docs/software-stack.md](docs/software-stack.md): OS、k3s、NVIDIA、推論エンジン
- [docs/operations.md](docs/operations.md): 構築フロー、監視、バックアップ、緊急対応
- [docs/security-and-secrets.md](docs/security-and-secrets.md): 1Password、API利用ポリシー、禁止事項
- [docs/repository-guidelines.md](docs/repository-guidelines.md): ディレクトリ構造、コーディング規約、コミット方針

## 作業ワークフロー

SDD ワークフロー（Tier制）に従う。詳細は `vendor/ai-sdd-guide/rules/workflow.md` を参照。

1. 作業範囲を確認し、Tier を判定する（0: 自明な修正、1: 小さなbugfix、2: 中〜大機能）。
2. 必ずfeatureブランチを作成し、`main`へ直接コミットしない。
3. Tier 1以上は `specs/<feature>/` に spec を作成してから実装する。
4. 実装・ドキュメント更新・テストを行う。
5. `git status`で意図しない変更がないことを確認する。
6. Conventional Commits形式でコミットする。
7. マージするときは必ずPRを作成し、ユーザーレビュー後に`main`へマージする。
8. PRのdescriptionは日本語で書く。

CI/CD自動デプロイはしない。本番サーバーへの適用は手動で`ansible-playbook`を実行する。
