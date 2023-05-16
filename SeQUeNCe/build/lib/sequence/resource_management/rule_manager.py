"""Definition of rule manager.

This module defines the rule manager, which is used by the resource manager to instantiate and control entanglement protocols.
This is achieved through rules (also defined in this module), which if met define a set of actions to take.
"""
import re
from typing import Callable, TYPE_CHECKING, List, Tuple
if TYPE_CHECKING:
    from ..entanglement_management.entanglement_protocol import EntanglementProtocol
    from .memory_manager import MemoryInfo, MemoryManager
    from .resource_manager import ResourceManager
    from ..network_management.reservation import Reservation


class RuleManager():
    """Class to manage and follow installed rules.

    The RuleManager checks available rules when the state of a memory is updated.
    Rules that are met have their action executed by the rule manager.

    Attributes:
        rules (List[Rules]): List of installed rules.
        resource_manager (ResourceManager): reference to the resource manager using this rule manager.
    """

    def __init__(self):
        """Constructor for rule manager class."""

        self.rules = []
        self.resource_manager = None

    def set_resource_manager(self, resource_manager: "ResourceManager"):
        """Method to set overseeing resource manager.

        Args:
            resource_manager (ResourceManager): resource manager to attach to.
        """

        self.resource_manager = resource_manager

    def load(self, rule: "Rule") -> bool:
        """Method to load rule into ruleset.

        Tries to insert rule into internal `rules` list based on priority.

        Args:
            rule (Rule): rule to insert.

        Returns:
            bool: success of rule insertion.
        """

        # binary search for inserting rule
        ##print('rule manager to load rule for node: ', self.resource_manager.owner.name)
        rule.set_rule_manager(self)
        left, right = 0, len(self.rules) - 1
        while left <= right:
            mid = (left + right) // 2
            if self.rules[mid].priority < rule.priority:
                left = mid + 1
            else:
                right = mid - 1
        self.rules.insert(left, rule)
        return True

    def expire(self, rule: "Rule") -> List["EntanglementProtocol"]:
        """Method to remove expired protocol.

        Args:
            rule (Rule): rule to remove.

        Returns:
            List[EntanglementProtocol]: list of protocols created by rule (if any).
        """

        self.rules.remove(rule)
        return rule.protocols

    def get_memory_manager(self):
        return self.resource_manager.get_memory_manager()

    def send_request(self, protocol, req_dst, req_condition_func):
        return self.resource_manager.send_request(protocol, req_dst, req_condition_func)

    def __len__(self):
        return len(self.rules)

    def __getitem__(self, item):
        return self.rules[item]


class Rule():
    """Definition of rule for the rule manager.

    Rule objects are installed on and interacted with by the rule manager.

    Attributes:
        priority (int): priority of the rule, used as a tiebreaker when conditions of multiple rules are met.
        action (Callable[[List["MemoryInfo"]], Tuple["Protocol", List["str"], List[Callable[["Protocol"], bool]]]]):
            action to take when rule condition is met.
        condition (Callable[["MemoryInfo", "MemoryManager"], List["MemoryInfo"]]): condition required by rule.
        protocols (List[Protocols]): protocols created by rule.
        rule_manager (RuleManager): reference to rule manager object where rule is installed.
    """

    def __init__(self, priority: int,
                 action: Callable[
                     [List["MemoryInfo"]], Tuple["Protocol", List["str"], List[Callable[["Protocol"], bool]]]],
                 condition: Callable[["MemoryInfo", "MemoryManager"], List["MemoryInfo"]]):
        """Constructor for rule class."""

        self.priority = priority
        self.action = action
        self.condition = condition
        self.protocols = []
        self.rule_manager = None
        self.success_count = 0
        self.failure_count = 0
        self.execution_count = 0

    def set_rule_manager(self, rule_manager: "RuleManager") -> None:
        """Method to assign rule to a rule manager.

        Args:
            rule_manager (RuleManager): manager to assign.
        """

        self.rule_manager = rule_manager

    def do(self, memories_info: List["MemoryInfo"]) -> None:
        """Method to perform rule activation and send requirements to other nodes.

        Args:
            memories_info (List[MemoryInfo]): list of memory infos for memories meeting requirements.
        """

        protocol, req_dsts, req_condition_funcs = self.action(memories_info)
        protocol.rule = self
        self.protocols.append(protocol)
        """#print()
        #print()
        #print('Protocol being currently  attached to memory: ', protocol.name)
        #print()
        #print()"""
        #if len(memories_info) > 0 and memories_info[0].state  == 'ENTANGLED':
        #    print('--------------------------------------------')
        for info in memories_info:
            #if info.state == 'ENTANGLED':
            #    print('protocol.name, req_dsts, req_condition_funcs', protocol.name, req_dsts, req_condition_funcs)
            info.memory.detach(info.memory.memory_array)
            info.memory.attach(protocol)
        #if len(memories_info) > 0 and memories_info[0].state  == 'ENTANGLED':
        #    print('--------------------------------------------')

        for dst, req_func in zip(req_dsts, req_condition_funcs):
            self.rule_manager.send_request(protocol, dst, req_func)
        
        #increment execution count
        #self.execution_count += 1
        #print(f'protocol.name : {protocol.name},   execution_count: {self.execution_count}')

    def is_valid(self, memory_info: "MemoryInfo") -> List["MemoryInfo"]:
        """Method to check for memories meeting condition.

        Args:
            memory_info (MemoryInfo): memory info object to test.

        Returns:
            List[memory_info]: list of memory info objects meeting requirements of rule.
        """
        manager = self.rule_manager.get_memory_manager()
        
        """if memory_info.index == 1 and self.rule_manager.resource_manager.owner.name == 'b':
            #print('We are in checking the is_valid for 1st memory of B')"""

        dummy_=self.condition(memory_info, manager)  #----------dummy_ will either be 0 or 2
        """#print(self)
        #print('memory_info is being compared with memory manager for: ', self.rule_manager.resource_manager.owner.name)
        #print('dummy_ size: ', len(dummy_))
        #print('dummy_ begins--------------')
        for info in dummy_:
            #print("{:6}\t{:15}\t{:9}\t{}".format(str(info.index), str(info.remote_node),
                                                     str(info.fidelity), str(info.entangle_time * 1e-12)))
        #print('dummy_ ends--------------')
        #print('memory_info for this rule: --------')
        #print("Index:\tEntangled Node:\tFidelity:\tEntanglement Time:")
        #for info in memory_info:
        #print("{:6}\t{:15}\t{:9}\t{}".format(str(memory_info.index), str(memory_info.remote_node),
                                                 str(memory_info.fidelity), str(memory_info.entangle_time * 1e-12)))

        #print('protocols list size: ', len(self.protocols))
        for pro in self.protocols:
            #p = re.compile('ESA*')
            #if p.match(str(pro.name)):
            #    #print('Ent Swap initiated at B')
            #print(str(pro.name))"""
            
        
        ##print("RETURN FROM RULE MANAGER", self.own.name)
        
        """for pro in self.protocols:
            #print("RETURN FROM RULE MANAGER-protocol name", pro.name)
            #print("RETURN FROM RULE MANAGER-node name", pro.own.name)
            #print("Index Rule:\tEntangled Node:\tFidelity:\tEntanglement Time:")
        
        for info in dummy_:
            #print("{:6}\t{:15}\t{:9}\t{}".format(str(info.index), str(info.remote_node),
                                    str(info.fidelity), str(info.entangle_time * 1e-12)))"""

        #if self.rule_manager.resource_manager.owner.name == 'c' and len(dummy_) == 0:
        #    print('Condition not met at rule for c')
    
        return dummy_

    def set_reservation(self, reservation: "Reservation") -> None:
        self.reservation = reservation

    def get_reservation(self) -> "Reservation":
        return self.reservation
