#!/usr/local/bin/python3.5

"""

    The begining of some work with OSPF

"""

from threading import Thread
from socket import socket, AF_INET, SOCK_RAW, SOL_SOCKET, SO_REUSEADDR
from socket import inet_aton, inet_ntoa, INADDR_ANY, IPPROTO_IP, IP_ADD_MEMBERSHIP
from struct import pack, unpack

mcast_group = '224.0.0.5'
local_ip = '172.16.50.13'


class OSPFSocket:
    """A raw socket, protocol 89 and multicast membership"""

    def __init__(self, mcast_group, local_ip, ospf):
        """Sets the multicast group and ip address to bind too"""
        
        self.mcast_group = mcast_group
        self.local_ip = local_ip
        self.sock = socket(AF_INET, SOCK_RAW, 89)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        mreq = inet_aton(self.mcast_group) + inet_aton(self.local_ip)
        self.sock.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)
        self.ospf = ospf

    def handle_close(self):
        self.close()

    def handle_read(self):
        """Returns data rercieved on the socket"""
        while True:
            data = (self.sock.recvfrom(1500))
            self.ospf.recieve_data(data[0])

class IPv4:
    """A class to handle IPv4"""

    def __init__(self):
        """Initialises the IPv4 header values"""

        self.ver = 4
        self.ihl = 0
        self.dscp = 0
        self.tl = 0
        self.ident = 0
        self.frag = 0
        self.ttl = 64
        self.proto = 89
        self.check = 0
        self.saddr = 0
        self.daddr = 0
        self.ver_ihl = (self.ver << 4) + self.ihl

    def unpack_header(self, data):
        """Takes the IPv4 header from a socket and unpacks the binary into the proper
           IPv4 headers.
        """
        
        ip_header = data[0:20]
        self.ip_header = unpack('!BBHHHBBH4s4s', ip_header)
        self.ver_ihl = self.ip_header[0]
        self.ver = (self.ver_ihl >> 4)
        self.ihl = self.ver_ihl - (self.ver << 4)
        self.dscp = self.ip_header[1]
        self.tl = self.ip_header[2]
        self.ident = self.ip_header[3]
        self.frag = self.ip_header[4]
        self.ttl = self.ip_header[5]
        self.proto = self.ip_header[6]
        self.check = self.ip_header[7]
        self.saddr = inet_ntoa(self.ip_header[8])
        self.daddr = inet_ntoa(self.ip_header[9])


class OSPF:
    def __init__(self):
        self.ip_header = IPv4()
        self.ospf_header = Header()
        self.ospf_hello = Hello()

    def recieve_data(self, data):
        self.ip_header.unpack_header(data)
        self.ospf_header.unpack_header(data)
               
        if self.ospf_header.mtype == 1:
           self.ospf_hello.unpack_hello(data, self.ospf_header.length)
           print("OSPF Hello from Router: ", self.ip_header.saddr,"\n")
           print("Router ID: ", self.ospf_header.router, " Area: ", self.ospf_header.area, " Designated Router: ", self.ospf_hello.des_router)
           print("Interval: ", self.ospf_hello.interval, " Dead Interval: ", self.ospf_hello.dead_int)
           print("Neighbors: ", self.ospf_hello.neighbors)


class Header:
    """Handles the OSPF header"""

    def __init__(self):
        """Initializes the header fields of an OSPF header"""

        self.ver = 2
        self.mtype = 0
        self.length = 0
        self.router = 0
        self.area = 0
        self.check = 0
        self.auth_type = 0
        self.auth = 0

    def unpack_header(self, data):
        """Takes data from a raw socket and unpacks the OSPF header from
           packed binary.
        """

        ospf_header = data[20:44]
        self.ospf_header = unpack('!BBH4s4sHH8s', ospf_header)
        self.ver = self.ospf_header[0]
        self.mtype = self.ospf_header[1]
        self.length = self.ospf_header[2]
        self.router = inet_ntoa(self.ospf_header[3])
        self.area = inet_ntoa(self.ospf_header[4])
        self.check = self.ospf_header[5]
        self.auth_type = self.ospf_header[6]
        auth = unpack('!BBBBBBBB', self.ospf_header[7])
        self.auth = ''.join(map(str,auth))

class Hello:
    """Handles the OSPF Hello message"""

    def __init__(self):
        """Initilizes the fields of an OSPF Hello message"""
        
        self.net_mask = 0
        self.interval = 0
        self.options = 0
        self.priority = 0
        self.dead_int = 0
        self.des_router = 0
        self.back_router = 0
        self.neighbors = []
        self.length = 0

    def unpack_hello(self, data, length):
        """Takes data from a raw socket and unpacks the OSPF Hello message
           from the packed binary
        """

        hello_header = data[44:64]
        self.hello_header = unpack('!4sHBB4s4s4s', hello_header)
        self.net_mask = inet_ntoa(self.hello_header[0])
        self.interval = self.hello_header[1]
        self.options = self.hello_header[2]
        self.priority = self.hello_header[3]
        dead = unpack('!BBBB', self.hello_header[4])
        self.dead_int = int(''.join(map(str,dead)))
        self.des_router = inet_ntoa(self.hello_header[5])
        self.back_router = inet_ntoa(self.hello_header[6])

        neighbor_length = length - 44
        neighbor_packed = data[64: 64 + neighbor_length]
        self.neighbors = []

        for pos in range(0, neighbor_length, 4):
            neighbor = inet_ntoa(neighbor_packed[pos:pos+4])
            self.neighbors.append(neighbor)

def print_hello():
    while True:
        print("hello")

def main():
    ospf = OSPF()
    conn = OSPFSocket(mcast_group, local_ip, ospf)
    t = Thread(target=conn.handle_read)
    t.start()

if __name__ == '__main__':
    main()
