from functools import lru_cache

from embedding import Embed
from .solution import Solution


class Bin(object):
    """ Container for logical nodes mapped on the Bin associated to a VM """

    def __init__(self, vm_type):
        self.vm_type = vm_type
        self.items = set()
        self.used_cores = 0
        self.used_memory = 0

    def add_item(self, u, req_cores, req_memory):
        self.items.add(u)
        self.used_cores += req_cores
        self.used_memory += req_memory

    def __str__(self):
        """ Printable representation """
        return f"Bin(vm_type={self.vm_type}, items={self.items}, used cores={self.used_cores}, used memory={self.used_memory})"


class EmbedHeu(Embed):
    @lru_cache(maxsize=256)
    def get_cheapest_feasible(self, cores, memory):
        """Given a demand in terms of number of cores and memory return the cheapest EC2 instance with enough resources.
        """
        if (cores > self.physical.get_cores(self.vm_max_cores) or memory > self.physical.get_memory(
                self.vm_max_cores)) and (
                cores > self.physical.get_cores(self.vm_max_memory) or memory > self.physical.get_memory(
            self.vm_max_memory)):
            return None

        return min(((vm, self.physical.get_hourly_cost(vm)) for vm in self.physical.vm_options if
                    cores <= self.physical.get_cores(vm) and memory <= self.physical.get_memory(vm)),
                   key=lambda x: x[1])[0]

    @Embed.timeit
    def __call__(self, **kwargs):
        """
        """
        self.vm_max_cores = max(self.physical.vm_options, key=lambda vm: self.physical.get_cores(vm))
        self.vm_max_memory = max(self.physical.vm_options, key=lambda vm: self.physical.get_memory(vm))

        bins = []
        for u in self.logical.nodes():
            req_cores, req_memory = self.logical.requested_cores(u), self.logical.requested_memory(u)
            # Check if the item fits in an already opened bin.
            # In such a case, it adds the logical node to the item list and update resources usage.
            for bin in bins:
                if bin.used_cores + req_cores <= self.physical.get_cores(
                        bin.vm_type) and bin.used_memory + req_memory <= self.physical.get_memory(bin.vm_type):
                    bin.add_item(u, req_cores, req_memory)
                    break
            else:
                # Check if it is convenient to upgrade a bin type.
                # To this end, given an item u and bin b it gets
                # - the cheapest available bin b' with enough resources to contain the items of b and u
                # - the cheapest available bin b'' with enough resources to contain i
                # If the cost of b' is smaller than the cost of b upgrade b to b', otherwise keep b and open b''.
                vm_to_pack_u = self.get_cheapest_feasible(req_cores, req_memory)
                for bin in reversed(bins):
                    vm_to_upgrade = self.get_cheapest_feasible(req_cores + bin.used_cores, req_memory + bin.used_memory)
                    if vm_to_upgrade and self.physical.get_hourly_cost(vm_to_upgrade) < self.physical.get_hourly_cost(
                            vm_to_pack_u) + self.physical.get_hourly_cost(bin.vm_type):
                        bin.vm_type = vm_to_upgrade
                        bin.add_item(u, req_cores, req_memory)
                        break
                else:
                    # Open a new bin b'' and insert u on it.
                    new_bin = Bin(vm_to_pack_u)
                    new_bin.add_item(u, req_cores, req_memory)
                    bins.append(new_bin)
        # print(self.get_cheapest_feasible.cache_info())
        return round(sum(self.physical.get_hourly_cost(bin.vm_type) for bin in bins), 2), \
               Solution(self.physical, self.logical, {(bin.vm_type, i): bin.items for i, bin in enumerate(bins)})
