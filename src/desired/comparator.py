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


def compare_ospf_configuration(
    device_name: str,
    desired_ospf: dict[str, Any],
    actual_ospf: dict[str, Any],
) -> list[dict[str, Any]]:
    """Compare desired OSPF configuration with actual OSPF state."""

    results = []

    desired_instance = desired_ospf["instance"]

    if not actual_ospf:
        return [
            {
                "device": device_name,
                "field": "ospf",
                "desired": "present",
                "actual": "missing",
                "status": "DRIFT",
            }
        ]

    actual_instance = actual_ospf

    for field in ("name", "admin_state", "version", "router_id"):
        results.append(
            {
                "device": device_name,
                "field": f"ospf.instance.{field}",
                "desired": desired_instance[field],
                "actual": actual_instance[field],
                "status": (
                    "PASS"
                    if desired_instance[field] == actual_instance[field]
                    else "DRIFT"
                ),
            }
        )

    for area_name, desired_area in desired_instance["areas"].items():
        actual_area = actual_instance["areas"].get(area_name)

        if actual_area is None:
            results.append(
                {
                    "device": device_name,
                    "field": f"ospf.area.{area_name}",
                    "desired": "present",
                    "actual": "missing",
                    "status": "DRIFT",
                }
            )
            continue

        actual_interfaces = {
            interface["name"]: interface
            for interface in actual_area["interfaces"]
        }

        for interface_name, desired_interface in (
            desired_area["interfaces"].items()
        ):
            actual_interface = actual_interfaces.get(interface_name)

            if actual_interface is None:
                results.append(
                    {
                        "device": device_name,
                        "field": (
                            f"ospf.area.{area_name}."
                            f"interface.{interface_name}"
                        ),
                        "desired": "present",
                        "actual": "missing",
                        "status": "DRIFT",
                    }
                )
                continue

            for field, desired_value in desired_interface.items():
                actual_value = actual_interface.get(field)

                results.append(
                    {
                        "device": device_name,
                        "field": (
                            f"ospf.area.{area_name}."
                            f"interface.{interface_name}.{field}"
                        ),
                        "desired": desired_value,
                        "actual": actual_value,
                        "status": (
                            "PASS"
                            if desired_value == actual_value
                            else "DRIFT"
                        ),
                    }
                )

    return results
