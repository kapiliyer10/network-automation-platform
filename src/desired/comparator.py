from typing import Any

def compare_interfaces(
        device_name: str,
        desired_interfaces: dict[str, dict[str, Any]],
        actual_interfaces: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Compare desired interface state with actual interface state."""

    actual_by_name = {
        interface["name"]: interface
        for interface in actual_interfaces
    }

    results = []

    for interface_name, desired in desired_interfaces.items():
        actual = actual_by_name.get(interface_name)

        if actual is None:
            results.append(
                {
                    "device": device_name,
                    "interface": interface_name,
                    "field": "interface",
                    "desired": "present",
                    "actual": "missing",
                    "status": "DRIFT",
                }
            )
            continue

        for field, desired_value in desired.items():
            actual_value = actual.get(field)

            status = (
                "PASS" if desired_value == actual_value
                else "DRIFT"
            )

            results.append(
                {
                    "device": device_name,
                    "interface": interface_name,
                    "field": field,
                    "desired": desired_value,
                    "actual": actual_value,
                    "status": status,
                }
            )

    return results
