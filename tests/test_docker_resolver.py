from types import SimpleNamespace

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

    networks = (
        container.attrs.get("NetworkSettings", {})
        .get("Networks", {})
    )
    network = networks.get("clab")

    if network is None or not network.get("IPAddress"):
        network_mode = container.attrs.get("HostConfig", {}).get(
            "NetworkMode", ""
        )
        assert network_mode.startswith("container:"), network_mode

        holder_name = network_mode.partition(":")[2]
        holder = client.containers.get(holder_name)
        holder_networks = (
            holder.attrs.get("NetworkSettings", {})
            .get("Networks", {})
        )
        network = holder_networks.get("clab")

    assert network is not None and network.get("IPAddress")
    expected_ip = network["IPAddress"]

    actual_ip = resolve_container_ip(container_name)

    assert actual_ip == expected_ip


class _FakeContainer:
    def __init__(self, networks, network_mode="bridge", status="running"):
        self.status = status
        self.attrs = {
            "NetworkSettings": {"Networks": networks},
            "HostConfig": {"NetworkMode": network_mode},
        }


class _FakeContainerCollection:
    def __init__(self, containers):
        self._containers = containers

    def get(self, name):
        try:
            return self._containers[name]
        except KeyError as exc:
            raise docker.errors.NotFound(
                f"Container not found: {name}"
            ) from exc


def _patch_docker_client(monkeypatch, containers):
    client = SimpleNamespace(
        containers=_FakeContainerCollection(containers)
    )
    monkeypatch.setattr(
        "src.network.docker_resolver.docker.from_env",
        lambda: client,
    )


def test_resolve_container_ip_from_direct_clab_network(monkeypatch):
    container_name = "clab-srl-lab-R1"

    container = _FakeContainer({
        "clab": {"IPAddress": "172.20.20.4"}
    })

    _patch_docker_client(monkeypatch, {
        container_name: container,
    })

    assert resolve_container_ip(container_name) == "172.20.20.4"


def test_resolve_container_ip_from_network_namespace_holder(monkeypatch):
    container_name = "clab-srl-lab-R1"
    holder_name = "clab-srl-lab-R1-netns"

    router = _FakeContainer(
        networks={},
        network_mode=f"container:{holder_name}",
    )

    holder = _FakeContainer({
        "clab": {"IPAddress": "172.20.20.4"}
    })

    _patch_docker_client(monkeypatch, {
        container_name: router,
        holder_name: holder,
    })

    assert resolve_container_ip(container_name) == "172.20.20.4"


def test_resolve_unknown_container(monkeypatch):
    _patch_docker_client(monkeypatch, {})

    with pytest.raises(DockerResolverError, match="Container not found"):
        resolve_container_ip("clab-srl-lab-does-not-exist")
