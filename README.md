# Network Automation & Programmability Platform

A Python-based network automation platform that implements a closed-loop, model-driven network management workflow:

**Discover → Retrieve State → Normalize → Compare Desired vs Actual → Detect Drift → Generate Configuration → Apply Configuration → Verify → Expose through REST API → Run through CI/CD**

The platform uses a reproducible Containerlab-based Nokia SR Linux environment and combines gNMI, YANG, OpenConfig where applicable, NETCONF, Jinja2, Ansible, FastAPI, Docker, pytest, and GitHub Actions.

---

## 1. Project Objective

The goal of this project is to build a reusable network automation platform rather than a collection of standalone scripts.

The core workflow is:

```text
Desired State
      │
      ▼
Discover Actual State
      │
      ▼
Normalize Network Data
      │
      ▼
Compare Desired vs Actual
      │
      ├───────────────┐
      │               │
      ▼               ▼
    PASS             DRIFT
      │               │
      │               ▼
      │       Generate Configuration
      │               │
      │               ▼
      │        Apply Configuration
      │               │
      └───────┬───────┘
              ▼
       Retrieve Actual State
              │
              ▼
            Verify
              │
           PASS / FAIL
              │
              ▼
        Expose through API
              │
              ▼
             CI/CD
```

The important design principle is that configuration application is followed by explicit state retrieval and validation. A successful configuration operation by itself is not treated as proof that the desired network state has been achieved.

---

## 2. Architecture

```text
                              FastAPI
                                 │
                                 ▼
                         Workflow / Reporting
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
       State Discovery       Validation       Configuration
              │                  │                  │
              ▼                  ▼                  ▼
            gNMI             Comparison          NETCONF
              │                  │                  │
              ▼                  ▼                  ▼
        YANG / device       Desired State       NETCONF/YANG
        data retrieval          │
              │                  │
              └──────────────┬───┘
                             ▼
                    Normalized Application
                           State Model
                             │
                             ▼
                       SR Linux Devices
                             │
                         Containerlab
```

Ansible sits beside the Python application as an orchestration layer:

```text
                 Ansible
                    │
                    ▼
          Python Automation Workflow
                    │
                    ▼
                 Devices
```

Python owns the application and network-automation business logic. Ansible invokes and orchestrates the existing Python workflow instead of duplicating networking logic.

---

## 3. Normalized Internal Data Model

A key architectural feature is the separation of device-specific responses from application/business logic.

The intended pattern is:

```text
Device
  │
  ▼
gNMI / YANG
  │
  ▼
Device-specific response
  │
  ▼
Parser / Adapter
  │
  ▼
Normalized application model
  │
  ├── Validation
  ├── Comparison
  ├── Reporting
  ├── Configuration workflow
  └── REST API
```

Examples of normalized data include:

```json
{
  "name": "ethernet-1/1",
  "admin_state": "enable",
  "oper_state": "up"
}
```

and:

```json
{
  "interface": "ethernet-1/1",
  "subinterface_index": 0,
  "ip_address": "10.0.12.1/30",
  "origin": "static",
  "status": "preferred"
}
```

This keeps vendor/device-specific details inside the network layer and allows the rest of the application to operate on stable internal structures.

---

## 4. Technology Stack

### Programming and Environment

- Python 3.12
- Linux
- YAML
- Git
- Docker

### Networking

- IPv4
- Ethernet
- Routing
- OSPF
- Network device state

### Model-Driven Network Management

- YANG
- gNMI
- OpenConfig where applicable
- NETCONF
- RESTCONF as a secondary/deferred demonstration

### Configuration and Orchestration

- Jinja2
- Ansible

### Application Layer

- FastAPI
- REST API
- Uvicorn

### Testing and CI/CD

- pytest
- GitHub Actions
- Docker image build
- Live NETCONF integration testing

---

## 5. Network Lab

The project uses a three-router Nokia SR Linux topology running in Containerlab.

```text
                 R1
                /  \
               /    \
              /      \
             R2------R3
```

The lab provides:

- Management connectivity
- IPv4 connectivity
- OSPF routing
- Observable device state
- gNMI access
- NETCONF access

The Containerlab topology is:

```text
topology/srl-lab.clab.yml
```

The startup configurations are:

```text
configs/srl/
├── R1.cli
├── R2.cli
└── R3.cli
```

The lab can be brought up and down using the project scripts:

```bash
./scripts/lab_up.sh
./scripts/lab_down.sh
```

---

## 6. Repository Structure

```text
.
├── ansible/
│   ├── ansible.cfg
│   ├── configure_devices.yml
│   └── inventory.ini
│
├── configs/
│   ├── desired/
│   │   └── desired_state.yaml
│   ├── inventory/
│   │   └── devices.yaml
│   └── srl/
│       ├── R1.cli
│       ├── R2.cli
│       └── R3.cli
│
├── scripts/
│   ├── __init__.py
│   ├── lab_down.sh
│   ├── lab_up.sh
│   ├── run_device.py
│   └── wait_for_ospf.sh
│
├── src/
│   ├── api/
│   │   └── main.py
│   ├── config/
│   │   ├── netconf_applier.py
│   │   ├── netconf_renderer.py
│   │   └── renderer.py
│   ├── desired/
│   │   ├── comparator.py
│   │   ├── loader.py
│   │   └── validator.py
│   ├── inventory/
│   │   └── loader.py
│   ├── network/
│   │   ├── docker_resolver.py
│   │   ├── gnmi_client.py
│   │   ├── netconf_client.py
│   │   └── state.py
│   ├── reporting.py
│   └── workflow.py
│
├── templates/
│   └── srlinux/
│       └── interfaces.cli.j2
│
├── tests/
│   ├── integration/
│   │   ├── test_netconf_applier.py
│   │   └── test_netconf_client.py
│   └── test_*.py
│
├── topology/
│   └── srl-lab.clab.yml
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
└── requirements.txt
```

---

## 7. Milestone Summary

### Milestone 1 — Network Lab Foundation

Built a reproducible three-router Containerlab environment with SR Linux, IPv4 connectivity, management connectivity, OSPF, and observable device state.

**Status: Complete**

### Milestone 2 — Inventory & Endpoint Discovery

Implemented reusable YAML inventory loading and dynamic endpoint resolution while keeping logical device identity separate from the current runtime endpoint.

**Status: Complete**

### Milestone 3 — Device State Discovery

Implemented reusable device-state discovery using gNMI and YANG-backed device data.

The normalized state includes:

- Hostname
- Interfaces
- Interface administrative state
- Interface operational state
- IPv4 addresses
- Routes
- OSPF neighbors
- OSPF configuration

**Status: Complete**

### Milestone 4 — Desired State

Defined intended network state using YAML and added desired-state loading and validation.

**Status: Complete**

### Milestone 5 — State Comparison & Drift Detection

Implemented desired-versus-actual comparison and reporting of:

- PASS
- DRIFT

**Status: Complete**

### Milestone 6 — Configuration Generation

Implemented configuration rendering using YAML and Jinja2 for SR Linux CLI configuration.

**Status: Complete**

### Milestone 7 — Model-Driven Configuration

Implemented the primary model-driven configuration workflow using NETCONF + YANG.

The workflow is:

```text
Desired State
      ↓
NETCONF Configuration Generation
      ↓
edit-config
      ↓
commit
      ↓
Retrieve Actual State
      ↓
Verify
```

**Status: Complete**

### Milestone 8 — RESTCONF Demonstration

RESTCONF remains part of the project scope as a secondary model-driven technology, but it has intentionally not been expanded into a second large implementation.

**Status: Deferred / Secondary**

### Milestone 9 — Ansible Integration

Integrated Ansible specifically for orchestration. The playbook invokes the existing Python automation workflow.

**Status: Complete**

### Milestone 10 — FastAPI REST API

Exposed the automation functionality through a REST API without duplicating networking logic.

**Status: Complete**

### Milestone 11 — Docker Packaging

Packaged the automation application with Python, FastAPI, supporting libraries, and the existing automation code.

The network lab remains separate from the automation application.

**Status: Complete**

### Milestone 12 — CI/CD

Implemented GitHub Actions to:

```text
Git Push / Pull Request
        ↓
Compile / Lint Check
        ↓
Application Tests
        ↓
NETCONF Integration Tests
        ↓
Docker Build
        ↓
Publish Test Results
```

The CI workflow also waits for OSPF convergence before live integration testing.

**Status: Complete**

### Milestone 13 — End-to-End Automation Workflow

Combined the major components into the closed-loop automation workflow:

```text
Desired State
      ↓
Discover Actual State
      ↓
Detect Drift
      ↓
Generate Configuration
      ↓
Apply Configuration
      ↓
Retrieve State
      ↓
Verify
      ↓
PASS / FAIL
```

**Status: Complete**

---

## 8. Inventory

Device inventory is stored in:

```text
configs/inventory/devices.yaml
```

The inventory identifies logical devices and their Containerlab-related information.

The application resolves current management endpoints dynamically from the running environment. This avoids making the higher-level workflow dependent on fixed runtime container IP addresses.

---

## 9. Desired State

The intended network state is stored in:

```text
configs/desired/desired_state.yaml
```

The desired state covers resources such as:

- Interface administrative state
- Interface description
- IPv4 configuration
- Network-instance interfaces
- OSPF configuration

The desired-state loader converts the YAML definition into the representation consumed by the comparison and configuration workflows.

---

## 10. State Discovery

The state layer retrieves device state through the gNMI client.

The normalized device-state layer exposes:

```text
hostname
interfaces
ip_addresses
routes
ospf_neighbors
ospf
```

Interface state includes fields such as:

```text
name
admin_state
oper_state
```

IPv4 address data includes fields such as:

```text
interface
subinterface_index
ip_address
origin
status
```

Route data includes fields such as:

```text
prefix
active
metric
preference
route_type
```

OSPF neighbor data includes:

```text
interface
router_id
address
state
```

---

## 11. Drift Detection

The comparison workflow evaluates:

```text
Desired State
      +
Actual State
      ↓
Comparison Engine
      ↓
PASS / DRIFT
```

A controlled mismatch can look like:

```text
Interface: ethernet-1/2

Desired:  enable
Actual:   disable
Status:   DRIFT
```

The reporting layer summarizes per-device and overall results.

Example:

```json
{
  "devices": {
    "R1": {
      "status": "DRIFT",
      "total": 12,
      "passed": 11,
      "drifted": 1
    },
    "R2": {
      "status": "PASS",
      "total": 12,
      "passed": 12,
      "drifted": 0
    },
    "R3": {
      "status": "PASS",
      "total": 12,
      "passed": 12,
      "drifted": 0
    }
  },
  "overall_status": "DRIFT"
}
```

---

## 12. Configuration Generation

The repository contains two configuration-generation paths.

### Jinja2 path

The Jinja2 renderer generates SR Linux CLI configuration.

```text
Desired State
      ↓
Jinja2 Template
      ↓
Generated CLI Configuration
```

Template:

```text
templates/srlinux/interfaces.cli.j2
```

Generated configuration can be written under:

```text
generated/
```

The CLI-rendering path is separate from the primary NETCONF application path.

### NETCONF path

The primary live configuration workflow builds NETCONF `edit-config` payloads from desired state.

The NETCONF configuration layer:

1. Builds the required configuration payloads.
2. Sends the payloads through the NETCONF client.
3. Commits the candidate configuration.
4. Performs validation against the resulting device state.

---

## 13. NETCONF and YANG

NETCONF is the primary model-driven configuration mechanism in the completed workflow.

The application uses NETCONF operations such as:

```text
edit-config
commit
```

The client also retrieves configuration/state needed for round-trip verification.

The design goal is:

```text
Desired State
      ↓
Model-driven configuration
      ↓
Device
      ↓
Actual State
      ↓
Comparison
      ↓
PASS / DRIFT
```

---

## 14. Ansible Integration

Ansible is used for orchestration rather than as the location of the core network logic.

The main playbook is:

```text
ansible/configure_devices.yml
```

Run it with:

```bash
ansible-playbook -i ansible/inventory.ini ansible/configure_devices.yml
```

The playbook invokes the existing Python workflow:

```text
Ansible
   ↓
python -m scripts.run_device
   ↓
Python automation engine
   ↓
Device
```

This keeps state handling, comparison, configuration generation, NETCONF operations, validation, and reporting centralized in Python.

---

## 15. FastAPI REST API

The API is implemented in:

```text
src/api/main.py
```

Start the API directly with:

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | API root/health message |
| GET | `/devices` | List devices from inventory |
| GET | `/devices/{id}` | Get a specific device |
| GET | `/devices/{id}/state` | Retrieve normalized device state |
| POST | `/devices/{id}/validate` | Validate device against desired state |
| POST | `/devices/{id}/configure` | Reconcile a device with desired state |
| GET | `/drift` | Validate all devices and summarize drift |

Example:

```bash
curl http://127.0.0.1:8000/
```

List devices:

```bash
curl http://127.0.0.1:8000/devices
```

Get device state:

```bash
curl http://127.0.0.1:8000/devices/R1/state
```

Validate a device:

```bash
curl -X POST http://127.0.0.1:8000/devices/R1/validate
```

Reconcile a device:

```bash
curl -X POST http://127.0.0.1:8000/devices/R1/configure
```

Check overall drift:

```bash
curl http://127.0.0.1:8000/drift
```

### Important API behavior

The current `/devices/{id}/configure` endpoint performs **desired-state reconciliation**.

It does not accept arbitrary user-supplied configuration in the request body.

The API delegates to the existing workflow/configuration modules rather than directly implementing separate device configuration logic.

---

## 16. Docker

The automation application is packaged using Docker.

### Build

```bash
docker build -t network-automation-platform .
```

### Run

```bash
docker run -d \
  --name network-automation-api \
  --network clab \
  -p 8000:8000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --env-file .env \
  network-automation-platform
```

The image runs:

```text
uvicorn src.api.main:app
```

on port `8000`.

The Docker image contains the Python application and its required supporting libraries. The Containerlab network environment remains separate.

---

## 17. Environment Variables and Secrets

The repository contains:

```text
.env.example
```

Create your local environment file with:

```bash
cp .env.example .env
```

Set the required credentials in `.env`.

The actual `.env` file is intentionally ignored by Git.

Do not commit credentials or other secrets.

GitHub Actions receives the required gNMI credentials through repository secrets:

```text
GNMI_USERNAME
GNMI_PASSWORD
```

---

## 18. Testing Strategy

The project uses pytest at both application and live network-integration levels.

### Application/non-integration tests

```bash
pytest -q --ignore=tests/integration
```

### Integration tests

```bash
pytest -q tests/integration
```

### Full suite

```bash
pytest -q
```

The integration tests use the real Containerlab SR Linux environment and validate live NETCONF round trips.

Coverage areas include:

- Inventory loading
- Docker endpoint resolution
- gNMI client operations
- Device state discovery
- Desired-state loading
- State comparison
- Drift detection
- CLI configuration rendering
- NETCONF configuration rendering
- NETCONF application
- Workflow execution
- Reporting
- FastAPI endpoints

### Latest verified result

The complete Docker-hosted pytest run was:

```text
83 passed in 75.71s
```

The live NETCONF integration suite was:

```text
8 passed in 63.68s
```

A focused application/API/workflow/reporting run was:

```text
12 passed in 1.00s
```

These numbers reflect the verified project state during final integration testing and may change as tests are added or modified.

---

## 19. CI/CD

The GitHub Actions workflow is:

```text
.github/workflows/ci.yml
```

It runs on:

- Pushes to `main`
- Pull requests targeting `main`

The pipeline is:

```text
Checkout repository
        ↓
Install Containerlab
        ↓
Prepare repository path for lab
        ↓
Set up Python 3.12
        ↓
Install dependencies
        ↓
Start Containerlab network
        ↓
Wait for OSPF convergence
        ↓
Compile/lint check
        ↓
Run non-integration pytest tests
        ↓
Run live integration tests
        ↓
Build Docker image
        ↓
Stop network lab
        ↓
Publish pytest result artifacts
```

The OSPF readiness step prevents live integration tests from starting before the routing control plane has converged.

---

## 20. OSPF Convergence Check

The project includes:

```text
scripts/wait_for_ospf.sh
```

Before the CI integration tests execute, this script waits for the three-router OSPF topology to become ready.

The readiness condition requires the expected OSPF neighbors to be present and in the `full` state.

This makes the integration test environment deterministic enough for CI execution.

---

## 21. End-to-End Demonstration

The strongest project demonstration is a controlled drift-and-reconciliation workflow.

### Step 1 — Verify clean state

```bash
curl http://127.0.0.1:8000/drift
```

Expected logical result:

```text
R1  PASS
R2  PASS
R3  PASS

Overall: PASS
```

### Step 2 — Introduce controlled drift

A controlled change can be made to an existing device setting so that the actual state differs from the desired state.

Example:

```text
R1
ethernet-1/2

Desired admin state: enable
Actual admin state:  disable
```

The drift endpoint then reports:

```text
R1  DRIFT
R2  PASS
R3  PASS

Overall: DRIFT
```

### Step 3 — Reconcile

Run:

```bash
curl -X POST http://127.0.0.1:8000/devices/R1/configure
```

The workflow:

```text
Desired State
      ↓
Build NETCONF configuration
      ↓
edit-config
      ↓
commit
      ↓
Retrieve actual state
      ↓
Validate
```

### Step 4 — Verify recovery

Run:

```bash
curl http://127.0.0.1:8000/drift
```

Expected result after successful reconciliation:

```text
R1  PASS
R2  PASS
R3  PASS

Overall: PASS
```

This demonstrates the project's closed-loop behavior:

**Detect → Correct → Verify**

rather than merely sending configuration to devices.

---

## 22. Running the Project Locally

### Prerequisites

Install:

- Linux
- Python 3.12
- Docker
- Containerlab
- Git

### Clone the repository

```bash
git clone https://github.com/kapiliyer10/network-automation-platform.git
cd network-automation-platform
```

### Create a virtual environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Create local environment configuration

```bash
cp .env.example .env
```

Populate `.env` with the required credentials.

### Start the network lab

```bash
./scripts/lab_up.sh
```

### Wait for OSPF convergence

```bash
./scripts/wait_for_ospf.sh
```

### Run tests

```bash
pytest -q
```

### Start FastAPI

```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Stop the lab

```bash
./scripts/lab_down.sh
```

---

## 23. Running the Python Workflow Directly

A device-specific workflow can also be invoked from the command line:

```bash
python -m scripts.run_device --device R1
```

The command executes the Python automation workflow and reports the resulting validation records.

---

## 24. Design Decisions

### Why normalize state?

Raw device responses can contain vendor-specific structures. Normalization keeps higher-level application logic independent of those structures.

### Why use gNMI for state retrieval?

The completed project uses gNMI as the primary state-discovery mechanism and exposes a reusable normalized device-state layer.

### Why use NETCONF for configuration?

NETCONF provides the primary model-driven configuration path and supports the closed-loop requirement:

```text
Configure → Retrieve → Verify
```

### Why keep Ansible?

Ansible provides an orchestration mechanism for repeated and multi-device execution while Python remains the owner of the actual automation logic.

### Why expose FastAPI?

The REST API provides an application-facing interface to the existing automation workflow.

### Why use Docker?

Docker packages the automation application in a reproducible runtime environment while keeping the actual network lab separate.

### Why use live integration tests?

Application-level tests cannot fully prove that NETCONF operations work against a real network device. The live integration suite validates the actual network-management path against the Containerlab SR Linux environment.

---

## 25. Scope Boundaries

The project intentionally keeps the core implementation focused.

### Included

- Network state discovery
- Desired-state modeling
- Drift detection
- Configuration generation
- NETCONF configuration
- Verification
- Ansible orchestration
- FastAPI API
- Docker packaging
- pytest
- GitHub Actions
- Containerlab-based integration environment

### Secondary / Deferred

- RESTCONF as a small demonstration rather than a second large implementation
- Additional network resource types
- Expanded deployment automation

The objective is to make the existing technologies work together as a complete engineering workflow rather than continuously adding unrelated technologies.

---

## 26. Future Extensions

Potential future extensions include:

- A small RESTCONF state/configuration demonstration
- Additional YANG-modeled network resources
- More configuration resources in desired state
- More live integration tests
- Additional CI/CD stages
- Cloud/IaC integration when relevant to a specific target role

These are extensions to the completed core platform, not prerequisites for the current project.

---

## 27. Portfolio Narrative

This project demonstrates the ability to build and integrate a network automation system using software-engineering practices.

The core story is:

```text
Network Device
      ↓
Model-Driven State Discovery
      ↓
Normalized Application State
      ↓
Desired-State Comparison
      ↓
Drift Detection
      ↓
Model-Driven Configuration
      ↓
Post-Change Verification
      ↓
REST API
      ↓
Ansible Orchestration
      ↓
Docker
      ↓
CI/CD
```

The result is a reusable **Network Automation / NetDevOps platform** rather than a set of isolated networking scripts.

---

## 28. Project Highlights

- Reproducible three-router SR Linux lab
- Dynamic device endpoint discovery
- gNMI-based state retrieval
- YANG/model-driven network management
- Normalized internal state model
- Desired-state representation in YAML
- Automated drift detection
- Jinja2 CLI configuration rendering
- NETCONF + YANG configuration
- Post-configuration verification
- Ansible orchestration
- FastAPI REST API
- Dockerized automation application
- pytest unit/application testing
- Live NETCONF integration testing
- GitHub Actions CI/CD
- OSPF-aware CI readiness checking
- End-to-end drift remediation demonstration

---

## 29. Status

**Project 1 — Network Automation & Programmability Platform: Core implementation complete.**

The main closed-loop workflow has been implemented, tested, containerized, exposed through an API, integrated with Ansible, and executed through CI/CD.

The primary remaining item is the intentionally limited RESTCONF demonstration.

---

## 30. License

No license has been specified for this repository.
