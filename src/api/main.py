from pathlib import Path

from dotenv import load_dotenv
import os

from fastapi import FastAPI, HTTPException

from src.inventory.loader import load_inventory
from src.network.state import get_device_state
from src.desired.loader import load_desired_state
from src.workflow import (
    validate_device,
    configure_and_validate_device_netconf,
)
from src.workflow import validate_all_devices
from src.reporting import summarize_results

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_FILE = PROJECT_ROOT / "configs" / "inventory" / "devices.yaml"
load_dotenv()

app = FastAPI(
    title="Network Automation Platform",
    version="1.0.0",
)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Network Automation Platform API"
    }


@app.get("/devices")
def get_devices() -> dict:
    inventory = load_inventory(INVENTORY_FILE)

    return {
        "devices": inventory["devices"]
    }

@app.get("/devices/{device_id}")
def get_device(device_id: str) -> dict:
    inventory = load_inventory(INVENTORY_FILE)

    device = inventory["devices"].get(device_id)

    if device is None:
        raise HTTPException(
            status_code=404,
            detail=f"Device '{device_id}' not found",
        )

    return {
        "device": device_id,
        **device,
    }

@app.get("/devices/{device_id}/state")
def get_device_state_endpoint(device_id: str) -> dict:
    inventory = load_inventory(INVENTORY_FILE)

    device = inventory["devices"].get(device_id)

    if device is None:
        raise HTTPException(
            status_code=404,
            detail=f"Device '{device_id}' not found",
        )

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]

    state = get_device_state(
        device_name=device_id,
        inventory=inventory,
        username=username,
        password=password,
    )

    return {
        "device": device_id,
        "state": state,
    }

@app.post("/devices/{device_id}/validate")
def validate_device_endpoint(device_id: str) -> dict:
    inventory = load_inventory(INVENTORY_FILE)

    device = inventory["devices"].get(device_id)
    if device is None:
        raise HTTPException(
            status_code=404,
            detail=f"Device '{device_id}' not found",
        )

    desired_state = load_desired_state(
        PROJECT_ROOT / "configs" / "desired" / "desired_state.yaml"
    )

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]

    results = validate_device(
        device_name=device_id,
        inventory=inventory,
        desired_state=desired_state,
        username=username,
        password=password,
    )

    return {
        "device": device_id,
        "results": results,
    }

@app.post("/devices/{device_id}/configure")
def configure_device_endpoint(device_id: str) -> dict:
    inventory = load_inventory(INVENTORY_FILE)

    device = inventory["devices"].get(device_id)
    if device is None:
        raise HTTPException(
            status_code=404,
            detail=f"Device '{device_id}' not found",
        )

    desired_state = load_desired_state(
        PROJECT_ROOT / "configs" / "desired" / "desired_state.yaml"
    )

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]

    results = configure_and_validate_device_netconf(
        device_name=device_id,
        inventory=inventory,
        desired_state=desired_state,
        username=username,
        password=password,
    )

    return {
        "device": device_id,
        "results": results,
    }

@app.get("/drift")
def get_drift() -> dict:
    inventory = load_inventory(INVENTORY_FILE)

    desired_state = load_desired_state(
        PROJECT_ROOT / "configs" / "desired" / "desired_state.yaml"
    )

    username = os.environ["GNMI_USERNAME"]
    password = os.environ["GNMI_PASSWORD"]

    results = validate_all_devices(
        inventory=inventory,
        desired_state=desired_state,
        username=username,
        password=password,
    )

    return summarize_results(results)
