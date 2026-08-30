#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOPOLOGY="$PROJECT_ROOT/topology/srl-lab.clab.yml"

containerlab deploy --reconfigure -t "$TOPOLOGY"
