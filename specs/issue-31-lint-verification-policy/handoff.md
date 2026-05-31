# Handoff: issue-31-lint-verification-policy

## Context

- Tier: 1
- Goal: issue 検証時の lint 運用を明確化し、`dotfiles/.codex/.tmp/` 由来ノイズを除外する

## Must Implement (from tasks.md)

1. `.yamllint` で `dotfiles/.codex/.tmp/` を除外
2. `.ansible-lint` で `dotfiles/.codex/.tmp/` を除外
3. `docs/repository-guidelines.md` に lint 方針（変更ファイル単位 / repo-wide）と既存負債の扱いを記載

## Constraints

- 既存 role の lint 負債（`container` / `gpu_plugin` / `preflight`）はこの issue で修正しない
- 変更は lint 設定と運用ドキュメントに限定する
