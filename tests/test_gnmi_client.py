import os
from pathlib import Path

import pytest

from src.inventory.loader import load_inventory
from src.network.docker_resolver import resolve_container_ip
from src.network.gnmi_client import GNMIClient, GNMIError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_FILE = PROJECT_ROOT / "configs" / "inventory" / "devices.yaml"


@pytest.mark.parametrize(
    "interface_name",
    [
        "ethernet-1/1",
        "ethernet-1/2",
    ],
)
def test_gnmi_get_interfaces_oper_state(interface_name):
    inventory = load_inventory(INVENTORY_FILE)

    r1 = inventory["devices"]["R1"]
    host = resolve_container_ip(r1["container"])

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]

    client = GNMIClient(
        host=host,
        port=57401,
        username=username,
        password=password,
    )

    oper_state = client.get_interface_oper_state(interface_name)

    assert oper_state == "up"


def test_gnmi_get_invalid_interface():
    inventory = load_inventory(INVENTORY_FILE)

    r1 = inventory["devices"]["R1"]
    host = resolve_container_ip(r1["container"])

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]

    client = GNMIClient(
        host=host,
        port=57401,
        username=username,
        password=password,
    )

    with pytest.raises(GNMIError):
        client.get_interface_oper_state("ethernet-1/99")