import argparse
#import socket
#import struct
#import time

host_name = socket.gethostname()
address = socket.gethostbyname(host_name)
sock = socket.socket(type = socket.SOCK_DGRAM)
sock.setblocking(False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Send a file to a requester")
