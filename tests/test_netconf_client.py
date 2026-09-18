from unittest.mock import patch

from src.network.netconf_client import NETCONFClient,parse_interface_ipv4

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
            username="admin",
            password="NokiaSrl1!",
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
            username="admin",
            password="NokiaSrl1!",
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
        "admin_state": "enable",
        "address": "10.0.12.1/30",
    }
