# Network Topology

## 1. Primary `network-automation-platform` Lab

The primary `network-automation-platform` environment is a three-router Nokia SR Linux topology running in Containerlab.

```text
                 R1
                /  \
               /    \
              /      \
             R2------R3
```

The lab provides management and IPv4 connectivity across the three routers. OSPF provides internal routing, while eBGP runs as a full mesh between all three routers. gNMI supports on-demand device-state retrieval and the separate streaming telemetry pipeline, while NETCONF provides model-driven configuration access.

See [Routing Protocols: OSPF and BGP](routing-protocols.md) for protocol configuration and verification details.

### Primary Lab Management Addressing

The three routers use fixed management IPv4 addresses on the Containerlab `clab` network. These addresses also match their generated gNMI TLS certificate identities.

| Router | Management IPv4 address |
| ------ | ----------------------- |
| R1     | `172.20.20.4`           |
| R2     | `172.20.20.2`           |
| R3     | `172.20.20.3`           |

The addresses are explicitly assigned through `mgmt-ipv4` in `topology/srl-lab.clab.yml`. Router startup configurations are maintained under `configs/srl/`.

### Router Link and Loopback Addressing

| Link | Subnet | First router | Second router |
|---|---|---|---|
| R1-R2 | `10.0.12.0/30` | R1: `10.0.12.1` | R2: `10.0.12.2` |
| R2-R3 | `10.0.23.0/30` | R2: `10.0.23.1` | R3: `10.0.23.2` |
| R3-R1 | `10.0.31.0/30` | R3: `10.0.31.2` | R1: `10.0.31.1` |

| Router | Loopback |
|---|---|
| R1 | `10.255.0.1/32` |
| R2 | `10.255.0.2/32` |
| R3 | `10.255.0.3/32` |

The loopbacks provide stable router identifiers and prefixes for routing verification.

### Lab Lifecycle and Readiness

Start and stop the primary lab from the repository root:

```bash
./scripts/lab_up.sh
./scripts/lab_down.sh
```

The CI workflow uses `scripts/wait_for_ospf.sh` to wait for the expected OSPF neighbors to reach the Full state before running live integration tests.

**TLS and management network considerations:**

- `lab_up.sh` reuses existing TLS artifacts during normal startup.
- `lab_down.sh` uses Containerlab's `--keep-mgmt-net` option to preserve the management network used by the telemetry containers.
- After redeployment, restart gNMIc if its subscriptions do not reconnect automatically:

```bash
docker restart gnmic
```

The destructive `--reconfigure` operation is not part of normal startup. It regenerates certificates and requires the gNMIc container to be recreated with the current CA certificate.

### Streaming Telemetry and Monitoring

The primary lab also supplies telemetry to the independent gNMIc, Prometheus, and Grafana monitoring stack. These services run as separate Docker containers and do not add Containerlab nodes or change the router topology.

The telemetry guide owns the OpenConfig subscriptions, TLS configuration, scrape settings, dashboard details, deployment steps, and validation results: [Streaming Telemetry and Monitoring](streaming-telemetry.md).

## 2. Expanded Topology Used by `network-test-validation-platform`

The `srl-expanded` Containerlab profile retains the three Nokia SR Linux routers and adds two Linux endpoints, H1 and H2, for end-to-end traffic testing.

```text
       H1                              H2
       |                               |
       R1-----------------------------R2
        \                             /
         \                           /
          \-----------R3------------/
```

The topology definition is `topology/srl-expanded.clab.yml`. Router startup configurations are stored under `configs/srl-expanded/`.

- H1 connects to R1 through `ethernet-1/3` and uses `10.0.14.2/30`.
- H2 connects to R2 through `ethernet-1/3` and uses `10.0.24.2/30`.
- Both endpoints use the `network-test-endpoint:1.0` Docker image, built from `topology/tcp-endpoint/Dockerfile`.
- Router containers use the `clab-srl-expanded-` naming prefix.

Build the endpoint image from the `network-automation-platform` repository root:

```bash
docker build -t network-test-endpoint:1.0 topology/tcp-endpoint
```

Deploy and stop the expanded topology:

```bash
./scripts/lab_expanded_up.sh
./scripts/lab_expanded_down.sh
```

`network-test-validation-platform` uses this profile for connectivity, interface and protocol checks, OSPF and route validation, LLDP neighbor validation, failure and recovery tests, TCP/UDP application exchanges, performance and latency measurements, controlled traffic impairments, and packet capture.

## 3. Project Boundary

`network-automation-platform` owns network automation and device-management workflows, while `network-test-validation-platform` owns network-behavior validation. The projects are maintained in separate repositories with independent workflows; the test-validation platform uses the expanded lab profile defined in this repository.
