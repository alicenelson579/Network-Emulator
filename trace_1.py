import argparse
import socket
import struct
import time

host_name = socket.gethostname()
address = socket.gethostbyname(host_name)
sock = socket.socket(type = socket.SOCK_DGRAM)
sock.setblocking(False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "trace a route")

    parser.add_argument("-a", required = True, type = int)
    parser.add_argument("-b", required = True)
    parser.add_argument("-c", required = True, type = int)
    parser.add_argument("-d", required = True)
    parser.add_argument("-e", required = True, type = int)
    parser.add_argument("-f", required = True)

    args = parser.parse_args()

    port = args.a
    src_name = args.b
    src_port = args.c
    dest_name = args.d
    dest_port = args.e
    options = args.f