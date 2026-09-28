from unittest.mock import Mock, patch

from src.workflow import (
    configure_and_validate_device_netconf,
    configure_and_validate_all_devices_netconf,
)


def test_configure_and_validate_device_netconf():
    inventory = {
        "devices": {
            "R1": {
                "container": "clab-srl-lab-R1",
            },
        },
    }

    desired_state = {
        "devices": {
            "R1": {
                "interfaces": {
                    "ethernet-1/1": {
                        "admin_state": "enable",
                    },
                },
                "network_instances": {},
            },
        },
    }

    fake_client = Mock()

    interface_results = [
        {
            "device": "R1",
            "field": "admin_state",
            "status": "PASS",
        }
    ]

    network_instance_results = []

    ospf_results = []

    with (
        patch(
            "src.workflow.resolve_container_ip",
            return_value="10.0.0.1",
        ),
        patch(
            "src.workflow.NETCONFClient",
            return_value=fake_client,
        ),
        patch(
            "src.workflow.apply_device_netconf_config",
        ) as apply_config,
        patch(
            "src.workflow.validate_device_interfaces_netconf",
            return_value=interface_results,
        ),
        patch(
            "src.workflow.validate_device_network_instances_netconf",
            return_value=network_instance_results,
        ),
        patch(
            "src.workflow.validate_device_ospf_netconf",
            return_value=ospf_results,
        ),
    ):
        results = configure_and_validate_device_netconf(
            device_name="R1",
            inventory=inventory,
            desired_state=desired_state,
            username="test-user",
            password="test-password",
        )

    apply_config.assert_called_once()
    assert results == interface_results


def test_configure_and_validate_all_devices_netconf():
    inventory = {
        "devices": {
            "R1": {"container": "clab-srl-lab-R1"},
            "R2": {"container": "clab-srl-lab-R2"},
            "R3": {"container": "clab-srl-lab-R3"},
        }
    }

    desired_state = {
        "devices": {
            "R1": {},
            "R2": {},
            "R3": {},
        }
    }

    device_results = {
        "R1": [{"device": "R1", "status": "PASS"}],
        "R2": [{"device": "R2", "status": "PASS"}],
        "R3": [{"device": "R3", "status": "PASS"}],
    }

    with patch(
        "src.workflow.configure_and_validate_device_netconf",
        side_effect=[
            device_results["R1"],
            device_results["R2"],
            device_results["R3"],
        ],
    ) as configure_device:

        results = configure_and_validate_all_devices_netconf(
            inventory=inventory,
            desired_state=desired_state,
            username="test-user",
            password="test-password",
        )

    assert results == device_results
    assert configure_device.call_count == 3
