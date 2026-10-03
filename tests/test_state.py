from unittest.mock import Mock, patch
from xmlrpc import client

from src.network.state import get_device_state


def test_get_device_state():
    inventory = {
        "devices": {
            "R1": {
                "container": "clab-srl-lab-R1",
                "platform": "srlinux",
                "role": "router",
            }
        }
    }

    with patch(
        "src.network.state.resolve_container_ip",
        return_value="10.0.0.1",
    ), patch(
        "src.network.state.GNMIClient"
    ) as mock_client:

        client = mock_client.return_value
        client.get_hostname.return_value = "R1"
        client.get_interfaces.return_value = [
            {
                "name": "ethernet-1/1",
                "admin_state": "enable",
                "oper_state": "up",
            }
        ]

        client.get_ip_addresses.return_value = [
            {
                "interface": "ethernet-1/1",
                "subinterface_index": 0,
                "ip_address": "10.0.1.1/24",
                "origin": "static",
                "status": "preferred",
            }
        ]

        client.get_routes.return_value = [
            {
                "prefix": "10.0.2.0/24",
                "active": True,
                "metric": 10,
                "preference": 170,
                "route_type": "ospf",
            }
        ]

        client.get_all_ospf_neighbors.return_value = [
            {
                "interface": "ethernet-1/1",
                "router_id": "10.0.0.2",
                "address": "10.0.1.2",
                "state": "full",
            }
        ]

        client.get_ospf_configuration.return_value = {
            "name": "default",
            "admin_state": "enable",
            "version": 2,
            "router_id": "10.0.0.1",
            "areas": {},
        }

        result = get_device_state(
            device_name="R1",
            inventory=inventory,
            username="admin",
            password="admin",
        )

    assert result["hostname"] == "R1"
    assert "interfaces" in result
    assert "ip_addresses" in result
    assert "routes" in result
    assert "ospf_neighbors" in result
    assert "ospf" in result

    assert result["interfaces"][0]["name"] == "ethernet-1/1"
    assert result["ip_addresses"][0]["ip_address"] == "10.0.1.1/24"
    assert result["routes"][0]["prefix"] == "10.0.2.0/24"
    assert result["ospf_neighbors"][0]["state"] == "full"
    assert result["ospf"]["router_id"] == "10.0.0.1"
