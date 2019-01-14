import json
import logging
import os
import warnings

import networkx as nx


class PhysicalNetwork(object):

    def __init__(self, g, grouped_interfaces=False):
        self._g = g
        self.grouped_interfaces = grouped_interfaces
        self._log = logging.getLogger(__name__)

    @property
    def g(self):
        return self._g

    @g.setter
    def g(self, g_new):
        warnings.warn("original physical network has been modified")
        self._g = g_new

    def edges(self, keys=False):
        return self._g.edges(keys=keys)

    def nodes(self):
        return self._g.nodes()

    def cores(self, node):
        if 'nb_cores' in self._g.nodes[node]:
            return self._g.nodes[node]['nb_cores']
        return 0

    def memory(self, node):
        if 'ram_size' in self._g.nodes[node]:
            return self._g.nodes[node]['ram_size']
        return 0

    def link_rate(self, i, j, device='dummy_interface'):
        return self._g[i][j][device]['rate']

    def get_nw_interfaces(self, i, j):
        return self._g[i][j]

    def get_neighbors(self, i):
        return self._g[i]

    def get_associated_interfaces(self, i, j):
        if not self.grouped_interfaces:
            raise ValueError("not defined")
        return self._g[i][j]['dummy_interface']['associated_interfaces']

    @classmethod
    def grid5000(cls, name, n_interfaces_to_consider=float('inf'), group_interfaces=False):
        """Import the physical network topology from a Grid5000 cluster.

        Parameters
        ----------
        name : the name of the cluster in grid5000 to be considered
            The corresponding filename should be placed in instances/physical/name.json

        n_interfaces_to_consider : the maximum number of network interfaces to be considered per node (optional, default: all)

        group_interfaces : True if the interfaces towards the same destination node should be considered as a single one (optional, default: False)
            This option allow traffic from a Node i to a Node j to be splitted between different interfaces. E.g., 50% on eth0 and 50% on eth1

        Returns
        -------
        an instance of the PhysicalNetwork class
        """
        g = nx.MultiGraph()
        # compute nodes
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "physical_topo", name + ".json")) as f:
            data = json.load(f)

            for node in data['items']:
                # from byte to mebibyte
                g.add_node(node['uid'], nb_cores=node['architecture']['nb_cores'] * node['architecture']['nb_procs'],
                           ram_size=node['main_memory']['ram_size'] / (1024 ** 2))

                n_added_interfaces = 0
                for interface, link in enumerate(node['network_adapters']):
                    if link['device'].startswith("eth") and link['enabled'] and link['driver'] == "ixgbe":
                        source, dest, device_name, device_rate = node['uid'], link['switch'], link['device'], link[
                            'rate'] / 10 ** 6
                        if not group_interfaces:
                            g.add_edge(source, dest, key=device_name, rate=device_rate)
                        else:
                            if not g.has_edge(source, dest):
                                g.add_edge(source, dest, key='dummy_interface', rate=device_rate,
                                           associated_interfaces={device_name: device_rate})
                            else:
                                g[source][dest]['dummy_interface']['rate'] += device_rate
                                g[source][dest]['dummy_interface']['associated_interfaces'][device_name] = device_rate

                        n_added_interfaces += 1
                        if n_added_interfaces == n_interfaces_to_consider:
                            break

        return cls(g, group_interfaces)

    @classmethod
    def crete_test_nw(cls):
        """ small network to run tests
        """
        raise NotImplementedError
