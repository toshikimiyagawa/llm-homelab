# Qwen3.5-122B-A10B NVFP4 vLLM Migration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current Qwen3.6-35B-A3B vLLM backend with Qwen3.5-122B-A10B in 4bit NVFP4 form while preserving Hermes agent tool calling.

**Architecture:** Use the pre-quantized `RedHatAI/Qwen3.5-122B-A10B-NVFP4` checkpoint placed under `/opt/models`, expose it as `qwen3.5-122b-a10b-nvfp4`, and keep the current Qwen tool-calling flags. Start with conservative runtime limits (`max_model_len=32768`, `max_num_seqs=4`) to fit a single RTX Pro 6000 96GB before tuning upward.

**Tech Stack:** Ansible role templates, Kubernetes Deployment manifest, vLLM OpenAI-compatible server, Qwen3.5 NVFP4 checkpoint, pytest static tests, yamllint.

---

## File Structure

- `roles/vllm/defaults/main.yml`: model path/name, model dir, context and concurrency limits.
- `inventory/group_vars/all/vars.yml`: environment-level model path/name override.
- `roles/vllm/templates/vllm-deployment.yml.j2`: existing vLLM args; should retain tool calling and avoid explicit quantization args.
- `tests/vllm/test_role.py`: static vLLM role contract.
- `.devcontainer/project-tools.yml`: opencode default model config.
- `tests/opencode/test_devcontainer_config.py`: opencode static contract.
- `docs/software-stack.md`: current software stack and vLLM model notes.
- `docs/operations.md`: runtime curl/tool-call verification examples.

## Implementation Sequence

Follow `specs/qwen35-122b-nvfp4/tasks.md` exactly. Do not download model weights or apply the playbook until the code PR is merged and the model directory exists on `llm01`.

