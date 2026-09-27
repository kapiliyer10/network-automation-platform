import os
from pathlib import Path

from dotenv import load_dotenv

from src.config.netconf_applier import apply_device_netconf_config
from src.desired.loader import load_desired_state
from src.desired.validator import (
    validate_device_interfaces_netconf,
    validate_device_network_instances_netconf,
    validate_device_ospf_netconf,
)
from src.inventory.loader import load_inventory
from src.network.docker_resolver import resolve_container_ip
from src.network.netconf_client import NETCONFClient


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INVENTORY_FILE = (
    PROJECT_ROOT / "configs" / "inventory" / "devices.yaml"
)

DESIRED_STATE_FILE = (
    PROJECT_ROOT / "configs" / "desired" / "desired_state.yaml"
)

load_dotenv(PROJECT_ROOT / ".env")


def test_apply_device_netconf_config_round_trip():
    inventory = load_inventory(INVENTORY_FILE)
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    device_name = "R1"
    device = desired_state["devices"][device_name]

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]

    # Safety check: R1 must already match the desired state.
    before_interfaces = validate_device_interfaces_netconf(
        device_name=device_name,
        inventory=inventory,
        desired_state=desired_state,
        username=username,
        password=password,
    )

    before_network_instances = validate_device_network_instances_netconf(
        device_name=device_name,
        inventory=inventory,
        desired_state=desired_state,
        username=username,
        password=password,
    )

    before_ospf = validate_device_ospf_netconf(
        device_name=device_name,
        inventory=inventory,
        desired_state=desired_state,
        username=username,
        password=password,
    )

    before_results = (
        before_interfaces
        + before_network_instances
        + before_ospf
    )

    assert before_results
    assert all(
        result["status"] == "PASS"
        for result in before_results
    ), (
        f"Unexpected R1 state; refusing to modify it: "
        f"{before_results}"
    )

    # Build the NETCONF client.
    host = resolve_container_ip(
        inventory["devices"][device_name]["container"]
    )

    client = NETCONFClient(
        host=host,
        port=830,
        username=username,
        password=password,
    )

    # Apply the complete desired state and commit once.
    apply_device_netconf_config(
        client=client,
        desired_interfaces=device["interfaces"],
        desired_network_instances=device.get(
            "network_instances",
            {},
        ),
        desired_ospf=device.get("ospf"),
    )

    # Retrieve actual state and compare again.
    after_interfaces = validate_device_interfaces_netconf(
        device_name=device_name,
        inventory=inventory,
        desired_state=desired_state,
        username=username,
        password=password,
    )

    after_network_instances = validate_device_network_instances_netconf(
        device_name=device_name,
        inventory=inventory,
        desired_state=desired_state,
        username=username,
        password=password,
    )

    after_ospf = validate_device_ospf_netconf(
        device_name=device_name,
        inventory=inventory,
        desired_state=desired_state,
        username=username,
        password=password,
    )

    after_results = (
        after_interfaces
        + after_network_instances
        + after_ospf
    )

    assert after_results
    assert all(
        result["status"] == "PASS"
        for result in after_results
    ), f"R1 has drift after NETCONF apply: {after_results}"
