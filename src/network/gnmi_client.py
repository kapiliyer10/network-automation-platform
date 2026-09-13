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

    def get_hostname(self) -> str:
        """Return the device hostname."""
        result = self.get(["/system/name"])

        try:
            return result["notification"][0]["update"][0]["val"]["host-name"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GNMIError(
                f"Unable to extract hostname from device {self.target}"
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

    def get_interfaces(self) -> list[dict[str, str]]:
        """Return discovered interfaces with administrative and operational state."""
        result = self.get(["/interface"])
        try:
            interfaces = result["notification"][0]["update"][0]["val"]["srl_nokia-interfaces:interface"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GNMIError(
                f"Unable to extract interfaces from device {self.target}"
            ) from exc

        return [
            {
                "name": interface["name"],
                "admin_state": interface["admin-state"],
                "oper_state": interface["oper-state"],
            }
            for interface in interfaces
        ]

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

    def get_ip_addresses(self) -> list[dict[str, str | int]]:
        """Return discovered IPv4 addresses and their interface/subinterface."""
        result = self.get(["/interface/subinterface/ipv4"])

        try:
            interfaces = result["notification"][0]["update"][0]["val"]["srl_nokia-interfaces:interface"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GNMIError(
                f"Unable to extract IP addresses from device {self.target}"
            ) from exc

        addresses = []

        for interface in interfaces:
            interface_name = interface["name"]

            for subinterface in interface.get("subinterface", []):
                subinterface_index = subinterface["index"]

                ipv4 = subinterface.get("ipv4", {})
                for address in ipv4.get("address", []):
                    addresses.append(
                        {
                            "interface": interface_name,
                            "subinterface_index": subinterface_index,
                            "ip_address": address["ip-prefix"],
                            "origin": address["origin"],
                            "status": address["status"],

                        }
                    )

        return addresses

    def get_routes(self) -> list[dict[str, str | int | bool]]:
        """Return discovered IPv4 routes from the default network instance."""

        result = self.get([
            "/network-instance[name=default]/route-table"
        ])

        try:
            routes = result["notification"][0]["update"][0]["val"][
            "srl_nokia-ip-route-tables:ipv4-unicast"]["route"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GNMIError(
                f"Unable to extract routes from device {self.target}"
            ) from exc

        return [
            {
                "prefix": route["ipv4-prefix"],
                "active": route["active"],
                "metric": route["metric"],
                "preference": route["preference"],
                "route_type": route["route-type"].split(":")[-1],
            }
            for route in routes
        ]

    def get_interface_ipv4(self, interface_name: str) -> dict[str, Any]:
        """Return IPv4 state for interface subinterface 0."""
        result = self.get([
            f"/interface[name={interface_name}]/"
            "subinterface[index=0]/ipv4"
        ])

        try:
            ipv4 = result["notification"][0]["update"][0]["val"]

            address = ipv4.get("address", [])

            return {
                "admin_state": ipv4["admin-state"],
                "address": address[0]["ip-prefix"] if address else None,
            }

        except (KeyError, IndexError, TypeError) as exc:
            raise GNMIError(
                f"Unable to extract IPv4 state for interface "
                f"{interface_name} from device {self.target}"
            ) from exc


    def get_network_instance_interfaces(
        self,
        network_instance_name: str,
    ) -> list[dict[str, str]]:
        """Return interfaces associated with a network instance."""
        result = self.get([
            f"/network-instance[name={network_instance_name}]/interface"
        ])

        try:
            interfaces = result["notification"][0]["update"][0]["val"][
                "interface"
            ]
        except (KeyError, IndexError, TypeError) as exc:
            raise GNMIError(
                f"Unable to extract interfaces for network instance "
                f"{network_instance_name} from device {self.target}"
            ) from exc

        return [
            {
                "name": interface["name"],
                "oper_state": interface["oper-state"],
            }
            for interface in interfaces
        ]
