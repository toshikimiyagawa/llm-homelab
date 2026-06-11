import json
from pathlib import Path


ROOT = Path(__file__).parents[2]
DEVCONTAINER = ROOT / ".devcontainer" / "devcontainer.json"


def _remote_env():
    return json.loads(DEVCONTAINER.read_text())["remoteEnv"]


def test_remote_env_sets_claude_config_dir():
    # Point Claude Code's config dir at the persisted ~/.claude symlink so that
    # ~/.claude.json (oauth/onboarding/trust state) survives container rebuilds
    # instead of landing in the ephemeral $HOME. See issue #111.
    assert _remote_env()["CLAUDE_CONFIG_DIR"] == "/home/ubuntu/.claude"


def test_remote_env_keeps_gh_config_dir():
    assert _remote_env()["GH_CONFIG_DIR"] == "/home/ubuntu/.gh-config"
