import argparse
import socket
import struct
import time

host_name = socket.gethostname()
address = socket.gethostbyname(host_name)
sock = socket.socket(type = socket.SOCK_DGRAM)
sock.setblocking(True)
NUM_BYTES_IN_HEADER = 26

def ip_to_int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]

def int_to_ip(addr):
    return socket.inet_ntoa(struct.pack("!I", addr))

class node: 
    def __init__(self, ip, port):
        self.ip     = ip
        self.port   = port
        self.ip_num = ip_to_int(ip)
        self.pair   = (ip, port)

    @classmethod
    def from_str_pair(self, node_pair):
        return node(node_pair[0], int(node_pair[1]))

    def __eq__(self, node2):
        return self.ip_num == node2.ip_num and self.port == node2.port
    
    def __hash__(self):
        return hash((self.ip_num, self.port))
    
    def __str__(self):
        return "IP: " + self.ip + " Port: " + str(self.port)

class packet:
    def __init__(self):
        self.src          = None
        self.dest         = None
        self.length       = None
        self.type         = None
        self.seq_num      = None
        self.inner_length = None
        self.payload      = None
        self.packet       = None
        self.next         = None
        self.recfrom      = None
    
    # def log(self, msg):
    #     with open(log_name, "w") as log_file:
    #         log_file.write("A packet was dropping because " + msg + "\n")
    #         log_file.write("Dropped packet info:\n")
    #         log_file.write("Source (address, port): " + str(self.src) + "\n")
    #         log_file.write("Destination (address, port)" + str(self.dest) + "\n")
    #         log_file.write("Packet type: " + self.type + "\n")
    #         log_file.write("Time of loss: " + str(get_time_ms()) + "\n")
    #         log_file.write("Priority: " + str(self.priority) + "\n")
    #         log_file.write("Payload Size: " + str(self.inner_length) + "\n")
    
    def send(self, next):
        sock.sendto(self.encapsulate(), next.pair)
    def decapsulate(self):
        header = struct.unpack("!BIHIHIcII", self.packet[:NUM_BYTES_IN_HEADER])
        self.src          = node(int_to_ip(header[1]), header[2])
        self.dest         = node(int_to_ip(header[3]), header[4])
        # print("source: " + str(self.src))
        # print("dest: " + str(self.dest))
        self.length       = header[5]
        self.type         = header[6].decode("utf-8")
        self.seq_num      = header[7]
        self.inner_length = header[8]
        self.payload = self.packet[NUM_BYTES_IN_HEADER:]
    def encapsulate(self):
        header = struct.pack("!BIHIHIcII", 1, self.src.ip_num, self.src.port, self.dest.ip_num, self.dest.port, self.length, self.type.encode(), self.seq_num, self.inner_length)
        if (self.payload == None):
            self.packet = header
        else:
            self.packet = header + self.payload
        return self.packet

if __name__ == "__main__":
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

    host_node = node(address, port)
    src_node = node(socket.gethostbyname(src_name), src_port)
    dest_node = node(socket.gethostbyname(dest_name), dest_port)

    sock.bind((address, port))

    ttl = 0
    found = False
    while not found:
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

        rec_packet = packet()
        rec_packet.packet, rec_addr = sock.recvfrom(1024)
        rec_packet.decapsulate()
        rec_ttl = struct.unpack("!I", rec_packet.payload)[0]
        print("IP: " + rec_packet.src.ip + " Port: " + str(rec_packet.src.port))
        if options == 1:
            print("TTL: " + str(rec_ttl) + " Src: " + str(rec_packet.src) + " Dest: " + str(rec_packet.dest))
        if (rec_packet.src == dest_node):
            found = True
        else:
            ttl += 1



