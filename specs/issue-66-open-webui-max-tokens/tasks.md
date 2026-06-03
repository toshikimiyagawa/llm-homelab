# Tasks: issue-66-open-webui-max-tokens

## Implementation Tasks

- [x] T1: Open WebUI のデフォルト推論パラメータに `max_tokens` を追加する。対応AC: AC1, AC2
- [x] T2: Deployment テンプレートで `DEFAULT_MODEL_PARAMS` をコンテナ環境に渡す。対応AC: AC2
- [x] T3: `docs/software-stack.md` に Open WebUI の max_tokens 方針を追記する。対応AC: AC3
- [x] T4: `docs/operations.md` に長い会話時の失敗条件と回避策を追記する。対応AC: AC3
- [x] T5: `tests/open_webui/test_role.py` に回帰テストを追加する。対応AC: AC1-AC4

## Tests

- [x] AC1, AC2, AC4 -> `uvx pytest tests/open_webui/test_role.py -q`
- [x] AC3 -> `rg -n "DEFAULT_MODEL_PARAMS|max_tokens|vLLM|40960" docs/software-stack.md docs/operations.md`

## Verification Notes

- RED: `uvx pytest tests/open_webui/test_role.py -q` initially failed because `open_webui_default_model_params`, `DEFAULT_MODEL_PARAMS`, and doc references were absent.
- GREEN: `uvx pytest tests/open_webui/test_role.py -q` passed with `3 passed` after adding defaults, deployment env, and docs.
- `yamllint -s roles/open_webui/defaults/main.yml roles/open_webui/tasks/main.yml roles/open_webui/templates/open-webui-deployment.yml.j2` passed.
- Live `ansible-playbook playbooks/21-open-webui.yml --vault-password-file /home/ubuntu/.vault_pass --ssh-common-args='-o ControlPath=/tmp/ansible-ssh-%h-%p-%r'` completed with `ok=18 changed=1 failed=0` after switching the Deployment strategy to `Recreate`.
- Live deployment env includes `DEFAULT_MODEL_PARAMS={"max_tokens": 8192}`.

## Definition of Done

- [x] AC1-AC4 are verified
- [x] SDD traceability remains in the PR
