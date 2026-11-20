# gNMI, NETCONF, and YANG

## 1. Management-Plane Overview

`network-automation-platform` uses gNMI as the primary mechanism for operational state discovery and NETCONF as the primary model-driven configuration mechanism. YANG provides the data-model foundation for structured device management.

## 2. gNMI State Discovery

The Python gNMI client retrieves device information from the Nokia SR Linux lab. The state layer parses device-specific responses and exposes normalized application structures. This on-demand state-discovery path is separate from the continuous gNMIc streaming telemetry pipeline described in Section 4.

The documented normalized state includes hostname, interfaces, IPv4 addresses, routes, OSPF neighbors, and OSPF configuration.

This normalization keeps comparison and reporting logic independent of raw, device-specific gNMI responses.

## 3. NETCONF Configuration

The NETCONF configuration path builds payloads from desired state, applies them to SR Linux devices, commits the changes, and supports configuration read-back and post-change validation. The detailed configuration paths, including Jinja2 CLI generation and Ansible orchestration, are documented in [Configuration Generation and Ansible](configuration-and-ansible.md).

## 4. Streaming Telemetry with gNMIc

The platform uses gNMIc for continuous OpenConfig telemetry subscriptions, independently of the Python client's on-demand gNMI state-discovery workflow. The verified subscriptions and their implementation are documented in [Streaming Telemetry and Monitoring](streaming-telemetry.md).

## 5. gNMI and NETCONF Responsibilities

| Mechanism | Project responsibility |
|---|---|
| gNMI (Python client) | Retrieve operational state for application discovery and normalization |
| gNMIc | Collect streaming OpenConfig telemetry and expose Prometheus metrics |
| YANG | Provides structured models for network data and configuration |
| NETCONF | Apply model-driven configuration and support read-back / verification |

The Python application's implemented state-discovery and NETCONF configuration workflows use Nokia SR Linux's native YANG models. The separate gNMIc monitoring pipeline uses the explicitly verified OpenConfig interface paths listed in Section 4. This documentation does not imply that every resource uses OpenConfig or that every operational protocol state is discovered.
