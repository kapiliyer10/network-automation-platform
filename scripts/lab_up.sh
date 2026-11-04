#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOPOLOGY="$PROJECT_ROOT/topology/srl-lab.clab.yml"

# Reuse the existing lab directory and TLS artifacts.
# A clean reconfiguration requires refreshing the gNMIc CA mount.
containerlab deploy -t "$TOPOLOGY"
