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

The lab provides:

- Management connectivity
- IPv4 connectivity
- OSPF routing
- gNMI access for state discovery
- Streaming OpenConfig telemetry for interface counters and operational status
- NETCONF access for model-driven configuration

The primary lab uses OSPF for internal routing and a three-router eBGP full mesh. See [Routing Protocols: OSPF and BGP](routing-protocols.md) for configuration details and the verified operational state.

### Primary Lab Management Addressing

The three routers use fixed management IPv4 addresses in the Containerlab `clab` network. These addresses also match their generated gNMI TLS certificate identities.

| Router | Management IPv4 address |
|---|---|
| R1 | `172.20.20.4` |
| R2 | `172.20.20.2` |
| R3 | `172.20.20.3` |

The addresses are explicitly assigned through `mgmt-ipv4` in `topology/srl-lab.clab.yml`.

The topology definition is `topology/srl-lab.clab.yml`. Router startup configurations are stored under `configs/srl/`.

Start and stop the primary lab from the repository root:

```bash
./scripts/lab_up.sh
./scripts/lab_down.sh
```

The CI workflow uses `scripts/wait_for_ospf.sh` to wait for the expected OSPF neighbors to reach the Full state before live integration tests run.

For the normal lab lifecycle, `lab_up.sh` reuses the existing TLS artifacts and `lab_down.sh` uses Containerlab's `--keep-mgmt-net` option. This preserves the management network used by the external telemetry containers. After redeployment, restart gNMIc if its subscriptions do not reconnect automatically:

```bash
docker restart gnmic
```

A destructive `--reconfigure` operation is not part of the normal startup procedure. It regenerates certificates and requires the gNMIc container to be recreated with the current CA certificate.



### Streaming Telemetry and Monitoring

The primary three-router lab also runs a separate streaming telemetry pipeline. It monitors `ethernet-1/1` on R1, R2, and R3 without requiring the expanded `network-test-validation-platform` topology or its Linux endpoints.

The monitoring data flow is:

```text
R1 / R2 / R3
     |
     | Secure gNMI STREAM subscriptions
     v
   gNMIc
     |
     | Prometheus metrics (:9804/metrics)
     v
 Prometheus (:9090)
     |
     v
 Grafana (:3000)
```

The monitoring components run as Docker containers on the `clab` network alongside the primary lab.

| Component | Role | Endpoint |
|---|---|---|
| gNMIc | Collects OpenConfig telemetry from all three routers | Metrics exporter on port `9804` |
| Prometheus | Scrapes and stores telemetry time series | Port `9090` |
| Grafana | Displays the SR Linux Streaming Telemetry dashboard | Port `3000`, bound to host loopback |

The gNMIc subscriptions use the secure gNMI endpoint on TCP port `57400`, with TLS CA validation and credentials supplied through environment variables. Interface telemetry is sampled every five seconds; Prometheus scrapes the exporter every 15 seconds.

Relevant configuration files:

- `telemetry/gnmic.yaml`
- `telemetry/prometheus.yml`

The monitoring pipeline is independent of the Python automation workflow. Its detailed configuration, verified OpenConfig paths, dashboard panels, and validation results are documented in [Streaming Telemetry and Monitoring](streaming-telemetry.md).

## 2. Expanded Topology Used by `network-test-validation-platform`

`network-test-validation-platform` uses a separate `srl-expanded` Containerlab profile. It retains the three Nokia SR Linux routers and adds two Linux endpoints, H1 and H2, for end-to-end traffic testing.

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
- Router container names use the `clab-srl-expanded-` prefix.

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

`network-automation-platform` owns network automation and device-management workflows. `network-test-validation-platform` owns network-behavior validation. The projects use separate repositories and workflows; `network-test-validation-platform` consumes the expanded lab profile.
