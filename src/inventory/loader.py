from pathlib import Path
from typing import Any

import yaml


class InventoryError(Exception):
    """Raised when the device inventory is invalid."""


def load_inventory(path: str | Path) -> dict[str, Any]:
    """Load and validate the device inventory YAML file."""
    inventory_path = Path(path)

    if not inventory_path.is_file():
        raise InventoryError(f"Inventory file not found: {inventory_path}")

    try:
        with inventory_path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        raise InventoryError(f"Invalid YAML: {exc}") from exc

    if not isinstance(data, dict):
        raise InventoryError("Inventory root must be a mapping.")

    devices = data.get("devices")
    if not isinstance(devices, dict) or not devices:
        raise InventoryError("'devices' must be a non-empty mapping.")

    required_fields = {"host", "platform", "role"}

    for name, device in devices.items():
        if not isinstance(device, dict):
            raise InventoryError(f"Device '{name}' must be a mapping.")

        missing = required_fields - device.keys()
        if missing:
            raise InventoryError(
                f"Device '{name}' is missing: {', '.join(sorted(missing))}"
            )

    return data