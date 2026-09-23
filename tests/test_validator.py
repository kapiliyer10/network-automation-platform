import os
from pathlib import Path

from dotenv import load_dotenv

from src.desired.loader import load_desired_state
from src.inventory.loader import load_inventory
from src.desired.validator import (
    validate_device_interfaces,
    validate_device_network_instances,
    validate_device_interfaces_netconf,
    validate_device_network_instances_netconf,
    validate_device_ospf,
    validate_device_ospf_netconf,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INVENTORY_FILE = (
    PROJECT_ROOT / "configs" / "inventory" / "devices.yaml"
)

DESIRED_STATE_FILE = (
    PROJECT_ROOT / "configs" / "desired" / "desired_state.yaml"
)

load_dotenv(PROJECT_ROOT / ".env")


def test_validate_interfaces():
    inventory = load_inventory(INVENTORY_FILE)
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]

    for device_name in inventory["devices"]:
        results = validate_device_interfaces(
            device_name=device_name,
            inventory=inventory,
            desired_state=desired_state,
            username=username,
            password=password,
        )

        assert results, f"{device_name} returned no validation results"

        assert all(
            result["status"] == "PASS"
            for result in results
        ), f"{device_name} has interface drift: {results}"


def test_validate_r1_interfaces_detects_drift():
    inventory = load_inventory(INVENTORY_FILE)
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    # Create a controlled mismatch in memory.
    desired_state["devices"]["R1"]["interfaces"]["ethernet-1/2"][
        "admin_state"
    ] = "disable"

    results = validate_device_interfaces(
        device_name="R1",
        inventory=inventory,
        desired_state=desired_state,
        username=os.environ["GNMI_USERNAME"],
        password=os.environ["GNMI_PASSWORD"],
    )

    drifted = [
        result
        for result in results
        if result["interface"] == "ethernet-1/2"
        and result["field"] == "admin_state"
    ]

    assert len(drifted) == 1
    assert drifted[0]["desired"] == "disable"
    assert drifted[0]["actual"] == "enable"
    assert drifted[0]["status"] == "DRIFT"


def test_validate_network_instances():
    inventory = load_inventory(INVENTORY_FILE)
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    results = validate_device_network_instances(
        device_name="R1",
        inventory=inventory,
        desired_state=desired_state,
        username=os.environ["GNMI_USERNAME"],
        password=os.environ["GNMI_PASSWORD"],
    )

    assert results

    assert all(
        result["status"] == "PASS"
        for result in results
    )


def test_validate_r1_network_instances_detects_drift():
    inventory = load_inventory(INVENTORY_FILE)
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    desired_state["devices"]["R1"]["network_instances"]["default"][
        "interfaces"
    ] = [
        "ethernet-1/1.0",
        "ethernet-1/99.0",
    ]

    results = validate_device_network_instances(
        device_name="R1",
        inventory=inventory,
        desired_state=desired_state,
        username=os.environ["GNMI_USERNAME"],
        password=os.environ["GNMI_PASSWORD"],
    )

    drifted = [
        result
        for result in results
        if result["interface"] == "ethernet-1/99.0"
    ]

    assert len(drifted) == 1
    assert drifted[0]["network_instance"] == "default"
    assert drifted[0]["status"] == "DRIFT"


def test_validate_ospf():
    inventory = load_inventory(INVENTORY_FILE)
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    results = validate_device_ospf(
        device_name="R1",
        inventory=inventory,
        desired_state=desired_state,
        username=os.environ["GNMI_USERNAME"],
        password=os.environ["GNMI_PASSWORD"],
    )

    assert results
    assert all(
        result["status"] == "PASS"
        for result in results
    )


def test_validate_r1_ospf_detects_drift():
    inventory = load_inventory(INVENTORY_FILE)
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    desired_state["devices"]["R1"]["ospf"]["instance"][
        "router_id"
    ] = "9.9.9.9"

    results = validate_device_ospf(
        device_name="R1",
        inventory=inventory,
        desired_state=desired_state,
        username=os.environ["GNMI_USERNAME"],
        password=os.environ["GNMI_PASSWORD"],
    )

    drifted = [
        result
        for result in results
        if result["field"] == "ospf.instance.router_id"
    ]

    assert len(drifted) == 1
    assert drifted[0]["desired"] == "9.9.9.9"
    assert drifted[0]["actual"] == "1.1.1.1"
    assert drifted[0]["status"] == "DRIFT"


def test_validate_interfaces_netconf():
    inventory = load_inventory(INVENTORY_FILE)
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]

    results = validate_device_interfaces_netconf(
        device_name="R1",
        inventory=inventory,
        desired_state=desired_state,
        username=username,
        password=password,
    )

    assert results
    assert all(
        result["status"] == "PASS"
        for result in results
    )


def test_validate_network_instances_netconf():
    inventory = load_inventory(INVENTORY_FILE)
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    results = validate_device_network_instances_netconf(
        device_name="R1",
        inventory=inventory,
        desired_state=desired_state,
        username=os.environ["GNMI_USERNAME"],
        password=os.environ["GNMI_PASSWORD"],
    )

    assert results
    assert all(
        result["status"] == "PASS"
        for result in results
    )


def test_validate_ospf_netconf():
    inventory = load_inventory(INVENTORY_FILE)
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    results = validate_device_ospf_netconf(
        device_name="R1",
        inventory=inventory,
        desired_state=desired_state,
        username=os.environ["GNMI_USERNAME"],
        password=os.environ["GNMI_PASSWORD"],
    )
    assert results
    assert all(
        result["status"] == "PASS"
        for result in results
    )
