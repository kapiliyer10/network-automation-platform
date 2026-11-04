# Desired State and Drift Detection

## 1. Desired-State Source

The intended network state is stored in:

```text
configs/desired/desired_state.yaml
```

The desired-state loader reads and validates this YAML representation before the comparison and configuration workflows consume it.

The documented desired-state resources include:

- Interface administrative state
- Interface description
- IPv4 configuration
- Network-instance interfaces
- OSPF configuration
- BGP desired-state configuration support

BGP desired-state and NETCONF configuration support was added as an implemented Project 1 extension. This document does not claim that BGP operational session state is included in the normalized gNMI state-discovery model.

## 2. Actual-State Discovery

The state-discovery layer uses gNMI to retrieve device information. Retrieved device-specific data is converted into a normalized application model before comparison.

The normalized state documented by the project includes:

- Hostname
- Interfaces
- IPv4 addresses
- Routes
- OSPF neighbors
- OSPF configuration

Example normalized interface fields:

```text
name
admin_state
oper_state
```

Example IPv4 address fields:

```text
interface
subinterface_index
ip_address
origin
status
```

Example route fields:

```text
prefix
active
metric
preference
route_type
```

Example OSPF neighbor fields:

```text
interface
router_id
address
state
```

## 3. Comparison and Drift Detection

The comparison workflow evaluates desired state against normalized actual state:

```text
Desired State + Actual State
              |
              v
       Comparison Engine
              |
              v
          PASS / DRIFT
```

A controlled mismatch can be reported as:

```text
Interface: ethernet-1/2

Desired:  enable
Actual:   disable
Status:   DRIFT
```

The reporting layer summarizes per-device and overall results. A device can pass while another device reports drift; the overall result reflects the device-level outcomes.

## 4. Reconciliation and Verification

When drift is detected, the workflow can generate and apply the required NETCONF configuration. It then retrieves and validates the resulting device state.

```text
Detect Drift
     |
     v
Build NETCONF Configuration
     |
     v
Apply and Commit
     |
     v
Retrieve State / Configuration
     |
     v
Verify Desired State
     |
     v
PASS / FAIL
```

The important design rule is that a successful configuration operation alone does not establish that the desired state has been achieved. The post-change verification step checks the resulting state.
