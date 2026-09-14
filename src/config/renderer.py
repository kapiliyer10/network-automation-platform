from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader


class ConfigRenderError(Exception):
    """Raised when configuration rendering fails."""


def render_device_config(
    desired_interfaces: dict[str, dict[str, Any]],
    desired_network_instances: dict[str, dict[str, Any]],
    desired_ospf: dict[str, Any],
    template_path: str | Path,
) -> str:
    """Render interface configuration from desired state."""
    template_path = Path(template_path)

    if not template_path.is_file():
        raise ConfigRenderError(
            f"Template not found: {template_path}"
        )

    try:
        env = Environment(
            loader=FileSystemLoader(template_path.parent)
        )

        template = env.get_template(template_path.name)

        return template.render(
            interfaces=desired_interfaces,
            network_instances=desired_network_instances,
            ospf=desired_ospf,
        ).strip()

    except Exception as exc:
        raise ConfigRenderError(
            f"Failed to render configuration: {exc}"
        ) from exc

def render_all_device_configs(
        desired_state: dict[str, Any],
        template_path: str | Path,
) -> dict[str, str]:
    """Render interface configuration for every device."""
    device_configs = {}

    for device_name, device in desired_state["devices"].items():
        interfaces = device["interfaces"]
        network_instances = device.get("network_instances", {})

        device_configs[device_name] = render_device_config(
            desired_interfaces=interfaces,
            template_path=template_path,
            desired_network_instances=network_instances,
            desired_ospf=device.get("ospf", {}),
        )

    return device_configs

def write_device_configs(
    device_configs: dict[str, str],
    output_dir: str | Path,
) -> None:
    """Write rendered device configurations to .cli files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for device_name, config in device_configs.items():
        config_file = output_path / f"{device_name}.cli"
        config_file.write_text(
            config + "\n",
            encoding="utf-8",
        )
