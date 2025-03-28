import argparse
import socket
import struct
import time

from node import node
from packet import packet

#constants
NS_PER_SEC = 1000000000
MS_PER_SEC = 1000
NS_PER_MS  = 1000000

forwarding_table = {}
network_topology = {}
port = None
host_node = None
cur_link_num = 0

host_name = socket.gethostname()
address = socket.gethostbyname(host_name)
sock = socket.socket(type = socket.SOCK_DGRAM)
sock.setblocking(False)

# Get the current time in seconds after the epoch, 
# with millisecond percision
def get_time_ms():
    return round((time.time_ns() / NS_PER_SEC), 3)

# Print the network topology, as described in the topology file
def print_topology():
    for entry in network_topology.keys():
        cur = str(entry)+ " | Edges: "
        for x in network_topology[entry].keys():
            cur = cur + " (" + str(x) + "):" + str(network_topology[entry][x])
        " ".join(["(" + str(x) + ") : " + str(network_topology[entry][x]) for x in network_topology[entry].keys()])
        print(cur)

# Reads the topology file and stores it's data in network_topology
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

# Prints the current forwarding table
def print_forward_table():
    print("Forwarding Table:")
    print("Length: " + str(len(forwarding_table.keys())))
    for dest_node in forwarding_table.keys():
        print("(" + str(dest_node) + "): (" + str(forwarding_table[dest_node]) + ")")

# Build the emulator's forwarding table using Djikstra's algorithm
def build_forward_table():
    global forwarding_table
    forwarding_table = {}
    # List of nodes already added to the forwarding table
    added_nodes = [host_node]
    # Each entry is a (node, total cost to that node) pair
    costs = {}
    # Where packets headed towards key node will be forwarded to next
    next_hop = {}
    # Iterate over the host node's edges and get their costs 
    for edge in network_topology[host_node].keys():
        # Check if the edge is active
        if (network_topology[host_node][edge] > 0):
            costs[edge] = network_topology[host_node][edge]
            next_hop[edge] = edge
    # Loop while there are still nodes left to add to the forwarding table
    while len(added_nodes) < len(network_topology.keys()) and len([x for x in costs.keys() if x not in added_nodes]) > 0:
        # Determine which unadded node that's adjacent to an added node has 
        # the lowest cost, then add it to the forwarding table
        next_node = min({k: v for k, v in costs.items() if k not in added_nodes}, key = costs.get)
        added_nodes.append(next_node)
        forwarding_table[next_node] = next_hop[next_node]
        # Calculate the costs of all unadded nodes adjacent to the newly added node
        for edge in network_topology[next_node]:
            if edge not in added_nodes and network_topology[next_node][edge] > 0:
                if edge not in costs.keys() or costs[edge] > costs[next_node] + network_topology[next_node][edge]:
                    costs[edge] = costs[next_node] + network_topology[next_node][edge]
                    next_hop[edge] = next_hop[next_node]
    print_forward_table()

# Initialize a hello packet
hello_packet              = packet()
hello_packet.type         = "H"
hello_packet.seq_num      = 0
hello_packet.length       = 0
hello_packet.inner_length = 0

# Send hello packets to each of the host node's neighbors
def send_hello():
    # Get list of all active neighbors of the host node 
    valid_edges = [x for x in network_topology[host_node].keys() if network_topology[host_node][x] > 0]

    for edge in valid_edges:
        hello_packet.dest = edge
        hello_packet.send(forwarding_table[edge])

# Create and send a link state packets to each of host node's neighbors
def send_link_state():
    global cur_link_num
    # Initialize a link state packet
    link_state_packet = packet()
    link_state_packet.src = host_node
    link_state_packet.type = "L"
    link_state_packet.seq_num = cur_link_num
    link_state_packet.inner_length = 4
    data = struct.pack("!I", 100)
    # Get list of host node's active edges
    valid_edges = [x for x in network_topology[host_node].keys() if network_topology[host_node][x] > 0]
    # Adds the ip and port of every node the host node is connected to, 
    # as well as the cost of that connection
    for edge in valid_edges:
        data = data + struct.pack("!IHI", edge.ip_num, edge.port, network_topology[host_node][edge])
        link_state_packet.inner_length += 10
    link_state_packet.payload = data
    link_state_packet.length = 9 + link_state_packet.inner_length
    # Send the link state packet to each of host node's neighbors
    for edge in valid_edges:
        link_state_packet.dest = edge
        link_state_packet.send(forwarding_table[edge])
    # cur_link_num tracks the number of times link state packets have been sent, 
    # which allows emulators to determine which of two link state packets was sent more recently
    cur_link_num += 1 


# This is the main function that will loop infinitely while the emulator is running,
# handling packet forwarding, timing of sending hello and link state packets, and 
# receiving of hello and link state packets. It also disables any connection 
def create_routes():
    next_hello = time.time_ns()
    next_link_state = next_hello
    # Each value is the timestamp of the last time a 
    # hello packet was received from they key node
    latest_timestamp = {}
    # Each value is the largest sequence number of a link 
    # state packet received from the key node
    largest_seq_num = {}
    for edge in network_topology[host_node].keys():
        latest_timestamp[edge] = time.time_ns()
    while True:
        new_packet = packet()
        # Check if the emulator has received a packet
        try:
            new_packet.packet, rec_addr = sock.recvfrom(1024)
        except:
            pass
        cur_time = time.time_ns() # Record time packet was received
        if (new_packet.packet != None):
            new_packet.decapsulate()
            rec_node = node(rec_addr[0], rec_addr[1])
            
            if new_packet.type == "H": # Check if received packet is a hello packet
                # Check if the connection between the host node and the source of the hello packet is inactive, 
                # and if it is, mark it as active, rebuild the forwarding table, and update neighbors with link 
                # state packets
                if latest_timestamp[new_packet.src] == None:
                    network_topology[host_node][new_packet.src] = abs(network_topology[host_node][new_packet.src])
                    network_topology[new_packet.src][host_node] = abs(network_topology[new_packet.src][host_node])
                    build_forward_table()
                    send_link_state()
                    #print("connection to node " + str(new_packet.src) + " has been reestablished")
                # Update latest_timestamp
                latest_timestamp[new_packet.src] = cur_time
            elif new_packet.type == "L": # Check if received packet is a link state packet
                # Make sure the packet's sender is actually adjacent to host node and there hasn't been another link state 
                # packet with a larger sequence number received
                if new_packet.src not in largest_seq_num.keys() or new_packet.seq_num > largest_seq_num[new_packet.src]:
                    ttl = struct.unpack("!I", new_packet.payload[:4])[0] # Get time to live (ttl) from link state packet payload
                    if (ttl > 0): # Ensure packet still has time to live, this prevents link state packets looping infinitely
                        largest_seq_num[new_packet.src] = new_packet.seq_num
                        # Mark all connections  to and from the link state packet's source node as inactive
                        for edge in network_topology[new_packet.src]:
                            network_topology[new_packet.src][edge] = abs(network_topology[new_packet.src][edge]) * -1
                        for n in network_topology.keys():
                            if new_packet.src in network_topology[n] and network_topology[n][new_packet.src] > 0:
                                network_topology[n][new_packet.src] = abs(network_topology[n][new_packet.src]) * -1
                        # Read the link state packet's data and mark all listed connections as active, 
                        # with the cost specified by the the packet
                        for i in range(0, int((new_packet.inner_length - 4) / 10)):
                            entry = struct.unpack("!IHI", new_packet.payload[(i * 10)+4:(i * 10)+14])
                            edge_node = node(node.int_to_ip(entry[0]), entry[1])
                            network_topology[new_packet.src][edge_node] = entry[2]
                            network_topology[edge_node][new_packet.src] = entry[2]
                        # Rebuild the forwarding table with the new information
                        build_forward_table()
                        # Decrement the ttl and forward the packet to all neighbors
                        new_ttl = struct.pack("!I", ttl - 1)
                        new_packet.payload = new_ttl + new_packet.payload[4:]
                        for edge in network_topology[host_node].keys():
                            # Check if connection is active and the dest node isn't where the 
                            # link state packet was sent from
                            if (network_topology[host_node][edge] > 0 and rec_node != edge):
                                new_packet.dest = edge
                                new_packet.send(forwarding_table[edge])
            elif new_packet.type == "O": # Check if received packet is a network trace packet
                ttl = struct.unpack("!I", new_packet.payload[:4])[0]
                # If tll is 0, send a return packet to the packet source so it knows where 
                # the packet ended up
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
                    sock.sendto(ret_packet.packet, new_packet.src.pair)
                # Otherwise, send the packet on it's way, with a decremented ttl
                else:
                    if new_packet.dest in forwarding_table.keys():
                        new_packet.payload = struct.pack("!I", ttl - 1)
                        new_packet.send(forwarding_table[new_packet.dest])
            # If the received packet isn't a hello, link state, or network trace packet, 
            # forward it towards it's destination
            else: 
                if new_packet.dest in forwarding_table.keys():
                    new_packet.send(forwarding_table[new_packet.dest])
        # If it's time to send another round of hello packets, do so, 
        # then set the next time for hello packets to be sent as 2 milliseconds from now
        if cur_time >= next_hello:
            next_hello = cur_time + NS_PER_MS * 2
            send_hello()
        # Check if the emulator hasn't received a hello packet from each of it's neighboring 
        # nodes, and if not, mark that connection as inactive, rebuild the forwarding table,
        # and resend link state packets
        for edge in latest_timestamp.keys():
            if latest_timestamp[edge] != None and cur_time > latest_timestamp[edge] + 50 * NS_PER_MS:
                network_topology[host_node][edge] = abs(network_topology[host_node][edge]) * -1
                network_topology[edge][host_node] = abs(network_topology[edge][host_node]) * -1
                build_forward_table()
                send_link_state()
                latest_timestamp[edge] = None

        # If it's time to send another round of link state packets, do so, 
        # then set the next time for link state packets to be sent as 10 milliseconds from now
        if cur_time >= next_link_state:
            next_link_state = cur_time + NS_PER_MS * 10
            send_link_state()


if __name__ == "__main__":
    # Get the emulator's arguments
    parser = argparse.ArgumentParser(description = "emulate a network")

    parser.add_argument("-p", required = True, type = int)
    parser.add_argument("-f", required = True)

    args = parser.parse_args()

    port       = args.p
    file_name  = args.f

    # Define the host node and bind the socket to it
    host_node = node(address, port)
    hello_packet.src = host_node
    sock.bind((address, port))

    # Read the network's initial topology
    read_topology(file_name)
    # Build the initial forwarding table
    build_forward_table()
    # Call create_routes, turning the emulator on
    create_routes()



