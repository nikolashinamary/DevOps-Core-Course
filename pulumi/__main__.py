import pulumi
import pulumi_yandex as yandex

cfg = pulumi.Config("yandex")
app = pulumi.Config("app")

cloud_id = cfg.require("cloudId")
folder_id = cfg.require("folderId")
token = cfg.require_secret("token")

zone = app.get("zone") or "ru-central1-a"
vm_name = app.get("vmName") or "pulumi-vm"
network_name = app.get("networkName") or "pulumi-network"
subnet_name = app.get("subnetName") or "pulumi-subnet"
subnet_cidr = app.get("subnetCidr") or "192.168.20.0/24"
image_id = app.get("imageId") or "fd865v46cboopthn7u0k"
ssh_username = app.get("sshUsername") or "ubuntu"
ssh_public_key = app.require("sshPublicKey")
ssh_allowed_cidr = app.get("sshAllowedCidr") or "0.0.0.0/0"

# Free-tier oriented defaults for this lab.
cores = app.get_int("cores") or 2
memory_gb = app.get_int("memoryGb") or 1
core_fraction = app.get_int("coreFraction") or 20
disk_size_gb = app.get_int("diskSizeGb") or 10
preemptible = app.get_bool("preemptible")
if preemptible is None:
    preemptible = True

provider = yandex.Provider(
    "yandex-provider",
    cloud_id=cloud_id,
    folder_id=folder_id,
    token=token,
    zone=zone,
)

network = yandex.VpcNetwork(
    "network",
    name=network_name,
    opts=pulumi.ResourceOptions(provider=provider),
)

subnet = yandex.VpcSubnet(
    "subnet",
    name=subnet_name,
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=[subnet_cidr],
    opts=pulumi.ResourceOptions(provider=provider),
)

security_group = yandex.VpcSecurityGroup(
    "vm-security-group",
    name=f"{vm_name}-sg",
    network_id=network.id,
    ingresses=[
        yandex.VpcSecurityGroupIngressArgs(
            description="SSH",
            protocol="TCP",
            port=22,
            v4_cidr_blocks=[ssh_allowed_cidr],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="HTTP",
            protocol="TCP",
            port=80,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
        yandex.VpcSecurityGroupIngressArgs(
            description="App port",
            protocol="TCP",
            port=5000,
            v4_cidr_blocks=["0.0.0.0/0"],
        ),
    ],
    egresses=[
        yandex.VpcSecurityGroupEgressArgs(
            description="Allow all egress",
            protocol="ANY",
            from_port=0,
            to_port=65535,
            v4_cidr_blocks=["0.0.0.0/0"],
        )
    ],
    opts=pulumi.ResourceOptions(provider=provider),
)

boot_disk = yandex.ComputeDisk(
    "boot-disk",
    name=f"{vm_name}-boot-disk",
    zone=zone,
    size=disk_size_gb,
    type="network-hdd",
    image_id=image_id,
    opts=pulumi.ResourceOptions(provider=provider),
)

vm = yandex.ComputeInstance(
    "vm",
    name=vm_name,
    zone=zone,
    platform_id="standard-v1",
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=cores,
        memory=memory_gb,
        core_fraction=core_fraction,
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        disk_id=boot_disk.id,
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,
            security_group_ids=[security_group.id],
        )
    ],
    scheduling_policy=yandex.ComputeInstanceSchedulingPolicyArgs(preemptible=preemptible),
    metadata={"ssh-keys": f"{ssh_username}:{ssh_public_key}"},
    opts=pulumi.ResourceOptions(provider=provider),
)


def first_interface_ip(interfaces):
    if not interfaces:
        return None
    iface = interfaces[0]
    # Provider returns nested maps/objects depending on SDK/runtime serialization.
    return iface.get("nat_ip_address") if isinstance(iface, dict) else iface.nat_ip_address


def first_interface_private_ip(interfaces):
    if not interfaces:
        return None
    iface = interfaces[0]
    return iface.get("ip_address") if isinstance(iface, dict) else iface.ip_address


pulumi.export("externalIp", vm.network_interfaces.apply(first_interface_ip))
pulumi.export("internalIp", vm.network_interfaces.apply(first_interface_private_ip))
pulumi.export("sshCommand", pulumi.Output.concat("ssh ", ssh_username, "@", vm.network_interfaces.apply(first_interface_ip)))
