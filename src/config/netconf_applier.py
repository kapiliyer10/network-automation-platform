from src.config.netconf_renderer import build_device_netconf_configs
from src.network.netconf_client import NETCONFClient


class NETCONFApplyError(Exception):
    """Raised when NETCONF configuration application fails."""


def apply_device_netconf_config(
    client: NETCONFClient,
    desired_interfaces: dict,
    desired_network_instances: dict,
    desired_ospf: dict | None,
    desired_bgp: dict | None = None,
    desired_routing_policies: dict | None = None,
) -> None:
    """Apply all generated NETCONF configuration and commit once."""

    configs = build_device_netconf_configs(
        client=client,
        desired_interfaces=desired_interfaces,
        desired_network_instances=desired_network_instances,
        desired_ospf=desired_ospf,
        desired_bgp=desired_bgp,
        desired_routing_policies=desired_routing_policies,
    )

    for config in configs:
        client.edit_config(config)

    client.commit()
