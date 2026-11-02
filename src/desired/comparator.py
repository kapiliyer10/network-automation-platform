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

def compare_bgp_configuration(
    device_name: str,
    desired_bgp: dict[str, Any],
    actual_bgp: dict[str, Any],
) -> list[dict[str, Any]]:
    """Compare desired BGP configuration with actual BGP state."""

    if not actual_bgp:
        return [{
            "device": device_name,
            "field": "bgp",
            "desired": "present",
            "actual": "missing",
            "status": "DRIFT",
        }]

    results = []

    fields = (
        "autonomous_system",
        "router_id",
        "afi_safi",
        "peer_groups",
        "neighbors",
    )

    for field in fields:
        desired_value = desired_bgp.get(field, {})
        actual_value = actual_bgp.get(field, {})

        results.append({
            "device": device_name,
            "field": f"bgp.{field}",
            "desired": desired_value,
            "actual": actual_value,
            "status": (
                "PASS"
                if desired_value == actual_value
                else "DRIFT"
            ),
        })

    # Desired-state YAML uses a string for a single policy.
    # NETCONF returns a list because these are YANG leaf-lists.
    for field in ("import_policy", "export_policy"):
        desired_value = desired_bgp.get(field, [])

        if isinstance(desired_value, str):
            desired_value = [desired_value]

        actual_value = actual_bgp.get(field, [])

        results.append({
            "device": device_name,
            "field": f"bgp.{field}",
            "desired": desired_value,
            "actual": actual_value,
            "status": (
                "PASS"
                if desired_value == actual_value
                else "DRIFT"
            ),
        })

    return results


def _normalize_prefix_sets(prefix_sets: dict[str, Any]) -> dict:
    """Normalize prefix-set contents so ordering does not affect comparison."""

    normalized = {}

    for name, prefix_set in prefix_sets.items():
        prefixes = [
            (
                entry["prefix"],
                entry["mask_length_range"],
            )
            for entry in prefix_set.get("prefixes", [])
        ]

        normalized[name] = sorted(prefixes)

    return normalized


def _normalize_policies(policies: dict[str, Any]) -> dict:
    """Normalize policy statements for order-independent comparison."""

    normalized = {}

    for name, policy in policies.items():
        statements = []

        for statement in policy.get("statements", []):
            match = statement.get("match", {})

            statements.append((
                str(statement["sequence"]),
                match.get("prefix_set"),
                match.get("match_set_options", "any"),
                statement.get("action"),
            ))

        normalized[name] = {
            "default_action": policy.get("default_action"),
            "statements": sorted(
                statements,
                key=lambda statement: statement[0],
            ),
        }

    return normalized


def compare_routing_policy_configuration(
    device_name: str,
    desired_routing_policies: dict[str, Any],
    actual_routing_policies: dict[str, Any],
) -> list[dict[str, Any]]:
    """Compare desired routing policies with actual router state."""

    if not actual_routing_policies:
        return [{
            "device": device_name,
            "field": "routing_policy",
            "desired": "present",
            "actual": "missing",
            "status": "DRIFT",
        }]

    desired_prefix_sets = _normalize_prefix_sets(
        desired_routing_policies.get("prefix_sets", {})
    )

    actual_prefix_sets = _normalize_prefix_sets(
        actual_routing_policies.get("prefix_sets", {})
    )

    desired_policies = _normalize_policies(
        desired_routing_policies.get("policies", {})
    )

    actual_policies = _normalize_policies(
        actual_routing_policies.get("policies", {})
    )

    results = []

    for field, desired_value, actual_value in (
        (
            "routing_policy.prefix_sets",
            desired_prefix_sets,
            actual_prefix_sets,
        ),
        (
            "routing_policy.policies",
            desired_policies,
            actual_policies,
        ),
    ):
        results.append({
            "device": device_name,
            "field": field,
            "desired": desired_value,
            "actual": actual_value,
            "status": (
                "PASS"
                if desired_value == actual_value
                else "DRIFT"
            ),
        })

    return results
