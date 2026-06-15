# Spec: Qwen3.5-122B-A10B NVFP4 vLLM migration

**Status**: frozen
**Tier**: 2
**Created**: 2026-06-15

## 目的

`llm01` のメイン vLLM モデルを `Qwen3.6-35B-A3B` から `Qwen3.5-122B-A10B` の 4bit 量子化 checkpoint へ変更する。

RTX Pro 6000 Blackwell 96GB での単一 GPU 運用を前提に、4bit checkpoint は vLLM / llm-compressor docs に掲載されている `RedHatAI/Qwen3.5-122B-A10B-NVFP4` を採用する。既存の Hermes agent / OpenAI-compatible tool calling の知見を維持し、検索 tool call が出るよう `qwen3_coder` parser と `enable_thinking=false` を継続する。

## スコープ

### 含む

- vLLM の model path / served model name / docs / tests を `Qwen3.5-122B-A10B-NVFP4` に変更する。
- 4bit 量子化 checkpoint として NVFP4 を使う。
- `--enable-auto-tool-choice`、`--reasoning-parser qwen3`、`--tool-call-parser qwen3_coder`、`--default-chat-template-kwargs '{"enable_thinking": false}'` を維持する。
- pre-quantized checkpoint を使うため、vLLM 起動 arg に `--quantization moe_wna16` 等を追加しない。
- `vllm_max_model_len` は初期値 `32768` に下げる。
- `vllm_max_num_seqs` は初期値 `4` に下げる。
- opencode の model / context limit を追従する。
- docs に NVFP4、保守的な初期 context、tool calling 設定を明記する。
- static tests と lint を更新する。
- 実機では model directory の存在を確認し、なければモデル取得が必要であることを STOP 条件として扱う。

### 含まない

- モデルウェイトの自動ダウンロード Ansible 化。
- vLLM image tag の固定。
- マルチモーダル入力の有効化。
- tensor parallel / multi GPU 化。
- `qwen3_xml` や custom chat template の導入。必要なら tool calling 実機検証後の follow-up とする。

## 設計

モデルは local path `/models/Qwen3.5-122B-A10B-NVFP4` として vLLM container に渡す。host 側では `/opt/models/Qwen3.5-122B-A10B-NVFP4` に配置する。served model name は `qwen3.5-122b-a10b-nvfp4` とする。

NVFP4 は pre-quantized checkpoint であるため、vLLM 起動時に追加の quantization arg は付けない。Qwen 公式 GPTQ-Int4 discussion でも Int4 quants に `--quantization moe_wna16` を付けると失敗すると報告されており、pre-quantized weights の metadata に任せる。

Qwen3.5/Qwen3.6 は Gated Delta Networks 系 MoE のため、Qwen3.6 で得た知見を引き継ぐ。tool calling は vLLM Qwen3.5/Qwen3.6 recipe の `--enable-auto-tool-choice --tool-call-parser qwen3_coder` を採用し、reasoning parser は `qwen3`、Hermes agent 向けには `enable_thinking=false` を既定にする。

122B 4bit は 35B より大きく、初回起動は VRAM / KV cache / CUDA graph capture の余裕を見て保守的に始める。`max_model_len=32768`、`max_num_seqs=4` を初期値とし、実機で余裕が確認できた場合だけ後続 PR で引き上げる。

## 受け入れ基準

1. `inventory/group_vars/all/vars.yml` と `roles/vllm/defaults/main.yml` が `/models/Qwen3.5-122B-A10B-NVFP4` と `qwen3.5-122b-a10b-nvfp4` を使う。
2. `roles/vllm/defaults/main.yml` の `vllm_model_dir` が `Qwen3.5-122B-A10B-NVFP4` である。
3. `vllm_max_model_len` が `32768`、`vllm_max_num_seqs` が `4` である。
4. Deployment は `--enable-auto-tool-choice`、`--reasoning-parser qwen3`、`--default-chat-template-kwargs '{"enable_thinking": false}'`、`--tool-call-parser qwen3_coder` を維持する。
5. Deployment に `--quantization`、`moe_wna16`、`--limit-mm-per-prompt`、`--allowed-local-media-path` を追加しない。
6. docs は Qwen3.5-122B-A10B-NVFP4、NVFP4 4bit、保守的な初期 context、tool calling 設定を説明する。
7. opencode config は `vllm/qwen3.5-122b-a10b-nvfp4` を既定 model とし、context limit は `32768`、output は `8192` のままにする。
8. `uvx pytest tests/vllm/test_role.py tests/opencode/test_devcontainer_config.py -q` が pass する。
9. `uvx pytest -q` が pass する。
10. `yamllint roles/vllm/ inventory/group_vars/all/vars.yml docs/software-stack.md docs/operations.md .devcontainer/project-tools.yml` が pass する。
11. 実機 apply 前に `/opt/models/Qwen3.5-122B-A10B-NVFP4` が存在する。存在しない場合は apply せず、人間にモデル取得を依頼する。
12. 実機 apply 後、vLLM Pod が Running/Ready になり、`/v1/models` が `qwen3.5-122b-a10b-nvfp4` を返す。
13. 実機 apply 後、tool choice smoke request が `finish_reason=tool_calls` と `web_search` tool call を返す。

## リスク / ロールバック

- **VRAM不足**: 122B 4bit でも KV cache と CUDA graph capture で不足する可能性がある。初期値を `32768` / `4` に下げ、失敗した場合はさらに context / seqs を下げるか Qwen3.6 に戻す。
- **vLLM image compatibility**: `latest` が NVFP4 checkpoint に対応している必要がある。Pod 起動ログで未対応が出た場合は STOP し、image tag 固定または別 checkpoint 選定を後続 issue にする。
- **tool calling 安定性**: Qwen3.5 122B では community reports に `qwen3_xml` / custom chat template の議論がある。まず公式 recipe の `qwen3_coder` と Qwen3.6 実測済み設定を採用し、Hermes agent 実機検証で問題が残る場合だけ follow-up で parser/template を変更する。
- **モデル未配置**: この spec はモデル download 自動化を含まない。未配置なら apply しない。

## 参考

- vLLM Qwen3.5/Qwen3.6 recipe
- vLLM llm-compressor Qwen3.5 quantized checkpoints
- Qwen3.5-122B-A10B Hugging Face model card
- Qwen3.5-122B-A10B-GPTQ-Int4 discussion about not using `--quantization moe_wna16`

