#!/usr/bin/env bash
# Install Ansible + 1Password CLI if missing, then apply playbooks/07-tailscale.yml.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# --- Ansible ---
if ! command -v ansible-playbook &>/dev/null; then
  echo "[setup] Installing ansible-core via uv..."
  uv tool install ansible-core
fi

# --- 1Password CLI ---
if ! command -v op &>/dev/null; then
  echo "[setup] Installing 1Password CLI..."
  OP_VERSION="v2.30.0"
  ARCH="$(uname -m)"
  case "${ARCH}" in
    x86_64)  OP_ARCH="amd64" ;;
    aarch64) OP_ARCH="arm64" ;;
    *)       echo "ERROR: unsupported arch: ${ARCH}"; exit 1 ;;
  esac
  TMPDIR="$(mktemp -d)"
  curl -sSfL \
    "https://cache.agilebits.com/dist/1P/op2/pkg/${OP_VERSION}/op_linux_${OP_ARCH}_${OP_VERSION}.zip" \
    -o "${TMPDIR}/op.zip"
  unzip -qq "${TMPDIR}/op.zip" op -d "${TMPDIR}"
  sudo install -m 755 "${TMPDIR}/op" /usr/local/bin/op
  rm -rf "${TMPDIR}"
  echo "[setup] 1Password CLI installed: $(op --version)"
fi

# --- 1Password 認証確認 ---
if ! op account list &>/dev/null; then
  echo "ERROR: 1Password CLI が認証できません。"
  echo "Mac の 1Password デスクトップアプリが起動・アンロックされているか確認してください。"
  exit 1
fi

# --- Ansible collections ---
echo "[setup] Checking Ansible collections..."
ansible-galaxy collection install -r "${REPO_ROOT}/requirements.yml"

cd "${REPO_ROOT}"

# --- dry-run ---
echo ""
echo "=== dry-run (--check --diff) ==="
ansible-playbook playbooks/07-tailscale.yml --check --diff

# --- apply ---
echo ""
echo "=== applying ==="
ansible-playbook playbooks/07-tailscale.yml
