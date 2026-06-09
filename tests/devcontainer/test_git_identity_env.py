import json
from pathlib import Path


ROOT = Path(__file__).parents[2]
DEVCONTAINER = ROOT / ".devcontainer" / "devcontainer.json"
GIT_IDENTITY_ENV = {
    "GIT_AUTHOR_NAME",
    "GIT_AUTHOR_EMAIL",
    "GIT_COMMITTER_NAME",
    "GIT_COMMITTER_EMAIL",
}


def _devcontainer_config():
    return json.loads(DEVCONTAINER.read_text())


def test_remote_env_keeps_gh_config_dir():
    remote_env = _devcontainer_config()["remoteEnv"]

    assert remote_env["GH_CONFIG_DIR"] == "/home/ubuntu/.gh-config"


def test_remote_env_does_not_forward_git_identity_env():
    remote_env = _devcontainer_config()["remoteEnv"]

    assert GIT_IDENTITY_ENV.isdisjoint(remote_env)
