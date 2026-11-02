import copy
from pathlib import Path

import pytest
import yaml

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
            "lo0.0",
        ]


def test_desired_state_contains_ospf():
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    expected_router_ids = {
        "R1": "1.1.1.1",
        "R2": "2.2.2.2",
        "R3": "3.3.3.3",
    }

    for device_name, expected_router_id in expected_router_ids.items():
        ospf = desired_state["devices"][device_name]["ospf"]["instance"]

        assert ospf["name"] == "default"
        assert ospf["admin_state"] == "enable"
        assert ospf["version"] == "ospf-v2"
        assert ospf["router_id"] == expected_router_id

        assert set(
            ospf["areas"]["0.0.0.0"]["interfaces"]
        ) == {
            "ethernet-1/1.0",
            "ethernet-1/2.0",
        }

def test_desired_state_contains_bgp():
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    expected = {
        "R1": (65001, "1.1.1.1"),
        "R2": (65002, "2.2.2.2"),
        "R3": (65003, "3.3.3.3"),
    }

    for device_name, (expected_asn, expected_router_id) in expected.items():
        bgp = desired_state["devices"][device_name]["bgp"]

        assert bgp["autonomous_system"] == expected_asn
        assert bgp["router_id"] == expected_router_id
        assert bgp["afi_safi"]["ipv4_unicast"]["admin_state"] == "enable"
        assert len(bgp["peer_groups"]) == 2
        assert len(bgp["neighbors"]) == 2
        assert bgp["import_policy"] == "allow-bgp-loopbacks"
        assert bgp["export_policy"] == "allow-bgp-loopbacks"

    policies = desired_state["routing_policies"]

    assert "bgp-loopbacks" in policies["prefix_sets"]
    assert "allow-bgp-loopbacks" in policies["policies"]


@pytest.mark.parametrize(
    ("mutate", "error_message"),
    [
        (
            lambda state: state["devices"]["R1"]["bgp"].update(
                autonomous_system=0
            ),
            "autonomous_system",
        ),
        (
            lambda state: state["devices"]["R1"]["bgp"].update(
                router_id="invalid"
            ),
            "router_id",
        ),
        (
            lambda state: state["devices"]["R1"]["bgp"]["neighbors"][
                "10.0.12.2"
            ].update(peer_group="missing-group"),
            "unknown peer group",
        ),
        (
            lambda state: state["devices"]["R1"]["bgp"].update(
                export_policy="missing-policy"
            ),
            "export_policy",
        ),
        (
            lambda state: state["routing_policies"]["prefix_sets"][
                "bgp-loopbacks"
            ]["prefixes"][0].update(prefix="10.255.0.1/33"),
            "Invalid network prefix",
        ),
        (
            lambda state: state["routing_policies"]["policies"][
                "allow-bgp-loopbacks"
            ]["statements"][0].update(action="permit"),
            "action",
        ),
    ],
    ids=[
        "invalid-asn",
        "invalid-router-id",
        "unknown-peer-group",
        "unknown-export-policy",
        "invalid-prefix",
        "invalid-policy-action",
    ],
)
def test_desired_state_rejects_invalid_bgp_configuration(
    tmp_path,
    mutate,
    error_message,
):
    desired_state = copy.deepcopy(
        load_desired_state(DESIRED_STATE_FILE)
    )

    mutate(desired_state)

    desired_state_file = tmp_path / "desired.yaml"
    desired_state_file.write_text(
        yaml.safe_dump(desired_state, sort_keys=False),
        encoding="utf-8",
    )

    with pytest.raises(DesiredStateError, match=error_message):
        load_desired_state(desired_state_file)
