# Spec: issue-64-vllm-recreate

## Intent

Stabilize vLLM updates on `llm01` by preventing old and new vLLM Pods from
starting on the same fixed RTX Pro 6000 GPU during Deployment rollouts.

The change also preserves the tool-call options that were manually tested on
the live vLLM Deployment.

## Tier

Tier 1: localized bugfix to one Kubernetes manifest template plus static tests.

## Acceptance Criteria

- [ ] AC1: The vLLM Deployment template uses `strategy.type: Recreate`.
- [ ] AC2: The vLLM Deployment template includes `--enable-auto-tool-choice`.
- [ ] AC3: The vLLM Deployment template includes `--tool-call-parser hermes`.
- [ ] AC4: Static tests cover AC1 through AC3 and API verification behavior.
- [ ] AC5: Targeted tests and lint for the changed files pass.
- [ ] AC6: The vLLM API verification task does not depend on tools installed inside the vLLM container image.

## Out Of Scope

- Open WebUI per-model max output token tuning.
- Changing vLLM model, GPU UUID, image tag, or GPU memory utilization.
- Changing live Kubernetes resources outside the Ansible-managed template.
