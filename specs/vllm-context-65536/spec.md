# Spec: vLLM 65,536 context window

## Intent

Raise the Qwen3.5-122B-A10B-NVFP4 vLLM context window from 32,768 to
65,536 tokens so Hermes Agent can initialize with its minimum 64K context
requirement.

The model, served model name, tool-calling flags, and `vllm_max_num_seqs` stay
unchanged.

## Acceptance Criteria

1. `roles/vllm/defaults/main.yml` sets `vllm_max_model_len: 65536`.
2. opencode devcontainer configuration advertises context limit `65536` for
   `qwen3.5-122b-a10b-nvfp4`.
3. Documentation describes the current vLLM backend context as 65K and notes
   the increase is based on observed KV cache headroom.
4. Existing vLLM and opencode tests pass with expectations updated to 65,536.
5. After applying to `llm01`, `/v1/models` reports `max_model_len: 65536` and
   the vLLM Deployment is Ready.
