from src.network.netconf_client import NETCONFClient
from src.config.netconf_renderer import build_device_netconf_configs


def test_build_device_netconf_configs():
    client = NETCONFClient(
        host="test-host",
        port=830,
        username="test-user",
        password="test-password",
    )

    desired_interfaces = {
        "ethernet-1/1": {
            "admin_state": "enable",
            "ipv4": {
                "admin_state": "enable",
                "address": "10.0.12.1/30",
            },
        },
        "ethernet-1/2": {
            "admin_state": "enable",
            "ipv4": {
                "admin_state": "enable",
                "address": "10.0.31.1/30",
            },
        },
    }

    desired_network_instances = {
        "default": {
            "interfaces": [
                "ethernet-1/1.0",
                "ethernet-1/2.0",
                "lo0.0",
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
                        "ethernet-1/2.0": {},
                        "lo0.0": {
                            "passive": True,
                        },
                    },
                },
            },
        },
    }

    configs = build_device_netconf_configs(
        client=client,
        desired_interfaces=desired_interfaces,
        desired_network_instances=desired_network_instances,
        desired_ospf=desired_ospf,
    )

    assert len(configs) == 9

    assert any(
        "<name>ethernet-1/1</name>" in config
        for config in configs
    )

    assert any(
        "<name>lo0.0</name>" in config
        for config in configs
    )

    assert any(
        "<name>default</name>" in config
        and "<router-id>1.1.1.1</router-id>" in config
        for config in configs
    )

    assert any(
        "<interface-name>lo0.0</interface-name>" in config
        and "<passive>true</passive>" in config
        for config in configs
    )
    assert any(
        "srl_nokia-ospf-types:ospf-v2" in config
        for config in configs
    )
