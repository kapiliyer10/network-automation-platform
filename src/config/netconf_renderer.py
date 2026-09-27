from typing import Any

from src.network.netconf_client import NETCONFClient


class NETCONFConfigError(Exception):
    """Raised when NETCONF configuration generation fails."""


def build_device_netconf_configs(
    client: NETCONFClient,
    desired_interfaces: dict[str, dict[str, Any]],
    desired_network_instances: dict[str, dict[str, Any]],
    desired_ospf: dict[str, Any] | None,
) -> list[str]:
    """Build NETCONF edit-config payloads from desired device state."""

    configs = []

    for interface_name, interface in desired_interfaces.items():
        ipv4 = interface.get("ipv4", {})

        configs.append(
            client.build_interface_edit_config(
                interface_name=interface_name,
                admin_state=interface["admin_state"],
                ipv4_admin_state=ipv4.get("admin_state"),
                ipv4_address=ipv4.get("address"),
            )
        )

    for network_instance_name, network_instance in (
        desired_network_instances.items()
    ):
        for interface_name in network_instance.get("interfaces", []):
            configs.append(
                client.build_network_instance_interface_edit_config(
                    network_instance_name=network_instance_name,
                    interface_name=interface_name,
                )
            )

    if desired_ospf:
        instance = desired_ospf["instance"]

        configs.append(
            client.build_ospf_instance_edit_config(
                network_instance_name="default",
                ospf_instance_name=instance["name"],
                admin_state=instance["admin_state"],
                version=(
                    "srl_nokia-ospf-types:" + instance["version"]
                    if ":" not in instance["version"]
                    else instance["version"]
                ),
                router_id=instance["router_id"],
            )
        )

        for area_id, area in instance["areas"].items():
            for interface_name, interface in (
                area["interfaces"].items()
            ):
                configs.append(
                    client.build_ospf_area_interface_edit_config(
                        network_instance_name="default",
                        ospf_instance_name=instance["name"],
                        area_id=area_id,
                        interface_name=interface_name,
                        passive=interface.get("passive", False),
                    )
                )

    return configs
