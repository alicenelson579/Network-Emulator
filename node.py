import struct
import socket

# A class representing a node in the network,
# defined by the node's ip and port

class node:

    # These 2 functions convert between an ip address represented with a string 
    # formatted as "255.255.255.255" and an ip address represented as an integer
    @classmethod
    def ip_to_int(self, addr):
        return struct.unpack("!I", socket.inet_aton(addr))[0]

    @classmethod
    def int_to_ip(self, addr):
        return socket.inet_ntoa(struct.pack("!I", addr))
    

    
    def __init__(self, ip, port):
        self.ip     = ip
        self.port   = port
        self.ip_num = node.ip_to_int(ip)
        self.pair   = (ip, port)

    # initialize a new node from a tuple with the format ("255.255.255.255", "1")
    @classmethod
    def from_str_pair(self, node_pair):
        return node(node_pair[0], int(node_pair[1]))
    
    def __eq__(self, node2):
        return self.ip_num == node2.ip_num and self.port == node2.port
    
    def __hash__(self):
        return hash((self.ip_num, self.port))
    
    def __str__(self):
        return "IP: " + self.ip + " Port: " + str(self.port)