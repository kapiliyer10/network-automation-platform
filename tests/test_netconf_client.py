from unittest.mock import patch

from src.network.netconf_client import (
    NETCONFClient,
    parse_interface_ipv4,
    parse_interface_config,
    parse_network_instance_interfaces,
    parse_ospf_configuration,)

def test_get_capabilities():
    fake_session = type(
        "FakeSession",
        (),
        {
            "server_capabilities": [
                "urn:ietf:params:netconf:base:1.0",
                "urn:ietf:params:netconf:base:1.1",
            ]
        },
    )()

    class FakeContextManager:
        def __enter__(self):
            return fake_session

        def __exit__(self, exc_type, exc, tb):
            return False

    with patch(
        "src.network.netconf_client.manager.connect",
        return_value=FakeContextManager(),
    ) as mock_connect:

        client = NETCONFClient(
            host="172.20.20.4",
            port=830,
            username="test-user",
            password="test-password",
        )

        capabilities = client.get_capabilities()

    assert capabilities == [
        "urn:ietf:params:netconf:base:1.0",
        "urn:ietf:params:netconf:base:1.1",
    ]

    mock_connect.assert_called_once()


def test_get_yang_library():
    fake_response = type(
        "FakeResponse",
        (),
        {
            "data_xml": (
                "<data>"
                "<yang-library "
                'xmlns="urn:ietf:params:xml:ns:yang:ietf-yang-library">'
                "</yang-library>"
                "</data>"
            )
        },
    )()

    class FakeSession:
        def get(self, filter):
            assert filter[0] == "subtree"
            assert "ietf-yang-library" in filter[1]
            return fake_response

    class FakeContextManager:
        def __enter__(self):
            return FakeSession()

        def __exit__(self, exc_type, exc, tb):
            return False

    with patch(
        "src.network.netconf_client.manager.connect",
        return_value=FakeContextManager(),
    ):
        client = NETCONFClient(
            host="172.20.20.4",
            port=830,
            username="test-user",
            password="test-password",
        )

        result = client.get_yang_library()

    assert "<yang-library" in result


def test_parse_interface_ipv4():
    response_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <data xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
        <interface xmlns="urn:nokia.com:srlinux:chassis:interfaces">
            <name>ethernet-1/1</name>
            <subinterface>
                <index>0</index>
                <ipv4>
                    <admin-state>enable</admin-state>
                    <address>
                        <ip-prefix>10.0.12.1/30</ip-prefix>
                        <origin>static</origin>
                        <primary/>
                        <status>preferred</status>
                    </address>
                </ipv4>
            </subinterface>
        </interface>
    </data>
    """

    result = parse_interface_ipv4(response_xml)

    assert result == {
        "admin_state": "enable",
        "address": "10.0.12.1/30",
    }


def test_get_interface_config():
    fake_response = type(
        "FakeResponse",
        (),
        {
            "data_xml": """<?xml version="1.0" encoding="UTF-8"?>
            <data xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
                <interface xmlns="urn:nokia.com:srlinux:chassis:interfaces">
                    <name>ethernet-1/1</name>
                    <admin-state>enable</admin-state>
                    <subinterface>
                        <index>0</index>
                        <ipv4>
                            <admin-state>enable</admin-state>
                            <address>
                                <ip-prefix>10.0.12.1/30</ip-prefix>
                            </address>
                        </ipv4>
                    </subinterface>
                </interface>
            </data>
            """,
        },
    )()

    class FakeSession:
        def get_config(self, source, filter):
            assert source == "running"
            assert filter[0] == "subtree"
            assert "ethernet-1/1" in filter[1]
            assert "<index>0</index>" in filter[1]
            return fake_response

    class FakeContextManager:
        def __enter__(self):
            return FakeSession()

        def __exit__(self, exc_type, exc, tb):
            return False

    with patch(
        "src.network.netconf_client.manager.connect",
        return_value=FakeContextManager(),
    ):
        client = NETCONFClient(
            host="test-host",
            port=830,
            username="test-user",
            password="test-password",
        )

        result = client.get_interface_config(
            interface_name="ethernet-1/1",
            subinterface_index=0,
        )

    assert result == {
        "name": "ethernet-1/1",
        "admin_state": "enable",
        "ipv4": {
            "admin_state": "enable",
            "address": "10.0.12.1/30",
        },
    }


def test_build_interface_edit_config():
    client = NETCONFClient(
        host="test-host",
        port=830,
        username="test-user",
        password="test-password",
    )

    result = client.build_interface_edit_config(
        interface_name="ethernet-1/1",
        admin_state="enable",
    )

    assert "<config" in result
    assert 'xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"' in result
    assert 'xmlns="urn:nokia.com:srlinux:chassis:interfaces"' in result
    assert 'nc:operation="merge"' in result
    assert "<name>ethernet-1/1</name>" in result
    assert "<admin-state>enable</admin-state>" in result


def test_build_interface_edit_config_with_ipv4():
    client = NETCONFClient(
        host="test-host",
        port=830,
        username="test-user",
        password="test-password",
    )

    result = client.build_interface_edit_config(
        interface_name="ethernet-1/1",
        admin_state="enable",
        ipv4_admin_state="enable",
        ipv4_address="10.0.12.1/30",
    )

    assert "<subinterface>" in result
    assert "<index>0</index>" in result
    assert "<ipv4>" in result
    assert "<admin-state>enable</admin-state>" in result
    assert "<ip-prefix>10.0.12.1/30</ip-prefix>" in result


def test_edit_config():
    class FakeSession:
        def edit_config(self, target, config):
            assert target == "candidate"
            assert "<config" in config
            assert "<name>ethernet-1/1</name>" in config
            assert "<admin-state>enable</admin-state>" in config

            return type("FakeResponse", (), {"ok": True})()

    class FakeContextManager:
        def __enter__(self):
            return FakeSession()

        def __exit__(self, exc_type, exc, tb):
            return False

    with patch(
        "src.network.netconf_client.manager.connect",
        return_value=FakeContextManager(),
    ):
        client = NETCONFClient(
            host="test-host",
            port=830,
            username="test-user",
            password="test-password",
        )

        config_xml = client.build_interface_edit_config(
            interface_name="ethernet-1/1",
            admin_state="enable",
        )

        response = client.edit_config(config_xml)

    assert response.ok is True


def test_commit():
    class FakeSession:
        def commit(self):
            return type("FakeResponse", (), {"ok": True})()

    class FakeContextManager:
        def __enter__(self):
            return FakeSession()

        def __exit__(self, exc_type, exc, tb):
            return False

    with patch(
        "src.network.netconf_client.manager.connect",
        return_value=FakeContextManager(),
    ):
        client = NETCONFClient(
            host="test-host",
            port=830,
            username="test-user",
            password="test-password",
        )

        response = client.commit()

    assert response.ok is True


def test_parse_interface_config():
    response_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <data xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
        <interface xmlns="urn:nokia.com:srlinux:chassis:interfaces">
            <name>ethernet-1/1</name>
            <admin-state>enable</admin-state>
            <subinterface>
                <index>0</index>
                <ipv4>
                    <admin-state>enable</admin-state>
                    <address>
                        <ip-prefix>10.0.12.1/30</ip-prefix>
                    </address>
                </ipv4>
            </subinterface>
        </interface>
    </data>
    """

    result = parse_interface_config(response_xml)

    assert result == {
        "name": "ethernet-1/1",
        "admin_state": "enable",
        "ipv4": {
            "admin_state": "enable",
            "address": "10.0.12.1/30",
        },
    }


def test_parse_network_instance_interfaces():
    response_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <data xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
        <network-instance
            xmlns="urn:nokia.com:srlinux:net-inst:network-instance">
            <name>default</name>
            <interface>
                <name>ethernet-1/1.0</name>
            </interface>
            <interface>
                <name>ethernet-1/2.0</name>
            </interface>
            <interface>
                <name>lo0.0</name>
            </interface>
        </network-instance>
    </data>
    """

    result = parse_network_instance_interfaces(
        response_xml,
        "default",
    )

    assert result == [
        "ethernet-1/1.0",
        "ethernet-1/2.0",
        "lo0.0",
    ]


def test_build_network_instance_interface_edit_config():
    client = NETCONFClient(
        host="test-host",
        port=830,
        username="test-user",
        password="test-password",
    )

    result = client.build_network_instance_interface_edit_config(
        network_instance_name="default",
        interface_name="ethernet-1/1.0",
    )

    assert "<config" in result
    assert 'xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"' in result
    assert (
        'xmlns="urn:nokia.com:srlinux:net-inst:network-instance"'
        in result
    )
    assert 'nc:operation="merge"' in result
    assert "<name>default</name>" in result
    assert "<name>ethernet-1/1.0</name>" in result


def test_get_network_instance_interfaces():
    fake_response = type(
        "FakeResponse",
        (),
        {
            "data_xml": """<?xml version="1.0" encoding="UTF-8"?>
            <data xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
                <network-instance
                    xmlns="urn:nokia.com:srlinux:net-inst:network-instance">
                    <name>default</name>
                    <interface>
                        <name>ethernet-1/1.0</name>
                    </interface>
                    <interface>
                        <name>ethernet-1/2.0</name>
                    </interface>
                    <interface>
                        <name>lo0.0</name>
                    </interface>
                </network-instance>
            </data>
            """,
        },
    )()

    class FakeSession:
        def get_config(self, source, filter):
            assert source == "running"
            assert filter[0] == "subtree"
            assert "network-instance" in filter[1]
            assert "<name>default</name>" in filter[1]
            return fake_response

    class FakeContextManager:
        def __enter__(self):
            return FakeSession()

        def __exit__(self, exc_type, exc, tb):
            return False

    with patch(
        "src.network.netconf_client.manager.connect",
        return_value=FakeContextManager(),
    ):
        client = NETCONFClient(
            host="test-host",
            port=830,
            username="test-user",
            password="test-password",
        )

        result = client.get_network_instance_interfaces("default")

    assert result == [
        "ethernet-1/1.0",
        "ethernet-1/2.0",
        "lo0.0",
    ]


def test_parse_ospf_configuration():
    response_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <data xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
        <network-instance
            xmlns="urn:nokia.com:srlinux:net-inst:network-instance">
            <name>default</name>
            <protocols>
                <ospf
                    xmlns="urn:nokia.com:srlinux:ospf:ospf">
                    <instance>
                        <name>default</name>
                        <admin-state>enable</admin-state>
                        <version>
                            srl_nokia-ospf-types:ospf-v2
                        </version>
                        <router-id>1.1.1.1</router-id>
                        <area>
                            <area-id>0.0.0.0</area-id>
                            <interface>
                                <interface-name>
                                    ethernet-1/1.0
                                </interface-name>
                            </interface>
                            <interface>
                                <interface-name>
                                    ethernet-1/2.0
                                </interface-name>
                            </interface>
                            <interface>
                                <interface-name>lo0.0</interface-name>
                                <passive>true</passive>
                            </interface>
                        </area>
                    </instance>
                </ospf>
            </protocols>
        </network-instance>
    </data>
    """

    result = parse_ospf_configuration(
        response_xml,
        "default",
        "default",
    )

    assert result == {
        "name": "default",
        "admin_state": "enable",
        "version": "ospf-v2",
        "router_id": "1.1.1.1",
        "areas": {
            "0.0.0.0": {
                "interfaces": [
                    {
                        "name": "ethernet-1/1.0",
                    },
                    {
                        "name": "ethernet-1/2.0",
                    },
                    {
                        "name": "lo0.0",
                        "passive": True,
                    },
                ]
            }
        },
    }


def test_get_ospf_configuration():
    fake_response = type(
        "FakeResponse",
        (),
        {
            "data_xml": """<?xml version="1.0" encoding="UTF-8"?>
            <data xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
                <network-instance
                    xmlns="urn:nokia.com:srlinux:net-inst:network-instance">
                    <name>default</name>
                    <protocols>
                        <ospf
                            xmlns="urn:nokia.com:srlinux:ospf:ospf">
                            <instance>
                                <name>default</name>
                                <admin-state>enable</admin-state>
                                <version>
                                    srl_nokia-ospf-types:ospf-v2
                                </version>
                                <router-id>1.1.1.1</router-id>
                                <area>
                                    <area-id>0.0.0.0</area-id>
                                    <interface>
                                        <interface-name>
                                            ethernet-1/1.0
                                        </interface-name>
                                    </interface>
                                    <interface>
                                        <interface-name>
                                            ethernet-1/2.0
                                        </interface-name>
                                    </interface>
                                    <interface>
                                        <interface-name>
                                            lo0.0
                                        </interface-name>
                                        <passive>true</passive>
                                    </interface>
                                </area>
                            </instance>
                        </ospf>
                    </protocols>
                </network-instance>
            </data>
            """,
        },
    )()

    class FakeSession:
        def get_config(self, source, filter):
            assert source == "running"
            assert filter[0] == "subtree"
            assert "network-instance" in filter[1]
            assert "<name>default</name>" in filter[1]
            assert "ospf" in filter[1]

            return fake_response

    class FakeContextManager:
        def __enter__(self):
            return FakeSession()

        def __exit__(self, exc_type, exc, tb):
            return False

    with patch(
        "src.network.netconf_client.manager.connect",
        return_value=FakeContextManager(),
    ):
        client = NETCONFClient(
            host="test-host",
            port=830,
            username="test-user",
            password="test-password",
        )

        result = client.get_ospf_configuration(
            network_instance_name="default",
            ospf_instance_name="default",
        )

    assert result == {
        "name": "default",
        "admin_state": "enable",
        "version": "ospf-v2",
        "router_id": "1.1.1.1",
        "areas": {
            "0.0.0.0": {
                "interfaces": [
                    {"name": "ethernet-1/1.0"},
                    {"name": "ethernet-1/2.0"},
                    {
                        "name": "lo0.0",
                        "passive": True,
                    },
                ]
            }
        },
    }


def test_build_ospf_instance_edit_config():
    client = NETCONFClient(
        host="test-host",
        port=830,
        username="test-user",
        password="test-password",
    )

    result = client.build_ospf_instance_edit_config(
        network_instance_name="default",
        ospf_instance_name="default",
        admin_state="enable",
        version="srl_nokia-ospf-types:ospf-v2",
        router_id="1.1.1.1",
    )

    assert "<config" in result
    assert (
        'xmlns="urn:nokia.com:srlinux:net-inst:network-instance"'
        in result
    )
    assert (
        'xmlns="urn:nokia.com:srlinux:ospf:ospf"'
        in result
    )
    assert 'nc:operation="merge"' in result
    assert "<name>default</name>" in result
    assert "<admin-state>enable</admin-state>" in result
    assert (
        "srl_nokia-ospf-types:ospf-v2"
        in result
    )
    assert "<router-id>1.1.1.1</router-id>" in result


def test_build_ospf_area_interface_edit_config():
    client = NETCONFClient(
        host="test-host",
        port=830,
        username="test-user",
        password="test-password",
    )

    result = client.build_ospf_area_interface_edit_config(
        network_instance_name="default",
        ospf_instance_name="default",
        area_id="0.0.0.0",
        interface_name="ethernet-1/1.0",
    )

    assert "<config" in result
    assert (
        'xmlns="urn:nokia.com:srlinux:net-inst:network-instance"'
        in result
    )
    assert (
        'xmlns="urn:nokia.com:srlinux:ospf:ospf"'
        in result
    )
    assert "<area-id>0.0.0.0</area-id>" in result
    assert (
        "<interface-name>ethernet-1/1.0</interface-name>"
        in result
    )
    assert "<passive>" not in result
