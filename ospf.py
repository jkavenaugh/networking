#!/usr/local/bin/python3.5

"""

    The begining of some work with OSPF

"""

from socket import socket, AF_INET, SOCK_RAW, SOL_SOCKET, SO_REUSEADDR
from socket import inet_aton, INADDR_ANY, IPPROTO_IP, IP_ADD_MEMBERSHIP
from struct import pack

mcast_group = '224.0.0.5'
local_ip = '172.16.50.13'

s = socket(AF_INET, SOCK_RAW, 89)
s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
# mreq = pack("4sl", inet_aton(mcast_group), inet_aton(local_ip))
mreq = inet_aton(mcast_group) + inet_aton(local_ip)
s.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)

while True:
    data = (s.recvfrom(1500))
    print(data)


