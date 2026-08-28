from pathlib import Path

from src.inventory.loader import load_inventory


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_FILE = PROJECT_ROOT / "configs" / "inventory" / "devices.yaml"


def test_inventory_loads():
    inventory = load_inventory(INVENTORY_FILE)

    assert "devices" in inventory
    assert set(inventory["devices"]) == {"R1", "R2", "R3"}


def test_inventory_contains_required_fields():
    inventory = load_inventory(INVENTORY_FILE)

    for device in inventory["devices"].values():
        assert device["container"]
        assert device["platform"] == "srlinux"
        assert device["role"] == "router"