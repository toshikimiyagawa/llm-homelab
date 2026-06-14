resource "cloudflare_zero_trust_access_policy" "warp_enrollment" {
  account_id = var.cloudflare_account_id
  name       = "${var.host_id}-warp-enrollment"
  decision   = "allow"

  include = [{
    email = {
      email = var.allowed_email
    }
  }]
}

resource "cloudflare_zero_trust_access_application" "warp_enrollment" {
  account_id = var.cloudflare_account_id
  name       = "${var.host_id}-warp-enrollment"
  type       = "warp"

  policies = [{
    id         = cloudflare_zero_trust_access_policy.warp_enrollment.id
    precedence = 1
  }]
}

resource "cloudflare_zero_trust_device_custom_profile" "llm01_warp" {
  account_id        = var.cloudflare_account_id
  name              = "${var.host_id}-warp-private-network"
  description       = "Route ${var.host_id} private network traffic through Cloudflare WARP."
  enabled           = true
  precedence        = 1
  match             = "identity.email == \"${var.allowed_email}\""
  allow_mode_switch = false
  allowed_to_leave  = false

  service_mode_v2 = {
    mode = "warp"
  }

  include = [{
    address     = var.warp_private_network_cidr
    description = "${var.host_id} private network"
  }]
}
