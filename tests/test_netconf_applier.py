from unittest.mock import Mock

from src.config.netconf_applier import apply_device_netconf_config


def test_apply_device_netconf_config():
    client = Mock()

    desired_interfaces = {
        "ethernet-1/1": {
            "admin_state": "enable",
            "ipv4": {
                "admin_state": "enable",
                "address": "10.0.12.1/30",
            },
        },
    }

    desired_network_instances = {
        "default": {
            "interfaces": [
                "ethernet-1/1.0",
            ],
        },
    }

    desired_ospf = {
        "instance": {
            "name": "default",
            "admin_state": "enable",
            "version": "ospf-v2",
            "router_id": "1.1.1.1",
            "areas": {
                "0.0.0.0": {
                    "interfaces": {
                        "ethernet-1/1.0": {},
                    },
                },
            },
        },
    }

    apply_device_netconf_config(
        client=client,
        desired_interfaces=desired_interfaces,
        desired_network_instances=desired_network_instances,
        desired_ospf=desired_ospf,
    )

    assert client.edit_config.call_count == 4
    client.commit.assert_called_once()
