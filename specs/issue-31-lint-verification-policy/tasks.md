# Tasks: issue-31-lint-verification-policy

## Implementation Tasks
- [x] T1: `.yamllint` の ignore 設定を現行構成に合わせ、`dotfiles/.codex/.tmp/` を除外する。対応AC: AC2
- [x] T2: `.ansible-lint` の `exclude_paths` に `dotfiles/.codex/.tmp/` を追加する。対応AC: AC3
- [x] T3: `docs/repository-guidelines.md` に issue 検証時の lint 実行方針（変更ファイル単位 / repo-wide の使い分け）を追記する。対応AC: AC1, AC4

## Tests (AC mapping)
- [x] AC1 → docs に issue 検証時の lint 方針が記載される
- [x] AC2 → `yamllint -s .` 実行で `dotfiles/.codex/.tmp/` の line-length エラーが出ない
- [x] AC3 → `ansible-lint` 実行で `dotfiles/.codex/.tmp/` 配下を対象にしない
- [x] AC4 → 既存 role の lint 負債は別 issue 扱いであることが docs に明記される

## Definition of Done
- [x] AC1-AC4 が確認できる
- [x] verify フェーズで sdd-reviewer の確認を通過する
