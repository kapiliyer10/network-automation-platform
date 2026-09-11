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
            "admin_state": "enable"
        },
        "ethernet-1/2": {
            "admin_state": "disable"
        },
    }

    result = render_interface_config(
        desired_interfaces=interfaces,
        template_path=TEMPLATE_FILE,
    )

    expected = (
        "set / interface ethernet-1/1 admin-state enable\n"
        "set / interface ethernet-1/2 admin-state disable"
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

    expected_config = (
        "set / interface ethernet-1/1 admin-state enable\n"
        "set / interface ethernet-1/2 admin-state enable"
    )

    assert configs["R1"] == expected_config
    assert configs["R2"] == expected_config
    assert configs["R3"] == expected_config

def test_write_device_configs(tmp_path):
    device_configs = {
        "R1": (
            "set / interface ethernet-1/1 admin-state enable\n"
            "set / interface ethernet-1/2 admin-state enable"
        ),
        "R2": (
            "set / interface ethernet-1/1 admin-state enable\n"
            "set / interface ethernet-1/2 admin-state enable"
        ),
        "R3": (
            "set / interface ethernet-1/1 admin-state enable\n"
            "set / interface ethernet-1/2 admin-state enable"
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