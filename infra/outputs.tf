output "k3s_node_public_ip" {
  description = "The public IP address of the K3s node."
  value       = oci_core_instance.k3s_node.public_ip
}
