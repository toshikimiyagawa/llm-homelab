# Multiple WARP Enrollment Identities Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow multiple exact email identities to enroll in Cloudflare WARP for `llm01`.

**Architecture:** Keep `allowed_email` for backward compatibility and add `allowed_emails` for additional identities. Terraform computes one normalized email list and reuses it for the Access policy and WARP device profile expression.

**Tech Stack:** Terraform `cloudflare/cloudflare` provider `~> 5.19`, pytest static contract tests, local ignored `terraform.tfvars`.

---

Follow `specs/issue-128-warp-multiple-identities/tasks.md` exactly. Do not commit real user emails; set them only in local `infra/cloudflare/terraform.tfvars`.

