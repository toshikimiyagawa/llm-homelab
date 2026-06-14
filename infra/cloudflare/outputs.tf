output "tunnel_id" {
  description = "Cloudflare Tunnel ID."
  value       = cloudflare_zero_trust_tunnel_cloudflared.llm01.id
}

output "tunnel_token" {
  description = "Cloudflare Tunnel token for cloudflared on llm01. Treat as a secret."
  value       = data.cloudflare_zero_trust_tunnel_cloudflared_token.llm01.token
  sensitive   = true
}
