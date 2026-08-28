import docker
import pytest

from src.network.docker_resolver import (
    DockerResolverError,
    resolve_container_ip,
)


@pytest.mark.parametrize(
    "container_name",
    [
        "clab-srl-lab-R1",
        "clab-srl-lab-R2",
        "clab-srl-lab-R3",
    ],
)
def test_resolve_container_ip_matches_docker(container_name):
    client = docker.from_env()

    container = client.containers.get(container_name)
    expected_ip = container.attrs["NetworkSettings"]["Networks"]["clab"]["IPAddress"]

    actual_ip = resolve_container_ip(container_name)

    assert actual_ip == expected_ip


def test_resolve_unknown_container():
    with pytest.raises(DockerResolverError, match="Container not found"):
        resolve_container_ip("clab-srl-lab-does-not-exist")