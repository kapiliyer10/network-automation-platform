from ipaddress import IPv4Address

import docker


class DockerResolverError(Exception):
    """Raised when a container's management IP cannot be resolved."""


def _get_clab_network(container):
    """Return the container's clab network details, if directly attached."""
    network_settings = container.attrs.get("NetworkSettings") or {}
    networks = network_settings.get("Networks") or {}
    return networks.get("clab")


def _resolve_management_network(container_name, container, client):
    """Resolve clab network details from the container or its namespace holder."""
    network = _get_clab_network(container)

    if network is not None and network.get("IPAddress"):
        return network

    host_config = container.attrs.get("HostConfig") or {}
    network_mode = host_config.get("NetworkMode", "")

    if not network_mode.startswith("container:"):
        if network is None:
            raise DockerResolverError(
                f"Container '{container_name}' is not connected to the clab network."
            )
        return network

    holder_name = network_mode.partition(":")[2]

    if not holder_name:
        raise DockerResolverError(
            f"Container '{container_name}' has an invalid "
            f"network namespace mode: {network_mode}"
        )

    try:
        holder = client.containers.get(holder_name)
    except docker.errors.NotFound as exc:
        raise DockerResolverError(
            f"Network namespace holder '{holder_name}' "
            f"for '{container_name}' was not found."
        ) from exc

    if holder.status != "running":
        raise DockerResolverError(
            f"Network namespace holder is not running: {holder_name}"
        )

    network = _get_clab_network(holder)

    if network is None:
        raise DockerResolverError(
            f"Network namespace holder '{holder_name}' "
            f"for '{container_name}' is not connected to the clab network."
        )

    return network


def resolve_container_ip(container_name: str) -> str:
    """Return the IPv4 address of a running container on the clab network."""
    client = docker.from_env()

    try:
        container = client.containers.get(container_name)
    except docker.errors.NotFound as exc:
        raise DockerResolverError(
            f"Container not found: {container_name}"
        ) from exc

    if container.status != "running":
        raise DockerResolverError(
            f"Container is not running: {container_name}"
        )

    network = _resolve_management_network(container_name, container, client)

    ip_address = network.get("IPAddress")

    if not ip_address:
        raise DockerResolverError(
            f"No IPv4 address found for '{container_name}' on clab."
        )

    try:
        IPv4Address(ip_address)
    except ValueError as exc:
        raise DockerResolverError(
            f"Invalid IPv4 address for '{container_name}': {ip_address}"
        ) from exc

    return ip_address
