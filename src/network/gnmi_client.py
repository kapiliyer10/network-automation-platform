from typing import Any

from pygnmi.client import gNMIclient


class GNMIError(Exception):
    """Raised when a gNMI operation fails."""


class GNMIClient:
    """Small wrapper around pyGNMI for SR Linux."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
    ) -> None:
        self.target = (host, port)
        self.username = username
        self.password = password

    def get(self, paths: list[str]) -> dict[str, Any]:
        """Retrieve data from the device using gNMI Get."""
        try:
            with gNMIclient(
                target=self.target,
                username=self.username,
                password=self.password,
                insecure=True,
            ) as client:
                return client.get(
                    path=paths,
                    encoding="json_ietf",
                )
        except Exception as exc:
            raise GNMIError(
                f"gNMI Get failed for {self.target}: {exc}"
            ) from exc

    def get_interface_oper_state(self, interface_name: str) -> str:
        """Return the operational state of an interface."""
        path = f"/interface[name={interface_name}]/oper-state"

        result = self.get([path])

        try:
            return result["notification"][0]["update"][0]["val"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GNMIError(
                f"Unable to extract oper-state for {interface_name}"
            ) from exc

    def get_ospf_interfaces(self) -> list[dict]:
        """Return OSPF interfaces in area 0."""

        path = (
            "/network-instance[name=default]/"
            "protocols/srl_nokia-ospf:ospf/"
            "instance[name=default]/"
            "area[area-id=0.0.0.0]/"
            "interface"
        )

        result = self.get([path])

        try:
            return result["notification"][0]["update"][0]["val"]["interface"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GNMIError(
                f"Unable to extract OSPF interfaces from device {self.target}"
            ) from exc

    def get_ospf_neighbors(self, interface_name: str) -> list[dict[str, str]]:
        """Return OSPF neighbors for an interface."""
        path = (
            "/network-instance[name=default]/"
            "protocols/srl_nokia-ospf:ospf/"
            "instance[name=default]/"
            "area[area-id=0.0.0.0]/"
            f"interface[interface-name={interface_name}]/"
            "neighbor"
    )


        result = self.get([path])

        if not result.get("notification"):
            raise GNMIError(
                f"Unable to extract OSPF neighbors for {interface_name}"
            )
        notification = result["notification"][0]

        if "update" not in notification:
            return []
        
        try:
            neighbors = notification["update"][0]["val"]["neighbor"]
            
        except (KeyError, IndexError, TypeError) as exc:
            raise GNMIError(
                f"Unable to extract OSPF neighbors for {interface_name}"
            ) from exc
        
        return [
            {
                "router_id": neighbor["router-id"],
                "address": neighbor["address"],
                "state": neighbor["adjacency-state"].split(":")[-1],
            }
            for neighbor in neighbors
        ]

    def get_all_ospf_neighbors(self) -> list[dict[str, str]]:
        """Return all OSPF neighbors on the device."""

        interfaces = self.get_ospf_interfaces()

        neighbors = []

        for interface in interfaces:
            interface_name = interface["interface-name"]

            interface_neighbors = self.get_ospf_neighbors(interface_name)

            for neighbor in interface_neighbors:
                neighbors.append(
                    {
                        "interface": interface_name,
                        "router_id": neighbor["router_id"],
                        "address": neighbor["address"],
                        "state": neighbor["state"],
                 }
                )

        return neighbors