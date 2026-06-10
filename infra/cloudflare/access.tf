resource "cloudflare_zero_trust_access_service_token" "api_clients" {
  account_id = var.cloudflare_account_id
  name       = "${var.host_id}-api-clients"
}

resource "cloudflare_zero_trust_access_application" "open_webui" {
  account_id       = var.cloudflare_account_id
  name             = "${var.host_id}-open-webui"
  domain           = local.hostnames.open_webui
  type             = "self_hosted"
  session_duration = "24h"

  policies = [{
    name       = "${var.host_id}-open-webui-google"
    decision   = "allow"
    precedence = 1

    include = [{
      email = {
        email = var.allowed_email
      }
    }]
  }]
}

resource "cloudflare_zero_trust_access_application" "ssh" {
  account_id       = var.cloudflare_account_id
  name             = "${var.host_id}-ssh"
  domain           = local.hostnames.ssh
  type             = "ssh"
  session_duration = "24h"

  policies = [{
    name       = "${var.host_id}-ssh-google"
    decision   = "allow"
    precedence = 1

    include = [{
      email = {
        email = var.allowed_email
      }
    }]
  }]
}

resource "cloudflare_zero_trust_access_application" "vllm" {
  account_id       = var.cloudflare_account_id
  name             = "${var.host_id}-vllm"
  domain           = local.hostnames.vllm
  type             = "self_hosted"
  session_duration = "24h"

  policies = [{
    name       = "${var.host_id}-vllm-service-auth"
    decision   = "non_identity"
    precedence = 1

    include = [{
      service_token = {
        token_id = cloudflare_zero_trust_access_service_token.api_clients.id
      }
    }]
  }]
}

resource "cloudflare_zero_trust_access_application" "ollama" {
  account_id       = var.cloudflare_account_id
  name             = "${var.host_id}-ollama"
  domain           = local.hostnames.ollama
  type             = "self_hosted"
  session_duration = "24h"

  policies = [{
    name       = "${var.host_id}-ollama-service-auth"
    decision   = "non_identity"
    precedence = 1

    include = [{
      service_token = {
        token_id = cloudflare_zero_trust_access_service_token.api_clients.id
      }
    }]
  }]
}
