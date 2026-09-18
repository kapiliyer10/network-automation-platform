from typing import Any

from ncclient import manager
import xml.etree.ElementTree as ET

class NETCONFError(Exception):
    """Raised when NETCONF operations fail."""

INTERFACE_NS = "urn:nokia.com:srlinux:chassis:interfaces"

def parse_interface_ipv4(response_xml: str) -> dict[str, str | None]:
        """Parse IPv4 data from a NETCONF interface response."""

        root = ET.fromstring(response_xml)

        interface = root.find(
            f".//{{{INTERFACE_NS}}}interface"
        )

        if interface is None:
            raise NETCONFError(
                "Interface element not found in NETCONF response"
            )

        subinterface = interface.find(
            f"{{{INTERFACE_NS}}}subinterface"
        )

        if subinterface is None:
            raise NETCONFError(
                "Subinterface element not found in NETCONF response"
            )

        ipv4 = subinterface.find(
            f"{{{INTERFACE_NS}}}ipv4"
        )

        if ipv4 is None:
            raise NETCONFError(
                "IPv4 element not found in NETCONF response"
            )

        admin_state = ipv4.find(
            f"{{{INTERFACE_NS}}}admin-state"
        )

        addresses = ipv4.findall(
            f"{{{INTERFACE_NS}}}address"
        )

        return {
            "admin_state": (
                admin_state.text
                if admin_state is not None
                else None
            ),
            "address": (
                addresses[0].find(
                    f"{{{INTERFACE_NS}}}ip-prefix"
                ).text
                if addresses
                and addresses[0].find(
                    f"{{{INTERFACE_NS}}}ip-prefix"
                ) is not None
                else None
            ),
        }

class NETCONFClient:
    """Small wrapper around ncclient for SR Linux."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def get_capabilities(self) -> list[str]:
        """Connect to the device and return server capabilities."""
        try:
            with manager.connect(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                hostkey_verify=False,
                allow_agent=False,
                look_for_keys=False,
            ) as session:
                return list(session.server_capabilities)

        except Exception as exc:
            raise NETCONFError(
                f"Unable to connect to NETCONF server "
                f"{self.host}:{self.port}"
            ) from exc


    def get_yang_library(self) -> str:
        """Retrieve the device YANG library as XML."""

        yang_library_filter = """
        <yang-library
            xmlns="urn:ietf:params:xml:ns:yang:ietf-yang-library"/>
        """

        
        with manager.connect(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            hostkey_verify=False,
            allow_agent=False,
            look_for_keys=False,
        ) as session:
            response = session.get(
                filter=("subtree", yang_library_filter)
            )

            return response.data_xml


    def get_schema(
        self,
        module_name: str,
        version: str | None = None,
    ) -> str:
        """Retrieve a YANG module schema from the device."""

        with manager.connect(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            hostkey_verify=False,
            allow_agent=False,
            look_for_keys=False,
        ) as session:

            response = session.get_schema(
                module_name,
                version=version,
            )

            return response.data


    def get_interface_ipv4(
        self,
        interface_name: str,
        subinterface_index: int = 0,
    ) -> dict[str, str | None]:
        """Retrieve IPv4 data for a subinterface as XML."""

        interface_filter = f"""
        <interface
            xmlns="urn:nokia.com:srlinux:chassis:interfaces">
            <name>{interface_name}</name>
            <subinterface>
                <index>{subinterface_index}</index>
                <ipv4>
                <admin-state/>
                <address/>
                </ipv4>
            </subinterface>
        </interface>
        """

        with manager.connect(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            hostkey_verify=False,
            allow_agent=False,
            look_for_keys=False,
        ) as session:

            response = session.get(
                filter=("subtree", interface_filter)
            )

            return parse_interface_ipv4(response.data_xml)


    def get_interface_config(
        self,
        interface_name: str,
        subinterface_index: int = 0,
    ) -> str:
        """Retrieve interface configuration from the running datastore."""

        interface_filter = f"""
        <interface
            xmlns="urn:nokia.com:srlinux:chassis:interfaces">
            <name>{interface_name}</name>
            <subinterface>
                <index>{subinterface_index}</index>
            </subinterface>
        </interface>
        """

        with manager.connect(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            hostkey_verify=False,
            allow_agent=False,
            look_for_keys=False,
        ) as session:

            response = session.get_config(
                source="running",
                filter=("subtree", interface_filter),
            )

            return parse_interface_ipv4(response.data_xml)