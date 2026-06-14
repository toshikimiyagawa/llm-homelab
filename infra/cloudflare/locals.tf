locals {
  allowed_warp_emails      = distinct(concat([var.allowed_email], var.allowed_emails))
  allowed_warp_email_match = join(" ", [for email in local.allowed_warp_emails : jsonencode(email)])
}
