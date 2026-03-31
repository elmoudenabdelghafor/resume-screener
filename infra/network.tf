resource "oci_core_vcn" "k3s_vcn" {
  compartment_id = var.compartment_ocid
  cidr_block     = "10.0.0.0/16"
  display_name   = "k3s-vcn"
  dns_label      = "k3svcn"
}

resource "oci_core_internet_gateway" "k3s_ig" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.k3s_vcn.id
  display_name   = "k3s-ig"
  enabled        = true
}

resource "oci_core_default_route_table" "k3s_rt" {
  manage_default_resource_id = oci_core_vcn.k3s_vcn.default_route_table_id

  route_rules {
    network_entity_id = oci_core_internet_gateway.k3s_ig.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
  }
}

resource "oci_core_subnet" "k3s_subnet" {
  compartment_id    = var.compartment_ocid
  vcn_id            = oci_core_vcn.k3s_vcn.id
  cidr_block        = "10.0.1.0/24"
  display_name      = "k3s-subnet"
  dns_label         = "k3ssubnet"
  route_table_id    = oci_core_vcn.k3s_vcn.default_route_table_id
  security_list_ids = [oci_core_vcn.k3s_vcn.default_security_list_id, oci_core_security_list.k3s_sec_list.id]
}
