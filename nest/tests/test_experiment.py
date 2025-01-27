# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2019-2020 NITK Surathkal

"""Test APIs from topology sub-package"""

import unittest
from nest.topology import Node, Router, connect
from nest.topology.network import Network
from nest.topology.address_helper import AddressHelper
from nest.experiment import Experiment, Flow, CoapFlow
from nest.clean_up import delete_namespaces
from nest.topology_map import TopologyMap
from nest import config

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
class TestExperiment(unittest.TestCase):
    def test_experiment(self, qdisc=None):
        n0 = Node("n0")
        n1 = Node("n1")
        r = Node("r")
        r.enable_ip_forwarding()

        (n0_r, r_n0) = connect(n0, r)
        (r_n1, n1_r) = connect(r, n1)

        n0_r.set_address("10.1.1.1/24")
        r_n0.set_address("10.1.1.2/24")
        r_n1.set_address("10.1.2.2/24")
        n1_r.set_address("10.1.2.1/24")

        n0.add_route("DEFAULT", n0_r)
        n1.add_route("DEFAULT", n1_r)

        n0_r.set_attributes("100mbit", "5ms")
        r_n0.set_attributes("100mbit", "5ms")

        r_n1.set_attributes("10mbit", "40ms", qdisc)
        n1_r.set_attributes("10mbit", "40ms")

        exp = Experiment("test-experiment")
        flow = Flow(n0, n1, n1_r.address, 0, 5, 2)
        exp.add_tcp_flow(flow)

        if qdisc:
            exp.require_qdisc_stats(r_n1)

        exp.run()

    def test_experiment_udp(self):
        n0 = Node("n0")
        n1 = Node("n1")
        r = Node("r")
        r.enable_ip_forwarding()

        (n0_r, r_n0) = connect(n0, r)
        (r_n1, n1_r) = connect(r, n1)

        n0_r.set_address("10.1.1.1/24")
        r_n0.set_address("10.1.1.2/24")
        r_n1.set_address("10.1.2.2/24")
        n1_r.set_address("10.1.2.1/24")

        n0.add_route("DEFAULT", n0_r)
        n1.add_route("DEFAULT", n1_r)

        n0_r.set_attributes("100mbit", "5ms")
        r_n0.set_attributes("100mbit", "5ms")

        r_n1.set_attributes("10mbit", "40ms", "pie")
        n1_r.set_attributes("10mbit", "40ms")

        exp = Experiment("test-experiment-udp")
        flow = Flow(n0, n1, n1_r.address, 0, 5, 2)
        exp.add_udp_flow(flow)

        exp.run()

    # Test `CoapFlow` API by generating GET and PUT CoAP traffic
    def test_experiment_coap(self):
        h1 = Node("h1")
        h2 = Node("h2")
        r = Router("r")

        n1 = Network("192.168.1.0/24")
        n2 = Network("192.168.3.0/24")

        (eth1, etr1) = connect(h1, r, network=n1)
        (etr2, eth2) = connect(r, h2, network=n2)

        AddressHelper.assign_addresses()

        eth1.set_attributes("1000mbit", "1ms")
        etr1.set_attributes("1000mbit", "1ms")
        etr2.set_attributes("1000mbit", "1ms")
        eth2.set_attributes("1000mbit", "1ms")

        h1.add_route("DEFAULT", eth1)
        h2.add_route("DEFAULT", eth2)

        exp = Experiment("test-experiment-coap")

        # Number of CON and NON messages to send
        n_con_msgs = 10
        n_non_msgs = 10

        # Configure a flow from `h1` to `h2`.
        flow_get = CoapFlow(h1, h2, eth2.get_address(), n_con_msgs, n_non_msgs)
        flow_put = CoapFlow(h1, h2, eth2.get_address(), n_con_msgs, n_non_msgs)

        # Add the above flows as CoAP flows to the current experiment
        exp.add_coap_flow(flow_get)
        exp.add_coap_flow(flow_put)

        # Run the experiment
        exp.run()

    def test_experiment_ipv6(self):
        # Test IPv6 with Duplicate Address Detection (DAD) disabled
        n0 = Node("n0")
        n1 = Node("n1")
        r = Node("r")
        r.enable_ip_forwarding()

        (n0_r, r_n0) = connect(n0, r)
        (r_n1, n1_r) = connect(r, n1)

        n0_r.set_address("10::1:1/122")
        r_n0.set_address("10::1:2/122")
        r_n1.set_address("10::2:2/122")
        n1_r.set_address("10::2:1/122")

        n0.add_route("DEFAULT", n0_r)
        n1.add_route("DEFAULT", n1_r)

        n0_r.set_attributes("100mbit", "5ms")
        r_n0.set_attributes("100mbit", "5ms")

        r_n1.set_attributes("10mbit", "40ms", "pie")
        n1_r.set_attributes("10mbit", "40ms")

        exp = Experiment("test-experiment-ipv6")
        flow = Flow(n0, n1, n1_r.address, 0, 5, 2)
        exp.add_tcp_flow(flow)

        exp.run()

    def test_experiment_ipv6_dad(self):
        # Test IPv6 with Duplicate Address Detection (DAD) enabled
        config.set_value("disable_dad", False)

        n0 = Node("n0")
        n1 = Node("n1")
        r = Node("r")
        r.enable_ip_forwarding()

        (n0_r, r_n0) = connect(n0, r)
        (r_n1, n1_r) = connect(r, n1)

        n0_r.set_address("10::1:1/122")
        r_n0.set_address("10::1:2/122")
        r_n1.set_address("10::2:2/122")
        n1_r.set_address("10::2:1/122")

        n0.add_route("DEFAULT", n0_r)
        n1.add_route("DEFAULT", n1_r)

        n0_r.set_attributes("100mbit", "5ms")
        r_n0.set_attributes("100mbit", "5ms")

        r_n1.set_attributes("10mbit", "40ms", "pie")
        n1_r.set_attributes("10mbit", "40ms")

        exp = Experiment("test-experiment-ipv6-dad")
        flow = Flow(n0, n1, n1_r.address, 0, 5, 2)
        exp.add_tcp_flow(flow)

        exp.run()

        # Resetting disable_dad in config
        config.set_value("disable_dad", True)

    def test_experiment_qdisc_codel(self):
        self.test_experiment("codel")

    def test_experiment_qdisc_fq_codel(self):
        self.test_experiment("fq_codel")

    def test_experiment_qdisc_pfifo(self):
        self.test_experiment("pfifo")

    def test_experiment_qdisc_pie(self):
        self.test_experiment("pie")

    def test_experiment_qdisc_fq_pie(self):
        self.test_experiment("fq_pie")

    def tearDown(self):
        delete_namespaces()
        TopologyMap.delete_all_mapping()


if __name__ == "__main__":
    unittest.main()
