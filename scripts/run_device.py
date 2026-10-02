import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from src.desired.loader import load_desired_state
from src.inventory.loader import load_inventory
from src.workflow import configure_and_validate_device_netconf


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INVENTORY_FILE = (
    PROJECT_ROOT / "configs" / "inventory" / "devices.yaml"
)

DESIRED_STATE_FILE = (
    PROJECT_ROOT / "configs" / "desired" / "desired_state.yaml"
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the network automation workflow for one device."
    )
    parser.add_argument(
        "--device",
        required=True,
        help="Device name from the project inventory, for example R1.",
    )

    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]

    inventory = load_inventory(INVENTORY_FILE)
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    results = configure_and_validate_device_netconf(
        device_name=args.device,
        inventory=inventory,
        desired_state=desired_state,
        username=username,
        password=password,
    )

    print(json.dumps(results, indent=2))

    return 0 if all(
        result["status"] == "PASS"
        for result in results
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
