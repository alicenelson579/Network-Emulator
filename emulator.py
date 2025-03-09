import argparse
import socket
import struct
import time

NS_PER_SEC = 1000000000
MS_PER_SEC = 1000
NS_PER_MS  = 1000000
NUM_BYTES_IN_HEADER = 26
forwarding_table = {}
network_topology = {}
port = None
host_node = None
cur_link_num = 0

host_name = socket.gethostname()
address = socket.gethostbyname(host_name)
sock = socket.socket(type = socket.SOCK_DGRAM)
sock.setblocking(False)

def ip_to_int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]

def int_to_ip(addr):
    return socket.inet_ntoa(struct.pack("!I", addr))

def get_time_ms():
    return round((time.time_ns() / NS_PER_SEC), 3)

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
    
    def send(self):
        if self.dest in forwarding_table.keys():
            sock.sendto(self.encapsulate(), forwarding_table[self.dest].pair)
        else:
            raise Exception("no forwarding entry found")
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

def print_topology():
    for entry in network_topology.keys():
        cur = str(entry)+ " | Edges: "
        for x in network_topology[entry].keys():
            cur = cur + " (" + str(x) + "):" + str(network_topology[entry][x])
        " ".join(["(" + str(x) + ") : " + str(network_topology[entry][x]) for x in network_topology[entry].keys()])
        print(cur)

def read_topology(filename):
    with open(filename, "r") as file:
        next_line = file.readline().split()
        while (next_line != []):
            src_node = node.from_str_pair(next_line[0].split(","))
            edges = {}
            for link in next_line[1:]:
                cur_node = node.from_str_pair(link.split(",")[:2])
                edges[cur_node] = int(link.split(",")[2])
            network_topology[src_node] = edges
            next_line = file.readline().split()
    print_topology()

def print_forward_table():
    print("Forwarding Table:")
    print("Length: " + str(len(forwarding_table.keys())))
    for dest_node in forwarding_table.keys():
        print("(" + str(dest_node) + "): (" + str(forwarding_table[dest_node]) + ")")

def build_forward_table():
    global forwarding_table
    forwarding_table = {}
    added_nodes = [host_node]
    #each entry is a (node, total cost to that node) pair
    costs = {}
    #where packets headed towards key node will be sent
    next_hop = {}
    for edge in network_topology[host_node].keys():
        if (network_topology[host_node][edge] > 0):
            costs[edge] = network_topology[host_node][edge]
            next_hop[edge] = edge

    while len(added_nodes) < len(network_topology.keys()) and len([x for x in costs.keys() if x not in added_nodes]) > 0:
        next_node = min({k: v for k, v in costs.items() if k not in added_nodes}, key = costs.get)
        added_nodes.append(next_node)
        forwarding_table[next_node] = next_hop[next_node]
        for edge in network_topology[next_node]:
            if edge not in added_nodes and network_topology[next_node][edge] > 0:
                if edge not in costs.keys() or costs[edge] > costs[next_node] + network_topology[next_node][edge]:
                    costs[edge] = costs[next_node] + network_topology[next_node][edge]
                    next_hop[edge] = next_hop[next_node]
    print_forward_table()


hello_packet              = packet()
hello_packet.type         = "H"
hello_packet.seq_num      = 0
hello_packet.length       = 0
hello_packet.inner_length = 0

def send_hello():
    valid_edges = [x for x in network_topology[host_node].keys() if network_topology[host_node][x] > 0]
    for edge in valid_edges:
        hello_packet.dest = edge
        hello_packet.send()

def send_link_state():
    global cur_link_num
    link_state_packet = packet()
    link_state_packet.src = host_node
    link_state_packet.type = "L"
    link_state_packet.seq_num = cur_link_num
    link_state_packet.inner_length = 4
    data = struct.pack("!I", 100)
    valid_edges = [x for x in network_topology[host_node].keys() if network_topology[host_node][x] > 0]
    #print("sending link state packet")
    for edge in valid_edges:
        #print(edge)
        data = data + struct.pack("!IHI", edge.ip_num, edge.port, network_topology[host_node][edge])
        link_state_packet.inner_length += 10
    link_state_packet.payload = data
    link_state_packet.length = 9 + link_state_packet.inner_length
    for edge in valid_edges:
        link_state_packet.dest = edge
        link_state_packet.send()
    cur_link_num += 1 



def create_routes():
    next_hello = time.time_ns()
    next_link_state = next_hello
    latest_timestamp = {}
    largest_seq_num = {}
    for edge in network_topology[host_node].keys():
        latest_timestamp[edge] = time.time_ns()
    while True:
        new_packet = packet()
        try:
            new_packet.packet, rec_addr = sock.recvfrom(1024)
        except:
            pass
        cur_time = time.time_ns()
        if (new_packet.packet != None):
            new_packet.decapsulate()
            rec_node = node(rec_addr[0], rec_addr[1])
            if new_packet.type == "H":
                if latest_timestamp[new_packet.src] == None:
                    network_topology[host_node][new_packet.src] = abs(network_topology[host_node][new_packet.src])
                    network_topology[new_packet.src][host_node] = abs(network_topology[new_packet.src][host_node])
                    build_forward_table()
                    send_link_state()
                    #print("connection to node " + str(new_packet.src) + " has been reestablished")
                latest_timestamp[new_packet.src] = cur_time
            elif new_packet.type == "L":
                if new_packet.src not in largest_seq_num.keys() or new_packet.seq_num > largest_seq_num[new_packet.src]:
                    ttl = struct.unpack("!I", new_packet.payload[:4])[0]
                    if (ttl > 0):
                        largest_seq_num[new_packet.src] = new_packet.seq_num
                        for edge in network_topology[new_packet.src]:
                            network_topology[new_packet.src][edge] = abs(network_topology[new_packet.src][edge]) * -1
                        for n in network_topology.keys():
                            if new_packet.src in network_topology[n] and network_topology[n][new_packet.src] > 0:
                                network_topology[n][new_packet.src] = abs(network_topology[n][new_packet.src]) * -1
                        for i in range(0, int((new_packet.inner_length - 4) / 10)):
                            entry = struct.unpack("!IHI", new_packet.payload[(i * 10)+4:(i * 10)+14])
                            edge_node = node(int_to_ip(entry[0]), entry[1])
                            network_topology[new_packet.src][edge_node] = entry[2]
                            network_topology[edge_node][new_packet.src] = entry[2]
                        build_forward_table()
                        new_ttl = struct.pack("!I", ttl - 1)
                        new_packet.payload = new_ttl + new_packet.payload[4:]
                        for edge in network_topology[host_node].keys():
                            if (network_topology[host_node][edge] > 0 and rec_node != edge):
                                new_packet.dest = edge
                                new_packet.send()
            elif new_packet.type == "O":
                ttl = struct.unpack("!I", new_packet.payload[:4])[0]
                if ttl == 0:
                    ret_packet = packet()
                    ret_packet.src = host_node
                    ret_packet.dest = new_packet.src
                    ret_packet.type = "O"
                    ret_packet.length = 0
                    ret_packet.inner_length = 0
                    ret_packet.seq_num = 0
                    ret_packet.payload = struct.pack("!I", 0)
                    ret_packet.encapsulate()
                    #print(new_packet.src)
                    sock.sendto(ret_packet.packet, new_packet.src.pair)
                else:
                    if new_packet.dest in forwarding_table.keys():
                        new_packet.payload = struct.pack("!I", ttl - 1)
                        new_packet.send()
                    
            else:
                if new_packet.dest in forwarding_table.keys():
                    new_packet.send()
        if cur_time >= next_hello:
            #print("cur time: " + str(cur_time) + " next hello: " + str(next_hello))
            next_hello = cur_time + NS_PER_MS * 2
            send_hello()

        for edge in latest_timestamp.keys():
            if latest_timestamp[edge] != None and cur_time > latest_timestamp[edge] + 50 * NS_PER_MS:
                #print("connection to node " + str(edge) + " has been broken")
                network_topology[host_node][edge] = abs(network_topology[host_node][edge]) * -1
                network_topology[edge][host_node] = abs(network_topology[edge][host_node]) * -1
                build_forward_table()
                send_link_state()
                latest_timestamp[edge] = None

        if cur_time >= next_link_state:
            next_link_state = cur_time + NS_PER_MS * 10
            send_link_state()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "emulate a network")

    parser.add_argument("-p", required = True, type = int)
    parser.add_argument("-f", required = True)

    args = parser.parse_args()

    port       = args.p
    file_name  = args.f

    host_node = node(address, port)
    hello_packet.src = host_node
    sock.bind((address, port))

    read_topology(file_name)
    build_forward_table()
    create_routes()



