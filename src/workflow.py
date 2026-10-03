from typing import Any

from src.config.netconf_applier import apply_device_netconf_config
from src.desired.validator import (
    validate_device_interfaces_netconf,
    validate_device_network_instances_netconf,
    validate_device_ospf_netconf,
    validate_device_interfaces,
    validate_device_network_instances,
    validate_device_ospf,
)
from src.network.docker_resolver import resolve_container_ip
from src.network.netconf_client import NETCONFClient


def configure_and_validate_device_netconf(
    device_name: str,
    inventory: dict[str, Any],
    desired_state: dict[str, Any],
    username: str,
    password: str,
) -> list[dict[str, Any]]:
    """Apply a device's desired state with NETCONF and verify it."""

    device = inventory["devices"][device_name]
    desired_device = desired_state["devices"][device_name]

    host = resolve_container_ip(device["container"])

    client = NETCONFClient(
        host=host,
        port=830,
        username=username,
        password=password,
    )

    apply_device_netconf_config(
        client=client,
        desired_interfaces=desired_device["interfaces"],
        desired_network_instances=desired_device.get(
            "network_instances",
            {},
        ),
        desired_ospf=desired_device.get("ospf"),
    )

    interface_results = validate_device_interfaces_netconf(
        device_name=device_name,
        inventory=inventory,
        desired_state=desired_state,
        username=username,
        password=password,
    )

    network_instance_results = validate_device_network_instances_netconf(
        device_name=device_name,
        inventory=inventory,
        desired_state=desired_state,
        username=username,
        password=password,
    )

    ospf_results = validate_device_ospf_netconf(
        device_name=device_name,
        inventory=inventory,
        desired_state=desired_state,
        username=username,
        password=password,
    )

    return (
        interface_results
        + network_instance_results
        + ospf_results
    )


def configure_and_validate_all_devices_netconf(
    inventory: dict[str, Any],
    desired_state: dict[str, Any],
    username: str,
    password: str,
) -> dict[str, list[dict[str, Any]]]:
    """Apply and validate NETCONF configuration for all devices."""

    results = {}

    for device_name in inventory["devices"]:
        results[device_name] = configure_and_validate_device_netconf(
            device_name=device_name,
            inventory=inventory,
            desired_state=desired_state,
            username=username,
            password=password,
        )

    return results


def validate_device(
    device_name: str,
    inventory: dict[str, Any],
    desired_state: dict[str, Any],
    username: str,
    password: str,
) -> list[dict[str, Any]]:
    """Validate one device against its desired state."""

    interface_results = validate_device_interfaces(
        device_name=device_name,
        inventory=inventory,
        desired_state=desired_state,
        username=username,
        password=password,
    )

    network_instance_results = validate_device_network_instances(
        device_name=device_name,
        inventory=inventory,
        desired_state=desired_state,
        username=username,
        password=password,
    )

    ospf_results = validate_device_ospf(
        device_name=device_name,
        inventory=inventory,
        desired_state=desired_state,
        username=username,
        password=password,
    )

    return (
        interface_results
        + network_instance_results
        + ospf_results
    )


def validate_all_devices(
    inventory: dict[str, Any],
    desired_state: dict[str, Any],
    username: str,
    password: str,
) -> dict[str, list[dict[str, Any]]]:
    """Validate all devices against their desired state."""

    results = {}

    for device_name in inventory["devices"]:
        results[device_name] = validate_device(
            device_name=device_name,
            inventory=inventory,
            desired_state=desired_state,
            username=username,
            password=password,
        )

    return results
