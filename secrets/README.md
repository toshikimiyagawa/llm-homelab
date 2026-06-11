# Secrets

This directory stores SOPS-encrypted project secrets.

## Key Material

- Commit `*.sops.yml` encrypted files only.
- Never commit `keys.txt`, `*.plain.yml`, `*.decrypted.yml`, or temporary decrypted files.
- The age private key lives at `~/.config/sops/age/keys.txt`.
- 1Password may store a backup item named `llm-homelab age private key` in the `LLM Server Infrastructure` vault.
- 1Password is only a recovery location for the age private key; normal Ansible runs use the local age key directly.
- SOPS / age CLI binaries are installed by `.devcontainer/project-tools.yml`; the age private key remains user-managed at `~/.config/sops/age/keys.txt` and must not be committed to the repository. age private key は repository に commit しない。

## In-repo Secrets

- `secrets/infra.sops.yml` is the SOPS-encrypted bundle for project secrets consumed by Ansible playbooks.
- Edit it with `sops secrets/infra.sops.yml`.
- Do not commit plaintext secret files or decrypted temporary outputs.
- The Tailscale auth key and Grafana admin password both live here.

## Editing

```bash
sops secrets/infra.sops.yml
```

## Ansible

Playbooks load encrypted variables with `community.sops.load_vars`; do not decrypt to a plaintext vars file.
Do not add Ansible Vault files under `inventory/`; inventory loading must not require
a vault password file.

## Temporary Cloudflare Tokens

Broad Cloudflare tokens used for one-time Tunnel or Access setup must be passed through environment variables and revoked after use. Do not store them in SOPS, Ansible Vault, or the repository.
