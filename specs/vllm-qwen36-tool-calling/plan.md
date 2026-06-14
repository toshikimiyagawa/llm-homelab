# vLLM Qwen3.6 Tool Calling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Ansible-managed vLLM Qwen3.6 server expose reliable OpenAI-compatible automatic tool calling for Hermes agent.

**Architecture:** Keep the existing vLLM Deployment shape and only change the tool/reasoning parser flags. Qwen3.6 remains the served model; `--enable-auto-tool-choice` stays enabled, `--reasoning-parser qwen3` is added, and `--tool-call-parser` moves from `hermes` to `qwen3_coder`.

**Tech Stack:** Ansible role templates, Kubernetes Deployment manifest, vLLM OpenAI-compatible server, pytest static tests, yamllint.

---

Follow `specs/vllm-qwen36-tool-calling/tasks.md` exactly. Runtime rollout is done after PR merge with `ansible-playbook playbooks/09-vllm.yml --tags vllm`.

