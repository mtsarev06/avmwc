from vmwc import *
from vmwc import VirtualMachine as DefaultVirtualMachine, VMWareClient as DefaultVMWareClient

from .vmware_tools import VMWareTools


class VirtualMachine(DefaultVirtualMachine):
    """
    Extends default VirtualMachine abilities:
    adds new vmware_tools attribute which is used
    for working with virtual machines.
    """
    def __init__(self, esx_client, raw_virtual_machine):
        super().__init__(esx_client, raw_virtual_machine)
        self.vmware_tools = VMWareTools(self)

    def vmware_tools_execute_process(self, program_path, working_directory,
                                     arguments="", environment_variables=None):
        return self.vmware_tools.\
            execute_process(program_path, working_directory,
                            arguments, environment_variables)

    @property
    def summary(self):
        return self._raw_virtual_machine.summary


class VMWareClient(DefaultVMWareClient):
    def get_virtual_machine(self, name) -> VirtualMachine:
        """
        Nothing is changed. Just redefined the method definition
        to provide correct return value.
        """
        return super().get_virtual_machine(name)

    def get_virtual_machines(self):
        """
        Abolutely the same method but returns VirtualMachine
        objects of the avmwc library.
        """
        for virtual_machine in self._iterate_virtual_machines():
            yield VirtualMachine(self, virtual_machine)

    def __enter__(self):
        super().__enter__()
        return self
