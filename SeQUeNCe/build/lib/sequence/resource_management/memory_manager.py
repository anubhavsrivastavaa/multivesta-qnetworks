"""Definition of Memory Manager.

This module provides a definition for the memory manager, which tracks the state of memories on a node.
There are three states of quantum memory represented by the string: "RAW", "OCCUPIED", "ENTANGLED".

* "RAW" denotes a free memory that is not entangling with other memories.
* "OCCUPIED" denotes a memory that is allocated to protocols or applications.
* "ENTANGLED" denotes a free memory that is entangling with other memories. 

This is done through instances of the MemoryInfo class, which track a single memory.
"""

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .resource_manager import ResourceManager
    from ..components.memory import Memory, MemoryArray


class MemoryManager():
    """Class to manage a node's memories.

    The memory manager tracks the entanglement state of a node's memories, along with other information (such as fidelity).

    Attributes:
        memory_array (MemoryArray): memory array object to be tracked.
        memory_map (List[MemoryInfo]): array of memory info objects corresponding to memory array.
        resource_manager (ResourceManager): resource manager object using the memory manager.
    """

    def __init__(self, memory_array: "MemoryArray"):
        """Constructor for memory manager.

        Args:
            memory_array (MemoryArray): memory array to monitor and manage.
        """

        self.memory_array = memory_array
        self.memory_array.attach(self)
        self.memory_map = [MemoryInfo(memory, index) for index, memory in enumerate(self.memory_array)]
        self.resource_manager = None

    def set_resource_manager(self, resource_manager: "ResourceManager") -> None:
        """Method to set the resource manager."""

        self.resource_manager = resource_manager

    def update(self, memory: "Memory", state: str) -> None:
        """Method to update the state of a memory.

        Modifies the memory info object corresponding to the memory.

        Args:
            memory (Memory): memory to update.
            state (str): new state for memory.
        """

        info = self.get_info_by_memory(memory)
        if state == "RAW":
            info.to_raw()
        elif state == "OCCUPIED":
            info.to_occupied()
        elif state == "ENTANGLED":
            ##print(f'To entangled called for the memory index {info.index} at the node {self.resource_manager.owner.name}')
            info.to_entangled()
        else:
            raise Exception("Unknown state '%s'" % state)

    def __len__(self):
        return len(self.memory_map)

    def __getitem__(self, item: int) -> "MemoryInfo":
        return self.memory_map[item]

    def get_info_by_memory(self, memory: "Memory") -> "MemoryInfo":
        """Gets memory info object for a desired memory."""

        index = self.memory_array.memories.index(memory)
        return self.memory_map[index]


class MemoryInfo():
    """Class to track memory information parameters for memory manager.

    The memory info class chiefly tracks a memory's entanglement state, in one of 3 allowed states:
    
    * RAW: Memory is unprocessed
    * OCCUPIED: Memory is occupied by some protocol
    * ENTANGLED: Memory has been successfully entangled

    The class additionally tracks other memory parameters and properties.

    Attributes:
        memory (Memory): specific memory being tracked.
        index (int): index of memory in memory array.
        state (str): state of memory.
        remote_node (str): name of node holding entangled memory.
        remote_memo (int): index of entangled memory on remote node.
        fidelity (int): fidelity of entanglement for memory.
        expire_event (Event): expiration event for the memory.
        entangle_time (int): time at which most recent entanglement is achieved.
    """

    def __init__(self, memory: "Memory", index: int, state="RAW"):
        """Constructor for memory info class.

        Args:
            memory (Memory): memory to monitor.
            index (int): index of memory in the corresponding memory array.
            state (str): state of memory to be monitored (default "RAW").
        """

        self.memory = memory
        self.index = index
        self.state = state
        self.remote_node = None
        self.remote_memo = None
        self.fidelity = 0
        self.expire_event = None
        self.entangle_time = -1

    def to_raw(self) -> None:
        """Method to set memory to raw (unentangled) state."""

        self.state = "RAW"
        self.memory.reset()
        self.remote_node = None
        self.remote_memo = None
        self.fidelity = 0
        self.entangle_time = -1

    def to_occupied(self) -> None:
        """Method to set memory to occupied state."""

        #assert self.state != "OCCUPIED"
        #if virtual link and protocol is "entanglement swap" and state=="ENTANGLED" and isfirstreq, call toentangled 
        #else info.to_occupied()
        #self.

        """if self.memory.memory_array.owner.name == 'd': #and self.remote_node == 'a':
            #print(f'Reached the to_occupied for d and entanglement to created for memory index: {self.index}')"""
        self.state = "OCCUPIED"
        self.entangle_time = self.memory.timeline.now() #Remove after testing

    def to_entangled(self) -> None:
        """Method to set memory to entangled state."""
        # print(f'entanglement link to be created with: {self.memory.entangled_memory["node_id"]}')
        
        # print('self.memory.memory_array.owner:   ', self.memory.memory_array.owner)
        """if self.memory.memory_array.owner.name == 'd': #and self.remote_node == 'a':
            #print(f'Reached the to_entangled for d and entanglement to created for memory index: {self.index}')"""
        self.state = "ENTANGLED"
        self.remote_node = self.memory.entangled_memory["node_id"]
        self.remote_memo = self.memory.entangled_memory["memo_id"]
        self.fidelity = self.memory.fidelity
        #print(f'Entanglement generated between: {self.memory.owner.name} and {self.remote_node}')
        #print(f'Time of entanglement creation: ', self.memory.timeline.now())
        #print('Number of events run before this Entanglement: ', self.memory.timeline.run_counter)
        self.entangle_time = self.memory.timeline.now()
