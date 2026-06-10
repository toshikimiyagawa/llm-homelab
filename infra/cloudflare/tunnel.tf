resource "cloudflare_zero_trust_tunnel_cloudflared" "llm01" {
  account_id = var.cloudflare_account_id
  name       = var.host_id
  config_src = "cloudflare"
}

resource "cloudflare_zero_trust_tunnel_cloudflared_config" "llm01" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_zero_trust_tunnel_cloudflared.llm01.id

  config = {
    ingress = [
      {
        hostname = local.hostnames.open_webui
        service  = local.tunnel_services.open_webui
      },
      {
        hostname = local.hostnames.ollama
        service  = local.tunnel_services.ollama
      },
      {
        hostname = local.hostnames.vllm
        service  = local.tunnel_services.vllm
        origin_request = {
          origin_server_name = local.vllm_origin_hostname
        }
      },
      {
        hostname = local.hostnames.ssh
        service  = local.tunnel_services.ssh
      },
      {
        service = var.tunnel_catch_all_service
      }
    ]
  }
}
