from src.config.netconf_renderer import build_device_netconf_configs
from src.network.netconf_client import NETCONFClient


class NETCONFApplyError(Exception):
    """Raised when NETCONF configuration application fails."""


def apply_device_netconf_config(
    client: NETCONFClient,
    desired_interfaces: dict,
    desired_network_instances: dict,
    desired_ospf: dict | None,
) -> None:
    """Apply all generated NETCONF configuration and commit once."""

    configs = build_device_netconf_configs(
        client=client,
        desired_interfaces=desired_interfaces,
        desired_network_instances=desired_network_instances,
        desired_ospf=desired_ospf,
    )

    for config in configs:
        client.edit_config(config)

    client.commit()
