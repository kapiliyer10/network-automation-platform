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


def test_build_device_netconf_configs_includes_bgp():
    client = NETCONFClient(
        host="test-host",
        port=830,
        username="test-user",
        password="test-password",
    )

    desired_bgp = {
        "autonomous_system": 65001,
        "router_id": "1.1.1.1",
        "afi_safi": {
            "ipv4_unicast": {
                "admin_state": "enable",
            },
        },
        "peer_groups": {
            "to-r2": {"peer_as": 65002},
        },
        "neighbors": {
            "10.0.12.2": {"peer_group": "to-r2"},
        },
        "import_policy": "allow-bgp-loopbacks",
        "export_policy": "allow-bgp-loopbacks",
    }

    desired_routing_policies = {
        "prefix_sets": {
            "bgp-loopbacks": {
                "prefixes": [
                    {
                        "prefix": "10.255.0.1/32",
                        "mask_length_range": "exact",
                    },
                ],
            },
        },
        "policies": {
            "allow-bgp-loopbacks": {
                "default_action": "reject",
                "statements": [
                    {
                        "sequence": 10,
                        "match": {
                            "prefix_set": "bgp-loopbacks",
                            "match_set_options": "any",
                        },
                        "action": "accept",
                    },
                ],
            },
        },
    }

    configs = build_device_netconf_configs(
        client=client,
        desired_interfaces={},
        desired_network_instances={},
        desired_ospf=None,
        desired_bgp=desired_bgp,
        desired_routing_policies=desired_routing_policies,
    )

    assert len(configs) == 2

    # Routing policy must be generated before BGP.
    assert "routing-policy" in configs[0]
    assert "bgp" in configs[1]
    assert "65001" in configs[1]
    assert "10.0.12.2" in configs[1]
