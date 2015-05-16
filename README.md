5/16/2015
    Removed inet_aton conversions for IPv4 addresses.
    Checks Header fields and checks for correct checksum.
    Checks Hello packet for proper Net Mask, HelloInterval,
    RouterDeadInterval and E-bit. Checks neighbors field 
    for proper IPv4 addresses.


OSPF code added
- Gets OSPF traffic
- Processes hello messages
- Sends generic hello message
