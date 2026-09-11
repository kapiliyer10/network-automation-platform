import os
from pathlib import Path

from dotenv import load_dotenv

from src.desired.loader import load_desired_state
from src.desired.validator import validate_device_interfaces
from src.inventory.loader import load_inventory


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
