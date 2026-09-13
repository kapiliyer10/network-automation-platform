from src.desired.comparator import (
    compare_interfaces,
    compare_network_instance_interfaces,
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
