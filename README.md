README.md

emulator.py

This is a simple script created for my computer networks course.
It emulates a simple router in a network of routers, and the shape of that
network is determined by a topology file.

Usage:
python3 emulator.py -p PORT -f FILENAME

There are two mandatory flags:

-p PORT
sets the port that the emulator will sit on

-f FILENAME
sets the name of the topology file that determines what
connections the emulator will make with other emulators

The Topology File

Each line of the topology file is a series of space-seperated tuples formatted as IP_ADDRESS,PORT which represent a node of the network.
The first tuple of a line specifies the IP address and port of the represented node.
Each following tuple is the IP and port of a node that the represented node has a connection to.

Example:

1.1.1.1,1 1.1.1.1,2

1.1.1.1,2 1.1.1.1,1 1.1.1.1,3

1.1.1.1,3 1.1.1.1,2

This topology file denotes a network of emulators all at the IP address 1.1.1.1,
with the emulators one ports 1 and 3 being connected to the emulator on port 2,
so the network would have the shape of:

1 - 2 - 3

network_trace.py

This script can be used to trace a path through the network from a source
node to a destination node.

Usage:
python3 network_trace.py -a PORT -b SRC_NAME -c SRC_PORT -d DEST_NAME -e DEST_PORT -f OPTIONS

-a PORT
The port that network_trace.py will send trace packets from.

-b SOURCE_NAME
The host name of the source node

-c SRC_PORT
The port the source node is on

-d DEST_NAME
The host name of the destination node

-e DEST_PORT
The port the destination node is on

-f OPTIONS
OPTIONS can be 0 or 1. If it's 0, network_trace will output the IP and port address of each
node traced from source to destination. If it's 1, in addition to printing the IP and port
of each traced node, it will print the TTL, source IP and port, and destination IP and port
of each sent and received packet.
