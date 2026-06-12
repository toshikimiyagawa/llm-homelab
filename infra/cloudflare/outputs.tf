output "tunnel_id" {
  description = "Cloudflare Tunnel ID."
  value       = cloudflare_zero_trust_tunnel_cloudflared.llm01.id
}

output "tunnel_token" {
  description = "Cloudflare Tunnel token for cloudflared on llm01. Treat as a secret."
  value       = data.cloudflare_zero_trust_tunnel_cloudflared_token.llm01.token
  sensitive   = true
}

output "hostnames" {
  description = "Public hostnames managed by Terraform."
  value       = local.hostnames
}

output "ssh_ca_public_key" {
  description = "Cloudflare Access short-lived SSH certificate CA public key for the SSH application."
  value       = cloudflare_zero_trust_access_short_lived_certificate.ssh.public_key
}

output "service_token_client_id" {
  description = "Cloudflare Access Service Token client ID for API clients."
  value       = cloudflare_zero_trust_access_service_token.api_clients.client_id
}

output "service_token_client_secret" {
  description = "Cloudflare Access Service Token client secret. Treat as a secret."
  value       = cloudflare_zero_trust_access_service_token.api_clients.client_secret
  sensitive   = true
}
