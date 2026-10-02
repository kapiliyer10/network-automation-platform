import sys
from unittest.mock import patch

from scripts.run_device import main


def test_main_passes_device_to_workflow():
    results = [
        {"device": "R1", "status": "PASS"},
    ]

    with (
        patch.object(sys, "argv", ["run_device.py", "--device", "R1"]),
        patch("scripts.run_device.load_dotenv"),
        patch("scripts.run_device.load_inventory", return_value={"devices": {"R1": {}}}),
        patch(
            "scripts.run_device.load_desired_state",
            return_value={"devices": {"R1": {}}},
        ),
        patch("scripts.run_device.configure_and_validate_device_netconf",
              return_value=results) as configure_device,
        patch.dict(
            "os.environ",
            {
                "GNMI_USERNAME": "test-user",
                "GNMI_PASSWORD": "test-password",
            },
            clear=False,
        ),
    ):
        exit_code = main()

    assert exit_code == 0

    configure_device.assert_called_once_with(
        device_name="R1",
        inventory={"devices": {"R1": {}}},
        desired_state={"devices": {"R1": {}}},
        username="test-user",
        password="test-password",
    )
