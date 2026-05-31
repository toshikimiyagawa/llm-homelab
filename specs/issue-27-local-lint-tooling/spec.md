# Spec: issue-27-local-lint-tooling

## Intent

ローカル環境で CI 相当の lint を事前実行できるようにするため、`pip`、`yamllint`、`ansible-lint` の導入経路と実行手順を明確にする。

## Acceptance Criteria

1. リポジトリの手順書に、`pip` / `yamllint` / `ansible-lint` の導入手順が記載されている。
2. devcontainer を利用する場合に `yamllint` / `ansible-lint` が自動導入される設定がある。
3. この作業環境で `yamllint -s .` と `ansible-lint` を実行した結果を確認できる。
