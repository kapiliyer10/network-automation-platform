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


def compare_network_instance_interfaces(
    device_name: str,
    network_instance_name: str,
    desired_interfaces: list[str],
    actual_interfaces: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Compare desired network-instance interface membership."""

    actual_names = {
        interface["name"]
        for interface in actual_interfaces
    }

    results = []

    for interface_name in desired_interfaces:
        status = (
            "PASS"
            if interface_name in actual_names
            else "DRIFT"
        )

        results.append(
            {
                "device": device_name,
                "network_instance": network_instance_name,
                "interface": interface_name,
                "status": status,
            }
        )

    return results
