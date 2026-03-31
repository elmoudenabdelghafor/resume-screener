variable "tenancy_ocid" {
  description = "The OCID of your Oracle Cloud tenancy."
  type        = string
}

variable "user_ocid" {
  description = "The OCID of your Oracle Cloud user."
  type        = string
}

variable "api_fingerprint" {
  description = "The fingerprint for your API key."
  type        = string
}

variable "api_private_key_path" {
  description = "The path to the private key used for API authentication."
  type        = string
}

variable "region" {
  description = "The OCI region where resources will be created."
  type        = string
  default     = "us-ashburn-1"
}

variable "compartment_ocid" {
  description = "The OCID of the compartment to deploy the resources in."
  type        = string
}

variable "ssh_public_key" {
  description = "The public key to allow SSH access to the compute instance."
  type        = string
}

variable "availability_domain" {
  description = "The availability domain to deploy the compute instance."
  type        = number
  default     = 0
}
