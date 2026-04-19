terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 4.0"
    }
  }
}

provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_ocid
}

data "oci_core_images" "ubuntu_images" {
  compartment_id = var.compartment_ocid
  operating_system = "Canonical Ubuntu"
  operating_system_version = "22.04"
}

resource "oci_core_virtual_network" "bot_vcn" {
  compartment_id = var.compartment_ocid
  display_name   = "bot-vcn"
  cidr_block     = "10.0.0.0/16"
}

resource "oci_core_subnet" "bot_subnet" {
  compartment_id      = var.compartment_ocid
  virtual_network_id  = oci_core_virtual_network.bot_vcn.id
  display_name        = "bot-subnet"
  cidr_block          = "10.0.1.0/24"
  dns_label           = "bot-subnet"
  prohibit_public_ip_on_vnic = false
}

resource "oci_core_internet_gateway" "bot_igw" {
  compartment_id   = var.compartment_ocid
  display_name     = "bot-igw"
  is_enabled       = true
  virtual_network_id = oci_core_virtual_network.bot_vcn.id
}

resource "oci_core_default_route_table" "bot_route_table" {
  compartment_id    = var.compartment_ocid
  vcn_id            = oci_core_virtual_network.bot_vcn.id
  route_rules {
    cidr_block = "0.0.0.0/0"
    network_entity_id = oci_core_internet_gateway.bot_igw.id
  }
}

resource "oci_core_default_security_list" "bot_sec_list" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_virtual_network.bot_vcn.id
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 22
      max = 22
    }
  }
  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 2375
      max = 2375
    }
  }
  egress_security_rules {
    protocol = "all"
    destination = "0.0.0.0/0"
  }
}

resource "oci_core_instance" "bot_vm" {
  compartment_id       = var.compartment_ocid
  availability_domain  = data.oci_identity_availability_domains.ads.availability_domains[0].name
  shape                = "VM.Standard.A1.Flex"
  shape_config {
    memory_in_gbs = 24
    ocpus         = 4
  }
  display_name = "bot-vm"

  create_vnic_details {
    subnet_id        = oci_core_subnet.bot_subnet.id
    assign_public_ip = true
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.ubuntu_images.images[0].id
  }

  metadata = {
    ssh_authorized_keys = file(var.ssh_public_key_path)
  }
}

output "instance_public_ip" {
  value = oci_core_instance.bot_vm.public_ip
}
