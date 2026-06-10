locals {
  tunnel_cname_target = "${cloudflare_zero_trust_tunnel_cloudflared.llm01.id}.cfargotunnel.com"
}

resource "cloudflare_dns_record" "tunnel" {
  for_each = local.hostnames

  zone_id = var.cloudflare_zone_id
  name    = each.value
  type    = "CNAME"
  content = local.tunnel_cname_target
  proxied = true
  ttl     = 1
}
