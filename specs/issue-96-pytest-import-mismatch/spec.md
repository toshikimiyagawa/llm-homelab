# Spec: issue-96 - pytest import mismatch を解消する

## Tier

Tier 1.

## Intent

`uvx pytest -q` の全体実行が、複数ディレクトリにある `test_role.py` の top-level module 名衝突で collection error になる問題を解消する。

この issue では pytest 全体実行の import mismatch 解消に絞る。CI に pytest job を追加する作業は #71 に残す。

## Design

`tests/` と role 別 test directory を Python package 化し、pytest が各 `test_role.py` を別 module として import できるようにする。

ファイル名 rename は行わない。既存の targeted pytest コマンドや過去 spec の参照を壊さず、最小差分で collection 問題を解消するため。

## Acceptance Criteria

1. **AC-1**: `uvx pytest -q` が import mismatch で collection error にならない。
2. **AC-2**: 既存の role test file 名 `test_role.py` は変更しない。
3. **AC-3**: `tests/` と該当 role test directory が package 化され、同名 test module が衝突しない。
4. **AC-4**: targeted pytest 例として `uvx pytest tests/cloudflared/test_role.py tests/ollama/test_role.py -q` が通る。

## Verification

- `uvx pytest -q`
- `uvx pytest tests/cloudflared/test_role.py tests/ollama/test_role.py -q`
- `git diff --check`

## Scope

In scope:

- `tests/**/__init__.py` の追加。
- #96 の spec と SDD state 更新。

Out of scope:

- CI workflow に pytest を追加すること（#71）。
- test file rename。
- 既存 test assertion の挙動変更。
