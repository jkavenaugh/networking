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
        return self.conn.recvfrom(1500)

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
        packet = data[0]
        ip_header = packet[0:20]
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
        return

def main():

    mcast_group = '224.0.0.5'
    local_ip = '172.16.50.13'
    conn = SocketOSPF(mcast_group, local_ip)
    conn.connect()
    
    ip_header = IPv4()

    while True:
        data = conn.get_data()
        ip_header.unpack_header(data)
        print("Source: ",ip_header.saddr, " Dest: ", ip_header.daddr)

if __name__ == '__main__':
    main()
