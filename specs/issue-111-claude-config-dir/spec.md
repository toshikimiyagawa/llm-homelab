# Spec: issue-111-claude-config-dir

- Tier: 1
- Status: spec
- Issue: #111

## Intent

devcontainer を `devcontainer up --remove-existing-container` で作り直しても Claude Code の
ログイン/オンボーディング状態が保持されるよう、`.devcontainer/devcontainer.json` の `remoteEnv`
に `CLAUDE_CONFIG_DIR=/home/ubuntu/.claude` を設定する。

`~/.claude` は既存の symlink（`/workspace/dotfiles/.claude`、永続バインドマウント）で永続化されているが、
`CLAUDE_CONFIG_DIR` が無いと Claude Code はトップレベル状態を `$HOME/.claude.json`（ephemeral）に書き、
rebuild で消えて再ログイン/再オンボーディングを誘発する。`CLAUDE_CONFIG_DIR` を永続ディレクトリへ向けることで
`.claude.json` を含む config を永続側へ集約する。

upstream agents-devcontainer は #32 で base に `CLAUDE_CONFIG_DIR` を追加済み。本リポジトリの生成済み
`.devcontainer/devcontainer.json` を `scaffold/merge.sh` で再生成して取り込む。再生成で base 由来の
GIT_AUTHOR 系が復活するが、これは issue #77 で意図的に削除済みのため再除去して維持する（upstream:
agents-devcontainer#33 で根本対応を依頼）。

## Acceptance Criteria

1. `.devcontainer/devcontainer.json` の `remoteEnv` に
   `"CLAUDE_CONFIG_DIR": "/home/ubuntu/.claude"` が含まれる。
2. `remoteEnv` は既存の `GH_CONFIG_DIR == "/home/ubuntu/.gh-config"` を維持する。
3. `remoteEnv` は GIT_AUTHOR/COMMITTER 系を定義しない（issue #77 の決定を維持。
   `tests/devcontainer/test_git_identity_env.py` が継続して通る）。
4. 上記を確認する regression test がある。

## Verification

- `python -m pytest tests/devcontainer/test_claude_config_dir.py tests/devcontainer/test_git_identity_env.py`

## Out of Scope

- `.gemini` / `.codex` の同等対応。
- agents-devcontainer 側の `merge.sh` 改修（agents-devcontainer#33 で対応）。
- 既存の永続化機構（`~/.claude` symlink、gh named volume、ssh ホストマウント）の変更。
