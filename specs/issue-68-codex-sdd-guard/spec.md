# Spec: issue-68-codex-sdd-guard

- Tier: 1
- Status: implement
- Issue: #68

## Intent

Codex の SDD PreToolUse guard が hook 実行時 cwd ではなく編集対象パスに基づいて worktree を判定し、linked worktree での source edit を正しく許可する。

## Acceptance Criteria

1. `codex-sdd-guard.sh` は `apply_patch` の絶対パスが linked worktree 配下を指す場合、primary checkout cwd から実行されても source edit として拒否しない。
2. `tool_input.workdir` がある場合、相対パスはその workdir を基準に repo/worktree root を解決する。
3. primary checkout 配下の source edit は引き続き拒否する。
4. `sed ... 2>/dev/null` のような読み取りコマンドを write と誤判定しない。
5. AGENTS.md に、作業中に新しい課題が出てきたら都度 issue 化する運用ルールが記載されている。

## Verification

- `cd vendor/ai-sdd-guide && uvx pytest tests/test_codex_sdd_guard.py`
- `git diff --submodule=log origin/main...HEAD`
