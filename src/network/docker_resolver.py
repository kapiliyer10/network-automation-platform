from ipaddress import IPv4Address
import docker


class DockerResolverError(Exception):
    """Raised when a container's management IP cannot be resolved."""


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

    networks = container.attrs["NetworkSettings"]["Networks"]
    network = networks.get("clab")

    if network is None:
        raise DockerResolverError(
            f"Container '{container_name}' is not connected to the clab network."
        )

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