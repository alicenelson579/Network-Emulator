import struct
from node import node
import socket

NUM_BYTES_IN_HEADER = 26

# A class to represent a packet sent from one node to another

class packet:
    def __init__(self):
        # the node the packet will be sent from
        self.src          = None
        # The node the packet will be sent to
        self.dest         = None
        # The length of the packet's data plus the length of inner_length value, 
        # plus the length of the sequence number, plus the length of the type value
        self.length       = None
        # The packet's tyep
        self.type         = None
        # The packet's Sequence Number
        self.seq_num      = None
        # The length of the packet's data in bytes
        self.inner_length = None
        # The data being sent
        self.payload      = None
        # All the packet's header and data packed together
        self.packet       = None
        # The next node the packet will be forwarded to on it's way to it's destination
        self.next         = None
    
    # Encapsulates, then sends the packet to the specified node
    def send(self, dest_node):
        sock = socket.socket(type = socket.SOCK_DGRAM)
        sock.setblocking(False)
        sock.sendto(self.encapsulate(), dest_node.pair)

    # Takes the data in self.packet and decapsulates it, 
    # filling out the packet's other attributes
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

    # Takes the data in a packet's attributes and 
    # encapsulates them into a single binary object
    def encapsulate(self):
        header = struct.pack("!BIHIHIcII", 1, self.src.ip_num, self.src.port, self.dest.ip_num, self.dest.port, self.length, self.type.encode(), self.seq_num, self.inner_length)
        if (self.payload == None):
            self.packet = header
        else:
            self.packet = header + self.payload
        return self.packet