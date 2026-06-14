"""
Static configuration tests for the vllm Ansible role.

Runtime acceptance criteria are verified by running the playbook against llm01.
These tests keep rollout and OpenAI-compatible server options checkable without
a live Kubernetes cluster.
"""
import re
from pathlib import Path


REPO_ROOT = Path(__file__).parents[2]
ROLE_ROOT = REPO_ROOT / "roles" / "vllm"
DEPLOYMENT_TMPL = ROLE_ROOT / "templates" / "vllm-deployment.yml.j2"
DEFAULTS = ROLE_ROOT / "defaults" / "main.yml"
TASKS = ROLE_ROOT / "tasks" / "main.yml"
GROUP_VARS = REPO_ROOT / "inventory" / "group_vars" / "all" / "vars.yml"
SOFTWARE_STACK_DOC = REPO_ROOT / "docs" / "software-stack.md"
OPERATIONS_DOC = REPO_ROOT / "docs" / "operations.md"


def test_deployment_uses_recreate_strategy_for_fixed_gpu():
    content = DEPLOYMENT_TMPL.read_text()
    assert "strategy:" in content
    assert "type: Recreate" in content


def test_deployment_enables_tool_call_options():
    content = DEPLOYMENT_TMPL.read_text()
    assert '"--enable-auto-tool-choice"' in content
    assert '"--reasoning-parser"' in content
    assert '"qwen3"' in content
    assert '"--default-chat-template-kwargs"' in content
    assert "enable_thinking" in content
    assert "false" in content
    assert '"--tool-call-parser"' in content
    assert '"qwen3_coder"' in content
    assert '"hermes"' not in content


def test_deployment_sets_max_model_len():
    content = DEPLOYMENT_TMPL.read_text()
    assert '"--max-model-len"' in content
    assert "vllm_max_model_len" in content


def test_deployment_caps_max_num_seqs_for_mamba_cache():
    # Qwen3.6-35B-A3B uses Gated DeltaNet (Mamba) blocks; max_num_seqs must not
    # exceed available Mamba cache blocks or CUDA graph capture fails at startup.
    content = DEPLOYMENT_TMPL.read_text()
    assert '"--max-num-seqs"' in content
    assert "vllm_max_num_seqs" in content


def test_default_max_num_seqs_within_mamba_block_limit():
    content = DEFAULTS.read_text()
    match = re.search(r"^vllm_max_num_seqs:\s*(\d+)", content, re.MULTILINE)
    assert match, "vllm_max_num_seqs must be set in defaults"
    assert int(match.group(1)) <= 754


def test_group_vars_serves_qwen36():
    content = GROUP_VARS.read_text()
    assert "vllm_model: /models/Qwen3.6-35B-A3B" in content
    assert "vllm_served_model_name: qwen3.6-35b-a3b" in content


def test_default_model_dir_is_qwen36():
    content = DEFAULTS.read_text()
    assert "vllm_model_dir: Qwen3.6-35B-A3B" in content


def test_default_max_model_len_without_yarn():
    content = DEFAULTS.read_text()
    # YaRN RoPE scaling is dropped: Qwen3.6-35B-A3B has a 262K native context.
    assert "yarn" not in content
    assert "vllm_rope_scaling_dict" not in content
    match = re.search(r"^vllm_max_model_len:\s*(\d+)", content, re.MULTILINE)
    assert match, "vllm_max_model_len must be set in defaults"
    assert int(match.group(1)) > 92736


def test_tasks_do_not_modify_model_config_for_yarn():
    content = TASKS.read_text()
    assert "YaRN RoPE" not in content
    assert "vllm_rope_scaling_dict" not in content
    assert "slurp" not in content


def test_deployment_is_text_only_no_multimodal_flags():
    content = DEPLOYMENT_TMPL.read_text()
    assert "--limit-mm-per-prompt" not in content
    assert "--allowed-local-media-path" not in content


def test_software_stack_doc_reflects_qwen36():
    content = SOFTWARE_STACK_DOC.read_text()
    assert "Qwen3.6-35B-A3B" in content
    assert "Qwen/Qwen3-30B-A3B" not in content


def test_operations_doc_curl_example_uses_qwen36():
    content = OPERATIONS_DOC.read_text()
    assert '"model":"qwen3.6-35b-a3b"' in content
    assert "qwen3-32b" not in content


def test_api_verification_uses_service_endpoint_not_pod_tools():
    content = TASKS.read_text()
    assert "curl -fsS" in content
    assert "get service vllm" in content
    assert "kubectl -n {{ vllm_namespace }} exec" not in content
    assert "-- wget" not in content
