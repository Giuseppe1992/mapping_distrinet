import json
import logging
import os
import warnings


class InstanceEC2(object):
    def __init__(self, vm_options):
        self._log = logging.getLogger(__name__)
        self._vm_options = vm_options

    @property
    def vm_options(self):
        return self._vm_options

    @vm_options.setter
    def vm_options(self, new_vm_options):
        warnings.warn("original VMs instances have been modified")
        self._vm_options = new_vm_options

    def get_memory(self, vm):
        return self._vm_options[vm]['memory']

    def get_cores(self, vm):
        return self._vm_options[vm]['vCPU']

    def get_hourly_cost(self, vm):
        return self._vm_options[vm]['hourly_cost']

    @classmethod
    def get_EC2_vritual_machines(cls, vm_type='general_purpose'):
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "instances", vm_type + ".json")) as f:
            vm_options = json.load(f)
        # gibibyte to mebibyte conversion
        for vm in vm_options:
            vm_options[vm]['memory'] *= 1024

        return cls(vm_options)
