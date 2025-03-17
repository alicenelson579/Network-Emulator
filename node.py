import struct
import socket

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