import json
import re
from pathlib import Path


ROOT = Path(__file__).parents[2]
PROJECT_TOOLS = ROOT / ".devcontainer" / "project-tools.yml"


def _opencode_config_script():
    content = PROJECT_TOOLS.read_text()
    match = re.search(
        r"- name: configure opencode for vLLM\n\s+run: \|\n(?P<script>(?:\s{6}.+\n)+)",
        content,
    )
    assert match is not None
    return "\n".join(line[6:] for line in match.group("script").splitlines())


def _opencode_config_json():
    script = _opencode_config_script()
    match = re.search(r"<<'EOF'\n(?P<json>.*)\n\s*EOF", script, re.DOTALL)
    assert match is not None
    return json.loads(match.group("json"))


def _opencode_install_step():
    content = PROJECT_TOOLS.read_text()
    match = re.search(
        r"- name: install opencode\n\s+run: (?P<cmd>.+)\n",
        content,
    )
    assert match is not None
    return match.group("cmd")


def test_opencode_binary_copied_from_actual_install_path():
    # The opencode installer places the binary in ~/.opencode/bin, not
    # ~/.local/bin. Copying from the wrong path fails with "No such file or
    # directory" and aborts post_install (set -euo pipefail).
    cmd = _opencode_install_step()
    assert ".opencode/bin/opencode" in cmd
    assert "/usr/local/bin/opencode" in cmd
    assert "~/.local/bin/opencode" not in cmd


def test_post_install_writes_global_opencode_config_path():
    script = _opencode_config_script()
    assert "mkdir -p /home/ubuntu/.config/opencode" in script
    assert "cat > /home/ubuntu/.config/opencode/opencode.json" in script
    assert "cat > /home/ubuntu/opencode.json" not in script


def test_opencode_config_uses_singular_provider_key():
    config = _opencode_config_json()
    assert "provider" in config
    assert "providers" not in config
    assert config["provider"]["vllm"]["npm"] == "@ai-sdk/openai-compatible"


def test_qwen_model_defines_context_and_output_limits():
    model = _opencode_config_json()["provider"]["vllm"]["models"]["qwen3-32b"]
    assert model["limit"] == {
        "context": 92736,
        "output": 8192,
    }


def test_vllm_api_key_is_dummy_not_secret():
    options = _opencode_config_json()["provider"]["vllm"]["options"]
    assert options["apiKey"] == "dummy"
