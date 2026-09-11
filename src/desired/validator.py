from typing import Any

from src.desired.comparator import compare_interfaces
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
