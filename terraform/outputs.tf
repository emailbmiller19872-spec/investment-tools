output "instance_public_ip" {
  description = "Public IP address for the deployed bot VM"
  value       = oci_core_instance.bot_vm.public_ip
}
