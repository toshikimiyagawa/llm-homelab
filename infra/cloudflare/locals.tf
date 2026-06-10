locals {
  vllm_origin_hostname = "vllm.${var.domain}"

  hostnames = {
    open_webui = "open-webui-${var.host_id}.${var.domain}"
    ollama     = "ollama-${var.host_id}.${var.domain}"
    vllm       = "vllm-${var.host_id}.${var.domain}"
    ssh        = "ssh-${var.host_id}.${var.domain}"
  }

  tunnel_services = {
    open_webui = var.open_webui_backend_url
    ollama     = var.ollama_backend_url
    vllm       = coalesce(var.vllm_backend_url, "https://${local.vllm_origin_hostname}")
    ssh        = var.ssh_backend_url
  }
}
