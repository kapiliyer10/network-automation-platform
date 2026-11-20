# Streaming Telemetry and Monitoring

## 1. Overview

`network-automation-platform` includes a streaming telemetry and observability extension
for the primary three-router Nokia SR Linux Containerlab topology.

The monitoring pipeline uses:

- Nokia SR Linux as the telemetry source.
- gNMIc for streaming telemetry collection.
- OpenConfig YANG paths for interface operational data.
- Prometheus for metric scraping and time-series storage.
- Grafana for monitoring dashboards.
- Docker for running the monitoring components.

The existing Python pyGNMI client continues to perform request-response
state discovery using Get RPC. The new gNMIc collector performs
continuous telemetry collection using Subscribe RPC.

## 2. Architecture

The implemented data flow is:

```text
Nokia SR Linux R1, R2, R3
          |
          | Secure gNMI subscriptions (TLS)
          v
        gNMIc
          |
          | HTTP /metrics (port 9804)
          v
      Prometheus
          |
          | Prometheus data source
          v
       Grafana
          |
          v
   Monitoring Dashboard
```

All three monitoring containers are attached to the existing Docker
network named `clab`.

The monitoring services are separate Docker containers. They are
not additional Containerlab nodes, and the original router topology
remains unchanged.

## 3. Lab Integration

The telemetry collector targets R1, R2, and R3 in the original `srl-lab` Containerlab profile. The router container names and fixed management addresses are documented in [Network Topology](network-topology.md).

The secure gRPC/gNMI management server listens on TCP port `57400`. Linux end hosts and traffic generators are not required for the currently implemented telemetry scope.

## 4. gNMI Capabilities Discovery

The gNMI Capabilities RPC was successfully executed against R1, R2,
and R3.

All three routers advertised:

| Capability | Result |
|---|---|
| gNMI version | 0.10.0 |
| JSON_IETF | Supported |
| PROTO | Supported |
| ASCII | Supported |
| Nokia native YANG models | Advertised |
| OpenConfig models | Advertised |

Capabilities discovery confirms model advertisement. It does not
guarantee that every path in an advertised model is implemented.
The selected paths were therefore tested using actual Get and
Subscribe RPC operations.

## 5. Authentication and TLS

The secure gRPC management server on each router has:

- gNMI service enabled.
- Operational state `UP`.
- Metadata authentication enabled.
- TLS profile `clab-profile`.
- Management network instance `mgmt`.
- TCP port `57400`.

The original lab CA certificate is located at:

`topology/clab-srl-lab/.tls/ca/ca.pem`

The CA certificate and all three router certificates were verified
using OpenSSL. All three router certificates passed CA-chain and
management-IP verification.

The gNMIc container mounts the CA certificate read-only at:

`/etc/gnmic/ca.pem`

Authentication credentials are stored in the local `.env` file:

- `GNMI_USERNAME`
- `GNMI_PASSWORD`

The Docker container receives them through:

- `GNMIC_USERNAME`
- `GNMIC_PASSWORD`

Credentials and private keys must not be committed to Git.

## 6. Implemented Telemetry Subscriptions

The current implementation subscribes to two OpenConfig paths
on `ethernet-1/1` of all three routers.

### 6.1 Incoming octets

```text
openconfig:/interfaces/interface[name=ethernet-1/1]/state/counters/in-octets
```

This retrieves the cumulative incoming octet counter.

### 6.2 Interface operational status

```text
openconfig:/interfaces/interface[name=ethernet-1/1]/state/oper-status
```

This retrieves the operational state, such as `UP` or `DOWN`.

### 6.3 Subscription parameters

| Parameter | Setting |
|---|---|
| Subscription mode | STREAM |
| Stream mode | SAMPLE |
| Sample interval | 5 seconds |
| Encoding | JSON_IETF |
| Interface | ethernet-1/1 |
| Routers | R1, R2, R3 |

The gNMIc configuration is maintained in:

`telemetry/gnmic.yaml`

## 7. gNMIc Prometheus Output

gNMIc exposes the received telemetry through its Prometheus output.

| Setting | Value |
|---|---|
| Listen address | `0.0.0.0:9804` |
| HTTP path | `/metrics` |
| Metric prefix | `srl` |
| Metric expiration | `60 seconds` |
| String handling | `strings-as-labels` enabled |

The `strings-as-labels` option converts string-valued updates into
Prometheus metric labels.

An observed interface-status metric has this structure:

```prometheus
srl_openconfig_interfaces_interfaces_interface_state_oper_status{
  interface_name="ethernet-1/1",
  oper_status="UP",
  source="172.20.20.4:57400",
  subscription_name="interface_oper_status"
} 1
```

The `oper_status` label contains the actual interface state.
The numeric value `1` represents the string-valued metric update.

The incoming-octets metric is:

`srl_openconfig_interfaces_interfaces_interface_state_counters_in_octets`

## 8. Prometheus Configuration

The Prometheus configuration is maintained in:

`telemetry/prometheus.yml`

| Parameter | Value |
|---|---|
| Scrape interval | `15 seconds` |
| Evaluation interval | `15 seconds` |
| Job name | `gnmic` |
| Scrape target | `gnmic:9804` |

Prometheus communicates with gNMIc using the Docker network name `clab`.

The target `gnmic:9804` is the exporter endpoint. Router identity
is represented by the `source` label in the individual metrics.

Prometheus uses the persistent Docker volume `prometheus-data`.

## 9. Grafana Configuration

Grafana uses Prometheus as its data source.

The configured data-source URL is:

`http://prometheus:9090`

The internal Docker hostname is used because Grafana and Prometheus
are attached to the same Docker network.

Grafana uses the persistent Docker volume `grafana-data`.

The Grafana web interface is available at:

`http://localhost:3000`

### 9.1 Dashboard

Dashboard name:

`SR Linux Streaming Telemetry`

The dashboard contains three implemented panels.

#### Panel 1: Incoming Traffic

PromQL:

```promql
rate(
  srl_openconfig_interfaces_interfaces_interface_state_counters_in_octets[1m]
) * 8
```

This calculates the average incoming bit rate over a one-minute
window. The result is displayed in bits per second.

#### Panel 2: Cumulative Incoming Octets

PromQL:

```promql
srl_openconfig_interfaces_interfaces_interface_state_counters_in_octets
```

This displays the cumulative incoming octet counter.
It is not a traffic-rate measurement.

#### Panel 3: Interface Operational Status

PromQL:

```promql
srl_openconfig_interfaces_interfaces_interface_state_oper_status
```

The query uses Instant mode and Table visualization.

The displayed fields are:

- Interface
- Status
- Router

Value mappings:

| Status | Color |
|---|---|
| UP | Green |
| DOWN | Red |

The colored background is applied through a field override on the
Status column rather than the entire table row.

## 10. Container Images and Versions

| Component | Docker image |
|---|---|
| gNMIc | `ghcr.io/openconfig/gnmic:0.49.1` |
| Prometheus | `prom/prometheus:v3.13.5` |
| Grafana | `grafana/grafana:13.3.0` |

Docker Compose is not required. The services are managed using
ordinary Docker commands.

## 11. Deployment and Startup

Deploy the original lab first:

```bash
./scripts/lab_up.sh
```

Confirm that R1, R2, and R3 are running and that the `clab` Docker
network exists.

The following commands assume that the original lab and its TLS
certificates have already been created. These `docker run` commands
create the monitoring containers; for subsequent starts, use the
restart procedure in Section 12.7.

### 11.1 Start gNMIc

Run from the project root:

```bash
(
    set -a
    source .env
    set +a

    export GNMIC_USERNAME="$GNMI_USERNAME"
    export GNMIC_PASSWORD="$GNMI_PASSWORD"

    docker run -d \
        --name gnmic \
        --network clab \
        -p 9804:9804 \
        --restart unless-stopped \
        -e GNMIC_USERNAME \
        -e GNMIC_PASSWORD \
        -v "$PWD/telemetry/gnmic.yaml:/etc/gnmic/gnmic.yaml:ro" \
        -v "$PWD/topology/clab-srl-lab/.tls/ca/ca.pem:/etc/gnmic/ca.pem:ro" \
        ghcr.io/openconfig/gnmic:0.49.1 \
        --config /etc/gnmic/gnmic.yaml subscribe
)
```

### 11.2 Start Prometheus

```bash
docker run -d \
    --name prometheus \
    --network clab \
    -p 9090:9090 \
    --restart unless-stopped \
    -v "$PWD/telemetry/prometheus.yml:/etc/prometheus/prometheus.yml:ro" \
    -v prometheus-data:/prometheus \
    prom/prometheus:v3.13.5 \
    --config.file=/etc/prometheus/prometheus.yml \
    --storage.tsdb.path=/prometheus
```

### 11.3 Start Grafana

```bash
docker run -d \
    --name grafana \
    --network clab \
    -p 127.0.0.1:3000:3000 \
    --restart unless-stopped \
    -v grafana-data:/var/lib/grafana \
    grafana/grafana:13.3.0
```

Change Grafana's initial default password at first login.

Configure the Prometheus data source using:

`http://prometheus:9090`

## 12. Validation and Troubleshooting

### 12.1 Check containers

```bash
docker ps
```

Expected monitoring containers:

- `gnmic`
- `prometheus`
- `grafana`

### 12.2 Check gNMIc logs

```bash
docker logs --tail 50 gnmic
```

Look for successful target client initialization and subscription
requests for all three routers.

### 12.3 Check the metrics endpoint

```bash
curl -fsS http://localhost:9804/metrics
```

Check incoming octets:

```bash
curl -fsS http://localhost:9804/metrics | grep in_octets
```

Check operational status:

```bash
curl -fsS http://localhost:9804/metrics | grep oper_status
```

### 12.4 Check Prometheus scraping

Open:

`http://localhost:9090/targets`

The `gnmic` target should report `UP`. Also verify that the exported metrics contain samples from all three router sources; a healthy scrape target alone does not confirm every subscription.

### 12.5 Check Prometheus queries

Incoming octets:

```promql
srl_openconfig_interfaces_interfaces_interface_state_counters_in_octets
```

Incoming bit rate:

```promql
rate(
  srl_openconfig_interfaces_interfaces_interface_state_counters_in_octets[1m]
) * 8
```

Interface operational status:

```promql
srl_openconfig_interfaces_interfaces_interface_state_oper_status
```

### 12.6 Check Grafana health

```bash
curl -fsS http://localhost:3000/api/health
```

### 12.7 Restart monitoring containers

After Docker Engine and the Containerlab lab are running:

```bash
docker start gnmic prometheus grafana
```

The containers use the `unless-stopped` restart policy.

After changing the host-side gNMIc YAML configuration, restart
the collector:

```bash
docker restart gnmic
```

## 13. Validation Results

The implementation was tested against the original `clab-srl-lab`
topology on November 4, 2026.

| Test | Result |
|---|---|
| R1 Capabilities RPC | Passed |
| R2 Capabilities RPC | Passed |
| R3 Capabilities RPC | Passed |
| TLS certificate verification | Passed on all three routers |
| OpenConfig incoming-octets Get | Passed on R1 |
| OpenConfig operational-status Get | Passed on R1, R2, R3 |
| SAMPLE streaming subscription | Passed on R1, R2, R3 |
| gNMIc Prometheus exporter | Passed |
| Prometheus scrape target | `UP` |
| Prometheus incoming-octets series | Three series |
| Prometheus interface-status series | Three series |
| Grafana health | `Database OK` |
| Grafana dashboard | Three panels created and saved |

All three routers reported `UP` for `ethernet-1/1` during validation.

Prometheus successfully queried the three routers' incoming-octet
counters and operational-status metrics.

## 14. Current Scope and Limitations

The verified implementation currently covers:

- Three Nokia SR Linux routers.
- Interface `ethernet-1/1` on each router.
- Incoming octet counters.
- Interface operational status.
- Five-second gNMI sample interval.
- Fifteen-second Prometheus scrape interval.
- One Grafana dashboard with three panels.

The following are not part of the currently verified implementation:

- Interface output counters.
- Interface error and drop counters.
- CPU and memory streaming telemetry.
- OSPF neighbor streaming telemetry.
- Additional interface subscriptions.
- Alert rules and notification delivery.
- Automated Grafana dashboard provisioning.

No Linux end hosts or traffic generators are included.

## 15. Security and Operational Notes

This monitoring stack is intended for a local Containerlab
development environment.

- gNMI uses TLS on TCP port `57400`.
- Router server certificates are verified against the original
  Containerlab CA.
- Username and password credentials are passed through environment
  variables.
- The CA certificate and YAML configuration files are mounted
  read-only into the gNMIc container.
- Prometheus and gNMIc HTTP endpoints are unauthenticated in this local setup.
- Grafana is bound to the host loopback address `127.0.0.1`.
- Prometheus and gNMIc ports (`9090` and `9804`) are published on all host interfaces.

Do not expose unauthenticated development endpoints to untrusted
networks.

Never commit `.env`, private keys, passwords, or other credentials.

## 16. Lab Lifecycle and TLS Identity

### Fixed management addresses

The primary lab's fixed router management addresses and container mapping are documented in [Network Topology](network-topology.md). Each management address matches the IP Subject Alternative Name in its generated router TLS certificate. The assignments are defined using `mgmt-ipv4` in `topology/srl-lab.clab.yml` to preserve router identity across normal lab redeployments.

### Normal startup and shutdown

The normal lifecycle scripts preserve the resources required by the monitoring stack:

- `scripts/lab_up.sh` deploys the topology without `--reconfigure`, reusing existing generated TLS artifacts.
- `scripts/lab_down.sh` destroys the router containers with `--keep-mgmt-net`, preserving the Docker management network used by gNMIc, Prometheus, and Grafana.

After redeploying the routers, gNMIc may need to re-establish its streaming subscriptions. The verified recovery procedure is:

```bash
docker restart gnmic
```

Verify that both telemetry metric families return three router sources:

- `srl_openconfig_interfaces_interfaces_interface_state_counters_in_octets`
- `srl_openconfig_interfaces_interfaces_interface_state_oper_status`

All three operational-status labels should report `UP`. A healthy Prometheus scrape target alone does not prove that all router subscriptions are healthy.

### Clean reconfiguration and certificates

`containerlab deploy --reconfigure` is not the normal startup procedure. It regenerates Containerlab artifacts, including TLS certificates.

After an intentional clean reconfiguration, verify the generated router certificates and CA. Recreate the gNMIc container with the regenerated CA file mounted at `/etc/gnmic/ca.pem`; restarting an existing container may retain an older bind-mounted certificate file. Then verify TLS connectivity and all three telemetry sources again.
