output "tunnel_id" {
  description = "Cloudflare Tunnel ID."
  value       = cloudflare_zero_trust_tunnel_cloudflared.llm01.id
}

output "hostnames" {
  description = "Public hostnames managed by Terraform."
  value       = local.hostnames
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
