# Network Automation & Programmability Platform

[![CI](https://github.com/kapiliyer10/network-automation-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/kapiliyer10/network-automation-platform/actions/workflows/ci.yml)

A Python-based network automation platform for Nokia SR Linux that implements a closed-loop, model-driven workflow: retrieve device state, normalize it, compare it with desired state, detect drift, apply configuration changes, and verify the result.

The platform combines **Python, gNMI, YANG, NETCONF, Jinja2, Ansible, FastAPI, Docker, pytest, and GitHub Actions** in a reproducible Containerlab environment.

## 1. Project Overview

The goal is to build a reusable network automation application rather than a collection of standalone scripts. Python owns the automation and validation logic; FastAPI exposes that workflow through a REST API, and Ansible provides an orchestration interface.

The central workflow is:

```text
Desired State + Device Inventory
              |
              v
      Discover Actual State
              |
              v
      Normalize Device Data
              |
              v
   Compare Desired vs Actual
              |
              v
       Detect Configuration Drift
              |
       +------+------+
       |             |
    No Drift       Drift
       |             |
       |             v
       |      Generate Configuration
       |             |
       |             v
       |       Apply Configuration
       |             |
       +------+------+
              |
              v
      Retrieve and Verify State
              |
              v
        Report Result
```

A successful configuration operation is not treated as proof of success by itself. The workflow retrieves state again and validates the result.

## 2. Key Features

- **Device inventory and endpoint discovery:** loads YAML inventory and resolves runtime device endpoints.
- **gNMI state discovery:** retrieves device state and converts device-specific responses into a normalized application model.
- **Streaming telemetry and observability:** uses gNMIc, OpenConfig, Prometheus, and Grafana to collect and visualize live SR Linux interface telemetry.
- **Desired-state management:** represents intended network configuration in YAML.
- **Drift detection:** compares desired and actual state and reports discrepancies.
- **Configuration generation:** renders SR Linux CLI configuration with Jinja2 and supports model-driven NETCONF/YANG configuration.
- **NETCONF verification:** applies configuration and supports configuration read-back and post-change verification.
- **Routing protocols:** the primary lab runs OSPF and a three-router eBGP full mesh. All six BGP sessions and route exchange were verified through the SR Linux CLI. The Python application manages BGP configuration but does not yet automate peer-state or route-table validation.
- **Orchestration and API:** integrates Ansible and exposes workflow operations through FastAPI.
- **Packaging and automation:** packages the application with Docker and runs tests through GitHub Actions.

## 3. Architecture

The application has separate access/orchestration interfaces, a Python automation workflow, and a Containerlab network environment. The Jinja2 CLI renderer is a separate configuration-rendering path; NETCONF is the primary model-driven live configuration path.

See **[System Architecture](docs/architecture.md)** for the component diagram, data flow, and configuration paths. The monitoring pipeline is documented in [Streaming Telemetry and Monitoring](docs/streaming-telemetry.md).

## 4. Network Lab

The primary `network-automation-platform` lab is a three-router Nokia SR Linux topology running in Containerlab:

```text
                 R1
                /  \
               /    \
              /      \
             R2------R3
```

It provides management connectivity, IPv4 connectivity, OSPF routing, gNMI access, and NETCONF access. The topology definition is `topology/srl-lab.clab.yml`; router startup configurations are under `configs/srl/`.

eBGP full mesh (AS 65001–65003) running; see `docs/routing-protocols.md`.

Start and stop the primary lab from the repository root:

```bash
./scripts/lab_up.sh
./scripts/lab_down.sh
```

### Relationship to `network-test-validation-platform`

`network-test-validation-platform`, the Network Test & Validation Platform, uses the separate `srl-expanded` profile. It retains the three SR Linux routers and adds Linux endpoints H1 and H2 for end-to-end traffic validation. `network-automation-platform` provides automation capabilities and lab infrastructure; `network-test-validation-platform` owns the network-behavior test suite.

See [Network Topology](docs/network-topology.md) for both lab profiles and their responsibilities.

## 5. Technology Stack

| Area | Technologies |
|---|---|
| Programming and environment | Python 3.12, Linux, YAML, Git |
| Network environment | Nokia SR Linux, Containerlab, Docker, IPv4, OSPF |
| Model-driven management | gNMI, YANG, NETCONF |
| Streaming telemetry and monitoring | gNMIc, OpenConfig, Prometheus, Grafana |
| Routing protocols | OSPF lab routing; BGP desired-state / NETCONF configuration and read-back validation |
| Configuration and orchestration | Jinja2, Ansible |
| Application interface | FastAPI, REST API, Uvicorn |
| Testing and CI/CD | pytest, GitHub Actions, live NETCONF integration tests |

## 6. Repository Structure

```text
.
├── .github/workflows/       # GitHub Actions CI workflow
├── ansible/                 # Ansible playbook and inventory
├── configs/
│   ├── desired/             # Desired network state
│   ├── inventory/           # Device inventory
│   └── srl/                 # Primary lab startup configuration
├── docs/                    # Architecture and technical documentation
├── generated/               # Rendered CLI configuration output
├── scripts/                 # Lab lifecycle and workflow entry points
├── src/
│   ├── api/                 # FastAPI application
│   ├── config/              # CLI and NETCONF configuration handling
│   ├── desired/             # Desired-state loading and comparison
│   ├── inventory/           # Inventory loading
│   ├── network/             # gNMI, NETCONF, state, and endpoint resolution
│   ├── reporting.py
│   └── workflow.py
├── templates/               # Jinja2 templates
├── telemetry/               # gNMIc and Prometheus configuration
├── tests/                   # Unit/application and integration tests
├── topology/                # Containerlab topology definitions and endpoint assets
├── Dockerfile
├── requirements.txt
└── README.md
```

## 7. Getting Started

### Prerequisites

- Linux environment
- Python 3.12
- Docker
- Containerlab
- Git

### Clone and install

```bash
git clone https://github.com/kapiliyer10/network-automation-platform.git
cd network-automation-platform

python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configure credentials

```bash
cp .env.example .env
```

Populate `.env` with the required local credentials. Do not commit `.env` or other secrets.

### Start the lab and wait for routing convergence

```bash
./scripts/lab_up.sh
./scripts/wait_for_ospf.sh
```

### Run tests and start the API

```bash
pytest -q
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

The API documentation is available through FastAPI's interactive documentation interface at `/docs` while the service is running.

### Stop the lab

```bash
./scripts/lab_down.sh
```

## 8. API Reference

The API is implemented in `src/api/main.py` and delegates to the existing Python workflow.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | API root; returns an informational message |
| `GET` | `/devices` | List inventory devices |
| `GET` | `/devices/{id}` | Retrieve one device from inventory |
| `GET` | `/devices/{id}/state` | Retrieve normalized device state |
| `POST` | `/devices/{id}/validate` | Validate a device against desired state |
| `POST` | `/devices/{id}/configure` | Reconcile a device with desired state |
| `GET` | `/drift` | Validate all devices and summarize drift |

Example requests:

```bash
curl http://127.0.0.1:8000/devices
curl http://127.0.0.1:8000/devices/R1/state
curl -X POST http://127.0.0.1:8000/devices/R1/validate
curl -X POST http://127.0.0.1:8000/devices/R1/configure
curl http://127.0.0.1:8000/drift
```

The `/devices/{id}/configure` endpoint performs desired-state reconciliation; it does not accept arbitrary configuration in the request body. See [FastAPI Reference](docs/fastapi-reference.md) for details.

## 9. Testing and CI/CD

Run the test suites locally:

```bash
# Application and non-integration tests
pytest -q --ignore=tests/integration

# Live network integration tests
pytest -q tests/integration

# Complete suite
pytest -q
```

**Latest verified full-suite result:** `100 passed in 87.47s` in the Docker-hosted test run recorded during project validation. Test duration and count can change as the environment and code evolve.

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on pushes and pull requests targeting `main`. It installs Containerlab and Python dependencies, starts the lab, waits for OSPF convergence, runs a Python compile check and both test groups, builds the Docker image, stops the lab, and uploads JUnit XML test results.

See [Testing and CI/CD](docs/testing-and-ci-cd.md) for the pipeline details and test scope.

## 10. Project Status and Documentation

**Core implementation: complete.** The platform includes state discovery, desired-state comparison, drift detection, configuration generation, NETCONF configuration and verification, Ansible orchestration, a FastAPI interface, Docker packaging, automated tests, and GitHub Actions CI/CD. The primary lab's three-router eBGP full mesh has been verified live: all six peer sessions reached Established and BGP routes were exchanged. The Python application supports BGP configuration management and read-back validation, but does not yet automate operational peer-state or route-table checks.

The RESTCONF demonstration remains deferred and is not part of the completed core workflow. No license file is currently specified for the repository.

**Streaming telemetry extension: complete.** The primary three-router lab now uses gNMIc, Prometheus, and Grafana for OpenConfig interface-counter and operational-status monitoring. See [Streaming Telemetry and Monitoring](docs/streaming-telemetry.md).

![SR Linux Streaming Telemetry Dashboard](docs/images/grafana-dashboard.png)

Detailed documentation:

- [System Architecture](docs/architecture.md)
- [Network Topology](docs/network-topology.md)
- [Routing Protocols: OSPF and BGP](docs/routing-protocols.md)
- [Desired State and Drift Detection](docs/desired-state-and-drift.md)
- [gNMI, NETCONF, and YANG](docs/gnmi-netconf-and-yang.md)
- [Streaming Telemetry and Monitoring](docs/streaming-telemetry.md)
- [Configuration Generation and Ansible](docs/configuration-and-ansible.md)
- [FastAPI Reference](docs/fastapi-reference.md)
- [Testing and CI/CD](docs/testing-and-ci-cd.md)
- [Milestones](docs/milestones.md)
