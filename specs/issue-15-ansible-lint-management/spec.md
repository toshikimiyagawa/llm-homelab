# Spec: issue-15-ansible-lint-management

## Intent

`ansible-lint` の既存違反は今回の初期設定更新とは分離し、CI の必須ゲートは `yamllint` を維持する。
同時に、`ansible-lint` の結果は CI 上で可視化し、別タスクで段階的に解消できる状態にする。

## Acceptance Criteria

1. `yamllint` はこれまで通り PR で fail-fast な必須チェックとして動作する。
2. `ansible-lint` は PR で実行されるが、既存違反では PR を fail させない。
3. `ansible-lint` の実行結果は CI ログ上で確認できる。
4. 既存 role の `var-naming` / `no-handler` を今回の変更で修正しない。
