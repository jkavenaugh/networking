#!/usr/bin/python3

"""

    The begining of some work with OSPF

"""

from threading import Thread
from socket import socket, AF_INET, SOCK_RAW, SOL_SOCKET, SO_REUSEADDR
from socket import inet_aton, inet_ntoa, INADDR_ANY, IPPROTO_IP, IP_ADD_MEMBERSHIP
import struct
import time
import os
import signal

mcast_group = '224.0.0.5'
local_ip = '172.16.50.208'
subnet_mask = '255.255.255.0'
area_id = '0.0.0.0'
router_id = '4.4.4.4'
router_priority = 0
hello_interval = 10
router_dead_interval = 40



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

    def receive_data(self):
        """Returns data received on the socket"""
        while True:
            data = (self.sock.recvfrom(1500))
            self.ospf.receive_data(data[0])
    def send_data(self, data, dest_ip):

        self.sock.sendto(data, (dest_ip,0))

    def close(self):
        socket.close()


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
        self.ttl = 225
        self.proto = 89
        self.check = 0
        self.saddr = 0
        self.daddr = 0
        self.ver_ihl = (self.ver << 4) + self.ihl

    def unpack(self, data):
        """Takes the IPv4 header from a socket and unpacks the binary into the proper
           IPv4 headers.
        """
        
        ip_header = data[0:20]
        self.ip_header = struct.unpack('!BBHHHBBH4s4s', ip_header)
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

        self.hello = Hello()
        self.hello.net_mask = inet_aton(subnet_mask)
        self.hello.interval = hello_interval
        self.hello.ebit = True
        self.hello.priority = router_priority
        self.hello.dead_int = router_dead_interval
        self.hello.des_router = inet_aton('0.0.0.0')
        self.hello.back_router = inet_aton('0.0.0.0')
        self.hello.neighbors = []

        self.header = Header()
        self.header.ver = 2
        self.header.mtype = 1
        self.header.length = 24 + len(self.hello.pack())
        self.header.router = inet_aton(router_id)
        self.header.area = inet_aton(area_id)
        self.header.check = 0
        self.header.auth_type = 0
        self.header.auth = struct.pack('B', 0)

        self.conn = OSPFSocket(mcast_group, local_ip, self)
        t = Thread(target=self.conn.receive_data)
        t.start()
        h = Thread(target=self.send_hello)
        h.start()


    def receive_data(self, data):
        ip_header = IPv4()
        ospf_header = Header()
        ospf_hello = Hello()

        ip_header.unpack(data)
        if ip_header.saddr == local_ip: 
            return

        if ospf_header.unpack(data, self) is False:
            return
        if ospf_header.mtype == 1:
            if ospf_hello.unpack(data, ospf_header.length, self) is True:
                if ospf_header.router not in self.hello.neighbors:
                    self.hello.neighbors.append(ospf_header.router)

    def send_hello(self):
            
            while True:
                    
                hello = Hello()
                ospf = Header()
                
                hello_packed = self.hello.pack()
                self.header.length = 24 + len(hello_packed)
                self.header.checkflag = True
                header_packed = self.header.pack()
                self.header.check = checksum(header_packed + hello_packed)
                header_packed = self.header.pack()
                packet = header_packed + hello_packed
                self.conn.send_data(packet, mcast_group)
                time.sleep(10)


def checksum(msg):
    s = 0
    for x in range(0, len(msg), 2):
        s += ((msg[x+1] << 8) + msg[x])

    s = (s >> 16) + (s & 0xffff)
    s += (s >> 16)
    s = ~s & 0xffff
    return s


class Header:
    """Handles the OSPF header"""

    def __init__(self):
        """Initializes the header fields of an OSPF header"""
        
        self.checkflag = False
        self.ver = 2
        self.mtype = 0
        self.length = 0
        self.router = 0
        self.area = 0
        self.check = 0
        self.auth_type = 0
        self.auth = 0

    def unpack(self, data, ospf):
        """Takes data from a raw socket and unpacks the OSPF header from
           packed binary.
        """

        ospf_header = data[20:44]
        ospf_header = struct.unpack('!BBH4s4sHH8s', ospf_header)
        ver = ospf_header[0]
        mtype = ospf_header[1]
        length = ospf_header[2]
        router = ospf_header[3]
        area = ospf_header[4]

        try:
            inet_ntoa(ospf_header[3])
            inet_ntoa(ospf_header[4])
        except OSError:
            return False

        check = ospf_header[5]
        auth_type = ospf_header[6]
        auth = struct.unpack('!BBBBBBBB', ospf_header[7])
        auth = ''.join(map(str, auth))

        if ver != 2:
            return False
        elif mtype < 0 or mtype > 5:
            return False
        elif router == ospf.header.router:
            return False
        elif area != ospf.header.area:
            return False
        elif checksum(data[20:length+20]):
            return False
        elif auth_type:
            return False

        self.ver = ver
        self.mtype = mtype
        self.length = length
        self.router = router
        self.area = area
        self.check = check
        self.auth_type = auth_type
        self.auth = auth

    def pack(self):

        head = struct.pack('!BBH4s4s', self.ver, self.mtype, self.length, self.router, self.area) 
        if self.checkflag:
            self.check = 0
            auth = struct.pack('!H', self.auth_type)
            self.checkflag = False
        else:
            auth = struct.pack('!H8s', self.auth_type, self.auth)
      
        check = struct.pack('H', self.check)
       
        return head + check + auth


class Hello:
    """Handles the OSPF Hello message"""

    def __init__(self):
        """Initilizes the fields of an OSPF Hello message"""
        
        self.net_mask = 0
        self.interval = 0
        self.mtbit = False
        self.ebit = False
        self.mcbit = False
        self.npbit = False
        self.lbit = False
        self.dcbit = False
        self.obit = False
        self.dnbit = False
        self.priority = 0
        self.dead_int = 0
        self.des_router = 0
        self.back_router = 0
        self.neighbors = []
        self.length = 0

        self.set_options()

    def set_options(self):
        self.options = 0
        if self.mtbit:
            self.options = 1
        if self.ebit:
            self.options += 2
        if self.mcbit:
            self.options += 4
        if self.npbit:
            self.options += 8
        if self.lbit:
            self.options += 16
        if self.dcbit:
            self.options += 32
        if self.obit:
            self.options += 64
        if self.dnbit:
            self.options += 128


    def unpack(self, data, length, ospf):
        """Takes data from a raw socket and unpacks the OSPF Hello message
           from the packed binary
        """

        hello_header = data[44:64]
        hello_header = struct.unpack('!4sHBBi4s4s', hello_header)
        net_mask = hello_header[0]
        interval = hello_header[1]
        options = hello_header[2]
        priority = hello_header[3]
        dead_int = hello_header[4]
        des_router = hello_header[5]
        back_router = hello_header[6]

        if net_mask != ospf.hello.net_mask:
            return False
        elif interval != ospf.hello.interval:
            return False
        elif dead_int != ospf.hello.dead_int:
            return False
        elif ((options  & 2) >> 1) != ospf.hello.ebit:
            return False

        self.net_mask = net_mask
        self.interval = interval
        self.options = options
        self.priority = priority
        self.dead_int = dead_int
        self.des_router = des_router
        self.back_router = back_router

        neighbor_length = length - 44
        neighbor_packed = data[64: 64 + neighbor_length]
        self.neighbors = []

        for pos in range(0, neighbor_length, 4):
            try:
               inet_ntoa(neighbor_packed[pos:pos+4])
               self.neighbors.append(neighbor_packed[pos:pos+4])
            except OSError:
               pass

        return True

    def pack(self):
        self.set_options()        
        hello_message = struct.pack('!4sHBBi4s4s', self.net_mask, self.interval, self.options, self.priority, self.dead_int, self.des_router, self.back_router)
        
        neighbors_packed = b''
        for neighbor in self.neighbors:
            neighbors_packed = b''.join([neighbors_packed, neighbor])
        
        hello = hello_message + neighbors_packed
        return hello

def main():
    if os.getuid():
        print("Must be run as Root")
        exit()

    ospf = OSPF()

if __name__ == '__main__':
    main()
