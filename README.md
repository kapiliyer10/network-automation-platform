# Network Automation & Programmability Platform

[![CI](https://github.com/kapiliyer10/network-automation-platform/actions/workflows/ci.yml/badge.svg)](https://github.com/kapiliyer10/network-automation-platform/actions/workflows/ci.yml)

A Python-based network automation platform for Nokia SR Linux, developed and tested in a three-router Containerlab environment.

The platform automates device-state discovery, comparison against YAML-based desired configurations, configuration drift detection, and network configuration management. It uses gNMI to retrieve device state and NETCONF/YANG as the primary model-driven configuration mechanism. FastAPI provides REST API access, Ansible supports orchestration, and a separate telemetry pipeline uses gNMIc, Prometheus, and Grafana for network monitoring.

## 1. Project Overview

The platform follows a desired-state approach: it retrieves actual device state and compares it against the intended configuration. Detected discrepancies can be reconciled through configuration changes, followed by read-back verification.

### Core Automation Workflow

```mermaid
flowchart TD
    A["Desired State and Device Inventory<br/>YAML"]
    B["Python Automation Engine"]
    C["Retrieve Device State<br/>gNMI"]
    D["Normalize Device State"]
    E["Compare Desired and Actual State"]
    F{"Configuration Drift Detected?"}
    G["Apply Required Configuration<br/>NETCONF / YANG"]
    H["Read-back Verification"]
    I["Report: No Changes Required"]
    J["Report Configuration Result"]

    A --> B --> C --> D --> E --> F
    F -- No --> I
    F -- Yes --> G --> H --> J
```
## 2. Key Features

### Network State Discovery and Drift Detection

- **Device inventory and endpoint discovery:** Loads YAML-based device inventory and resolves runtime device endpoints.
- **gNMI state discovery:** Retrieves device state and normalizes device-specific responses into an application model.
- **Desired-state management:** Maintains intended network configurations in YAML.
- **Configuration drift detection:** Compares desired and actual device state to identify and report discrepancies.

### Configuration Management and Routing

- **NETCONF/YANG configuration:** Supports model-driven configuration deployment and configuration read-back verification.
- **Jinja2 configuration generation:** Renders Nokia SR Linux CLI configuration through a separate configuration-generation path.
- **Routing protocol configuration:** Supports OSPF and BGP configuration management. The three-router lab runs OSPF and an eBGP full mesh; all six BGP peer sessions and route exchange have been verified through the SR Linux CLI.

  **Current limitation:** The Python application does not yet automate operational BGP peer-state or route-table validation.

### API, Orchestration and CI/CD

- **REST API:** Exposes network automation workflows through FastAPI.
- **Automation orchestration:** Integrates Ansible to invoke automation workflows.
- **Containerization:** Uses Docker to package the application.
- **Automated testing and CI/CD:** Uses pytest and GitHub Actions to execute automated tests and validate changes.

### Streaming Telemetry and Observability

- **Telemetry collection:** Uses gNMIc and OpenConfig to collect SR Linux interface telemetry.
- **Metrics monitoring:** Uses Prometheus to collect and store telemetry metrics.
- **Visualization:** Uses Grafana dashboards to monitor interface counters and operational status.

## 3. Architecture

The platform separates its core automation workflow, management interfaces, and monitoring infrastructure.

- **Core automation:** The Python engine processes desired state, retrieves device state through gNMI, detects configuration drift, and manages configuration reconciliation.
- **Management interfaces:** FastAPI exposes the automation workflow through REST endpoints, while Ansible provides orchestration.
- **Configuration methods:** NETCONF/YANG is the primary mechanism for live model-driven configuration. Jinja2 provides a separate CLI configuration-rendering path.
- **Monitoring pipeline:** gNMIc collects streaming telemetry, Prometheus stores metrics, and Grafana provides visualization. This pipeline operates separately from the configuration workflow.

For detailed component diagrams and implementation flows, see [System Architecture](docs/architecture.md) and [Streaming Telemetry and Monitoring](docs/streaming-telemetry.md).

## 4. Network Lab

The platform is developed and tested on a three-router Nokia SR Linux topology deployed using Containerlab.

### Network Topology

```mermaid
flowchart TD
    R1["R1"]
    R2["R2"]
    R3["R3"]

    R1 ---|10.0.12.0/30| R2
    R1 ---|10.0.31.0/30| R3
    R2 ---|10.0.23.0/30| R3
```

### Routing and Management

- **OSPF:** Provides internal routing across the three-router topology.
- **eBGP:** A full-mesh peering arrangement runs across AS 65001–65003. All six BGP peer sessions and route exchange have been verified through the SR Linux CLI.
- **Management:** gNMI and NETCONF provide device access for state retrieval and configuration management.

The Containerlab topology is defined in `topology/srl-lab.clab.yml`, with router startup configurations maintained under `configs/srl/`.

### Related Network Test and Validation Project

A separate project, `network-test-validation-platform`, uses an expanded lab profile named `srl-expanded`. It retains the three SR Linux routers and adds Linux endpoints H1 and H2 for end-to-end traffic testing.

The responsibilities are separated:
- `network-automation-platform`: Network automation, device management, and configuration workflows.
- `network-test-validation-platform`: Network behavior testing and end-to-end validation.

See [Network Topology](docs/network-topology.md) for details about both lab profiles.

## 5. Technology Stack

| Category | Technologies |
|---|---|
| Programming and Development | Python 3.12, Linux, YAML, Git |
| Network Infrastructure | Nokia SR Linux, Containerlab, Docker, IPv4 |
| Routing Protocols | OSPF, BGP |
| Network Programmability | gNMI, NETCONF, YANG, OpenConfig |
| Configuration and Orchestration | Jinja2, Ansible |
| API Development | FastAPI, REST API, Uvicorn |
| Monitoring and Observability | gNMIc, Prometheus, Grafana |
| Testing and CI/CD | pytest, GitHub Actions |

## 6. Repository Structure

The repository is organized into application modules, network configuration, automation workflows, and supporting infrastructure.

```text
.
├── .github/workflows/       # GitHub Actions CI pipeline
├── ansible/                 # Ansible playbooks and inventory
├── configs/
│   ├── desired/             # Desired network configurations
│   ├── inventory/           # Network device inventory
│   └── srl/                 # Nokia SR Linux startup configurations
├── docs/                    # Architecture and technical documentation
├── generated/               # Generated CLI configuration files
├── scripts/                 # Lab lifecycle and automation scripts
├── src/
│   ├── api/                 # FastAPI application
│   ├── config/              # Configuration rendering and NETCONF handling
│   ├── desired/             # Desired-state loading and comparison
│   ├── inventory/           # Device inventory handling
│   ├── network/             # gNMI, NETCONF and device-state operations
│   ├── reporting.py         # Automation result reporting
│   └── workflow.py          # Core automation workflow
├── templates/               # Jinja2 configuration templates
├── telemetry/               # gNMIc and Prometheus configuration
├── tests/                   # Unit, application and integration tests
├── topology/                # Containerlab topology definitions
├── Dockerfile
├── requirements.txt
└── README.md
```

## 7. Getting Started

Follow these steps to set up the application, deploy the network lab, and run the automation platform locally.

### Prerequisites

- Linux environment
- Python 3.12
- Docker with the Docker daemon running
- Containerlab
- Git

### 1. Clone the Repository and Install Dependencies

```bash
git clone https://github.com/kapiliyer10/network-automation-platform.git
cd network-automation-platform

python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Credentials

Create your local environment file:

```bash
cp .env.example .env
```

Populate `.env` with the required credentials for your environment. Keep credentials and other secrets out of version control; do not commit `.env`.

### 3. Deploy the Network Lab

Start the three-router Nokia SR Linux topology and wait for OSPF convergence:

```bash
./scripts/lab_up.sh
./scripts/wait_for_ospf.sh
```

### 4. Run the Automated Tests

With the lab running and the virtual environment activated, execute the test suite:

```bash
pytest -q
```

### 5. Start the REST API

Start the FastAPI application:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

Once the service is running, access the interactive API documentation at:

`http://127.0.0.1:8000/docs`

Keep the API process running while using the endpoints. Stop it with `Ctrl+C` when finished.

### 6. Stop the Network Lab

After completing your work, shut down the Containerlab environment:

```bash
./scripts/lab_down.sh
```

## 8. API Reference

The platform exposes its network automation capabilities through a REST API built with FastAPI. The API is implemented in `src/api/main.py` and delegates operations to the existing Python automation workflow.

### Available Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/` | Returns an informational API message |
| `GET` | `/devices` | Lists devices from the inventory |
| `GET` | `/devices/{id}` | Retrieves inventory details for a device |
| `GET` | `/devices/{id}/state` | Retrieves normalized device state |
| `POST` | `/devices/{id}/validate` | Compares device state against desired configuration |
| `POST` | `/devices/{id}/configure` | Reconciles device configuration with desired state |
| `GET` | `/drift` | Checks all inventoried devices and summarizes configuration drift |

### Example API Requests

The following examples assume the API is running locally on port `8000`.

```bash
# List inventory devices
curl http://127.0.0.1:8000/devices

# Retrieve device state
curl http://127.0.0.1:8000/devices/R1/state

# Validate device configuration
curl -X POST http://127.0.0.1:8000/devices/R1/validate

# Reconcile device configuration
curl -X POST http://127.0.0.1:8000/devices/R1/configure

# Check configuration drift across devices
curl http://127.0.0.1:8000/drift
```

**Note:** The `/devices/{id}/validate` endpoint checks the device against its desired state. The `/devices/{id}/configure` endpoint performs desired-state reconciliation; it does not accept arbitrary configuration in the request body.

For endpoint implementation details and additional examples, see the [FastAPI Reference](docs/fastapi-reference.md).

## 9. Testing and CI/CD

The platform uses pytest for automated testing, including application-level tests and integration tests against the Containerlab network environment.

### Running Tests Locally

```bash
# Application and non-integration tests
pytest -q --ignore=tests/integration

# Live network integration tests
pytest -q tests/integration

# Complete test suite
pytest -q
```

### Test Results

**Previously recorded full-suite result:** `100 passed in 87.47s` during Docker-hosted project validation.

**Latest local full-suite result:** `102 passed in 96.56s` with Containerlab `0.75.0`. This run includes the updated Docker network resolver tests. The CI workflow is pinned to Containerlab `0.83.0`; that CI environment still requires verification.

The test suites cover application functionality and interactions with the live network lab, including network configuration and management workflows.

### Continuous Integration

GitHub Actions automates the validation workflow through `.github/workflows/ci.yml`. The pipeline runs on pushes and pull requests targeting `main` and performs the following steps:

1. Installs Containerlab and Python dependencies.
2. Deploys the network lab and waits for OSPF convergence.
3. Runs Python compilation checks and both application and integration test groups.
4. Builds the application Docker image.
5. Stops the network lab and uploads JUnit XML test results.

For detailed test coverage, execution procedures, and CI pipeline information, see [Testing and CI/CD](docs/testing-and-ci-cd.md).

## 10. Project Status

The core automation workflow and streaming telemetry extension have been implemented and verified in the primary three-router Nokia SR Linux lab.

### Implemented and Verified

- **Network automation:** Device-state discovery, desired-state comparison, drift detection, NETCONF configuration, and read-back verification.
- **Network environment:** Three-router OSPF topology and eBGP full-mesh connectivity. All six BGP peer sessions reached Established, and route exchange was verified through the SR Linux CLI.
- **Application integration:** FastAPI, Ansible, and Docker integration.
- **Testing and CI/CD:** Automated pytest suites and GitHub Actions pipeline.
- **Monitoring:** Streaming telemetry using gNMIc and OpenConfig, with Prometheus metrics and Grafana dashboards for interface counters and operational status.

### Scope and Limitations

The RESTCONF demonstration remains deferred and is not part of the completed core workflow. BGP operational peer-state and route-table validation limitations are documented under [Key Features](#2-key-features).

### Telemetry Dashboard

The following dashboard shows the streaming telemetry monitoring implemented for the three-router lab.

![SR Linux Streaming Telemetry Dashboard](docs/images/grafana-dashboard.png)

### Technical Documentation

The following documents provide additional implementation details:

| Area | Documentation |
|---|---|
| Architecture | [System Architecture](docs/architecture.md) |
| Network Design | [Network Topology](docs/network-topology.md) |
| Routing | [OSPF and BGP](docs/routing-protocols.md) |
| Configuration Management | [Desired State and Drift Detection](docs/desired-state-and-drift.md) |
| Network Programmability | [gNMI, NETCONF and YANG](docs/gnmi-netconf-and-yang.md) |
| Configuration and Orchestration | [Jinja2 and Ansible](docs/configuration-and-ansible.md) |
| API Development | [FastAPI Reference](docs/fastapi-reference.md) |
| Monitoring | [Streaming Telemetry and Monitoring](docs/streaming-telemetry.md) |
| Quality Assurance | [Testing and CI/CD](docs/testing-and-ci-cd.md) |
| Development Progress | [Project Milestones](docs/milestones.md) |
