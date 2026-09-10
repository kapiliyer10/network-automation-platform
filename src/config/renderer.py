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
