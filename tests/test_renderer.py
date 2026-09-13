from pathlib import Path

from src.config.renderer import render_interface_config
from src.config.renderer import render_all_device_configs
from src.desired.loader import load_desired_state
from src.config.renderer import write_device_configs

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_FILE = (
    PROJECT_ROOT / "templates" / "srlinux" / "interfaces.cli.j2"
)


def test_render_interface_config():
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

    result = render_interface_config(
        desired_interfaces=interfaces,
        template_path=TEMPLATE_FILE,
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
            "set / interface ethernet-1/2 subinterface 0 ipv4 address 10.0.31.1/30"
        ),
        "R2": (
            "set / interface ethernet-1/1 admin-state enable\n"
            "set / interface ethernet-1/1 subinterface 0 ipv4 admin-state enable\n"
            "set / interface ethernet-1/1 subinterface 0 ipv4 address 10.0.12.2/30\n"
            "set / interface ethernet-1/2 admin-state enable\n"
            "set / interface ethernet-1/2 subinterface 0 ipv4 admin-state enable\n"
            "set / interface ethernet-1/2 subinterface 0 ipv4 address 10.0.23.1/30"
        ),
        "R3": (
            "set / interface ethernet-1/1 admin-state enable\n"
            "set / interface ethernet-1/1 subinterface 0 ipv4 admin-state enable\n"
            "set / interface ethernet-1/1 subinterface 0 ipv4 address 10.0.23.2/30\n"
            "set / interface ethernet-1/2 admin-state enable\n"
            "set / interface ethernet-1/2 subinterface 0 ipv4 admin-state enable\n"
            "set / interface ethernet-1/2 subinterface 0 ipv4 address 10.0.31.2/30"
        ),
    }

    assert configs == expected_configs


def test_write_device_configs(tmp_path):
    device_configs = {
        "R1": (
            "set / interface ethernet-1/1 admin-state enable\n"
            "set / interface ethernet-1/1 subinterface 0 ipv4 admin-state enable\n"
            "set / interface ethernet-1/1 subinterface 0 ipv4 address 10.0.12.1/30\n"
            "set / interface ethernet-1/2 admin-state enable\n"
            "set / interface ethernet-1/2 subinterface 0 ipv4 admin-state enable\n"
            "set / interface ethernet-1/2 subinterface 0 ipv4 address 10.0.31.1/30"
        ),
        "R2": (
            "set / interface ethernet-1/1 admin-state enable\n"
            "set / interface ethernet-1/1 subinterface 0 ipv4 admin-state enable\n"
            "set / interface ethernet-1/1 subinterface 0 ipv4 address 10.0.12.2/30\n"
            "set / interface ethernet-1/2 admin-state enable\n"
            "set / interface ethernet-1/2 subinterface 0 ipv4 admin-state enable\n"
            "set / interface ethernet-1/2 subinterface 0 ipv4 address 10.0.23.1/30"
        ),
        "R3": (
            "set / interface ethernet-1/1 admin-state enable\n"
            "set / interface ethernet-1/1 subinterface 0 ipv4 admin-state enable\n"
            "set / interface ethernet-1/1 subinterface 0 ipv4 address 10.0.23.2/30\n"
            "set / interface ethernet-1/2 admin-state enable\n"
            "set / interface ethernet-1/2 subinterface 0 ipv4 admin-state enable\n"
            "set / interface ethernet-1/2 subinterface 0 ipv4 address 10.0.31.2/30"
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
