from pathlib import Path

from src.config.renderer import render_device_config
from src.config.renderer import render_all_device_configs
from src.desired.loader import load_desired_state
from src.config.renderer import write_device_configs

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_FILE = (
    PROJECT_ROOT / "templates" / "srlinux" / "interfaces.cli.j2"
)


def test_render_device_config():
    interfaces = {
        "ethernet-1/1": {
            "admin_state": "enable",
            "ipv4": {
                "admin_state": "enable",
                "address": "10.0.12.1/30",
            },
        },

        "ethernet-1/2": {
            "admin_state": "disable",
            "ipv4": {
                "admin_state": "enable",
                "address": "10.0.12.2/30",
            },
        },
    }

    result = render_device_config(
        desired_interfaces=interfaces,
        desired_network_instances={},
        template_path=TEMPLATE_FILE,
        desired_ospf={},
    )

    expected = (
    "set / interface ethernet-1/1 admin-state enable\n"
    "set / interface ethernet-1/1 subinterface 0 ipv4 admin-state enable\n"
    "set / interface ethernet-1/1 subinterface 0 ipv4 address 10.0.12.1/30\n"
    "set / interface ethernet-1/2 admin-state disable\n"
    "set / interface ethernet-1/2 subinterface 0 ipv4 admin-state enable\n"
    "set / interface ethernet-1/2 subinterface 0 ipv4 address 10.0.12.2/30"
    )

    assert result == expected


def test_render_all_device_configs():
    desired_state = load_desired_state(
        PROJECT_ROOT / "configs" / "desired" / "desired_state.yaml"
    )

    configs = render_all_device_configs(
        desired_state=desired_state,
        template_path=TEMPLATE_FILE,
    )

    assert set(configs) == {"R1", "R2", "R3"}

    expected_configs = {
        "R1": (
                    "set / interface ethernet-1/1 admin-state enable\n"
                    "set / interface ethernet-1/1 subinterface 0 ipv4 admin-state enable\n"
                    "set / interface ethernet-1/1 subinterface 0 ipv4 address 10.0.12.1/30\n"
                    "set / interface ethernet-1/2 admin-state enable\n"
                    "set / interface ethernet-1/2 subinterface 0 ipv4 admin-state enable\n"
                    "set / interface ethernet-1/2 subinterface 0 ipv4 address 10.0.31.1/30\n"
                    "set / network-instance default interface ethernet-1/1.0\n"
                    "set / network-instance default interface ethernet-1/2.0\n"
                    "set / network-instance default interface lo0.0\n"
                    "set / network-instance default protocols ospf instance default admin-state enable\n"
                    "set / network-instance default protocols ospf instance default version ospf-v2\n"
                    "set / network-instance default protocols ospf instance default router-id 1.1.1.1\n"
                    "set / network-instance default protocols ospf instance default area 0.0.0.0 interface ethernet-1/1.0\n"
                    "set / network-instance default protocols ospf instance default area 0.0.0.0 interface ethernet-1/2.0\n"
                ),
                "R2": (
                    "set / interface ethernet-1/1 admin-state enable\n"
                    "set / interface ethernet-1/1 subinterface 0 ipv4 admin-state enable\n"
                    "set / interface ethernet-1/1 subinterface 0 ipv4 address 10.0.12.2/30\n"
                    "set / interface ethernet-1/2 admin-state enable\n"
                    "set / interface ethernet-1/2 subinterface 0 ipv4 admin-state enable\n"
                    "set / interface ethernet-1/2 subinterface 0 ipv4 address 10.0.23.1/30\n"
                    "set / network-instance default interface ethernet-1/1.0\n"
                    "set / network-instance default interface ethernet-1/2.0\n"
                    "set / network-instance default interface lo0.0\n"
                    "set / network-instance default protocols ospf instance default admin-state enable\n"
                    "set / network-instance default protocols ospf instance default version ospf-v2\n"
                    "set / network-instance default protocols ospf instance default router-id 2.2.2.2\n"
                    "set / network-instance default protocols ospf instance default area 0.0.0.0 interface ethernet-1/1.0\n"
                    "set / network-instance default protocols ospf instance default area 0.0.0.0 interface ethernet-1/2.0\n"
                ),
                "R3": (
                    "set / interface ethernet-1/1 admin-state enable\n"
                    "set / interface ethernet-1/1 subinterface 0 ipv4 admin-state enable\n"
                    "set / interface ethernet-1/1 subinterface 0 ipv4 address 10.0.23.2/30\n"
                    "set / interface ethernet-1/2 admin-state enable\n"
                    "set / interface ethernet-1/2 subinterface 0 ipv4 admin-state enable\n"
                    "set / interface ethernet-1/2 subinterface 0 ipv4 address 10.0.31.2/30\n"
                    "set / network-instance default interface ethernet-1/1.0\n"
                    "set / network-instance default interface ethernet-1/2.0\n"
                    "set / network-instance default interface lo0.0\n"
                    "set / network-instance default protocols ospf instance default admin-state enable\n"
                    "set / network-instance default protocols ospf instance default version ospf-v2\n"
                    "set / network-instance default protocols ospf instance default router-id 3.3.3.3\n"
                    "set / network-instance default protocols ospf instance default area 0.0.0.0 interface ethernet-1/1.0\n"
                    "set / network-instance default protocols ospf instance default area 0.0.0.0 interface ethernet-1/2.0\n"
                ),
    }

    expected_configs = {
        name: config.removesuffix("\n")
        for name, config in expected_configs.items()
    }

    # Verify the original interface and OSPF output separately.
    # BGP and routing-policy output has its own dedicated test.
    for router, config in configs.items():
        base_lines = [
            line for line in config.splitlines()
            if line
            and " protocols bgp " not in line
            and not line.startswith("set / routing-policy ")
        ]
        assert "\n".join(base_lines) == expected_configs[router].removesuffix("\n")


def test_write_device_configs(tmp_path):
    device_configs = {
        "R1": (
            "set / interface ethernet-1/1 admin-state enable\n"
            "set / interface ethernet-1/1 subinterface 0 ipv4 admin-state enable\n"
            "set / interface ethernet-1/1 subinterface 0 ipv4 address 10.0.12.1/30\n"
            "set / interface ethernet-1/2 admin-state enable\n"
            "set / interface ethernet-1/2 subinterface 0 ipv4 admin-state enable\n"
            "set / interface ethernet-1/2 subinterface 0 ipv4 address 10.0.31.1/30\n"
            "set / network-instance default interface ethernet-1/1.0\n"
            "set / network-instance default interface ethernet-1/2.0\n"
            "set / network-instance default protocols ospf instance default admin-state enable\n"
            "set / network-instance default protocols ospf instance default version ospf-v2\n"
            "set / network-instance default protocols ospf instance default router-id 1.1.1.1\n"
            "set / network-instance default protocols ospf instance default area 0.0.0.0 interface ethernet-1/1.0\n"
            "set / network-instance default protocols ospf instance default area 0.0.0.0 interface ethernet-1/2.0\n"
            "set / network-instance default protocols ospf instance default area 0.0.0.0 interface lo0.0\n"
            "set / network-instance default protocols ospf instance default area 0.0.0.0 interface lo0.0 passive true"
        ),
        "R2": (
            "set / interface ethernet-1/1 admin-state enable\n"
            "set / interface ethernet-1/1 subinterface 0 ipv4 admin-state enable\n"
            "set / interface ethernet-1/1 subinterface 0 ipv4 address 10.0.12.2/30\n"
            "set / interface ethernet-1/2 admin-state enable\n"
            "set / interface ethernet-1/2 subinterface 0 ipv4 admin-state enable\n"
            "set / interface ethernet-1/2 subinterface 0 ipv4 address 10.0.23.1/30\n"
            "set / network-instance default interface ethernet-1/1.0\n"
            "set / network-instance default interface ethernet-1/2.0\n"
            "set / network-instance default protocols ospf instance default admin-state enable\n"
            "set / network-instance default protocols ospf instance default version ospf-v2\n"
            "set / network-instance default protocols ospf instance default router-id 2.2.2.2\n"
            "set / network-instance default protocols ospf instance default area 0.0.0.0 interface ethernet-1/1.0\n"
            "set / network-instance default protocols ospf instance default area 0.0.0.0 interface ethernet-1/2.0\n"
            "set / network-instance default protocols ospf instance default area 0.0.0.0 interface lo0.0\n"
            "set / network-instance default protocols ospf instance default area 0.0.0.0 interface lo0.0 passive true"
        ),
        "R3": (
            "set / interface ethernet-1/1 admin-state enable\n"
            "set / interface ethernet-1/1 subinterface 0 ipv4 admin-state enable\n"
            "set / interface ethernet-1/1 subinterface 0 ipv4 address 10.0.23.2/30\n"
            "set / interface ethernet-1/2 admin-state enable\n"
            "set / interface ethernet-1/2 subinterface 0 ipv4 admin-state enable\n"
            "set / interface ethernet-1/2 subinterface 0 ipv4 address 10.0.31.2/30\n"
            "set / network-instance default interface ethernet-1/1.0\n"
            "set / network-instance default interface ethernet-1/2.0\n"
            "set / network-instance default protocols ospf instance default admin-state enable\n"
            "set / network-instance default protocols ospf instance default version ospf-v2\n"
            "set / network-instance default protocols ospf instance default router-id 3.3.3.3\n"
            "set / network-instance default protocols ospf instance default area 0.0.0.0 interface ethernet-1/1.0\n"
            "set / network-instance default protocols ospf instance default area 0.0.0.0 interface ethernet-1/2.0\n"
            "set / network-instance default protocols ospf instance default area 0.0.0.0 interface lo0.0\n"
            "set / network-instance default protocols ospf instance default area 0.0.0.0 interface lo0.0 passive true"
        ),
    }

    write_device_configs(
        device_configs=device_configs,
        output_dir=tmp_path,
    )

    for device_name, expected_config in device_configs.items():
        config_file = tmp_path / f"{device_name}.cli"

        assert config_file.is_file()
        assert config_file.read_text(encoding="utf-8") == (
            expected_config + "\n"
        )


def test_render_all_device_configs_includes_bgp():
    desired_state = load_desired_state(
        PROJECT_ROOT / "configs" / "desired" / "desired_state.yaml"
    )

    configs = render_all_device_configs(
        desired_state=desired_state,
        template_path=TEMPLATE_FILE,
    )

    expected_bgp = {
        "R1": [
            "set / network-instance default protocols bgp autonomous-system 65001",
            "set / network-instance default protocols bgp router-id 1.1.1.1",
            "set / network-instance default protocols bgp afi-safi ipv4-unicast admin-state enable",
            "set / network-instance default protocols bgp group to-r2 peer-as 65002",
            "set / network-instance default protocols bgp group to-r3 peer-as 65003",
            "set / network-instance default protocols bgp neighbor 10.0.12.2 peer-group to-r2",
            "set / network-instance default protocols bgp neighbor 10.0.31.2 peer-group to-r3",
        ],
        "R2": [
            "set / network-instance default protocols bgp autonomous-system 65002",
            "set / network-instance default protocols bgp router-id 2.2.2.2",
            "set / network-instance default protocols bgp afi-safi ipv4-unicast admin-state enable",
            "set / network-instance default protocols bgp group to-r1 peer-as 65001",
            "set / network-instance default protocols bgp group to-r3 peer-as 65003",
            "set / network-instance default protocols bgp neighbor 10.0.12.1 peer-group to-r1",
            "set / network-instance default protocols bgp neighbor 10.0.23.2 peer-group to-r3",
        ],
        "R3": [
            "set / network-instance default protocols bgp autonomous-system 65003",
            "set / network-instance default protocols bgp router-id 3.3.3.3",
            "set / network-instance default protocols bgp afi-safi ipv4-unicast admin-state enable",
            "set / network-instance default protocols bgp group to-r1 peer-as 65001",
            "set / network-instance default protocols bgp group to-r2 peer-as 65002",
            "set / network-instance default protocols bgp neighbor 10.0.31.1 peer-group to-r1",
            "set / network-instance default protocols bgp neighbor 10.0.23.1 peer-group to-r2",
        ],
    }

    expected_policy = [
        "set / routing-policy prefix-set bgp-loopbacks prefix 10.255.0.1/32 mask-length-range exact",
        "set / routing-policy prefix-set bgp-loopbacks prefix 10.255.0.2/32 mask-length-range exact",
        "set / routing-policy prefix-set bgp-loopbacks prefix 10.255.0.3/32 mask-length-range exact",
        "set / routing-policy policy allow-bgp-loopbacks default-action policy-result reject",
        "set / routing-policy policy allow-bgp-loopbacks statement 10 match prefix prefix-set bgp-loopbacks match-set-options any",
        "set / routing-policy policy allow-bgp-loopbacks statement 10 action policy-result accept",
    ]

    for router, config in configs.items():
        lines = config.splitlines()

        actual_bgp = [
            line for line in lines
            if " protocols bgp " in line
            and " import-policy " not in line
            and " export-policy " not in line
        ]
        actual_policy = [
            line for line in lines
            if line.startswith("set / routing-policy ")
        ]

        assert actual_bgp == expected_bgp[router]
        assert actual_policy == expected_policy

        actual_policy_attachments = [
            line for line in lines
            if line.startswith(
                "set / network-instance default protocols bgp import-policy "
            )
            or line.startswith(
                "set / network-instance default protocols bgp export-policy "
            )
        ]

        assert actual_policy_attachments == [
            "set / network-instance default protocols bgp import-policy [ allow-bgp-loopbacks ]",
            "set / network-instance default protocols bgp export-policy [ allow-bgp-loopbacks ]",
        ]
