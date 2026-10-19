FROM python:3.12-alpine

RUN apk add --no-cache iproute2 iperf3 tcpdump

WORKDIR /app
COPY tcp_server.py /app/tcp_server.py
COPY udp_server.py /app/udp_server.py

CMD ["sleep", "infinity"]
