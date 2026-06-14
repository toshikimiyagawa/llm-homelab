# Disable Qwen3.6 Thinking for vLLM Tool Calls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Qwen3.6 reliably emit OpenAI-compatible tool calls for Hermes agent by disabling thinking in the vLLM chat template defaults.

**Architecture:** Keep the existing Qwen3.6 tool parser configuration and add one vLLM serve arg: `--default-chat-template-kwargs '{"enable_thinking": false}'`. This makes the behavior observed in the successful runtime smoke test the server default.

**Tech Stack:** Ansible role templates, Kubernetes Deployment manifest, vLLM OpenAI-compatible server, pytest static tests, yamllint.

---

Follow `specs/vllm-disable-thinking-for-tools/tasks.md` exactly. Runtime rollout is required after merge because the static tests only verify rendered args.

