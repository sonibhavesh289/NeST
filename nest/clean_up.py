# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2019-2020 NITK Surathkal

"""
This module contains methods to kill any running processes in namespaces
and delete all namespaces after the experiment is complete.
"""

import atexit
from . import engine
from .topology_map import TopologyMap

def kill_processes():
    """
    Kill any running processes in namespaces
	"""
    for namespace in TopologyMap.get_namespaces():
        engine.kill_all_processes(namespace['id'])

@atexit.register
def delete_namespaces():
    """
    Delete all the newly generated namespaces
    """
    namespaces = TopologyMap.get_namespaces()

    for namepspace in namespaces:
        engine.delete_ns(namepspace['id'])

    print('Cleaned up environment!')