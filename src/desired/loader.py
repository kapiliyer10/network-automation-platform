from pathlib import Path
from typing import Any

import yaml

class DesiredStateError(Exception):
    """Raised when the desired-state configuration is invalid."""

def load_desired_state(path: str | Path) -> dict[str, Any]:
    """Load and validate the desired-state YAML file."""
    desired_state_path = Path(path)

    if not desired_state_path.is_file():
        raise DesiredStateError(f"Desired-state file not found: {desired_state_path}"
        )

    try:
        with desired_state_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

    except yaml.YAMLError as e:
            raise DesiredStateError(f"Error parsing desired-state YAML file: {e}")

    if not isinstance(data, dict):
        raise DesiredStateError("Desired-state root must be a mapping.")

    devices = data.get("devices")

    if not isinstance(devices, dict):
        raise DesiredStateError("Desired-state 'devices' must be a mapping.")

    for device_name, device_config in devices.items():
        if not isinstance(device_config, dict):
            raise DesiredStateError(
                f"Device '{device_name}' configuration must be a mapping."
                )

        interfaces = device_config.get("interfaces")

        if not isinstance(interfaces, dict):
            raise DesiredStateError(
                f"Device '{device_name}' must contain a non-empty "
                "'interfaces' mapping."
            )

        for interface_name, interface_config in interfaces.items():
            if not isinstance(interface_config, dict):
                raise DesiredStateError(
                    f"Interface '{interface_name}' configuration for device "
                    f"'{device_name}' must be a mapping."
                )

            if "admin_state" not in interface_config:
                raise DesiredStateError(
                    f"Interface '{interface_name}' for device '{device_name}' "
                    "must contain 'admin_state'."
                )

    return data
