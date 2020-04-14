# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2019-2020 NITK Surathkal

import re
import subprocess
import json
import time
import numpy as np

from . import utils
import nest.topology.id_generator as id_generator
from .results import SsResults

INTERVAL = 0.2
RUN_TIME = 60
STATS_TO_PLOT = list()


def run_ss(cmd):
    """
    runs the ss command

    :param cmd: conmplete ss command to be run
    :type cmd: string

    :return output of the ss command
    """
    proc = subprocess.Popen(cmd.split(), stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = proc.communicate()

    # if there is an error
    if stderr:
        return None

    return stdout.decode();  # stdout is a bytes-like object. Hence the usage of decode()


def parse(ns_name, param_list, destination_ip, lock):
    """
    parses the required data from ss command's output

    :param param_list: list of the stats to be parsed
    :type param_list: list of string
    :param destination_ip: destination ip address of the socket
    :type destination_ip: string

    return
    """
    command = 'ip netns exec {} ss -i {} -n dst {}'.format(ns_name, 'dport != 12865 and sport != 12865' , destination_ip) #NOTE: Assumed that netserver runs on default port
    json_stats = {}
    cur_time = 0.0

    stats_dict_list = {}
    start_time = time.time()
    
    # This loop runs the ss command every `INTERVAL`s for `RUN_TIME`s
    while time.time() <= (start_time+RUN_TIME):
        stats = run_ss(command)
        port_pattern = re.escape(destination_ip) + r':\d+'
        port_list = re.findall(port_pattern, stats)
        extract_port_pattern = re.escape(destination_ip) + r':'
        port_list = [re.sub(extract_port_pattern, '', port) for port in port_list]
        cur_timestamp = time.time()
        
        for port in port_list:
            if port not in stats_dict_list:
                stats_dict_list[port] = [{"timestamp": str(cur_timestamp)}]
            else:
                stats_dict_list[port].append({"timestamp": str(cur_timestamp)})

        for param in param_list:
            pattern = r'\s' + re.escape(param) + r'[\s:]\w+\.?\w*(?:[\/\,]\w+\.?\w*)*\s'
            # result list stores all the string that is matched by the `pattern`
            result_list = re.findall(pattern, stats)
            # pattern to match the required param in result_list
            pattern = r'^' + re.escape(param) + r'[:\s]'

            val = ''
            for i in range(len(result_list)):
                result = result_list[i].strip()
                val = re.sub(pattern, '', result)
                # remove the units at the end
                val = re.sub(r'[A-Za-z]', '', val)
                try:
                    # rtt has both avg and dev rtt separated by a /
                    if param == 'rtt':
                        avg_rtt = val.split('/')[0]
                        dev_rtt = val.split('/')[1]
                        stats_dict_list[port_list[i]][-1]['rtt'] = avg_rtt
                        stats_dict_list[port_list[i]][-1]['dev_rtt'] = dev_rtt
                    else:
                        stats_dict_list[port_list[i]][-1][param] = val
                except:
                    pass
        time.sleep(INTERVAL)

    lock.acquire()
    SsResults.add_result(ns_name, {destination_ip: stats_dict_list})
    lock.release()

def parse_and_plot(filename, parameters):
    """

    parses the json from a file and plots time vs `parameter`

    :param filename: path of the json file
    :type filename: string
    :param paramter: parameters to be plotted (eg. cwnd, rtt)
    :type parameter: list of strings
    """
    f = open(filename, 'r')

    # stats stores the json object as list of dicts with timestamp as keys
    stats = json.load(f)

    x = list()
    y = np.empty((len(parameters), int(RUN_TIME/INTERVAL)+1))

    param_map = {}

    for i in range(len(parameters)):
        param_map[parameters[i]] = i

    # Loops through the list of dicts and stores the values of timestamps
    # in x and value of the required `paramter` in y for plotting
    index = 0
    for stat in stats:
        for key, val in stat.items():
            x.append(float(key))
            for param, value in val.items():
                if param in parameters:
                    try:
                        y[param_map[param], index] = float(value)
                    except:
                        y[param_map[param], index] = 0.0
            index = index + 1
    # utils.plot(x, y, xlabel='time', ylabel=parameter)
    utils.sub_plots(x, y, xlabel='time', ylabel=parameters)
    f.close()

# TODO: Integrate with nest


def parse_ss(ns_name, destination_ip, stats_to_plot, start_time, run_time, lock):
    param_list = ['cwnd', 'rwnd', 'rtt', 'ssthresh', 'rto', 'delivery_rate']
    global RUN_TIME
    RUN_TIME = run_time
    global STATS_TO_PLOT 
    STATS_TO_PLOT = stats_to_plot
    
    if(start_time != 0):
        time.sleep(start_time)

    parse(ns_name, param_list, destination_ip, lock)


