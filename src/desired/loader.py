import ipaddress
from pathlib import Path
from typing import Any

import yaml

class DesiredStateError(Exception):
    """Raised when the desired-state configuration is invalid."""



def _validate_routing_policies(routing_policies: Any) -> set[str]:
    """Validate shared BGP prefix sets and routing policies."""

    if not isinstance(routing_policies, dict):
        raise DesiredStateError("'routing_policies' must be a mapping.")

    prefix_sets = routing_policies.get("prefix_sets")
    policies = routing_policies.get("policies")

    if not isinstance(prefix_sets, dict) or not prefix_sets:
        raise DesiredStateError(
            "'routing_policies.prefix_sets' must be a non-empty mapping."
        )

    if not isinstance(policies, dict) or not policies:
        raise DesiredStateError(
            "'routing_policies.policies' must be a non-empty mapping."
        )

    for name, prefix_set in prefix_sets.items():
        if not isinstance(prefix_set, dict):
            raise DesiredStateError(f"Prefix set '{name}' must be a mapping.")

        prefixes = prefix_set.get("prefixes")
        if not isinstance(prefixes, list) or not prefixes:
            raise DesiredStateError(
                f"Prefix set '{name}' must contain a non-empty prefixes list."
            )

        for entry in prefixes:
            if not isinstance(entry, dict):
                raise DesiredStateError(
                    f"Entries in prefix set '{name}' must be mappings."
                )

            prefix = entry.get("prefix")
            try:
                ipaddress.ip_network(prefix, strict=True)
            except (ValueError, TypeError):
                raise DesiredStateError(
                    f"Invalid network prefix '{prefix}' in prefix set '{name}'."
                )

            if entry.get("mask_length_range") != "exact":
                raise DesiredStateError(
                    f"Prefix '{prefix}' in '{name}' must use "
                    "'mask_length_range: exact'."
                )

    for policy_name, policy in policies.items():
        if not isinstance(policy, dict):
            raise DesiredStateError(
                f"Routing policy '{policy_name}' must be a mapping."
            )

        if policy.get("default_action") not in {"accept", "reject"}:
            raise DesiredStateError(
                f"Routing policy '{policy_name}' must have "
                "default_action 'accept' or 'reject'."
            )

        statements = policy.get("statements")
        if not isinstance(statements, list) or not statements:
            raise DesiredStateError(
                f"Routing policy '{policy_name}' must contain statements."
            )

        sequences = set()

        for statement in statements:
            if not isinstance(statement, dict):
                raise DesiredStateError(
                    f"Statements in policy '{policy_name}' must be mappings."
                )

            sequence = statement.get("sequence")
            if (
                not isinstance(sequence, int)
                or isinstance(sequence, bool)
                or sequence <= 0
                or sequence in sequences
            ):
                raise DesiredStateError(
                    f"Policy '{policy_name}' has an invalid or duplicate "
                    f"statement sequence: {sequence}."
                )
            sequences.add(sequence)

            match = statement.get("match")
            if not isinstance(match, dict):
                raise DesiredStateError(
                    f"Statement {sequence} in '{policy_name}' "
                    "must contain a match mapping."
                )

            prefix_set_name = match.get("prefix_set")
            if prefix_set_name not in prefix_sets:
                raise DesiredStateError(
                    f"Statement {sequence} in '{policy_name}' references "
                    f"unknown prefix set '{prefix_set_name}'."
                )

            if match.get("match_set_options") not in {"any", "all"}:
                raise DesiredStateError(
                    f"Statement {sequence} in '{policy_name}' must specify "
                    "'match_set_options' as 'any' or 'all'."
                )

            if statement.get("action") not in {"accept", "reject"}:
                raise DesiredStateError(
                    f"Statement {sequence} in '{policy_name}' must have "
                    "action 'accept' or 'reject'."
                )

    return set(policies)


def _validate_bgp_configuration(
    device_name: str,
    bgp: Any,
    available_policies: set[str],
) -> None:
    """Validate a device's BGP desired-state configuration."""

    if not isinstance(bgp, dict):
        raise DesiredStateError(
            f"BGP configuration for device '{device_name}' must be a mapping."
        )

    required_fields = (
        "autonomous_system",
        "router_id",
        "afi_safi",
        "peer_groups",
        "neighbors",
        "import_policy",
        "export_policy",
    )

    for field in required_fields:
        if field not in bgp:
            raise DesiredStateError(
                f"BGP configuration for '{device_name}' is missing '{field}'."
            )

    asn = bgp["autonomous_system"]
    if (
        not isinstance(asn, int)
        or isinstance(asn, bool)
        or not 1 <= asn <= 4294967295
    ):
        raise DesiredStateError(
            f"BGP autonomous_system for '{device_name}' must be "
            "an integer between 1 and 4294967295."
        )

    try:
        router_id = ipaddress.ip_address(bgp["router_id"])
        if router_id.version != 4:
            raise ValueError("BGP router ID must be IPv4.")
    except (ValueError, TypeError):
        raise DesiredStateError(
            f"BGP router_id for '{device_name}' must be a valid IPv4 address."
        )

    afi_safi = bgp["afi_safi"]
    if not isinstance(afi_safi, dict):
        raise DesiredStateError(
            f"BGP afi_safi for '{device_name}' must be a mapping."
        )

    ipv4_unicast = afi_safi.get("ipv4_unicast")
    if (
        not isinstance(ipv4_unicast, dict)
        or ipv4_unicast.get("admin_state") not in {"enable", "disable"}
    ):
        raise DesiredStateError(
            f"BGP IPv4 unicast configuration for '{device_name}' "
            "must specify admin_state as 'enable' or 'disable'."
        )

    peer_groups = bgp["peer_groups"]
    if not isinstance(peer_groups, dict) or not peer_groups:
        raise DesiredStateError(
            f"BGP peer_groups for '{device_name}' must be a non-empty mapping."
        )

    for group_name, group in peer_groups.items():
        if not isinstance(group, dict):
            raise DesiredStateError(
                f"BGP peer group '{group_name}' on '{device_name}' "
                "must be a mapping."
            )

        peer_as = group.get("peer_as")
        if (
            not isinstance(peer_as, int)
            or isinstance(peer_as, bool)
            or not 1 <= peer_as <= 4294967295
        ):
            raise DesiredStateError(
                f"BGP peer group '{group_name}' on '{device_name}' "
                "must have a valid peer_as."
            )

    neighbors = bgp["neighbors"]
    if not isinstance(neighbors, dict) or not neighbors:
        raise DesiredStateError(
            f"BGP neighbors for '{device_name}' must be a non-empty mapping."
        )

    for address, neighbor in neighbors.items():
        try:
            neighbor_ip = ipaddress.ip_address(address)
            if neighbor_ip.version != 4:
                raise ValueError("BGP neighbor address must be IPv4.")
        except (ValueError, TypeError):
            raise DesiredStateError(
                f"Invalid BGP neighbor address '{address}' on '{device_name}'."
            )

        if not isinstance(neighbor, dict):
            raise DesiredStateError(
                f"BGP neighbor '{address}' on '{device_name}' must be a mapping."
            )

        group_name = neighbor.get("peer_group")
        if group_name not in peer_groups:
            raise DesiredStateError(
                f"BGP neighbor '{address}' on '{device_name}' "
                f"references unknown peer group '{group_name}'."
            )

    for policy_field in ("import_policy", "export_policy"):
        policy_name = bgp[policy_field]
        if policy_name not in available_policies:
            raise DesiredStateError(
                f"BGP {policy_field} '{policy_name}' on '{device_name}' "
                "does not reference a defined routing policy."
            )


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

            ipv4 = interface_config.get("ipv4")

            if ipv4 is not None:
                if not isinstance(ipv4, dict):
                    raise DesiredStateError(
                        f"IPv4 configuration for interface '{interface_name}' "
                        f"on '{device_name}' must be a mapping."
                    )

                if "admin_state" not in ipv4:
                    raise DesiredStateError(
                        f"IPv4 configuration for interface '{interface_name}' "
                        f"on '{device_name}' is missing 'admin_state'."
                    )

                if "address" not in ipv4:
                    raise DesiredStateError(
                        f"IPv4 configuration for interface '{interface_name}' "
                        f"on '{device_name}' is missing 'address'."
                    )

        ospf = device_config.get("ospf")

        if ospf is not None:
            if not isinstance(ospf, dict):
                raise DesiredStateError(
                    f"OSPF configuration for device '{device_name}' "
                    "must be a mapping."
                )

            instance = ospf.get("instance")

            if not isinstance(instance, dict):
                raise DesiredStateError(
                    f"OSPF instance configuration for device '{device_name}' "
                    "must be a mapping."
                )

            required_fields = [
                "name",
                "admin_state",
                "version",
                "router_id",
                "areas",
            ]

            for field in required_fields:
                if field not in instance:
                    raise DesiredStateError(
                        f"OSPF instance for device '{device_name}' "
                        f"is missing '{field}'."
                    )

            if not isinstance(instance["areas"], dict) or not instance["areas"]:
                raise DesiredStateError(
                    f"OSPF instance for device '{device_name}' "
                    "must contain a non-empty 'areas' mapping."
                )

    bgp_devices = {
        name: device.get("bgp")
        for name, device in devices.items()
        if "bgp" in device
    }

    if bgp_devices:
        available_policies = _validate_routing_policies(
            data.get("routing_policies")
        )

        for device_name, bgp in bgp_devices.items():
            _validate_bgp_configuration(
                device_name=device_name,
                bgp=bgp,
                available_policies=available_policies,
            )

    return data
