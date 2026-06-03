# Spec: issue-48-sdd-pr47-cleanup

## Intent

PR #47 で #45 と vLLM 変更が混在した結果、main に残らなかった SDD traceability を復旧し、同じ混入を防ぐ運用を明文化する。

## Scope

### Include

- #45 の `spec.md` / `tasks.md` を main に追補する。
- `.sdd/tasks.json` に #45 と #48 の完了履歴を残す。
- `docs/repository-guidelines.md` に worktree 分離と commit 対象確認の運用を追記する。
- PR #47 に混在した vLLM 変更の扱いを issue / comment として記録する。

### Exclude

- PR #47 に含まれた vLLM 変更の revert。
- vLLM の追加実装・再検証。
- #45 の runtime code 変更。

## Acceptance Criteria

1. #45 の SDD artifacts が `specs/issue-45-prometheus-data-ownership/` に存在し、#45 の acceptance criteria と検証結果が追跡できる。
2. `.sdd/tasks.json` に #45 と #48 の完了履歴が存在する。
3. repository guidelines に、feature ごとの worktree 分離、stage 前の `git status` / `git diff --name-status` 確認、無関係変更を PR に混ぜない方針が明記されている。
4. PR #47 に混在した vLLM 変更の扱いが GitHub 上で追跡できる。
