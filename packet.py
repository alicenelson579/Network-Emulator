import struct
from node import node
import socket

NUM_BYTES_IN_HEADER = 26

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
    
    def send(self, forwarding_table):
        sock = socket.socket(type = socket.SOCK_DGRAM)
        sock.setblocking(False)
        if self.dest in forwarding_table.keys():
            sock.sendto(self.encapsulate(), forwarding_table[self.dest].pair)
        else:
            raise Exception("no forwarding entry found")
    def decapsulate(self):
        header = struct.unpack("!BIHIHIcII", self.packet[:NUM_BYTES_IN_HEADER])
        self.src          = node(node.int_to_ip(header[1]), header[2])
        self.dest         = node(node.int_to_ip(header[3]), header[4])
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