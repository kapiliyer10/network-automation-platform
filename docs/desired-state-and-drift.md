# Desired State and Drift Detection

## 1. Desired-State Source

The intended network state is stored in:

`configs/desired/desired_state.yaml`

The desired-state loader reads and validates this YAML representation before the comparison and configuration workflows consume it.

The desired-state model supports:

- Interface administrative state
- Interface description
- IPv4 configuration
- Network-instance interfaces
- OSPF configuration
- BGP configuration

BGP desired-state and NETCONF configuration support was added as an implemented extension to `network-automation-platform`. However, BGP operational peer state is not part of the normalized gNMI state-discovery model, so this document does not claim automated BGP session-state validation.

## 2. Actual-State Discovery

The state-discovery layer uses gNMI to retrieve device data. The retrieved device-specific data is mapped into a normalized application model, which provides a consistent representation for the comparison workflow.

The normalized application model currently includes:

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

The reporting layer summarizes comparison results for each device and across the overall network. Individual devices are evaluated separately, so one device can pass while another reports drift. The overall result reflects the combined device-level outcomes.

## 4. Reconciliation and Verification

When drift is detected, the workflow generates and applies the required NETCONF configuration. After the commit, it performs post-change verification by reading back the configuration and checking the resulting device state.

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
Read Back Configuration / Retrieve State
     |
     v
Verify Desired State
     |
     v
PASS / FAIL
```

A successful NETCONF commit confirms that the device accepted the configuration; it does not, by itself, prove that the desired state has been achieved. The workflow therefore verifies the read-back configuration and resulting device state.
