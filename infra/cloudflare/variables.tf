variable "cloudflare_account_id" {
  description = "Cloudflare account ID that owns the Zero Trust resources."
  type        = string
}

variable "cloudflare_zone_id" {
  description = "Cloudflare zone ID for domain."
  type        = string
}

variable "domain" {
  description = "Base DNS zone, for example solvelio.com."
  type        = string
}

variable "host_id" {
  description = "Host identifier used in public hostnames."
  type        = string
  default     = "llm01"
}

variable "allowed_email" {
  description = "Google account email allowed to access browser applications."
  type        = string
}

variable "allowed_emails" {
  description = "Additional exact email identities allowed to enroll WARP devices."
  type        = list(string)
  default     = []
}

variable "access_team_name" {
  description = "Cloudflare Zero Trust team name."
  type        = string
}

variable "warp_private_network_cidr" {
  description = "Cloudflare WARP private network CIDR routed to llm01 through the Cloudflare Tunnel."
  type        = string
}

variable "open_webui_backend_url" {
  description = "Origin URL for Open WebUI through the tunnel."
  type        = string
  default     = "http://localhost:8080"
}

variable "ollama_backend_url" {
  description = "Origin URL for Ollama through the tunnel."
  type        = string
  default     = "http://localhost:11434"
}

variable "vllm_backend_url" {
  description = "Origin URL for vLLM through Traefik."
  type        = string
  default     = null
}

variable "ssh_backend_url" {
  description = "Origin URL for Browser SSH through the tunnel."
  type        = string
  default     = "ssh://localhost:22"
}

variable "tunnel_catch_all_service" {
  description = "Final catch-all tunnel service."
  type        = string
  default     = "http_status:404"
}
