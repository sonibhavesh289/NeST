# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2019-2020 NITK Surathkal

"""Test APIs from topology sub-package"""

import unittest
import subprocess

from nest.topology import Node, connect, Switch, Router, Address
from nest.clean_up import delete_namespaces
from nest.topology_map import TopologyMap
from nest.topology.interface import Interface
from nest import config

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
class TestTopology(unittest.TestCase):
    def setUp(self):
        self.n0 = Node("n0")
        self.n1 = Node("n1")

    def tearDown(self):
        delete_namespaces()
        TopologyMap.delete_all_mapping()

    def test_p2p(self):
        (n0_n1, n1_n0) = connect(self.n0, self.n1)

        n0_n1.set_address("10.0.0.1/24")
        n1_n0.set_address("10.0.0.2/24")

        status = self.n0.ping("10.0.0.2")

        self.assertTrue(status)

    def test_p2p_ipv6(self):
        (n0_n1, n1_n0) = connect(self.n0, self.n1)

        self.n0.disable_ip_dad()
        self.n1.disable_ip_dad()

        n0_n1.set_address("2001:1:1:1443::411/122")
        n1_n0.set_address("2001:1:1:1443::412/122")

        status = self.n0.ping(n1_n0.address)

        self.assertTrue(status)

    def test_prp(self):
        # pylint: disable=invalid-name
        r = Node("r")
        r.enable_ip_forwarding()

        (n0_r, r_n0) = connect(self.n0, r)
        (r_n1, n1_r) = connect(r, self.n1)

        n0_r.set_address("10.1.1.1/24")
        r_n0.set_address("10.1.1.2/24")
        r_n1.set_address("10.1.2.2/24")
        n1_r.set_address("10.1.2.1/24")

        self.n0.add_route("DEFAULT", n0_r)
        self.n1.add_route("DEFAULT", n1_r)

        status = self.n0.ping("10.1.2.1")

        self.assertTrue(status)

    def test_prp_ipv6(self):
        # pylint: disable=invalid-name
        r = Node("r")
        r.enable_ip_forwarding(ipv6=True)

        (n0_r, r_n0) = connect(self.n0, r)
        (r_n1, n1_r) = connect(r, self.n1)

        self.n0.disable_ip_dad()
        self.n1.disable_ip_dad()

        n0_r.set_address("2001:0001:0001:1443::0411/122")
        r_n0.set_address("2001:0001:0001:1443::0412/122")
        r_n1.set_address("2001:0001:0001:1444::0412/122")
        n1_r.set_address("2001:0001:0001:1444::0411/122")

        self.n0.add_route("DEFAULT", n0_r)
        self.n1.add_route("DEFAULT", n1_r)

        status = self.n0.ping(n1_r.address)

        self.assertTrue(status)

    def test_p2p_multiple_set_address(self):
        (n0_n1, n1_n0) = connect(self.n0, self.n1)

        self.n0.disable_ip_dad()
        self.n1.disable_ip_dad()

        status_1 = self.n0.ping(Address("10.1.1.2/24"))
        status_2 = self.n0.ping(Address("10.1.1.3/24"))
        status_3 = self.n0.ping(Address("2001:1:1:1443::412/122"))

        self.assertFalse(status_1)
        self.assertFalse(status_2)
        self.assertFalse(status_3)

        n0_n1.set_address(["10.1.1.1/24", "2001:1:1:1443::411/122"])
        n1_n0.set_address(["10.1.1.2/24", "10.1.1.3/24", "2001:1:1:1443::412/122"])

        status_4 = self.n0.ping(n1_n0.get_address(ipv4=True, ipv6=False)[0])
        status_5 = self.n0.ping(n1_n0.get_address(ipv4=True, ipv6=False)[1])
        status_6 = self.n0.ping(n1_n0.get_address(ipv4=False, ipv6=True))

        self.assertTrue(status_4)
        self.assertTrue(status_5)
        self.assertTrue(status_6)

    def test_add_addr(self):
        (n0_n1, n1_n0) = connect(self.n0, self.n1)

        self.n0.disable_ip_dad()
        self.n1.disable_ip_dad()

        n0_n1.set_address(["10.1.1.1/24", "2001:1:1:1443::411/122"])
        n1_n0.set_address(["10.1.1.2/24", "2001:1:1:1443::412/122"])

        n1_n0.add_address(["10.1.1.3/24", "2001:1:1:1443::413/122"])

        status_1 = self.n0.ping(n1_n0.get_address(ipv4=True, ipv6=False)[0])
        status_2 = self.n0.ping(n1_n0.get_address(ipv4=True, ipv6=False)[1])
        status_3 = self.n0.ping(n1_n0.get_address(ipv4=False, ipv6=True)[0])
        status_4 = self.n0.ping(n1_n0.get_address(ipv4=False, ipv6=True)[1])

        self.assertTrue(status_1)
        self.assertTrue(status_2)
        self.assertTrue(status_3)
        self.assertTrue(status_4)

    def test_get_addr(self):
        (n0_n1, n1_n0) = connect(self.n0, self.n1)

        self.n0.disable_ip_dad()
        self.n1.disable_ip_dad()

        n0_n1.set_address(["10.0.0.1/24", "2001:1:1:1443::411/122"])
        n1_n0.set_address(["10.0.0.2/24", "2001:1:1:1443::412/122"])

        addr = n0_n1.get_address()
        self.assertEqual(
            (addr[0].get_addr(), addr[1].get_addr()),
            (
                Address("10.0.0.1/24").get_addr(),
                Address("2001:1:1:1443::411/122").get_addr(),
            ),
            "n0_n1 interface has unexpected addresses",
        )

        addr = n1_n0.get_address()
        self.assertEqual(
            (addr[0].get_addr(), addr[1].get_addr()),
            (
                Address("10.0.0.2/24").get_addr(),
                Address("2001:1:1:1443::412/122").get_addr(),
            ),
            "n1_n0 interface has unexpected address list",
        )

        addr = n0_n1.get_address(True, False, False)
        self.assertEqual(
            addr.get_addr(),
            Address("10.0.0.1/24").get_addr(),
            "n0_n1 interface has unexpected ipv4 address",
        )

        addr = n0_n1.get_address(False, True, False)
        self.assertEqual(
            addr.get_addr(),
            Address("2001:1:1:1443::411/122").get_addr(),
            "n0_n1 interface has unexpected ipv6 address",
        )

        addr = n0_n1.get_address(True, False, True)
        self.assertEqual(
            [addr[0].get_addr()],
            [Address("10.0.0.1/24").get_addr()],
            "n0_n1 interface has unexpected ipv4 address list",
        )

        addr = n0_n1.get_address(False, True, True)
        self.assertEqual(
            [addr[0].get_addr()],
            [Address("2001:1:1:1443::411/122").get_addr()],
            "n0_n1 interface has unexpected ipv6 address list",
        )

        addr = n0_n1.get_address(True, True, True)
        self.assertEqual(
            (addr[0].get_addr(), addr[1].get_addr()),
            (
                Address("10.0.0.1/24").get_addr(),
                Address("2001:1:1:1443::411/122").get_addr(),
            ),
            "n0_n1 interface has unexpected address lists",
        )

        with self.assertRaises(ValueError) as err:
            addr = n0_n1.get_address(False, False, False)
        self.assertEqual(
            str(err.exception), "Either ipv4 or ipv6 argument must be True"
        )

    def test_del_addr(self):
        (n0_n1, n1_n0) = connect(self.n0, self.n1)

        n0_n1.set_address(["10.1.1.1/24", "2001:1:1:1443::411/122"])
        n1_n0.set_address(["10.1.1.2/24", "10.1.1.3/24", "2001:1:1:1443::412/122"])

        # Test 1
        status_1 = self.n0.ping(Address("10.1.1.2/24"))

        self.assertTrue(status_1, "Ping failed")

        n1_n0.del_address("10.1.1.2/24")

        status_2 = self.n0.ping(Address("10.1.1.2/24"))

        self.assertFalse(status_2, "Address not deleted")

        addr = n1_n0.get_address(True, False, False)
        self.assertEqual(
            (Address("10.1.1.3/24").get_addr()),
            addr.get_addr(),
            "Failed to update address list",
        )

        # Test 2
        with self.assertLogs("nest.topology.device", level="WARNING") as log:
            n1_n0.del_address("10.0.0.1/24")
        self.assertEqual(
            log.output,
            [
                "WARNING:nest.topology.device:Cannot delete an address "
                "that is not assigned. (10.0.0.1/24)"
            ],
        )

        # Test 3
        n1_n0.del_address(["10.1.1.3/24", "2001:1:1:1443::412/122"])
        addr = n1_n0.get_address(True, True, True)
        self.assertEqual(
            [],
            addr,
            "Failed to update address list",
        )

    def test_simple_lan(self):
        # pylint: disable=too-many-locals
        n0 = Node("n0")
        n1 = Node("n1")
        n2 = Node("n2")
        n3 = Node("n3")
        s0 = Switch("s0")

        (n0_s0, _) = connect(n0, s0)
        (n1_s0, _) = connect(n1, s0)
        (n2_s0, _) = connect(n2, s0)
        (n3_s0, _) = connect(n3, s0)

        nodes = [n0, n1, n2, n3]
        interface = [n0_s0, n1_s0, n2_s0, n3_s0]

        n0_s0.set_address("10.0.0.1/24")
        n1_s0.set_address("10.0.0.2/24")
        n2_s0.set_address("10.0.0.3/24")
        n3_s0.set_address("10.0.0.4/24")

        for x in nodes:
            for y in interface:
                status = x.ping(y.address, packets=1)
                if not status:
                    break

        self.assertTrue(status)

    def test_dumbbell_lan(self):
        # pylint: disable=too-many-locals
        n0 = Node("n0")
        n1 = Node("n1")
        n2 = Node("n2")
        n3 = Node("n3")
        s0 = Switch("s0")
        s1 = Switch("s1")

        (n0_s0, _) = connect(n0, s0)
        (n1_s0, _) = connect(n1, s0)
        (n2_s1, _) = connect(n2, s1)
        (n3_s1, _) = connect(n3, s1)

        connect(s0, s1)

        nodes = [n0, n1, n2, n3]
        interface = [n0_s0, n1_s0, n2_s1, n3_s1]

        n0_s0.set_address("10.0.0.1/24")
        n1_s0.set_address("10.0.0.2/24")
        n2_s1.set_address("10.0.0.3/24")
        n3_s1.set_address("10.0.0.4/24")

        for x in nodes:
            for y in interface:
                status = x.ping(y.address, packets=1)
                if not status:
                    break

        self.assertTrue(status)

    def test_tcp_param(self):
        self.n0.configure_tcp_param("ecn", "1")
        ecn = self.n0.read_tcp_param("ecn")
        self.assertEqual(ecn, "1")

    def test_invalid_interface_name(self):
        # Disable topology map
        config.set_value("assign_random_names", False)

        # Valid interface name
        Interface("namewith15chars")

        # Invalid interface name
        with self.assertRaises(ValueError) as cm:
            Interface("looonginvalidname")
        err = cm.exception
        self.assertEqual(
            str(err),
            "Device name looonginvalidname is too long. Device names "
            "should not exceed 15 characters",
        )

        # Enable topology map
        config.set_value("assign_random_names", True)

    def test_invalid_veth_name(self):
        # Disable topology map
        config.set_value("assign_random_names", False)

        node0 = Node("longname0")
        node1 = Node("longname1")

        with self.assertRaises(ValueError) as cm:
            connect(node0, node1)
        err = cm.exception
        self.assertEqual(
            str(err),
            "Auto-generated device name longname0-longname1-0 is "
            "too long. The length of name should not exceed 15 characters.",
        )

        # Enable topology map
        config.set_value("assign_random_names", True)

    def test_valid_veth_name(self):
        node0 = Node("node0")
        node1 = Node("node1")

        eth0, eth1 = connect(node0, node1)

        self.assertEqual(
            eth0.name, "node0-node1-0", "eth0 has unexpected autogenerated name"
        )
        self.assertEqual(
            eth1.name, "node1-node0-0", "eth1 has unexpected autogenerated name"
        )

        eth2, eth3 = connect(node0, node1)

        self.assertEqual(
            eth2.name, "node0-node1-1", "eth2 has unexpected autogenerated name"
        )
        self.assertEqual(
            eth3.name, "node1-node0-1", "eth3 has unexpected autogenerated name"
        )

        eth4, eth5 = connect(node0, node1, "eth4", "eth5")

        self.assertEqual(eth4.name, "eth4", "eth4 has unexpected user-given name")
        self.assertEqual(eth5.name, "eth5", "eth5 has unexpected user-given name")

    def test_invalid_ifb_interface_name(self):
        # Disable topology map
        config.set_value("assign_random_names", False)

        node0 = Node("node0")
        node1 = Node("node1")
        eth0, _ = connect(node0, node1)

        with self.assertRaises(ValueError) as cm:
            eth0.set_attributes("10mbit", "10ms", "codel")
        err = cm.exception
        self.assertEqual(
            str(err),
            "Device name ifb-node0-node1-0 is too "
            "long. Device names should not exceed 15 characters",
        )

        # Enable topology map
        config.set_value("assign_random_names", True)

    def test_run_inside_node(self):
        (n0_n1, n1_n0) = connect(self.n0, self.n1)

        n0_n1.set_address("10.0.0.1/24")
        n1_n0.set_address("10.0.0.2/24")

        # Run ping from self.n0 to self.n1
        with self.n0:
            command = f"ping -c 1 {n1_n0.address.get_addr(with_subnet=False)}"
            with subprocess.Popen(
                command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE
            ) as proc:
                (stdout, _) = proc.communicate()

        self.assertEqual(stdout[:4], b"PING", "Invalid ping output")

    def test_prp_router_api(self):
        # pylint: disable=invalid-name
        r = Router("r")

        (n0_r, r_n0) = connect(self.n0, r)
        (r_n1, n1_r) = connect(r, self.n1)

        n0_r.set_address("10.1.1.1/24")
        r_n0.set_address("10.1.1.2/24")
        r_n1.set_address("10.1.2.2/24")
        n1_r.set_address("10.1.2.1/24")

        self.n0.add_route("DEFAULT", n0_r)
        self.n1.add_route("DEFAULT", n1_r)

        status = self.n0.ping("10.1.2.1")

        self.assertTrue(status)


if __name__ == "__main__":
    unittest.main()
