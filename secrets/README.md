# Secrets

This directory stores SOPS-encrypted project secrets.

## Key Material

- Commit `*.sops.yml` encrypted files only.
- Never commit `keys.txt`, `*.plain.yml`, `*.decrypted.yml`, or temporary decrypted files.
- The age private key lives at `~/.config/sops/age/keys.txt`.
- 1Password may store a backup item named `llm-homelab age private key` in the `LLM Server Infrastructure` vault.
- 1Password is only a recovery location for the age private key; normal Ansible runs use the local age key directly.

## Editing

```bash
sops secrets/infra.sops.yml
```

## Ansible

Playbooks load encrypted variables with `community.sops.load_vars`; do not decrypt to a plaintext vars file.

## Temporary Cloudflare Tokens

Broad Cloudflare tokens used for one-time Tunnel or Access setup must be passed through environment variables and revoked after use. Do not store them in SOPS, Ansible Vault, or the repository.
