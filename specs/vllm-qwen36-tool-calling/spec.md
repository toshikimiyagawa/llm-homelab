# Spec: vLLM Qwen3.6 tool calling for Hermes agent

**Status**: frozen
**Tier**: 1
**Created**: 2026-06-14

## 目的

Hermes agent が vLLM の Qwen3.6 backend に対して検索などの tool call を自動発火できるよう、vLLM の tool calling 起動オプションを Qwen3.6 向けに合わせる。

現状の Deployment は `--enable-auto-tool-choice` と `--tool-call-parser hermes` を含むが、Qwen3.5/Qwen3.6 の vLLM recipe では tool calling に `--tool-call-parser qwen3_coder` が案内されている。また Qwen3.6 は reasoning model なので、tool call と reasoning を分離するため `--reasoning-parser qwen3` を明示する。

## スコープ

### 含む

- `roles/vllm/templates/vllm-deployment.yml.j2` の vLLM 起動 args を更新する。
- `--enable-auto-tool-choice` は維持する。
- `--reasoning-parser qwen3` を追加する。
- `--tool-call-parser` を `qwen3_coder` に変更する。
- static tests と docs を更新する。

### 含まない

- Hermes agent 側の設定変更。
- vLLM image tag の固定・変更。
- model / max context / max num seqs / GPU 設定の変更。
- 外部 chat template file の追加。

## 受け入れ基準

1. vLLM Deployment args に `--enable-auto-tool-choice` が残る。
2. vLLM Deployment args に `--reasoning-parser` と `qwen3` が含まれる。
3. vLLM Deployment args に `--tool-call-parser` と `qwen3_coder` が含まれ、`hermes` parser は使わない。
4. docs が Hermes agent / Qwen3.6 tool calling 用の起動オプションを説明する。
5. `uvx pytest tests/vllm/test_role.py -q` が pass する。
6. `yamllint roles/vllm/ docs/software-stack.md docs/operations.md` が pass する。

## テスト方針

- `tests/vllm/test_role.py`
  - auto tool choice を維持すること。
  - reasoning parser `qwen3` を含むこと。
  - tool parser `qwen3_coder` を含むこと。
  - `hermes` parser を含まないこと。
- lint
  - `yamllint roles/vllm/ docs/software-stack.md docs/operations.md`

