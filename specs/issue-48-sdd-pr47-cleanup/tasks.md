# Tasks: issue-48-sdd-pr47-cleanup

## Implementation Tasks
- [x] T1: #45 の SDD artifacts を `specs/issue-45-prometheus-data-ownership/` に追加する。対応AC: AC1
- [x] T2: `.sdd/tasks.json` に #45 と #48 の完了履歴を追加する。対応AC: AC2
- [x] T3: `docs/repository-guidelines.md` に worktree 分離と commit 対象確認の運用を追記する。対応AC: AC3
- [x] T4: PR #47 に混在した vLLM 変更の扱いを GitHub issue/comment として記録する。対応AC: AC4

## Tests
- [x] AC1 → `test -f specs/issue-45-prometheus-data-ownership/spec.md && test -f specs/issue-45-prometheus-data-ownership/tasks.md`
- [x] AC2 → `jq -e '.[] | select(.id == "issue-45-prometheus-data-ownership" and .status == "completed")' .sdd/tasks.json` と #48 の同等確認が通る
- [x] AC3 → `rg -n "worktree|git status|git diff --name-status|無関係変更" docs/repository-guidelines.md` で追記内容が確認できる
- [x] AC4 → GitHub 上の追跡コメントまたは issue が存在する

## Definition of Done
- [x] AC1-AC4 が確認できる
- [x] JSON は `jq` で妥当性を確認する
- [x] sdd-reviewer 相当の確認を通過する
