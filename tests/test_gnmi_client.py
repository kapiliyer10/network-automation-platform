import os
from pathlib import Path
from dotenv import load_dotenv
import pytest

from src.inventory.loader import load_inventory
from src.network.docker_resolver import resolve_container_ip
from src.network.gnmi_client import GNMIClient, GNMIError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_FILE = PROJECT_ROOT / "configs" / "inventory" / "devices.yaml"
load_dotenv()


def test_gnmi_get_hostname():
    inventory = load_inventory(INVENTORY_FILE)

    r1 = inventory["devices"]["R1"]
    host = resolve_container_ip(r1["container"])

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]

    client = GNMIClient(
        host=host,
        port=57401,
        username=username,
        password=password,
    )

    hostname = client.get_hostname()

    assert hostname == "R1"


def test_gnmi_get_interfaces_oper_state():
    inventory = load_inventory(INVENTORY_FILE)

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]
    expected_interfaces = {"ethernet-1/1", "ethernet-1/2"}
    
    for device_name, device in inventory["devices"].items():
        host = resolve_container_ip(device["container"])

        client = GNMIClient(
            host=host,
            port=57401,
            username=username,
            password=password,
        )
        interfaces = client.get_interfaces()
        discovered = {interface["name"]: interface for interface in interfaces}

        for interface_name in expected_interfaces:
            assert interface_name in discovered, (
                f"{device_name} did not discover {interface_name}"
                )

            assert discovered[interface_name]["oper_state"] == "up", (
                f"{device_name} {interface_name} should be up, "
                f"but is {discovered[interface_name]['oper_state']}"
            )


def test_gnmi_get_interfaces():
    inventory = load_inventory(INVENTORY_FILE)

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]

    for device_name, device in inventory["devices"].items():
        host = resolve_container_ip(device["container"])

        client = GNMIClient(
            host=host,
            port=57401,
            username=username,
            password=password,
        )

        interfaces = client.get_interfaces()

        assert interfaces, f"{device_name} returned no interfaces"

        interface_names = {
            interface["name"]
            for interface in interfaces
        }

        assert "ethernet-1/1" in interface_names, (
            f"{device_name} is missing ethernet-1/1"
        )

        assert "ethernet-1/2" in interface_names, (
            f"{device_name} is missing ethernet-1/2"
        )


def test_gnmi_get_invalid_interface():
    inventory = load_inventory(INVENTORY_FILE)

    r1 = inventory["devices"]["R1"]
    host = resolve_container_ip(r1["container"])

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]

    client = GNMIClient(
        host=host,
        port=57401,
        username=username,
        password=password,
    )

    with pytest.raises(GNMIError):
        client.get_interface_oper_state("ethernet-1/99")


def test_gnmi_get_ospf_neighbors():
    inventory = load_inventory(INVENTORY_FILE)

    r1 = inventory["devices"]["R1"]
    host = resolve_container_ip(r1["container"])

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]

    client = GNMIClient(
        host=host,
        port=57401,
        username=username,
        password=password,
    )

    neighbors = client.get_ospf_neighbors("ethernet-1/1.0")

    assert len(neighbors) == 1
    assert neighbors[0]["router_id"] == "2.2.2.2"
    assert neighbors[0]["address"] == "10.0.12.2"
    assert neighbors[0]["state"] == "full"


def test_gnmi_get_all_ospf_neighbors():
    inventory = load_inventory(INVENTORY_FILE)

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]

    for device_name, device in inventory["devices"].items():
        host = resolve_container_ip(device["container"])

        client = GNMIClient(
            host=host,
            port=57401,
            username=username,
            password=password,
        )

        neighbors = client.get_all_ospf_neighbors()

        assert len(neighbors) == 2, (
            f"{device_name} should have 2 OSPF neighbors, "
            f"but found {len(neighbors)}"
        )

        assert all(
            neighbor["state"] == "full"
            for neighbor in neighbors
        ), f"{device_name} has a non-Full OSPF neighbor"


def test_gnmi_get_ip_addresses():
    inventory = load_inventory(INVENTORY_FILE)

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]

    for device_name, device in inventory["devices"].items():
        host = resolve_container_ip(device["container"])

        client = GNMIClient(
            host=host,
            port=57401,
            username=username,
            password=password,
        )

        addresses = client.get_ip_addresses()

        assert addresses, (
            f"{device_name} returned no IPv4 addresses"
        )

        interface_names = {
            address["interface"]
            for address in addresses
        }

        assert "ethernet-1/1" in interface_names, (
            f"{device_name} is missing IPv4 address on ethernet-1/1"
        )

        assert "ethernet-1/2" in interface_names, (
            f"{device_name} is missing IPv4 address on ethernet-1/2"
        )

        assert "lo0" in interface_names, (
            f"{device_name} is missing IPv4 address on lo0"
        )


def test_gnmi_get_routes():
    inventory = load_inventory(INVENTORY_FILE)

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]

    for device_name, device in inventory["devices"].items():
        host = resolve_container_ip(device["container"])

        client = GNMIClient(
            host=host,
            port=57401,
            username=username,
            password=password,
        )

        routes = client.get_routes()

        assert routes, f"{device_name} returned no routes"

        assert any(
            route["active"] for route in routes
        ), f"{device_name} has no active routes"

        assert any(
            route["route_type"] == "local"
            for route in routes
        ), f"{device_name} has no local routes"

        assert any(
            route["route_type"] == "ospfv2"
            for route in routes
        ), f"{device_name} has no OSPF routes"


def test_gnmi_get_interface_ipv4():
    inventory = load_inventory(INVENTORY_FILE)

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]

    host = resolve_container_ip(
        inventory["devices"]["R1"]["container"]
    )

    client = GNMIClient(
        host=host,
        port=57401,
        username=username,
        password=password,
    )

    result = client.get_interface_ipv4("ethernet-1/1")

    assert result["admin_state"] == "enable"
    assert result["address"] == "10.0.12.1/30"


def test_gnmi_get_network_instance_interfaces():
    inventory = load_inventory(INVENTORY_FILE)

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]

    host = resolve_container_ip(
        inventory["devices"]["R1"]["container"]
    )

    client = GNMIClient(
        host=host,
        port=57401,
        username=username,
        password=password,
    )

    interfaces = client.get_network_instance_interfaces("default")

    assert interfaces

    discovered = {
        interface["name"]: interface["oper_state"]
        for interface in interfaces
    }

    assert discovered["ethernet-1/1.0"] == "up"
    assert discovered["ethernet-1/2.0"] == "up"
    assert discovered["lo0.0"] == "up"


def test_gnmi_get_ospf_configuration():
    inventory = load_inventory(INVENTORY_FILE)

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]

    host = resolve_container_ip(
        inventory["devices"]["R1"]["container"]
    )

    client = GNMIClient(
        host=host,
        port=57401,
        username=username,
        password=password,
    )

    ospf = client.get_ospf_configuration()

    assert ospf["name"] == "default"
    assert ospf["admin_state"] == "enable"
    assert ospf["version"] == "ospf-v2"
    assert ospf["router_id"] == "1.1.1.1"

    interfaces = {
        interface["name"]: interface
        for interface in ospf["areas"]["0.0.0.0"]["interfaces"]
    }

    assert interfaces["ethernet-1/1.0"]["admin_state"] == "enable"
    assert interfaces["ethernet-1/2.0"]["admin_state"] == "enable"
    assert interfaces["lo0.0"]["passive"] is True
