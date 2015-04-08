#!/usr/local/bin/python3.5

"""

    The begining of some work with OSPF

"""

from socket import socket, AF_INET, SOCK_RAW, SOL_SOCKET, SO_REUSEADDR
from socket import inet_aton, inet_ntoa, INADDR_ANY, IPPROTO_IP, IP_ADD_MEMBERSHIP
from struct import pack, unpack

class SocketOSPF:

    def __init__(self, mcast_group, local_ip):
        self.mcast_group = mcast_group
        self.local_ip = local_ip
    def connect(self):    
        self.conn = socket(AF_INET, SOCK_RAW, 89)
        self.conn.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        mreq = inet_aton(self.mcast_group) + inet_aton(self.local_ip)
        self.conn.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)

    def get_data(self):
        data = self.conn.recvfrom(1500)
        return data[0]

class IPv4:

    def __init__(self):
        
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

class HeaderOSPF:

    def __init__(self):

        self.ver = 2
        self.mtype = 0
        self.length = 0
        self.router = 0
        self.area = 0
        self.check = 0
        self.auth_type = 0
        self.auth = 0

    def unpack_header(self, data):
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

class HelloOSPF:

    def __init__(self):
        self.net_mask = 0
        self.interval = 0
        self.options = 0
        self.priority = 0
        self.dead_int = 0
        self.des_router = 0
        self.back_router = 0
        self.neighbor = 0
        self.length = 0

    def unpack_hello(self, data, length):
        hello_header = data[44:64]
        neighbors = data[60:length]
        self.hello_header = unpack('!4sHBB4s4s4s', hello_header)
        self.net_mask = inet_ntoa(self.hello_header[0])
        self.interval = self.hello_header[1]
        self.options = self.hello_header[2]
        self.priority = self.hello_header[3]
        dead = unpack('!BBBB', self.hello_header[4])
        self.dead_int = int(''.join(map(str,dead)))
        self.des_router = inet_ntoa(self.hello_header[5])
        self.back_router = inet_ntoa(self.hello_header[6])

def main():

    mcast_group = '224.0.0.5'
    local_ip = '172.16.50.13'
    conn = SocketOSPF(mcast_group, local_ip)
    conn.connect()
    
    ip_header = IPv4()
    ospf_header = HeaderOSPF()

    while True:
        data = conn.get_data()
        if data:
            ip_header.unpack_header(data)
            ospf_header.unpack_header(data)
            if ospf_header.mtype == 1:
                ospf_hello = HelloOSPF()
                ospf_hello.unpack_hello(data, ospf_header.length)
                print("OSPF Hello from Router: ", ip_header.saddr,"\n")
                print("Router ID: ", ospf_header.router, " Area: ", ospf_header.area, " Designated Router: ", ospf_hello.des_router)
                print("Interval: ", ospf_hello.interval, " Dead Interval: ", ospf_hello.dead_int)
            
if __name__ == '__main__':
    main()
