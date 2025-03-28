import argparse
import socket
import struct
import time

from node import node
from packet import packet

# Initialize the socket
host_name = socket.gethostname()
address = socket.gethostbyname(host_name)
sock = socket.socket(type = socket.SOCK_DGRAM)
sock.setblocking(True)

if __name__ == "__main__":
    # Get argumments
    parser = argparse.ArgumentParser(description = "trace a route")

    parser.add_argument("-a", required = True, type = int)
    parser.add_argument("-b", required = True)
    parser.add_argument("-c", required = True, type = int)
    parser.add_argument("-d", required = True)
    parser.add_argument("-e", required = True, type = int)
    parser.add_argument("-f", required = True, type = int)

    args = parser.parse_args()

    port = args.a
    src_name = args.b
    src_port = args.c
    dest_name = args.d
    dest_port = args.e
    options = args.f

    # Define the host node, src_node, and dest_node, and bind socket to the host node
    host_node = node(address, port)
    src_node = node(socket.gethostbyname(src_name), src_port)
    dest_node = node(socket.gethostbyname(dest_name), dest_port)

    sock.bind((address, port))

    # Sends network trace packet with progressively higher TTLs until 
    # the destination node is found, printing out which nodes the packet reaches along the way
    ttl = 0
    found = False
    while not found:
        # Initialize and send the packet
        trace_packet = packet()
        trace_packet.src = host_node
        trace_packet.dest = dest_node
        trace_packet.length = 0
        trace_packet.inner_length = 0
        trace_packet.type = "O"
        trace_packet.payload = struct.pack("!I", ttl)
        trace_packet.seq_num = 0
        if options == 1:
            print("TTL: " + str(ttl) + " src: " + str(trace_packet.src) + " dest: " + str(trace_packet.dest))
        trace_packet.send(src_node)

        # Get a network trace packet returned to us, and print where it came from
        rec_packet = packet()
        rec_packet.packet, rec_addr = sock.recvfrom(1024)
        rec_packet.decapsulate()
        rec_ttl = struct.unpack("!I", rec_packet.payload)[0]
        print("IP: " + rec_packet.src.ip + " Port: " + str(rec_packet.src.port))
        if options == 1:
            print("TTL: " + str(rec_ttl) + " Src: " + str(rec_packet.src) + " Dest: " + str(rec_packet.dest))
        # Check if the destination node was reached, other wise increment ttl and try again
        if (rec_packet.src == dest_node):
            found = True
        else:
            ttl += 1



