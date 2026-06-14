resource "cloudflare_zero_trust_tunnel_cloudflared" "llm01" {
  account_id = var.cloudflare_account_id
  name       = var.host_id
  config_src = "cloudflare"
}

data "cloudflare_zero_trust_tunnel_cloudflared_token" "llm01" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.llm01.id
}

resource "cloudflare_zero_trust_tunnel_cloudflared_route" "llm01_lan" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.llm01.id
  network    = var.warp_private_network_cidr
  comment    = "${var.host_id} LAN via WARP"
}
