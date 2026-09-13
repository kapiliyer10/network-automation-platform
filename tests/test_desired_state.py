from pathlib import Path

import pytest

from src.desired.loader import DesiredStateError, load_desired_state

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DESIRED_STATE_FILE = (PROJECT_ROOT / "configs" / "desired" / "desired_state.yaml")


def test_desired_state_loads():
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    assert "devices" in desired_state
    assert set(desired_state["devices"]) == {"R1","R2","R3"}


def test_desired_state_contains_interfaces():
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    for device in desired_state["devices"].values():
        assert "interfaces" in device
        assert set(device["interfaces"]) == {
            "ethernet-1/1",
            "ethernet-1/2",
        }


def test_desired_state_contains_admin_state():
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    for device in desired_state["devices"].values():
        for interfaces in device["interfaces"].values():
            assert interfaces["admin_state"] == "enable"


def test_desired_state_contains_ipv4():
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    expected_addresses = {
        "R1": {
            "ethernet-1/1": "10.0.12.1/30",
            "ethernet-1/2": "10.0.31.1/30",
        },
        "R2": {
            "ethernet-1/1": "10.0.12.2/30",
            "ethernet-1/2": "10.0.23.1/30",
        },
        "R3": {
            "ethernet-1/1": "10.0.23.2/30",
            "ethernet-1/2": "10.0.31.2/30",
        },
    }

    for device_name, interfaces in expected_addresses.items():
        for interface_name, expected_address in interfaces.items():
            interface = desired_state["devices"][device_name]["interfaces"][
                interface_name
            ]

            assert interface["ipv4"]["admin_state"] == "enable"
            assert interface["ipv4"]["address"] == expected_address


def test_desired_state_rejects_invalid_ipv4_type(tmp_path):
    desired_state_file = tmp_path / "desired.yaml"

    desired_state_file.write_text(
        """
devices:
  R1:
    interfaces:
      ethernet-1/1:
        admin_state: enable
        ipv4: enable
""",
        encoding="utf-8",
    )

    with pytest.raises(DesiredStateError):
        load_desired_state(desired_state_file)


def test_desired_state_rejects_missing_ipv4_admin_state(tmp_path):
    desired_state_file = tmp_path / "desired.yaml"

    desired_state_file.write_text(
        """
devices:
  R1:
    interfaces:
      ethernet-1/1:
        admin_state: enable
        ipv4:
          address: 10.0.12.1/30
""",
        encoding="utf-8",
    )

    with pytest.raises(DesiredStateError):
        load_desired_state(desired_state_file)


def test_desired_state_rejects_missing_ipv4_address(tmp_path):
    desired_state_file = tmp_path / "desired.yaml"

    desired_state_file.write_text(
        """
devices:
  R1:
    interfaces:
      ethernet-1/1:
        admin_state: enable
        ipv4:
          admin_state: enable
""",
        encoding="utf-8",
    )

    with pytest.raises(DesiredStateError):
        load_desired_state(desired_state_file)


def test_desired_state_contains_network_instances():
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    for device in desired_state["devices"].values():
        network_instances = device["network_instances"]

        assert "default" in network_instances
        assert network_instances["default"]["interfaces"] == [
            "ethernet-1/1.0",
            "ethernet-1/2.0",
        ]
