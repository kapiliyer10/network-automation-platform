from pathlib import Path

from src.desired.loader import load_desired_state

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DESIRED_STATE_FILE = (PROJECT_ROOT / "configs" / "desired" / "desired_state.yaml")

def test_desired_state_loads():
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    assert "devices" in desired_state
    assert set(desired_state["devices"]) == {"R1","R2","R3"}

def test_desired_state_contains_interfaces():
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    for device in desired_state["devices"].values():
        assert "interfaces" in device
        assert set(device["interfaces"]) == {
            "ethernet-1/1",
            "ethernet-1/2",
        }

def test_desired_state_contains_admin_state():
    desired_state = load_desired_state(DESIRED_STATE_FILE)

    for device in desired_state["devices"].values():
        for interfaces in device["interfaces"].values():
            assert interfaces["admin_state"] == "enable"
