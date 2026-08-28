import os
from pathlib import Path

from src.inventory.loader import load_inventory
from src.network.docker_resolver import resolve_container_ip
from src.network.gnmi_client import GNMIClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_FILE = PROJECT_ROOT / "configs" / "inventory" / "devices.yaml"


def test_gnmi_get_interfaces():
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

    result = client.get(["interface"])

    assert "notification" in result
    assert result["notification"]