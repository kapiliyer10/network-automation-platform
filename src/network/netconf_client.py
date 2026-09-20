from typing import Any

from ncclient import manager
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

class NETCONFError(Exception):
    """Raised when NETCONF operations fail."""

INTERFACE_NS = "urn:nokia.com:srlinux:chassis:interfaces"
NETWORK_INSTANCE_NS = (
    "urn:nokia.com:srlinux:net-inst:network-instance"
)
OSPF_NS = "urn:nokia.com:srlinux:ospf:ospf"

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


def parse_interface_config(
    response_xml: str,
) -> dict[str, str | None]:
    """Parse interface-level configuration from a NETCONF response."""

    root = ET.fromstring(response_xml)

    interface = root.find(
        f".//{{{INTERFACE_NS}}}interface"
    )

    if interface is None:
        raise NETCONFError(
            "Interface element not found in NETCONF response"
        )

    admin_state = interface.find(
        f"{{{INTERFACE_NS}}}admin-state"
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


def parse_network_instance_interfaces(
    response_xml: str,
    network_instance_name: str,
) -> list[str]:
    """Parse interface membership from a NETCONF response."""

    root = ET.fromstring(response_xml)

    network_instances = root.findall(
        f".//{{{NETWORK_INSTANCE_NS}}}network-instance"
    )

    for network_instance in network_instances:
        name = network_instance.find(
            f"{{{NETWORK_INSTANCE_NS}}}name"
        )

        if name is not None and name.text == network_instance_name:
            interfaces = network_instance.findall(
                f"{{{NETWORK_INSTANCE_NS}}}interface"
            )

            return [
                interface_name.text
                for interface in interfaces
                if (
                    interface_name := interface.find(
                        f"{{{NETWORK_INSTANCE_NS}}}name"
                    )
                ) is not None
                and interface_name.text is not None
            ]

    raise NETCONFError(
        f"Network-instance '{network_instance_name}' "
        "not found in NETCONF response"
    )


def parse_ospf_configuration(
    response_xml: str,
    network_instance_name: str,
    ospf_instance_name: str,
) -> dict[str, Any]:
    """Parse OSPF configuration from a NETCONF response."""

    root = ET.fromstring(response_xml)

    network_instances = root.findall(
        f".//{{{NETWORK_INSTANCE_NS}}}network-instance"
    )

    for network_instance in network_instances:
        name = network_instance.find(
            f"{{{NETWORK_INSTANCE_NS}}}name"
        )

        if (
            name is None
            or name.text != network_instance_name
        ):
            continue

        ospf = network_instance.find(
            f"{{{NETWORK_INSTANCE_NS}}}protocols/"
            f"{{{OSPF_NS}}}ospf"
        )

        if ospf is None:
            break

        for instance in ospf.findall(
            f"{{{OSPF_NS}}}instance"
        ):
            instance_name = instance.find(
                f"{{{OSPF_NS}}}name"
            )

            if (
                instance_name is None
                or instance_name.text != ospf_instance_name
            ):
                continue

            admin_state = instance.find(
                f"{{{OSPF_NS}}}admin-state"
            )
            version = instance.find(
                f"{{{OSPF_NS}}}version"
            )
            router_id = instance.find(
                f"{{{OSPF_NS}}}router-id"
            )

            version_value = (
                version.text.strip()
                if version is not None
                else None
            )

            # Normalize:
            # srl_nokia-ospf-types:ospf-v2
            # -> ospf-v2
            if version_value and ":" in version_value:
                version_value = version_value.split(
                    ":", 1
                )[1]

            areas = {}

            for area in instance.findall(
                f"{{{OSPF_NS}}}area"
            ):
                area_id = area.find(
                    f"{{{OSPF_NS}}}area-id"
                )

                if (
                    area_id is None
                    or area_id.text is None
                ):
                    continue

                interfaces = []

                for interface in area.findall(
                    f"{{{OSPF_NS}}}interface"
                ):
                    interface_name = interface.find(
                        f"{{{OSPF_NS}}}interface-name"
                    )

                    if (
                        interface_name is None
                        or interface_name.text is None
                    ):
                        continue

                    parsed_interface = {
                        "name": interface_name.text.strip(),
                    }

                    passive = interface.find(
                        f"{{{OSPF_NS}}}passive"
                    )

                    if (
                        passive is not None
                        and passive.text is not None
                    ):
                        parsed_interface["passive"] = (
                            passive.text.lower() == "true"
                        )

                    interfaces.append(parsed_interface)

                areas[area_id.text] = {
                    "interfaces": interfaces,
                }

            return {
                "name": instance_name.text,
                "admin_state": (
                    admin_state.text
                    if admin_state is not None
                    else None
                ),
                "version": version_value,
                "router_id": (
                    router_id.text
                    if router_id is not None
                    else None
                ),
                "areas": areas,
            }

    raise NETCONFError(
        f"OSPF instance '{ospf_instance_name}' not found "
        f"in network-instance '{network_instance_name}'"
    )


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
    ) -> dict[str, str | None]:
        """Retrieve interface configuration from the running datastore."""

        interface_filter = f"""
        <interface
            xmlns="urn:nokia.com:srlinux:chassis:interfaces">
            <name>{interface_name}</name>
            <admin-state/>
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

            return parse_interface_config(response.data_xml)


    def get_network_instance_interfaces(
        self,
        network_instance_name: str,
    ) -> list[str]:
        """Retrieve interface membership from the running datastore."""

        network_instance_filter = f"""
        <network-instance
            xmlns="urn:nokia.com:srlinux:net-inst:network-instance">
            <name>{network_instance_name}</name>
            <interface>
                <name/>
            </interface>
        </network-instance>
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
                filter=("subtree", network_instance_filter),
            )

            return parse_network_instance_interfaces(
                response.data_xml,
                network_instance_name,
            )


    def build_interface_edit_config(
        self,
        interface_name: str,
        admin_state: str,
        ipv4_admin_state: str | None = None,
        ipv4_address: str | None = None,
    ) -> str:
        """Build a NETCONF edit-config payload for an interface."""

        interface_name = escape(interface_name)
        admin_state = escape(admin_state)
        ipv4_config = ""

        if ipv4_admin_state is not None and ipv4_address is not None:
            ipv4_admin_state = escape(ipv4_admin_state)
            ipv4_address = escape(ipv4_address)

            ipv4_config = f"""
            <subinterface>
                <index>0</index>
                <ipv4>
                    <admin-state>{ipv4_admin_state}</admin-state>
                    <address>
                        <ip-prefix>{ipv4_address}</ip-prefix>
                    </address>
                </ipv4>
            </subinterface>"""


        return f"""<config
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <interface
            xmlns="urn:nokia.com:srlinux:chassis:interfaces"
            nc:operation="merge">
            <name>{interface_name}</name>
            <admin-state>{admin_state}</admin-state>{ipv4_config}
        </interface>
    </config>"""


    def build_network_instance_interface_edit_config(
        self,
        network_instance_name: str,
        interface_name: str,
    ) -> str:
        """Build a NETCONF edit-config payload for network-instance membership."""

        network_instance_name = escape(network_instance_name)
        interface_name = escape(interface_name)

        return f"""<config
            xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
            xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <network-instance
                xmlns="urn:nokia.com:srlinux:net-inst:network-instance"
                nc:operation="merge">
                <name>{network_instance_name}</name>
                <interface nc:operation="merge">
                    <name>{interface_name}</name>
                </interface>
            </network-instance>
        </config>"""


    def get_ospf_configuration(
        self,
        network_instance_name: str,
        ospf_instance_name: str,
    ) -> dict[str, Any]:
        """Retrieve OSPF configuration from the running datastore."""

        ospf_filter = f"""
        <network-instance
            xmlns="urn:nokia.com:srlinux:net-inst:network-instance">
            <name>{network_instance_name}</name>
            <protocols>
                <ospf
                    xmlns="urn:nokia.com:srlinux:ospf:ospf">
                    <instance>
                        <name>{ospf_instance_name}</name>
                        <admin-state/>
                        <version/>
                        <router-id/>
                        <area>
                            <area-id/>
                            <interface/>
                        </area>
                    </instance>
                </ospf>
            </protocols>
        </network-instance>
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
                filter=("subtree", ospf_filter),
            )

            return parse_ospf_configuration(
                response.data_xml,
                network_instance_name,
                ospf_instance_name,
            )


    def build_ospf_instance_edit_config(
        self,
        network_instance_name: str,
        ospf_instance_name: str,
        admin_state: str,
        version: str,
        router_id: str,
    ) -> str:
        """Build a NETCONF edit-config payload for an OSPF instance."""

        network_instance_name = escape(network_instance_name)
        ospf_instance_name = escape(ospf_instance_name)
        admin_state = escape(admin_state)
        version = escape(version)
        router_id = escape(router_id)

        return f"""<config
            xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
            xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <network-instance
                xmlns="urn:nokia.com:srlinux:net-inst:network-instance"
                nc:operation="merge">
                <name>{network_instance_name}</name>
                <protocols>
                    <ospf
                        xmlns="urn:nokia.com:srlinux:ospf:ospf"
                        nc:operation="merge">
                        <instance nc:operation="merge">
                            <name>{ospf_instance_name}</name>
                            <admin-state>{admin_state}</admin-state>
                            <version
                                xmlns:srl_nokia-ospf-types="urn:nokia.com:srlinux:general:ospf-types">
                                {version}
                            </version>
                            <router-id>{router_id}</router-id>
                        </instance>
                    </ospf>
                </protocols>
            </network-instance>
        </config>"""


    def build_ospf_area_interface_edit_config(
        self,
        network_instance_name: str,
        ospf_instance_name: str,
        area_id: str,
        interface_name: str,
        passive: bool = False,
    ) -> str:
        """Build a NETCONF edit-config payload for an OSPF area interface."""

        network_instance_name = escape(network_instance_name)
        ospf_instance_name = escape(ospf_instance_name)
        area_id = escape(area_id)
        interface_name = escape(interface_name)

        passive_config = (
            "<passive>true</passive>"
            if passive
            else ""
        )

        return f"""<config
            xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"
            xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <network-instance
                xmlns="urn:nokia.com:srlinux:net-inst:network-instance"
                nc:operation="merge">
                <name>{network_instance_name}</name>
                <protocols>
                    <ospf
                        xmlns="urn:nokia.com:srlinux:ospf:ospf"
                        nc:operation="merge">
                        <instance nc:operation="merge">
                            <name>{ospf_instance_name}</name>
                            <area nc:operation="merge">
                                <area-id>{area_id}</area-id>
                                <interface nc:operation="merge">
                                    <interface-name>{interface_name}</interface-name>
                                    {passive_config}
                                </interface>
                            </area>
                        </instance>
                    </ospf>
                </protocols>
            </network-instance>
        </config>"""


    def edit_config(self, config_xml: str) -> Any:
            """Apply configuration to the candidate datastore."""

            with manager.connect(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                hostkey_verify=False,
                allow_agent=False,
                look_for_keys=False,
            ) as session:

                response = session.edit_config(
                    target="candidate",
                    config=config_xml,
                )

                return response


    def commit(self) -> Any:
        """Commit the candidate configuration."""

        with manager.connect(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            hostkey_verify=False,
            allow_agent=False,
            look_for_keys=False,
        ) as session:

            response = session.commit()

            return response
