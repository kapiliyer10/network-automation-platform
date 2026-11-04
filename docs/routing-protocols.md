# Routing Protocols: OSPF and BGP

## 1. Overview

Project 1 uses two routing protocols in its three-router Nokia SR Linux
Containerlab environment:

- OSPF (Open Shortest Path First): the Interior Gateway Protocol used
  for routing within the primary lab.
- BGP (Border Gateway Protocol): configured as eBGP between the three
  routers using separate autonomous system numbers.

Both protocols are configured on the live routers. Their operational
states have been inspected using the SR Linux CLI.

This document separates live protocol verification from the Python
application's automated configuration and state-validation capabilities.

## 2. Primary Lab Topology

The primary topology consists of three Nokia SR Linux routers connected
in a triangle.

```text
                  R1
                 /  \
                /    \
               /      \
              R2------R3
```

### 2.1 Point-to-point links

| Link | Subnet | First router | Second router |
|---|---|---|---|
| R1-R2 | 10.0.12.0/30 | R1: 10.0.12.1 | R2: 10.0.12.2 |
| R2-R3 | 10.0.23.0/30 | R2: 10.0.23.1 | R3: 10.0.23.2 |
| R3-R1 | 10.0.31.0/30 | R3: 10.0.31.2 | R1: 10.0.31.1 |

### 2.2 Loopback addresses

| Router | Loopback |
|---|---|
| R1 | 10.255.0.1/32 |
| R2 | 10.255.0.2/32 |
| R3 | 10.255.0.3/32 |

The loopbacks provide stable router identifiers and prefixes that can
be used when examining routing information.

## 3. OSPF — Interior Gateway Routing

### 3.1 What is OSPF?

OSPF stands for Open Shortest Path First.

It is a link-state Interior Gateway Protocol (IGP) used to exchange
routing information within an autonomous system.

Routers running OSPF discover neighbours, form adjacencies, exchange
link-state information and calculate routes using the Shortest Path
First algorithm.

OSPF uses areas to organise the routing domain. The primary Project 1
lab uses Area 0.0.0.0.

### 3.2 OSPF configuration in Project 1

The three routers use the following router IDs:

| Router | OSPF router ID |
|---|---|
| R1 | 1.1.1.1 |
| R2 | 2.2.2.2 |
| R3 | 3.3.3.3 |

OSPF is configured on the two point-to-point interfaces of each router:

- R1: ethernet-1/1.0 and ethernet-1/2.0
- R2: ethernet-1/1.0 and ethernet-1/2.0
- R3: ethernet-1/1.0 and ethernet-1/2.0

All three routers participate in Area 0.0.0.0.

The OSPF configuration is present in the router startup configuration
files under `configs/srl/`.

### 3.3 OSPF neighbour states

OSPF neighbours progress through states while establishing an
adjacency. The Full state indicates that the adjacency has completed
database synchronisation.

The live verification command is:

```bash
docker exec clab-srl-lab-R1 sr_cli -c \
  'show network-instance default protocols ospf neighbor'
```

Repeat for R2 and R3.

### 3.4 Verified OSPF result

The live lab verification returned two neighbours per router.

| Router | Neighbour router IDs | Observed state |
|---|---|---|
| R1 | 2.2.2.2, 3.3.3.3 | Full, Full |
| R2 | 1.1.1.1, 3.3.3.3 | Full, Full |
| R3 | 2.2.2.2, 1.1.1.1 | Full, Full |

This confirms that all three routers have established their expected
OSPF adjacencies in the primary lab.

### 3.5 OSPF in the automation workflow and CI

OSPF is used by the project as the primary lab's routing protocol and
as a readiness condition for live integration testing.

The GitHub Actions workflow runs:

```bash
./scripts/wait_for_ospf.sh
```

before executing the live integration tests.

This prevents the integration tests from proceeding before the
expected OSPF neighbours reach the Full state.

The Python project also contains OSPF state-discovery and validation
functionality, including neighbour and configuration-related tests.

## 4. BGP — Border Gateway Protocol

### 4.1 What is BGP?

BGP stands for Border Gateway Protocol.

It is a path-vector routing protocol used to exchange routing
information between autonomous systems.

An autonomous system (AS) is a routing domain identified by an
autonomous system number (ASN).

BGP peers establish sessions and exchange network prefixes. BGP
selects paths using attributes such as AS_PATH, LOCAL_PREF and
other routing-policy inputs.

Unlike OSPF, which forms link-state adjacencies, BGP establishes
a TCP-based peering session.

The two important operational states to understand are:

- OSPF: Full
- BGP: Established

### 4.2 BGP design in Project 1

Project 1 configures eBGP between three routers. Each router has a
different autonomous system number.

| Router | Local AS | BGP router ID |
|---|---:|---|
| R1 | 65001 | 1.1.1.1 |
| R2 | 65002 | 2.2.2.2 |
| R3 | 65003 | 3.3.3.3 |

Because each router has a different AS number, the configured
relationships are eBGP sessions.

### 4.3 BGP neighbour relationships

The topology uses a full-mesh arrangement: every router peers
directly with the other two routers.

| Local router | Local AS | BGP neighbour | Remote AS |
|---|---:|---|---:|
| R1 | 65001 | 10.0.12.2 | 65002 |
| R1 | 65001 | 10.0.31.2 | 65003 |
| R2 | 65002 | 10.0.12.1 | 65001 |
| R2 | 65002 | 10.0.23.2 | 65003 |
| R3 | 65003 | 10.0.31.1 | 65001 |
| R3 | 65003 | 10.0.23.1 | 65002 |

Each router has two configured BGP neighbours.

### 4.4 BGP desired state and configuration automation

BGP desired-state configuration is represented in:

`configs/desired/desired_state.yaml`

The BGP data includes:

- Local autonomous system number.
- Router ID.
- Address-family configuration.
- Peer groups.
- Neighbour addresses.
- Remote AS numbers.
- Import and export routing policies.

The project implements the following BGP configuration workflow:

1. Load the BGP desired state from YAML.
2. Validate the desired-state structure and values.
3. Generate BGP configuration through the configuration renderer.
4. Build NETCONF configuration payloads.
5. Apply configuration through NETCONF.
6. Retrieve BGP configuration for read-back.
7. Compare retrieved configuration with desired state.

The BGP routing policy in the current lab uses a prefix set containing
the three router loopbacks:

- 10.255.0.1/32
- 10.255.0.2/32
- 10.255.0.3/32

The `allow-bgp-loopbacks` policy has a default reject action and
permits the configured loopback prefixes.

### 4.5 BGP operational session verification

Configuration read-back and operational session verification are
different checks.

Configuration read-back confirms that the intended BGP configuration
is present on a router.

Operational session verification checks whether the router has
successfully established a BGP session with its neighbour.

The following SR Linux CLI command displays the BGP summary:

```bash
docker exec clab-srl-lab-R1 sr_cli -c \
  'show network-instance default protocols bgp summary'
```

For an individual peer, use:

```bash
docker exec clab-srl-lab-R1 sr_cli -c \
  'show network-instance default protocols bgp neighbor 10.0.12.2 detail'
```

Look for:

```text
Admin-state is enable, session-state is established
```

The detailed output also provides information such as:

- Local and remote AS numbers.
- Peer type.
- Peer group.
- Session uptime.
- TCP connection information.
- Received and advertised route counts.
- Negotiated capabilities.
- Peer flap information.

A BGP session in Established state confirms that the BGP peer
relationship has reached its operational state.

### 4.6 BGP received and advertised routes

To inspect routes received from a neighbour:

```bash
docker exec clab-srl-lab-R1 sr_cli -c \
  'show network-instance default protocols bgp neighbor 10.0.12.2 received-routes ipv4'
```

To inspect routes advertised to a neighbour:

```bash
docker exec clab-srl-lab-R1 sr_cli -c \
  'show network-instance default protocols bgp neighbor 10.0.12.2 advertised-routes ipv4'
```

To inspect the BGP IPv4 route table summary:

```bash
docker exec clab-srl-lab-R1 sr_cli -c \
  'show network-instance default protocols bgp routes ipv4 summary'
```

These checks help establish whether the session is exchanging routing
information rather than simply remaining established without useful
prefix exchange.

### 4.7 Verified live BGP result

The live SR Linux BGP summary reported:

| Router | BGP enabled | Configured peers | UP peers |
|---|---|---:|---:|
| R1 | Yes | 2 | 2 |
| R2 | Yes | 2 | 2 |
| R3 | Yes | 2 | 2 |

Detailed neighbour output also reported `session-state is established`
for the inspected peers.

The inspected peers reported two received IPv4 routes and two
advertised IPv4 routes, with one received route active for the
individual peer.

The BGP IPv4 route table summary on each router reported:

- 8 received BGP routes.
- 8 valid routes.
- 6 used routes.
- 6 available destinations.
- 2 destinations with ECMP multipaths.

The loopback prefixes were visible in the BGP route tables with
selected paths and AS_PATH information.

These results demonstrate that BGP sessions are established and
routing information is being exchanged in the live lab.

### 4.8 Current boundary of automated BGP verification

The live router CLI verification above establishes that BGP is
operational in the current lab.

However, the existing Python workflow's BGP validation is focused on
configuration read-back and desired-versus-actual configuration
comparison.

The project has not yet demonstrated an automated Python assertion
that retrieves each BGP peer's operational session state and checks
that it is Established.

Similarly, the live CLI route inspection is currently a manual
verification step rather than a completed automated route-validation
test within the Python workflow.

Do not confuse successful NETCONF configuration application with
successful BGP session establishment.

## 5. OSPF and BGP Comparison

| Area | OSPF | BGP |
|---|---|---|
| Full name | Open Shortest Path First | Border Gateway Protocol |
| Protocol type | Link-state IGP | Path-vector EGP |
| Main purpose | Routing within an autonomous system | Routing between autonomous systems |
| Neighbour relationship | OSPF adjacency | BGP peering session |
| Transport | IP protocol 89 | TCP port 179 |
| Important state | Full | Established |
| Main path mechanism | Shortest Path First calculation | BGP path selection and policy |
| Project 1 role | Primary lab routing and CI readiness | Full-mesh eBGP configuration and live peer operation |
| Live state verification | OSPF neighbour CLI | BGP summary and neighbour detail CLI |
| Python automation boundary | OSPF state and configuration validation | BGP configuration read-back and drift validation; operational session assertion remains future work |

## 6. Troubleshooting Checklist

### OSPF

If an OSPF neighbour does not reach Full:

1. Verify the physical or virtual interface is operational.
2. Check the interface IP addresses and subnet.
3. Confirm that both routers use the expected OSPF area.
4. Verify router IDs and OSPF interface configuration.
5. Inspect the OSPF neighbour state and relevant logs.
6. Confirm the expected adjacency after correcting the issue.

Useful command:

```bash
docker exec clab-srl-lab-R1 sr_cli -c \
  'show network-instance default protocols ospf neighbor'
```

### BGP

If a BGP peer is not Established:

1. Verify the peer IP address is reachable.
2. Check the local and remote AS numbers.
3. Verify the neighbour address and peer-group configuration.
4. Confirm that BGP is enabled in the correct network instance.
5. Check TCP connectivity to port 179.
6. Inspect the peer's session state and last received notification.
7. Verify import and export routing policies.
8. Check received and advertised routes after the session establishes.

Useful commands:

```bash
docker exec clab-srl-lab-R1 sr_cli -c \
  'show network-instance default protocols bgp summary'

docker exec clab-srl-lab-R1 sr_cli -c \
  'show network-instance default protocols bgp neighbor 10.0.12.2 detail'
```

## 7. Future Automation Improvements

The next useful enhancement is to bring BGP operational verification
into the Python automation workflow.

Potential implementation steps:

1. Verify which BGP operational-state paths are supported by the
   SR Linux gNMI implementation.
2. Retrieve BGP neighbour state for every configured peer.
3. Compare the observed peer address and remote AS against desired
   state.
4. Assert that each expected peer reaches Established.
5. Verify expected received prefixes and, where appropriate,
   advertised prefixes.
6. Report a clear PASS or FAIL result per peer and per router.
7. Add tests for established sessions, missing peers, incorrect
   remote AS values and session failures.
8. Test recovery after a peer is restored.

Any OpenConfig or native YANG path should be verified against the
running SR Linux version before it is treated as supported.

## 8. Final Summary

Project 1 has a working three-router OSPF and eBGP environment.

Live verification confirmed:

- Two OSPF neighbours in Full state on each router.
- Two BGP peers UP on each router.
- BGP neighbour details reporting Established sessions.
- IPv4 routes received, selected and advertised.
- BGP routing-table entries for the router loopbacks.

The Python application supports OSPF-related state and configuration
validation and BGP desired-state, NETCONF configuration, read-back
and configuration drift validation.

Automated BGP operational session and route assertions remain a
separate enhancement. This distinction preserves the project's
closed-loop design principle: configuration being accepted is not
proof that the intended routing behaviour has been achieved.
