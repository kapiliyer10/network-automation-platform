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
