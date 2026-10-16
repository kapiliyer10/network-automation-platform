"""UDP echo server for the expanded network test lab."""

import socket

HOST = "0.0.0.0"
PORT = 18081

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server:
    server.bind((HOST, PORT))
    print(f"Listening on UDP {HOST}:{PORT}", flush=True)

    while True:
        data, address = server.recvfrom(4096)

        if data:
            print(
                f"Received {data!r} from {address}",
                flush=True,
            )
            server.sendto(b"UDP_OK:" + data, address)
