# gNMI, NETCONF, and YANG

## 1. Management-Plane Overview

Project 1 uses gNMI as the primary mechanism for operational state discovery and NETCONF as the primary model-driven configuration mechanism. YANG provides the data-model foundation for structured device management.

## 2. gNMI State Discovery

The Python gNMI client retrieves device information from the Nokia SR Linux lab. The state layer parses device-specific responses and exposes normalized application structures. This on-demand state-discovery path is separate from the continuous gNMIc streaming telemetry pipeline described in Section 4.

The documented normalized state includes hostname, interfaces, IPv4 addresses, routes, OSPF neighbors, and OSPF configuration.

The normalization boundary keeps higher-level comparison and reporting logic separate from raw device responses.

## 3. NETCONF Configuration

The NETCONF configuration path builds configuration payloads from desired state and applies them to SR Linux devices.

The workflow uses operations such as:

```text
edit-config
commit
```

The project also supports configuration read-back and post-change validation. The intended lifecycle is:

```text
Desired State
      |
      v
NETCONF Configuration Rendering
      |
      v
Apply Configuration
      |
      v
Read Back Device Configuration / State
      |
      v
Compare and Verify
```

## 4. Streaming Telemetry with gNMIc

In addition to the Python application's on-demand gNMI state-discovery client, Project 1 includes a separate streaming telemetry pipeline based on gNMIc.

The pipeline collects telemetry from R1, R2, and R3 in the primary three-router Containerlab topology.

### Verified OpenConfig subscriptions

The current implementation subscribes to two OpenConfig paths for interface `ethernet-1/1` on each router:

| Telemetry | OpenConfig path |
|---|---|
| Incoming octets | `openconfig:/interfaces/interface[name=ethernet-1/1]/state/counters/in-octets` |
| Operational status | `openconfig:/interfaces/interface[name=ethernet-1/1]/state/oper-status` |

The subscriptions use gNMI STREAM mode with SAMPLE streaming and a five-second sample interval. The collector connects to the secure gNMI endpoint on TCP port `57400`, using CA certificate validation and credentials supplied through environment variables.

### Telemetry collection and visualization

The collection pipeline is:

gNMI-enabled SR Linux routers → gNMIc → Prometheus → Grafana

- **gNMIc** maintains the streaming subscriptions and exposes the received telemetry as Prometheus metrics on HTTP port `9804`, at `/metrics`.
- **Prometheus** scrapes the gNMIc metrics endpoint every 15 seconds and stores the time-series data.
- **Grafana** queries Prometheus and displays the `SR Linux Streaming Telemetry` dashboard.

The dashboard contains panels for incoming traffic rates, cumulative incoming octets, and interface operational status across R1, R2, and R3.

The gNMIc and Prometheus configuration files are maintained under `telemetry/`.

This monitoring pipeline is independent of the Python application's state-discovery and NETCONF configuration workflow. Only the two OpenConfig paths listed above have been verified on all three routers; advertised model support does not establish that every possible OpenConfig path is implemented or tested.

## 5. gNMI and NETCONF Responsibilities

| Mechanism | Project responsibility |
|---|---|
| gNMI (Python client) | Retrieve operational state for application discovery and normalization |
| gNMIc | Collect streaming OpenConfig telemetry and expose Prometheus metrics |
| YANG | Provides structured models for network data and configuration |
| NETCONF | Apply model-driven configuration and support read-back / verification |

The Python application's implemented state-discovery and NETCONF configuration workflows use Nokia SR Linux's native YANG models. The separate gNMIc monitoring pipeline uses the explicitly verified OpenConfig interface paths listed in Section 4. This documentation does not imply that every resource uses OpenConfig or that every operational protocol state is discovered.
