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

    return compare_interfaces(
        device_name=device_name,
        desired_interfaces=desired_interfaces,
        actual_interfaces=actual_interfaces,
    )
