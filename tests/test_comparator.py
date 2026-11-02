from src.desired.comparator import (
    compare_interfaces,
    compare_network_instance_interfaces,
    compare_ospf_configuration,
    compare_bgp_configuration,
    compare_routing_policy_configuration,
)


def test_compare_interfaces_pass():
    desired = {
        "ethernet-1/1": {
            "admin_state": "enable"
        }
    }

    actual = [
        {
            "name": "ethernet-1/1",
            "admin_state": "enable",
            "oper_state": "up",
        }
    ]

    results = compare_interfaces(
        device_name="R1",
        desired_interfaces=desired,
        actual_interfaces=actual,
    )

    assert results == [
        {
            "device": "R1",
            "interface": "ethernet-1/1",
            "field": "admin_state",
            "desired": "enable",
            "actual": "enable",
            "status": "PASS",
        }
    ]


def test_compare_interfaces_detects_drift():
    desired = {
        "ethernet-1/1": {
            "admin_state": "enable"
        }
    }

    actual = [
        {
            "name": "ethernet-1/1",
            "admin_state": "disable",
            "oper_state": "down",
        }
    ]

    results = compare_interfaces(
        device_name="R1",
        desired_interfaces=desired,
        actual_interfaces=actual,
    )

    assert results == [
        {
            "device": "R1",
            "interface": "ethernet-1/1",
            "field": "admin_state",
            "desired": "enable",
            "actual": "disable",
            "status": "DRIFT",
        }
    ]


def test_compare_network_instance_interfaces():
    desired = [
        "ethernet-1/1.0",
        "ethernet-1/2.0",
    ]

    actual = [
        {
            "name": "ethernet-1/1.0",
            "oper_state": "up",
        },
        {
            "name": "ethernet-1/2.0",
            "oper_state": "up",
        },
        {
            "name": "lo0.0",
            "oper_state": "up",
        },
    ]

    results = compare_network_instance_interfaces(
        device_name="R1",
        network_instance_name="default",
        desired_interfaces=desired,
        actual_interfaces=actual,
    )

    assert results == [
        {
            "device": "R1",
            "network_instance": "default",
            "interface": "ethernet-1/1.0",
            "status": "PASS",
        },
        {
            "device": "R1",
            "network_instance": "default",
            "interface": "ethernet-1/2.0",
            "status": "PASS",
        },
    ]


def test_compare_ospf_configuration():
    desired = {
        "instance": {
            "name": "default",
            "admin_state": "enable",
            "version": "ospf-v2",
            "router_id": "1.1.1.1",
            "areas": {
                "0.0.0.0": {
                    "interfaces": {
                        "ethernet-1/1.0": {
                            "admin_state": "enable",
                        },
                        "ethernet-1/2.0": {
                            "admin_state": "enable",
                        },
                        "lo0.0": {
                            "admin_state": "enable",
                            "passive": True,
                        },
                    }
                }
            },
        }
    }

    actual = {
        "name": "default",
        "admin_state": "enable",
        "version": "ospf-v2",
        "router_id": "1.1.1.1",
        "areas": {
            "0.0.0.0": {
                "interfaces": [
                    {
                        "name": "ethernet-1/1.0",
                        "admin_state": "enable",
                    },
                    {
                        "name": "ethernet-1/2.0",
                        "admin_state": "enable",
                    },
                    {
                        "name": "lo0.0",
                        "admin_state": "enable",
                        "passive": True,
                    },
                ]
            }
        },
    }

    results = compare_ospf_configuration(
        device_name="R1",
        desired_ospf=desired,
        actual_ospf=actual,
    )

    assert results
    assert all(
        result["status"] == "PASS"
        for result in results
    )


def test_compare_ospf_configuration_detects_drift():
    desired = {
        "instance": {
            "name": "default",
            "admin_state": "enable",
            "version": "ospf-v2",
            "router_id": "1.1.1.1",
            "areas": {
                "0.0.0.0": {
                    "interfaces": {
                        "ethernet-1/1.0": {
                            "admin_state": "enable",
                        },
                        "ethernet-1/2.0": {
                            "admin_state": "enable",
                        },
                        "lo0.0": {
                            "admin_state": "enable",
                            "passive": True,
                        },
                    }
                }
            },
        }
    }

    actual = {
        "name": "default",
        "admin_state": "enable",
        "version": "ospf-v2",
        "router_id": "9.9.9.9",
        "areas": {
            "0.0.0.0": {
                "interfaces": [
                    {
                        "name": "ethernet-1/1.0",
                        "admin_state": "enable",
                    },
                    {
                        "name": "ethernet-1/2.0",
                        "admin_state": "enable",
                    },
                    {
                        "name": "lo0.0",
                        "admin_state": "enable",
                        "passive": True,
                    },
                ]
            }
        },
    }

    results = compare_ospf_configuration(
        device_name="R1",
        desired_ospf=desired,
        actual_ospf=actual,
    )

    drifted = [
        result
        for result in results
        if result["field"] == "ospf.instance.router_id"
    ]

    assert len(drifted) == 1
    assert drifted[0]["desired"] == "1.1.1.1"
    assert drifted[0]["actual"] == "9.9.9.9"
    assert drifted[0]["status"] == "DRIFT"


def test_compare_bgp_configuration_pass():
    desired = {
        "autonomous_system": 65001,
        "router_id": "1.1.1.1",
        "afi_safi": {
            "ipv4_unicast": {"admin_state": "enable"},
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

    actual = {
        **desired,
        "import_policy": ["allow-bgp-loopbacks"],
        "export_policy": ["allow-bgp-loopbacks"],
    }

    results = compare_bgp_configuration(
        device_name="R1",
        desired_bgp=desired,
        actual_bgp=actual,
    )

    assert len(results) == 7
    assert all(result["status"] == "PASS" for result in results)


def test_compare_bgp_configuration_detects_peer_as_drift():
    desired = {
        "autonomous_system": 65001,
        "router_id": "1.1.1.1",
        "afi_safi": {
            "ipv4_unicast": {"admin_state": "enable"},
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

    actual = {
        **desired,
        "peer_groups": {
            "to-r2": {"peer_as": 65099},
        },
        "import_policy": ["allow-bgp-loopbacks"],
        "export_policy": ["allow-bgp-loopbacks"],
    }

    results = compare_bgp_configuration(
        device_name="R1",
        desired_bgp=desired,
        actual_bgp=actual,
    )

    drifted = [
        result for result in results
        if result["status"] == "DRIFT"
    ]

    assert len(drifted) == 1
    assert drifted[0]["field"] == "bgp.peer_groups"


def test_compare_routing_policy_configuration_pass():
    desired = {
        "prefix_sets": {
            "bgp-loopbacks": {
                "prefixes": [
                    {
                        "prefix": "10.255.0.1/32",
                        "mask_length_range": "exact",
                    },
                    {
                        "prefix": "10.255.0.2/32",
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

    # Same content, deliberately in a different prefix order.
    actual = {
        "prefix_sets": {
            "bgp-loopbacks": {
                "prefixes": [
                    {
                        "prefix": "10.255.0.2/32",
                        "mask_length_range": "exact",
                    },
                    {
                        "prefix": "10.255.0.1/32",
                        "mask_length_range": "exact",
                    },
                ],
            },
        },
        "policies": desired["policies"],
    }

    results = compare_routing_policy_configuration(
        device_name="R1",
        desired_routing_policies=desired,
        actual_routing_policies=actual,
    )

    assert len(results) == 2
    assert all(result["status"] == "PASS" for result in results)


def test_compare_routing_policy_configuration_detects_action_drift():
    desired = {
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

    actual = {
        "prefix_sets": desired["prefix_sets"],
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
                        "action": "reject",
                    },
                ],
            },
        },
    }

    results = compare_routing_policy_configuration(
        device_name="R1",
        desired_routing_policies=desired,
        actual_routing_policies=actual,
    )

    drifted = [
        result for result in results
        if result["status"] == "DRIFT"
    ]

    assert len(drifted) == 1
    assert drifted[0]["field"] == "routing_policy.policies"
