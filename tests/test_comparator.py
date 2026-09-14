from src.desired.comparator import (
    compare_interfaces,
    compare_network_instance_interfaces,
    compare_ospf_configuration,
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
