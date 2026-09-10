from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader


class ConfigRenderError(Exception):
    """Raised when configuration rendering fails."""


def render_interface_config(
    desired_interfaces: dict[str, dict[str, Any]],
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
            interfaces=desired_interfaces
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

        device_configs[device_name] = render_interface_config(
            desired_interfaces=interfaces,
            template_path=template_path,
        )

    return device_configs
