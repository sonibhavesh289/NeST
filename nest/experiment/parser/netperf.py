# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2019-2020 NITK Surathkal

import re
import subprocess
import time
import copy
import shlex
import tempfile
from ..results import NetperfResults


class NetperfRunner:
    """Runs netperf command and parses statistics from it's output

    Attributes
    ----------
    default_netperf_options : dict
        default options to run netperf command with
    netperf_tcp_options : dict
        tcp related netperf options
    netperf_udp_options : dict
        udp related netperf options
    out : File
        temporary file to hold the stats
    ns_name : str
        network namespace to run netperf from
    destination_ip : str
        ip address of the destination namespace
    start_time : num
        time at which netperf is to run
    run_time : num
        total time to run netperf for
    """

    tcp_output_options = [
        'THROUGHPUT', 'LOCAL_CONG_CONTROL', 'REMOTE_CONG_CONTROL', 'TRANSPORT_MSS',
        'LOCAL_SOCKET_TOS', 'REMOTE_SOCKET_TOS'
    ]

    default_netperf_options = {
        'banner': '-P 0',                           # Disable test banner
        'ipv4': '-4',                               # IPv4 Addresses
        # Test type (NOTE: TCP_STREAM only for now)
        'testname': '-t TCP_STREAM',
        # File to transmit (NOTE: Inspired from flent)
        'fill_file': '-F /dev/urandom',
        # Length of test (NOTE: Default 10s)
        'testlen': '-l {}'.format(10),
        # Generated interim results every INTERVAL secs
        'intervel': '-D -{}'.format(0.2),
        'debug': '-d',                              # Enable debug mode
    }

    netperf_tcp_options = {
        'cong_algo': '-K cubic',                    # Congestion algorithm
        'stats': '-k THROUGHPUT'                    # Stats required
    }

    netperf_udp_options = {
        'routing': '-R 1',                          # Enable routing
        'stats': '-k THROUGHPUT'                    # Stats required
    }

    def __init__(self, ns_name, destination_ip, start_time, run_time, **kwargs):
        """Constructor to initialize netperf runner

        Parameters
        ----------
        ns_name : str
            network namespace to run netperf from
        destination_ip : str
            ip address of the destination namespace
        start_time : num
            time at which netperf is to run
        run_time : num
            total time to run netperf for
        **kwargs
            netperf options to override
        """
        self.out = tempfile.TemporaryFile()
        self.ns_name = ns_name
        self.destination_ip = destination_ip
        self.start_time = start_time
        self.run_time = run_time
        self.options = copy.deepcopy(kwargs)

    # Should this be placed somewhere else?
    @staticmethod
    def run_netserver(ns_name):
        """Run netserver in `ns_name`

        Parameters
        ----------
        ns_name : str
            namespace to run netserver on
        """
        command = 'ip netns exec {} netserver'.format(ns_name)
        subprocess.Popen(shlex.split(command))

    def run(self):
        """ Runs netperf at t=`self.start_time`
        """
        netperf_options = copy.copy(NetperfRunner.default_netperf_options)
        test_options = None

        # Change the default runtime
        netperf_options['testlen'] = '-l {}'.format(self.run_time)
        # Set test
        netperf_options['testname'] = '-t {}'.format(self.options['testname'])

        if netperf_options['testname'] == '-t TCP_STREAM':
            test_options = copy.copy(NetperfRunner.netperf_tcp_options)
            test_options['cong_alg'] = '-K {}'.format(
                self.options['cong_algo'])
        elif netperf_options['testname'] == '-t UDP_STREAM':
            test_options = copy.copy(NetperfRunner.netperf_udp_options)

        netperf_options_list = list(netperf_options.values())
        netperf_options_string = ' '.join(netperf_options_list)
        test_options_list = list(test_options.values())
        test_options_string = ' '.join(test_options_list)

        command = 'ip netns exec {ns_name} netperf {options} -H {destination} -- {test_options}'.format(
            ns_name=self.ns_name, options=netperf_options_string, destination=self.destination_ip,
            test_options=test_options_string)

        if self.start_time != 0:
            time.sleep(self.start_time)

        proc = subprocess.Popen(command.split(),
                                stdout=self.out, stderr=subprocess.PIPE)

        proc.communicate()

    def parse(self):
        """Parse netperf output from `self.out`
        """
        self.out.seek(0)    # rewind to start of the temp file
        raw_stats = self.out.read().decode()

        # pattern that matches the netperf output corresponding to throughput
        throughput_pattern = r'NETPERF_INTERIM_RESULT\[\d+]=(?P<throughput>\d+\.\d+)'
        throughputs = [throughput.group('throughput') for throughput in re.finditer(
            throughput_pattern, raw_stats)]

        # pattern that matches the netperf output corresponding to interval
        timestamp_pattern = r'NETPERF_ENDING\[\d+]=(?P<timestamp>\d+\.\d+)'
        timestamps = [timestamp.group('timestamp') for timestamp in re.finditer(
            timestamp_pattern, raw_stats)]

        # pattern that gives the remote port
        remote_port_pattern = r'remote port is (?P<remote>\d+)'
        remote_port = re.search(remote_port_pattern, raw_stats).group('remote')

        stats_list = []

        for i in range(len(throughputs)):
            stats_list.append({
                'timestamp': timestamps[i],
                'throughput': throughputs[i]
            })

            stats_dict = {'{}:{}'.format(
                self.destination_ip, remote_port): stats_list}

        NetperfResults.add_result(self.ns_name, stats_dict)