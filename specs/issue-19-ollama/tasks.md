# Tasks: issue-19-ollama

> 他 agent が設計コンテキスト無しで実装できるよう、各タスクは具体的に（ファイルパス・変数・テスト）書く。

## 実装タスク（順序付き）

- [ ] T1: `roles/ollama/defaults/main.yml` を作成する。以下の変数を定義する。
  ```yaml
  ollama_version: "0.24.0"
  ollama_install_dir: /usr/local/bin
  ollama_models_dir: /opt/ollama/models
  ollama_host: "127.0.0.1"
  ollama_port: 11434
  ollama_cuda_visible_devices: "0"   # GTX 1650。実機確認後に inventory で上書き
  ```
  対応AC: AC2, AC3, AC4

- [ ] T2: `roles/ollama/tasks/main.yml` を作成する。以下のタスクを順に定義する。
  1. 現在インストール済みの Ollama バージョンを取得（`/usr/local/bin/ollama --version`）
  2. バージョン不一致またはバイナリ未存在の場合のみ GitHub Releases から
     `https://github.com/ollama/ollama/releases/download/v{{ ollama_version }}/ollama-linux-amd64`
     をダウンロードし `/usr/local/bin/ollama` に配置（mode: `0755`）
  3. `ollama` 実行ユーザー（`ollama` グループ）を作成
  4. `/opt/ollama/models` ディレクトリを作成（owner: root, mode: `0755`）
  5. `templates/override.conf.j2` を `/etc/systemd/system/ollama.service.d/override.conf` に配置
     → handler: `daemon-reload`
  6. `ollama.service` を `enabled: true`, `state: started` に設定
  対応AC: AC1, AC2, AC3, AC4, AC5

- [ ] T3: `roles/ollama/handlers/main.yml` を作成する。
  - `daemon-reload`: `systemctl daemon-reload`
  - `restart ollama`: `systemctl restart ollama`（`daemon-reload` の後に実行）
  対応AC: AC1, AC5

- [ ] T4: `roles/ollama/templates/override.conf.j2` を作成する。内容:
  ```ini
  [Service]
  Environment="OLLAMA_HOST={{ ollama_host }}:{{ ollama_port }}"
  Environment="OLLAMA_MODELS={{ ollama_models_dir }}"
  Environment="CUDA_VISIBLE_DEVICES={{ ollama_cuda_visible_devices }}"
  ```
  notify: `daemon-reload`, `restart ollama`
  対応AC: AC2, AC3, AC4

- [ ] T5: `playbooks/20-ollama.yml` を作成する。
  ```yaml
  ---
  - name: Install Ollama lightweight inference engine
    hosts: llm01
    become: true
    roles:
      - ollama
  ```
  対応AC: AC1

- [ ] T6: `playbooks/site.yml` に import を追加する（`10-flux-pro-display.yml` の後）。
  ```yaml
  - name: Install Ollama lightweight inference engine
    ansible.builtin.import_playbook: 20-ollama.yml
  ```
  対応AC: AC1

- [ ] T7: `docs/operations.md` に「Ollama」セクションを追加する。以下の内容を含む。
  - サービス状態確認: `systemctl status ollama`
  - ログ確認: `journalctl -u ollama -f`
  - ヘルスチェック: `curl http://127.0.0.1:11434/api/tags`
  - モデル一覧: `ollama list`
  - モデル手動取得例: `ollama pull qwen2.5:0.5b`（GTX 1650 の 4GB VRAM に収まる量子化モデル推奨）
  - GPU 確認: `nvidia-smi`（GTX 1650 の使用率が上がることを確認）
  対応AC: AC6

## テスト（受入条件との対応・必須）

- [ ] AC1 → `molecule/ollama/tests/test_service.py`: `ollama.service` が `active` かつ `enabled`
- [ ] AC2 → `molecule/ollama/tests/test_dirs.py`: `/opt/ollama/models` が存在し mode `0755`
- [ ] AC3 → `molecule/ollama/tests/test_network.py`: `ss -tlnp | grep 11434` が `127.0.0.1:11434` のみ
- [ ] AC4 → `molecule/ollama/tests/test_env.py`: override.conf に `CUDA_VISIBLE_DEVICES` が含まれる
- [ ] AC5 → AC1 テストの `enabled` アサーションで兼用
- [ ] AC6 → `molecule/ollama/tests/test_docs.py`: `docs/operations.md` に `ollama` セクションが存在する

> **Note**: Molecule テストは実機 GPU なしの CI 環境でも通るよう、`nvidia-smi` を呼ぶテストは skip/mock する。
> systemd の active 確認は `ansible.builtin.systemd` の `status` をアサートする形で実装する。

## 完了の定義

- [ ] 全 AC 対応テストが green
- [ ] `ansible-lint playbooks/20-ollama.yml` が通る
- [ ] `yamllint roles/ollama/` が通る
- [ ] CI green
- [ ] sdd-reviewer 合格
