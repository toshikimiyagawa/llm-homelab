# Spec: issue-31-lint-verification-policy

## Intent

issue 単位の検証で既存 lint 負債に引きずられないように、lint 実行ポリシーを明文化し、
運用上ノイズとなる対象（`dotfiles/.codex/.tmp` など）を除外して検証可能性を上げる。

## Acceptance Criteria

1. issue 検証時の lint 実行方針（変更ファイル単位 / repo-wide の使い分け）が文書化されている。
2. `yamllint -s .` 実行時に `dotfiles/.codex/.tmp/` 配下が検査対象から除外される。
3. `ansible-lint` 設定でも `dotfiles/.codex/.tmp/` 配下が除外される。
4. 既存 lint 違反（role 側の既存負債）をこの issue で修正しないことが明記されている。
