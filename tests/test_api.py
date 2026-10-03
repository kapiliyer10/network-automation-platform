from fastapi.testclient import TestClient
from unittest.mock import patch
from src.api.main import app
import os

client = TestClient(app)


def test_get_devices():
    response = client.get("/devices")

    assert response.status_code == 200

    data = response.json()

    assert "devices" in data
    assert set(data["devices"]) == {"R1", "R2", "R3"}

    assert data["devices"]["R1"]["container"] == "clab-srl-lab-R1"
    assert data["devices"]["R1"]["platform"] == "srlinux"
    assert data["devices"]["R1"]["role"] == "router"


def test_get_device():
    response = client.get("/devices/R1")

    assert response.status_code == 200

    data = response.json()

    assert data["device"] == "R1"
    assert data["container"] == "clab-srl-lab-R1"
    assert data["platform"] == "srlinux"
    assert data["role"] == "router"


def test_get_unknown_device():
    response = client.get("/devices/R99")

    assert response.status_code == 404

    data = response.json()

    assert data["detail"] == "Device 'R99' not found"


def test_get_device_state():
    expected_state = {
        "interfaces": [
            {
                "name": "ethernet-1/1",
                "admin_state": "enable",
                "oper_state": "up",
            }
        ],
        "ip_addresses": [],
        "routes": [],
        "ospf_neighbors": [],
        "ospf": {},
    }

    with patch(
        "src.api.main.get_device_state",
        return_value=expected_state,
    ):
        response = client.get("/devices/R1/state")

    assert response.status_code == 200

    data = response.json()

    assert data["device"] == "R1"
    assert data["state"] == expected_state


def test_validate_device():
    expected_results = [
        {
            "device": "R1",
            "field": "admin_state",
            "status": "PASS",
        }
    ]

    with (
        patch(
            "src.api.main.load_desired_state",
            return_value={"devices": {"R1": {}}},
        ),
        patch(
            "src.api.main.validate_device",
            return_value=expected_results,
        ) as validate,
    ):
        response = client.post("/devices/R1/validate")

    assert response.status_code == 200

    data = response.json()

    assert data["device"] == "R1"
    assert data["results"] == expected_results

    validate.assert_called_once_with(
        device_name="R1",
        inventory={
            "devices": {
                "R1": {
                    "container": "clab-srl-lab-R1",
                    "platform": "srlinux",
                    "role": "router",
                },
                "R2": {
                    "container": "clab-srl-lab-R2",
                    "platform": "srlinux",
                    "role": "router",
                },
                "R3": {
                    "container": "clab-srl-lab-R3",
                    "platform": "srlinux",
                    "role": "router",
                },
            }
        },
        desired_state={"devices": {"R1": {}}},
        username=os.environ["GNMI_USERNAME"],
        password=os.environ["GNMI_PASSWORD"],
    )


def test_configure_device():
    expected_results = [
        {
            "device": "R1",
            "field": "admin_state",
            "status": "PASS",
        }
    ]

    expected_desired_state = {
        "devices": {
            "R1": {
                "interfaces": {},
            }
        }
    }

    with (
        patch(
            "src.api.main.load_desired_state",
            return_value=expected_desired_state,
        ),
        patch(
            "src.api.main.configure_and_validate_device_netconf",
            return_value=expected_results,
        ) as configure_device,
        patch.dict(
            "os.environ",
            {
                "GNMI_USERNAME": "test-user",
                "GNMI_PASSWORD": "test-password",
            },
            clear=False,
        ),
    ):
        response = client.post("/devices/R1/configure")

    assert response.status_code == 200

    data = response.json()

    assert data["device"] == "R1"
    assert data["results"] == expected_results

    configure_device.assert_called_once()

    call_kwargs = configure_device.call_args.kwargs

    assert call_kwargs["device_name"] == "R1"
    assert call_kwargs["desired_state"] == expected_desired_state
    assert call_kwargs["username"] == "test-user"
    assert call_kwargs["password"] == "test-password"


def test_get_drift():
    validation_results = {
        "R1": [
            {"status": "PASS"},
            {"status": "PASS"},
        ],
        "R2": [
            {"status": "PASS"},
            {"status": "DRIFT"},
        ],
    }

    expected_summary = {
        "devices": {
            "R1": {
                "status": "PASS",
                "total": 2,
                "passed": 2,
                "drifted": 0,
            },
            "R2": {
                "status": "DRIFT",
                "total": 2,
                "passed": 1,
                "drifted": 1,
            },
        },
        "overall_status": "DRIFT",
    }

    with (
        patch(
            "src.api.main.validate_all_devices",
            return_value=validation_results,
        ),
        patch(
            "src.api.main.summarize_results",
            return_value=expected_summary,
        ),
    ):
        response = client.get("/drift")

    assert response.status_code == 200
    assert response.json() == expected_summary
