from pathlib import Path

from src.config.renderer import render_interface_config


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
