from typing import Any

from src.network.docker_resolver import resolve_container_ip
from src.network.gnmi_client import GNMIClient


def get_device_state(
    device_name: str,
    inventory: dict[str, Any],
    username: str,
    password: str,
) -> dict[str, Any]:
    """Retrieve normalized operational state for one device using gNMI."""

    device = inventory["devices"][device_name]

    host = resolve_container_ip(device["container"])

    client = GNMIClient(
        host=host,
        port=57401,
        username=username,
        password=password,
    )

    return {
        "hostname": client.get_hostname(),
        "interfaces": client.get_interfaces(),
        "ip_addresses": client.get_ip_addresses(),
        "routes": client.get_routes(),
        "ospf_neighbors": client.get_all_ospf_neighbors(),
        "ospf": client.get_ospf_configuration(),
    }
