import argparse
import socket
import struct
import time
import random

NS_PER_SEC = 1000000000
MS_PER_SEC = 1000000
NUM_BYTES_IN_HEADER = 26
queue_size = None
log_name = None
forwarding_table = []

host_name = socket.gethostname()
address = socket.gethostbyname(host_name)
sock = socket.socket(type = socket.SOCK_DGRAM)
sock.setblocking(False)

def ip_to_int(ip_str):
    l = ip_str.split(".")
    ret = int(l[0]) * (2**24)
    ret += int(l[1]) * (2**16)
    ret += int(l[2]) * (2**8)
    ret += int(l[3])
    return ret

def get_time_ms():
    return round((time.time_ns() / NS_PER_SEC), 3)

class node: 
    def __init__(self, ip, port):
        self.ip     = ip
        self.port   = port
        self.ip_num = ip_to_int(ip)
    def __init__(self, node_pair):
        self.ip     = node_pair[0]
        self.port   = int(node_pair[1])
        self.ip_num = ip_to_int(self.ip)
    def __eq__(self, node2):
        return self.ip_num == node2.ip_num and self.port == node2.port

class forwarding_table_entry:
    def __init__(self, dest, next):
        self.dest  = dest
        self.next  = next
        #self.delay = None
        #self.loss  = None

class packet:
    def __init__(self):
        self.priority     = None
        self.src          = None
        self.dest         = None
        self.length       = None
        self.type         = None
        self.seq_num      = None
        self.inner_length = None
        self.payload      = None
        self.packet       = None
        self.delay        = None
        self.next         = None
    def log(self, msg):
        with open(log_name, "w") as log_file:
            log_file.write("A packet was dropping because " + msg + "\n")
            log_file.write("Dropped packet info:\n")
            log_file.write("Source (address, port): " + str(self.src) + "\n")
            log_file.write("Destination (address, port)" + str(self.dest) + "\n")
            log_file.write("Packet type: " + self.type + "\n")
            log_file.write("Time of loss: " + str(get_time_ms()) + "\n")
            log_file.write("Priority: " + str(self.priority) + "\n")
            log_file.write("Payload Size: " + str(self.inner_length) + "\n")
    def route(self):
        for entry in forwarding_table:
            if (entry.dest[0] == self.dest[0] and entry.dest[1] == self.dest[1]):
                self.next = entry.next
                self.delay = entry.delay
                self.loss  = entry.loss
                sock.sendto(self.packet, self.next)
                return
        self.log("no forwarding entry found")
    def decapsulate(self):
        header = struct.unpack("!BIHIHIcII", self.packet[:NUM_BYTES_IN_HEADER])
        self.priority     = header[0]
        self.src          = (header[1], header[2])
        self.dest         = (header[3], header[4])
        self.length       = header[5]
        self.type         = header[6].decode("utf-8")
        self.seq_num      = header[7]
        self.inner_length = header[8]
        self.payload = self.packet[NUM_BYTES_IN_HEADER:].decode("utf-8")

def readtopology(filename):
    network_topology = {}
    with open(filename, "r") as file:
        next_line = file.readline().split()
        while (next_line != []):
            src_node = node(next_line[0].split(","))
            edges = {}
            for link in next_line[1:]:
                cur_node = node(link.split(",")[:2])
                edges[cur_node] = link.split(",")[2]
            network_topology[src_node] = edges
            next_line = file.readline().split()
    return network_topology


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Send a file to a requester")

    parser.add_argument("-p", required = True, type = int)
    parser.add_argument("-f", required = True)

    args = parser.parse_args()

    port       = args.p
    #queue_size = args.q
    file_name  = args.f
    #log_name   = args.l

    sock.bind((address, port))

    delay_until = None
    next_packet = None
    while True:
        new_packet = packet()
        try:
            new_packet.packet, address = sock.recvfrom(1024)
        except:
            pass
        if (new_packet.packet != None):
            new_packet.decapsulate()
            new_packet.route()
        if (next_packet != None and get_time_ms() > delay_until):
            next_packet.send()
            next_packet = None
        if next_packet == None:
            if (len(queue1) > 0):
                next_packet = queue1.pop(0)
            elif (len(queue2) > 0):
                next_packet = queue2.pop(0)
            elif (len(queue3) > 0):
                next_packet = queue3.pop(0)
            if (next_packet != None):
                delay_until = get_time_ms() + (next_packet.delay / MS_PER_SEC)



