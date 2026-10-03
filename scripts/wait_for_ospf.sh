#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

TIMEOUT=120
INTERVAL=5
START_TIME=$(date +%s)

echo "Waiting for OSPF convergence..."

while true; do
    if cd "$PROJECT_ROOT" && python - <<'PY'
import os
from pathlib import Path

from src.inventory.loader import load_inventory
from src.network.docker_resolver import resolve_container_ip
from src.network.gnmi_client import GNMIClient

project_root = Path.cwd()
inventory_file = project_root / "configs" / "inventory" / "devices.yaml"

inventory = load_inventory(inventory_file)

username = os.environ["GNMI_USERNAME"]
password = os.environ["GNMI_PASSWORD"]

for device_name, device in inventory["devices"].items():
    host = resolve_container_ip(device["container"])

    client = GNMIClient(
        host=host,
        port=57401,
        username=username,
        password=password,
    )

    neighbors = client.get_all_ospf_neighbors()

    if len(neighbors) != 2:
        raise RuntimeError(
            f"{device_name}: expected 2 OSPF neighbors, "
            f"found {len(neighbors)}"
        )

    if not all(neighbor["state"] == "full" for neighbor in neighbors):
        raise RuntimeError(
            f"{device_name}: not all OSPF neighbors are Full"
        )

print("OSPF convergence complete.")
PY
    then
        exit 0
    fi

    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))

    if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
        echo "ERROR: OSPF did not converge within ${TIMEOUT} seconds."
        exit 1
    fi

    echo "OSPF not ready yet. Retrying in ${INTERVAL}s..."
    sleep "$INTERVAL"
done
