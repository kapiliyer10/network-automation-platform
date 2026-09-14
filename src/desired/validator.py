from typing import Any

from src.desired.comparator import (
    compare_interfaces,
    compare_network_instance_interfaces,
    compare_ospf_configuration,
)
from src.network.docker_resolver import resolve_container_ip
from src.network.gnmi_client import GNMIClient


def validate_device_interfaces(
    device_name: str,
    inventory: dict[str, Any],
    desired_state: dict[str, Any],
    username: str,
    password: str,
) -> list[dict[str, Any]]:
    """Compare a device's desired interface state with its actual state."""

    device = inventory["devices"][device_name]

    host = resolve_container_ip(device["container"])

    client = GNMIClient(
        host=host,
        port=57401,
        username=username,
        password=password,
    )

    desired_interfaces = desired_state["devices"][device_name]["interfaces"]

    actual_interfaces = client.get_interfaces()

    actual_by_name = {
        interface["name"]: interface
        for interface in actual_interfaces
    }

    for interface_name in desired_interfaces:
        actual_interface = actual_by_name.get(interface_name)

        if actual_interface is not None:
            actual_interface["ipv4"] = client.get_interface_ipv4(
                interface_name
            )

    return compare_interfaces(
        device_name=device_name,
        desired_interfaces=desired_interfaces,
        actual_interfaces=actual_interfaces,
    )


def validate_device_network_instances(
    device_name: str,
    inventory: dict[str, Any],
    desired_state: dict[str, Any],
    username: str,
    password: str,
) -> list[dict[str, str]]:
    """Compare desired network-instance membership with actual state."""

    device = inventory["devices"][device_name]

    desired_network_instances = desired_state["devices"][device_name].get(
        "network_instances", {}
    )

    if not desired_network_instances:
        return []

    host = resolve_container_ip(device["container"])

    client = GNMIClient(
        host=host,
        port=57401,
        username=username,
        password=password,
    )

    results = []

    for network_instance_name, network_instance in (
        desired_network_instances.items()
    ):
        desired_interfaces = network_instance["interfaces"]

        actual_interfaces = client.get_network_instance_interfaces(
            network_instance_name
        )

        results.extend(
            compare_network_instance_interfaces(
                device_name=device_name,
                network_instance_name=network_instance_name,
                desired_interfaces=desired_interfaces,
                actual_interfaces=actual_interfaces,
            )
        )

    return results


def validate_device_ospf(
    device_name: str,
    inventory: dict[str, Any],
    desired_state: dict[str, Any],
    username: str,
    password: str,
) -> list[dict[str, Any]]:
    """Compare desired OSPF configuration with actual state."""

    device = inventory["devices"][device_name]

    desired_ospf = desired_state["devices"][device_name].get("ospf")

    if not desired_ospf:
        return []

    host = resolve_container_ip(device["container"])

    client = GNMIClient(
        host=host,
        port=57401,
        username=username,
        password=password,
    )

    actual_ospf = client.get_ospf_configuration()

    return compare_ospf_configuration(
        device_name=device_name,
        desired_ospf=desired_ospf,
        actual_ospf=actual_ospf,
    )
