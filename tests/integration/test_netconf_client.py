import os
from pathlib import Path

from dotenv import load_dotenv

from src.inventory.loader import load_inventory
from src.network.docker_resolver import resolve_container_ip
from src.network.netconf_client import NETCONFClient


PROJECT_ROOT = Path(__file__).resolve().parents[2]

INVENTORY_FILE = (
    PROJECT_ROOT / "configs" / "inventory" / "devices.yaml"
)

load_dotenv(PROJECT_ROOT / ".env")


def test_netconf_interface_ipv4_round_trip():
    inventory = load_inventory(INVENTORY_FILE)

    r1 = inventory["devices"]["R1"]
    host = resolve_container_ip(r1["container"])

    client = NETCONFClient(
        host=host,
        port=830,
        username=os.environ["GNMI_USERNAME"],
        password=os.environ["GNMI_PASSWORD"],
    )

    expected = {
        "name": "ethernet-1/1",
        "admin_state": "enable",
        "ipv4": {
            "admin_state": "enable",
            "address": "10.0.12.1/30",
        },
    }

    # Safety check: do not modify R1 if it is not already
    # in the expected state.
    current = client.get_interface_config("ethernet-1/1")

    assert current == expected, (
        f"Unexpected R1 state; refusing to modify it: {current}"
    )

    config_xml = client.build_interface_edit_config(
        interface_name="ethernet-1/1",
        admin_state="enable",
        ipv4_admin_state="enable",
        ipv4_address="10.0.12.1/30",
    )

    # Apply to candidate.
    client.edit_config(config_xml)

    # Make candidate active.
    client.commit()

    # Verify the resulting running configuration.
    actual = client.get_interface_config("ethernet-1/1")

    assert actual == expected


def test_netconf_get_network_instance_interfaces():
    inventory = load_inventory(INVENTORY_FILE)

    r1 = inventory["devices"]["R1"]
    host = resolve_container_ip(r1["container"])

    client = NETCONFClient(
        host=host,
        port=830,
        username=os.environ["GNMI_USERNAME"],
        password=os.environ["GNMI_PASSWORD"],
    )

    interfaces = client.get_network_instance_interfaces("default")

    assert interfaces == [
        "ethernet-1/1.0",
        "ethernet-1/2.0",
        "lo0.0",
    ]


def test_netconf_network_instance_interface_round_trip():
    inventory = load_inventory(INVENTORY_FILE)

    r1 = inventory["devices"]["R1"]
    host = resolve_container_ip(r1["container"])

    client = NETCONFClient(
        host=host,
        port=830,
        username=os.environ["GNMI_USERNAME"],
        password=os.environ["GNMI_PASSWORD"],
    )

    expected = [
        "ethernet-1/1.0",
        "ethernet-1/2.0",
        "lo0.0",
    ]

    # Safety check
    current = client.get_network_instance_interfaces("default")

    assert current == expected, (
        f"Unexpected R1 state; refusing to modify it: {current}"
    )

    config_xml = client.build_network_instance_interface_edit_config(
        network_instance_name="default",
        interface_name="ethernet-1/1.0",
    )

    client.edit_config(config_xml)
    client.commit()

    actual = client.get_network_instance_interfaces("default")

    assert actual == expected


def test_netconf_get_ospf_configuration():
    inventory = load_inventory(INVENTORY_FILE)

    r1 = inventory["devices"]["R1"]
    host = resolve_container_ip(r1["container"])

    client = NETCONFClient(
        host=host,
        port=830,
        username=os.environ["GNMI_USERNAME"],
        password=os.environ["GNMI_PASSWORD"],
    )

    result = client.get_ospf_configuration(
        network_instance_name="default",
        ospf_instance_name="default",
    )

    assert result == {
        "name": "default",
        "admin_state": "enable",
        "version": "ospf-v2",
        "router_id": "1.1.1.1",
        "areas": {
            "0.0.0.0": {
                "interfaces": [
                    {"name": "ethernet-1/1.0"},
                    {"name": "ethernet-1/2.0"},
                    {
                        "name": "lo0.0",
                        "passive": True,
                    },
                ]
            }
        },
    }


def test_netconf_ospf_instance_round_trip():
    inventory = load_inventory(INVENTORY_FILE)

    r1 = inventory["devices"]["R1"]
    host = resolve_container_ip(r1["container"])

    client = NETCONFClient(
        host=host,
        port=830,
        username=os.environ["GNMI_USERNAME"],
        password=os.environ["GNMI_PASSWORD"],
    )

    expected = {
        "name": "default",
        "admin_state": "enable",
        "version": "ospf-v2",
        "router_id": "1.1.1.1",
        "areas": {
            "0.0.0.0": {
                "interfaces": [
                    {"name": "ethernet-1/1.0"},
                    {"name": "ethernet-1/2.0"},
                    {
                        "name": "lo0.0",
                        "passive": True,
                    },
                ]
            }
        },
    }

    # Safety check
    current = client.get_ospf_configuration(
        network_instance_name="default",
        ospf_instance_name="default",
    )

    assert current == expected, (
        f"Unexpected R1 OSPF state; refusing to modify it: {current}"
    )

    config_xml = client.build_ospf_instance_edit_config(
        network_instance_name="default",
        ospf_instance_name="default",
        admin_state="enable",
        version="srl_nokia-ospf-types:ospf-v2",
        router_id="1.1.1.1",
    )

    client.edit_config(config_xml)
    client.commit()

    actual = client.get_ospf_configuration(
        network_instance_name="default",
        ospf_instance_name="default",
    )

    assert actual == expected


def test_netconf_ospf_area_interfaces_round_trip():
    inventory = load_inventory(INVENTORY_FILE)

    r1 = inventory["devices"]["R1"]
    host = resolve_container_ip(r1["container"])

    client = NETCONFClient(
        host=host,
        port=830,
        username=os.environ["GNMI_USERNAME"],
        password=os.environ["GNMI_PASSWORD"],
    )

    expected = {
        "name": "default",
        "admin_state": "enable",
        "version": "ospf-v2",
        "router_id": "1.1.1.1",
        "areas": {
            "0.0.0.0": {
                "interfaces": [
                    {"name": "ethernet-1/1.0"},
                    {"name": "ethernet-1/2.0"},
                    {
                        "name": "lo0.0",
                        "passive": True,
                    },
                ]
            }
        },
    }

    # Safety check
    current = client.get_ospf_configuration(
        network_instance_name="default",
        ospf_instance_name="default",
    )

    assert current == expected, (
        f"Unexpected R1 OSPF state; refusing to modify it: {current}"
    )

    # Normal OSPF interface
    normal_config = client.build_ospf_area_interface_edit_config(
        network_instance_name="default",
        ospf_instance_name="default",
        area_id="0.0.0.0",
        interface_name="ethernet-1/1.0",
        passive=False,
    )

    # Passive OSPF interface
    passive_config = client.build_ospf_area_interface_edit_config(
        network_instance_name="default",
        ospf_instance_name="default",
        area_id="0.0.0.0",
        interface_name="lo0.0",
        passive=True,
    )

    # Apply both changes to candidate
    client.edit_config(normal_config)
    client.edit_config(passive_config)

    # Commit once
    client.commit()

    # Verify final running configuration
    actual = client.get_ospf_configuration(
        network_instance_name="default",
        ospf_instance_name="default",
    )

    assert actual == expected
