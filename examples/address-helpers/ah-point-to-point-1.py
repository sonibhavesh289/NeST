# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2019-2022 NITK Surathkal

########################
# SHOULD BE RUN AS ROOT
########################
from nest.topology import *
from nest.topology.network import Network
from nest.topology.address_helper import AddressHelper

# This program emulates a point to point network between two hosts `h1` and
# `h2`. One ping packet is sent from `h1` to `h2`, and the success/failure
# of ping is reported. This program is similar to the point-to-point-1.py
# example available in `examples/tutorial/basic-examples`, the only difference
# is that we use an address helper in this program to assign IPv4 addresses to
# interfaces instead of manually assigning them. Note that two packages:
# `Network` and `AddressHelper` are imported in this program (Lines 8-9 above).

#################################
#       Network Topology        #
#                               #
#          5mbit, 5ms -->       #
#   h1 ------------------- h2   #
#       <-- 10mbit, 100ms       #
#                               #
#################################

# Create two hosts `h1` and `h2`
h1 = Node("h1")
h2 = Node("h2")

# Set the IPv4 address for the network, and not the interfaces.
# We will use the `AddressHelper` later to assign addresses to the interfaces.
n1 = Network("192.168.1.0/24")

# Connect the above two hosts using a veth pair. Note that `connect` API in
# this program takes `network` as an additional parameter. The following line
# implies that `eth1` and `eth2` interfaces on `h1` and `h2`, respectively are
# in the same network `n1`.
(eth1, eth2) = connect(h1, h2, network=n1)

# Assign IPv4 addresses to all the interfaces in the network.
AddressHelper.assign_addresses()

# Set the link attributes: `h1` --> `h2` and `h2` --> `h1`
eth1.set_attributes("5mbit", "5ms")
eth2.set_attributes("10mbit", "100ms")

# Send a `ping` from `h1` to `h2`.
h1.ping(eth2.address)
