"""TCP echo server for the expanded network test lab."""

import socket

HOST = "0.0.0.0"
PORT = 18080

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()

    print(f"Listening on {HOST}:{PORT}", flush=True)

    while True:
        connection, address = server.accept()

        with connection:
            data = connection.recv(4096)

            if data:
                print(f"Received {data!r} from {address}", flush=True)
                connection.sendall(b"TCP_OK:" + data)
