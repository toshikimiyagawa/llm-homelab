# Spec: issue-77-git-identity-env

- Tier: 1
- Status: spec
- Issue: #77

## Intent

devcontainer が空の `GIT_AUTHOR_*` / `GIT_COMMITTER_*` 環境変数をコンテナへ渡して Git identity を壊さないようにする。Git commit の identity は Git 本来の `git config user.name` / `user.email`、または利用者が明示した環境変数に任せる。

## Acceptance Criteria

1. `.devcontainer/devcontainer.json` の `remoteEnv` は `GIT_AUTHOR_NAME` / `GIT_AUTHOR_EMAIL` / `GIT_COMMITTER_NAME` / `GIT_COMMITTER_EMAIL` を定義しない。
2. `remoteEnv` は既存の `GH_CONFIG_DIR` 設定を維持する。
3. 空の Git identity 環境変数が devcontainer 設定から渡されないことを確認する regression test がある。

## Verification

- `python -m pytest tests/devcontainer/test_git_identity_env.py`
