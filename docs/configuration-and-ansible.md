# Configuration Generation and Ansible

## 1. Configuration Paths

The repository contains two configuration-generation paths: Jinja2 CLI rendering and NETCONF/YANG model-driven configuration.

### Jinja2 CLI rendering

The Jinja2 renderer uses templates such as:

```text
templates/srlinux/interfaces.cli.j2
```

The path is:

```text
Desired State
      |
      v
Jinja2 Template
      |
      v
Generated SR Linux CLI Configuration
```

Generated CLI output is written under `generated/`. This renderer is separate from the primary live NETCONF configuration path.

### NETCONF / YANG configuration

The primary live configuration workflow builds NETCONF `edit-config` payloads from desired state, applies the configuration, commits it, and validates the resulting device state.

```text
Desired State
      |
      v
NETCONF Configuration Rendering
      |
      v
edit-config
      |
      v
commit
      |
      v
Read Back and Verify
```

The implementation includes NETCONF configuration and read-back support for the implemented desired-state resources, including the BGP configuration extension.

## 2. Ansible Integration

Ansible is used as an orchestration layer. Python remains the owner of the network-automation business logic, including state handling, comparison, configuration generation, NETCONF operations, validation, and reporting.

The main playbook is:

```text
ansible/configure_devices.yml
```

Run it with:

```bash
ansible-playbook -i ansible/inventory.ini ansible/configure_devices.yml
```

The playbook invokes the existing Python workflow rather than duplicating the network automation logic:

```text
Ansible
   |
   v
Python Workflow Entry Point
   |
   v
Python Automation Engine
   |
   v
Network Devices
```
