variable "tenancy_ocid" {
  type        = string
  description = "OCI tenancy OCID"
}

variable "user_ocid" {
  type        = string
  description = "OCI user OCID"
}

variable "fingerprint" {
  type        = string
  description = "OCI API key fingerprint"
}

variable "private_key_path" {
  type        = string
  description = "Path to OCI private key file"
}

variable "ssh_public_key_path" {
  type        = string
  description = "Path to SSH public key used for VM access"
}

variable "compartment_ocid" {
  type        = string
  description = "OCI compartment OCID"
}

variable "region" {
  type        = string
  description = "OCI region"
}
