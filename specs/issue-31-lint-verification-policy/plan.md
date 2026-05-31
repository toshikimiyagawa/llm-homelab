# Plan: issue-31-lint-verification-policy

## Approach

lint の「実行対象」と「期待する結果」を分離して定義する。
設定面では `yamllint` / `ansible-lint` の除外パスを現行 dotfiles 構成に合わせて更新し、
運用面では `docs/repository-guidelines.md` に issue 検証時の実行方針を追記する。

## Impacted Files

- `.yamllint` — `dotfiles/.codex/.tmp/` を除外
- `.ansible-lint` — `dotfiles/.codex/.tmp/` を除外
- `docs/repository-guidelines.md` — issue 検証時の lint 方針を明文化

## Alternatives and Tradeoffs

- 既存 lint 違反を一括解消する案:
  - 本来は別 issue で段階対応すべき範囲が広く、#31 では方針定義を優先する。
- CI を変更して完全に変更ファイル限定にする案:
  - 将来検討余地はあるが、まずはローカル/運用方針を明確化して足場を作る。

## Risks / Rollback

- 除外パス設定の誤りで必要なファイルまで lint されなくなるリスク。
- ロールバックは設定差分を戻すのみで可能。
