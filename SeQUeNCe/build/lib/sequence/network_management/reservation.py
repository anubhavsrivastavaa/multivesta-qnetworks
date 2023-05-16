"""Definition of Reservation protocol and related tools.

This module provides a definition for the reservation protocol used by the network manager.
This includes the Reservation, MemoryTimeCard, and QCap classes, which are used by the network manager to track reservations.
Also included is the definition of the message type used by the reservation protocol.
"""

from enum import Enum, auto
from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from ..topology.node import QuantumRouter
    from ..resource_management.memory_manager import MemoryInfo, MemoryManager

from ..resource_management.rule_manager import Rule
from ..entanglement_management.generation import EntanglementGenerationA
from ..entanglement_management.purification import BBPSSW
from ..entanglement_management.swapping import EntanglementSwappingA, EntanglementSwappingB
from ..message import Message
from ..protocol import StackProtocol
from ..kernel.event import Event
from ..kernel.process import Process
import copy


class RSVPMsgType(Enum):
    """Defines possible message types for the reservation protocol."""

    REQUEST = auto()
    REJECT = auto()
    APPROVE = auto()


class ResourceReservationMessage(Message):
    """Message used by resource reservation protocol.

    This message contains all information passed between reservation protocol instances.
    Messages of different types contain different information.

    Attributes:
        msg_type (GenerationMsgType): defines the message type.
        receiver (str): name of destination protocol instance.
        reservation (Reservation): reservation object relayed between nodes.
        qcaps (List[QCaps]): cumulative quantum capacity object list (if `msg_type == REQUEST`)
        path (List[str]): cumulative node list for entanglement path (if `msg_type == APPROVE`)
    """

    def __init__(self, msg_type: any, receiver: str, reservation: "Reservation", **kwargs):
        Message.__init__(self, msg_type, receiver)
        self.reservation = reservation
        if self.msg_type is RSVPMsgType.REQUEST:
            self.qcaps = []
        elif self.msg_type is RSVPMsgType.REJECT:
            pass
        elif self.msg_type is RSVPMsgType.APPROVE:
            self.path = kwargs["path"]
        else:
            raise Exception("Unknown type of message")

    def __str__(self):
        return "ResourceReservationProtocol: \n\ttype=%s, \n\treservation=%s" % (self.msg_type, self.reservation)


class ResourceReservationProtocol(StackProtocol):
    """ReservationProtocol for  node resources.

    The reservation protocol receives network entanglement requests and attempts to reserve local resources.
    If successful, it will forward the request to another node in the entanglement path and create local rules.
    These rules are passed to the node's resource manager.
    If unsuccessful, the protocol will notify the network manager of failure.

    Attributes:
        own (QuantumRouter): node that protocol instance is attached to.
        name (str): label for protocol instance.
        timecards (List[MemoryTimeCard]): list of reservation cards for all memories on node.
        es_succ_prob (float): sets `success_probability` of `EntanglementSwappingA` protocols created by rules.
        es_degredation (float): sets `degredation` of `EntanglementSwappingA` protocols created by rules.
        accepted_reservation (List[Reservation]): list of all approved reservation requests.
    """

    def __init__(self, own: "QuantumRouter", name: str):
        """Constructor for the reservation protocol class.

        Args:
            own (QuantumRouter): node to attach protocol to.
            name (str): label for reservation protocol instance.
        """

        super().__init__(own, name)
        self.timecards = [MemoryTimeCard(i) for i in range(len(own.memory_array))]
        self.es_succ_prob = 1
        self.es_degradation = 0.95
        self.accepted_reservation = []

    def push(self, responder: str, start_time: int, end_time: int, memory_size: int, target_fidelity: float, isvirtual:bool):
        """Method to receive reservation requests from higher level protocol.

        Will evaluate request and determine if node can meet it.
        If it can, it will push the request down to a lower protocol.
        Otherwise, it will pop the request back up.

        Args:
            responder (str): node that entanglement is requested with.
            start_time (int): simulation time at which entanglement should start.
            end_time (int): simulation time at which entanglement should cease.
            memory_size (int): number of memories to be entangled.
            target_fidelity (float): desired fidelity of entanglement.

        Side Effects:
            May push/pop to lower/upper attached protocols (or network manager).
        """

        reservation = Reservation(self.own.name, responder, start_time, end_time, memory_size, target_fidelity, isvirtual)
        ##print(self.own.name)
        ##print(responder)
        if self.schedule(reservation):
            msg = ResourceReservationMessage(RSVPMsgType.REQUEST, self.name, reservation)
            qcap = QCap(self.own.name)
            msg.qcaps.append(qcap)
            ##print('--------------------push called ---------------- ', self.own.name)
            self._push(dst=responder, msg=msg)
        else:
            msg = ResourceReservationMessage(RSVPMsgType.REJECT, self.name, reservation)
            self._pop(msg=msg)

    def pop(self, src: str, msg: "ResourceReservationMessage"):
        """Method to receive messages from lower protocols.

        Messages may be of 3 types, causing different network manager behavior:

        1. REQUEST: requests are evaluated, and forwarded along the path if accepted. Otherwise a REJECT message is sent back.
        2. REJECT: any reserved resources are released and the message forwarded back towards the initializer.
        3. APPROVE: rules are created to achieve the approved request. The message is forwarded back towards the initializer.

        Args:
            src (str): source node of the message.
            msg (ResourceReservationMessage): message received.
        
        Side Effects:
            May push/pop to lower/upper attached protocols (or network manager).
        """
        ##print('--------------------pop called ---------------- ', self.own.name)
        if msg.msg_type == RSVPMsgType.REQUEST:
            assert self.own.timeline.now() < msg.reservation.start_time
            if self.schedule(msg.reservation):
                qcap = QCap(self.own.name)
                msg.qcaps.append(qcap)
                if self.own.name == msg.reservation.responder:
                    path = [qcap.node for qcap in msg.qcaps]
                    rules = self.create_rules(path, reservation=msg.reservation)
                    self.load_rules(rules, msg.reservation)
                    new_msg = ResourceReservationMessage(RSVPMsgType.APPROVE, self.name, msg.reservation, path=path)
                    self._pop(msg=msg)
                    self._push(dst=msg.reservation.initiator, msg=new_msg)
                else:
                    self._push(dst=msg.reservation.responder, msg=msg)
            else:
                new_msg = ResourceReservationMessage(RSVPMsgType.REJECT, self.name, msg.reservation)
                self._push(dst=msg.reservation.initiator, msg=new_msg)
        elif msg.msg_type == RSVPMsgType.REJECT:
            for card in self.timecards:
                card.remove(msg.reservation)
            if msg.reservation.initiator == self.own.name:
                self._pop(msg=msg)
            else:
                self._push(dst=msg.reservation.initiator, msg=msg)
        elif msg.msg_type == RSVPMsgType.APPROVE:
            rules = self.create_rules(msg.path, msg.reservation)
            self.load_rules(rules, msg.reservation)
            if msg.reservation.initiator == self.own.name:
                self._pop(msg=msg)
            else:
                self._push(dst=msg.reservation.initiator, msg=msg)
        else:
            raise Exception("Unknown type of message", msg.msg_type)

    def schedule(self, reservation: "Reservation") -> bool:
        """Method to attempt reservation request.

        Args:
            reservation (Reservation): reservation to approve or reject.

        Returns:
            bool: if reservation can be met or not.
        """

        if self.own.name in [reservation.initiator, reservation.responder]:
            counter = reservation.memory_size
        else:
            counter = reservation.memory_size * 2
        cards = []
        
        ##print('###########Adding Reservation#############')
        ##print('Node: ', self.own.name)
        for card in self.timecards:            
        #   #print('Card for memory id: ', card.memory_index)
            condition, isCardVirtual = card.add(reservation)
            if (not isCardVirtual) and condition:
                counter -= 1
                cards.append(card)
            if counter == 0:
                break

        if counter > 0:
            for card in cards:
                card.remove(reservation)
            return False

        return True

    def create_rules(self, path: List[str], reservation: "Reservation") -> List["Rule"]:
        """Method to create rules for a successful request.

        Rules are used to direct the flow of information/entanglement in the resource manager.

        Args:
            path (List[str]): list of node names in entanglement path.
            reservation (Reservation): approved reservation.

        Returns:
            List[Rule]: list of rules created by the method.
        """

        rules = []

        self.own.resource_manager.rule_manager.rules = []
        #print(f'Rules for this node: {self.own.name} are {len(self.own.resource_manager.rule_manager.rules)}')
        memory_indices = []
        virtual_indices = []
        memory_indices_occupied = []
        last_virtual_index = -1

        for card in self.timecards:
            if reservation in card.reservations:
                memory_indices.append(card.memory_index)
                #To maintain the virtual link indices 
                if card.has_virtual_reservation() and not reservation.isvirtual:
                    virtual_indices.append(card.memory_index)
                    if card.memory_index > last_virtual_index:
                        last_virtual_index= card.memory_index

        ##print('last_virtual_index', last_virtual_index)        

        # create rules for entanglement generation
        index = path.index(self.own.name)
        if index > 0:
            #To generate entanglement with left side node
            #To accept virtual links, we skip the generation step when a non physical neighbor is found
            if path[index - 1] in self.own.neighbors:
                ##print("###",self.own.name)
                #This will run for all nodes barring starting node
                def eg_rule_condition(memory_info: "MemoryInfo", manager: "MemoryManager"):
                    
                    # """
                    #     #########################################################
                    #     Adding special condition to ensure a-c happens before c-d
                    #     #########################################################
                    # """
                    # # if self.own.name == 'd' and path[index - 1] == 'c':
                    # #     print('Trying to generate ENT b/w d and c')

                    # if self.own.name == 'd' and path[index - 1] == 'c' and self.own.timeline.swap_success_count[2][0] == 0: #and self.own.timeline.swap_success_count[2][0] == 0):
                    #     # print('d-c generation can only begin once a-c swap is over')
                    #     return []                
                    
                    
                    """if manager.resource_manager.owner.name == 'd' and memory_info.index == 1:
                        #print('EG for node: ', manager.resource_manager.owner.name)
                        #print('memory_info.state ', memory_info.state)
                        #print('memory_info.index: ', memory_info.index)
                        #print('memory_indices[last_virtual_index + 1 : last_virtual_index + reservation.memory_size + 1]: ', memory_indices[last_virtual_index + 1 : last_virtual_index + reservation.memory_size + 1])
                        #print('reservation.memory_size', reservation.memory_size)
                    """
                    #memory_list = memory_indices[:reservation.memory_size]
                    #if index < len(path) - 1 and path[index + 1] not in self.own.neighbors:
                    #    memory_list.append(reservation.memory_size)                    

                    #memories_indices_free = [x for x in memory_indices if x not in virtual_indices]

                    #if memory_info.state == "RAW" and memory_info.index in memory_indices[:reservation.memory_size]:
                    #begin, end = last_virtual_index + 1 , (last_virtual_index+1) + reservation.memory_size
                    if memory_info.state == "RAW" and memory_info.index in memory_indices[last_virtual_index + 1 : last_virtual_index + reservation.memory_size + 1]:
                        #Check for node B's memory
                        """#print('self.own.name here is : ', self.own.name)
                        if self.own.name == 'd':
                            #print(f'In rule condition for Entanglement Generation  at node e for d')
                            #print('memory_info.index: ', memory_info.index)
                            #print('memory_info.state: ', memory_info.state)
                            #print('memory_info.remote_node: ', memory_info.remote_node)
                        """
                        return [memory_info]
                    else:
                        return []

                def eg_rule_action(memories_info: List["MemoryInfo"]):
                    memories = [info.memory for info in memories_info]
                    memory = memories[0]
                    mid = self.own.map_to_middle_node[path[index - 1]]
                    ##print('---------EntanglementGenerationA----------for pair: ', (self.own.name, path[index - 1]))
                    ##print('---------Middle node for this----------', mid)
                    protocol = EntanglementGenerationA(None, "EGA." + memory.name, mid, path[index - 1], memory)
                    return [protocol, [None], [None]]
                

                rule = Rule(10, eg_rule_action, eg_rule_condition)
                rules.append(rule)

            #memory_indices_occupied.append(memories_indices_free)
            
        if index < len(path) - 1:
            #To generate entanglement with right side node
            #To accept virtual links, we skip the generation step when a non physical neighbor is found
            if path[index + 1] in self.own.neighbors:
                #Starting node
                if index == 0:
                    def eg_rule_condition(memory_info: "MemoryInfo", manager: "MemoryManager"):
                        if memory_info.state == "RAW" and memory_info.index in memory_indices:
                            return [memory_info]
                        else:
                            return []
                #second to second last node
                else:
                    def eg_rule_condition(memory_info: "MemoryInfo", manager: "MemoryManager"):
                        
                        """
                            #########################################################
                            Adding special condition to ensure a-c happens before c-d
                            #########################################################
                        """
                        """if self.own.name == 'c':
                            print('At c executing some rules')

                        if self.own.name == 'c' and path[index + 1] == 'd':
                            print('Trying to generate ENT b/w c and d')
                            #print('swap_success_count: ', self.own.timeline.swap_success_count)"""
                        
                        # if self.own.name == 'c' and path[index + 1] == 'd' and self.own.timeline.swap_success_count[2][0] == 0: #and self.own.timeline.swap_success_count[2][0] == 0):
                        #     # print('c-d generation can only begin once a-c swap is over')
                        #     return []
                        
                        """if self.own.name == 'c' and path[index + 1] == 'd':
                            print(f'In rule condition for Entanglement Generation  at node d for e')
                            print('memory_info.index: ', memory_info.index)
                            print('memory_info.state: ', memory_info.state)
                            print('memory_info.remote_node: ', memory_info.remote_node)
                            print('last_virtual_index, reservation.memory_size: ',last_virtual_index, reservation.memory_size)
                            print('acceptable indexes: ', memory_indices[last_virtual_index + reservation.memory_size:])
                        """

                        #if memory_info.state == "RAW" and memory_info.index in memory_indices[reservation.memory_size:]:
                        if memory_info.state == "RAW" and memory_info.index in memory_indices[(last_virtual_index+1) + reservation.memory_size:]:
                            #Check for node B's memory
                            """#print('self.own.name here is : ', self.own.name)
                        
                            #print(f'In rule condition for Entanglement Generation  at node {self.own.name}')
                            #print('memory_info.index: ', memory_info.index)
                            #print('memory_info.state: ', memory_info.state)
                            #print('memory_info.remote_node: ', memory_info.remote_node)
                            """

                            #if self.own.name == 'c' and path[index + 1] == 'd':
                            #    print('memory found at c to generate entanglement with d')
                            
                            return [memory_info]
                        else:
                            return []

                def eg_rule_action(memories_info: List["MemoryInfo"]):
                    def req_func(protocols):
                        for protocol in protocols:
                            if isinstance(protocol,
                                          EntanglementGenerationA) and protocol.other == self.own.name and protocol.rule.get_reservation() == reservation:
                                return protocol

                    memories = [info.memory for info in memories_info]
                    memory = memories[0]
                    #memory = memories[-1]
                    mid = self.own.map_to_middle_node[path[index + 1]]
                    ##print('---------EntanglementGenerationA----------for pair: ', (self.own.name, path[index + 1]))
                    ##print('---------Middle node for this---------- ', mid)
                    protocol = EntanglementGenerationA(None, "EGA." + memory.name, mid, path[index + 1], memory)
                    return [protocol, [path[index + 1]], [req_func]]
                ##print('---------EntanglementGenerationA----------for pair: ', (self.own.name, path[index + 1]))
                rule = Rule(10, eg_rule_action, eg_rule_condition)
                rules.append(rule)

        ##print(f'For {self.own.name}: --- len(rules): {len(rules)}')


        # # create rules for entanglement purification
        # if index > 0:
        #     def ep_rule_condition(memory_info: "MemoryInfo", manager: "MemoryManager"):
        #         #if (memory_info.index in memory_indices[:reservation.memory_size]
        #         if (memory_info.index in memory_indices[last_virtual_index + 1 : last_virtual_index + reservation.memory_size + 1]
        #                 and memory_info.state == "ENTANGLED" and memory_info.fidelity < reservation.fidelity):
        #             for info in manager:
        #                 #if (info != memory_info and info.index in memory_indices[:reservation.memory_size]
        #                 if (info != memory_info and info.index in memory_indices[last_virtual_index + 1 : last_virtual_index + reservation.memory_size + 1]
        #                         and info.state == "ENTANGLED" and info.remote_node == memory_info.remote_node
        #                         and info.fidelity == memory_info.fidelity):
        #                     assert memory_info.remote_memo != info.remote_memo
        #                     return [memory_info, info]
        #         return []

        #     def ep_rule_action(memories_info: List["MemoryInfo"]):
        #         memories = [info.memory for info in memories_info]

        #         def req_func(protocols):
        #             _protocols = []
        #             for protocol in protocols:
        #                 if not isinstance(protocol, BBPSSW):
        #                     continue

        #                 if protocol.kept_memo.name == memories_info[0].remote_memo:
        #                     _protocols.insert(0, protocol)
        #                 if protocol.kept_memo.name == memories_info[1].remote_memo:
        #                     _protocols.insert(1, protocol)

        #             if len(_protocols) != 2:
        #                 return None

        #             protocols.remove(_protocols[1])
        #             _protocols[1].rule.protocols.remove(_protocols[1])
        #             _protocols[1].kept_memo.detach(_protocols[1])
        #             _protocols[0].meas_memo = _protocols[1].kept_memo
        #             _protocols[0].memories = [_protocols[0].kept_memo, _protocols[0].meas_memo]
        #             _protocols[0].name = _protocols[0].name + "." + _protocols[0].meas_memo.name
        #             _protocols[0].meas_memo.attach(_protocols[0])
        #             _protocols[0].t0 = _protocols[0].kept_memo.timeline.now()

        #             return _protocols[0]

        #         name = "EP.%s.%s" % (memories[0].name, memories[1].name)
        #         protocol = BBPSSW(None, name, memories[0], memories[1])
        #         dsts = [memories_info[0].remote_node]
        #         req_funcs = [req_func]
        #         return protocol, dsts, req_funcs

        #     rule = Rule(10, ep_rule_action, ep_rule_condition)
        #     rules.append(rule)

        # if index < len(path) - 1:
        #     if index == 0:
        #         def ep_rule_condition(memory_info: "MemoryInfo", manager: "MemoryManager"):
        #             if (memory_info.index in memory_indices
        #                     and memory_info.state == "ENTANGLED" and memory_info.fidelity < reservation.fidelity):
        #                 return [memory_info]
        #             return []
        #     else:
        #         def ep_rule_condition(memory_info: "MemoryInfo", manager: "MemoryManager"):
        #             if (memory_info.index in memory_indices[reservation.memory_size:]
        #             #if (memory_info.index in memory_indices[last_virtual_index + reservation.memory_size:]
        #                     and memory_info.state == "ENTANGLED" and memory_info.fidelity < reservation.fidelity):
        #                 return [memory_info]
        #             return []

        #     def ep_rule_action(memories_info: List["MemoryInfo"]):
        #         memories = [info.memory for info in memories_info]
        #         name = "EP.%s" % (memories[0].name)
        #         protocol = BBPSSW(None, name, memories[0], None)
        #         return protocol, [None], [None]

        #     rule = Rule(10, ep_rule_action, ep_rule_condition)
        #     rules.append(rule)

        # create rules for entanglement swapping
        def es_rule_actionB(memories_info: List["MemoryInfo"]):
            memories = [info.memory for info in memories_info]
            memory = memories[0]
            protocol = EntanglementSwappingB(None, "ESB." + memory.name, memory)
            return [protocol, [None], [None]]

        if index == 0:
            def es_rule_condition(memory_info: "MemoryInfo", manager: "MemoryManager"):
                if (memory_info.state == "ENTANGLED"
                        and memory_info.index in memory_indices
                        and memory_info.remote_node != path[-1]
                        #and memory_info.remote_node == path[index+1]
                        and memory_info.fidelity >= reservation.fidelity):                
                    return [memory_info]
                else:
                    return []

            rule = Rule(10, es_rule_actionB, es_rule_condition)
            rules.append(rule)

        elif index == len(path) - 1:
            def es_rule_condition(memory_info: "MemoryInfo", manager: "MemoryManager"):
                if (memory_info.state == "ENTANGLED"
                        and memory_info.index in memory_indices
                        and memory_info.remote_node != path[0]
                        #and memory_info.remote_node == path[index-1]
                        and memory_info.fidelity >= reservation.fidelity):
                    return [memory_info]
                else:
                    return []

            rule = Rule(10, es_rule_actionB, es_rule_condition)
            rules.append(rule)

        else:
            if self.own.timeline.swap_order == None:
                print('Computing Swap Order fo this request')
                swap_order = {}
                for p in path[1:-1]:
                    _path_ = copy.deepcopy(path)
                    while _path_.index(p) % 2 == 0:
                        _new_path = []
                        for i, n in enumerate(_path_):
                            if i % 2 == 0 or i == len(_path_) - 1:
                                _new_path.append(n)
                        _path_ = _new_path
                    swap_order[p] = len(_path_)
                swap_ls = [k for k, v in sorted(swap_order.items(), key=lambda item: item[1], reverse=True)]
                print(f'computed swap order: {swap_ls}')
                self.own.timeline.swap_order = swap_ls            
            
            # _path = path[:]
            # while _path.index(self.own.name) % 2 == 0:
            #     new_path = []
            #     for i, n in enumerate(_path):
            #         if i % 2 == 0 or i == len(_path) - 1:
            #             new_path.append(n)
            #     _path = new_path
            # _index = _path.index(self.own.name)
            # left, right = _path[_index - 1], _path[_index + 1]
            print(f'node: {self.own.name}')
            left, right = self.own.timeline.swap_schedule[self.own.name]

            def es_rule_conditionA(memory_info: "MemoryInfo", manager: "MemoryManager"):
                if (memory_info.state == "ENTANGLED"
                        and memory_info.index in memory_indices
                        and memory_info.remote_node == left
                        and memory_info.fidelity >= reservation.fidelity):
                    for info in manager:
                        if (info.state == "ENTANGLED"
                                and info.index in memory_indices
                                and info.remote_node == right
                                and info.fidelity >= reservation.fidelity):     
                            return [memory_info, info]
                    
                if (memory_info.state == "ENTANGLED"
                      and memory_info.index in memory_indices
                      and memory_info.remote_node == right
                      and memory_info.fidelity >= reservation.fidelity):
                    for info in manager:
                        if (info.state == "ENTANGLED"
                                and info.index in memory_indices
                                and info.remote_node == left
                                and info.fidelity >= reservation.fidelity):
                            return [memory_info, info]
                return []

            def es_rule_actionA(memories_info: List["MemoryInfo"]):
                memories = [info.memory for info in memories_info]

                def req_func1(protocols):
                    for protocol in protocols:
                        if (isinstance(protocol, EntanglementSwappingB)
                                and protocol.memory.name == memories_info[0].remote_memo):
                            return protocol

                def req_func2(protocols):
                    for protocol in protocols:
                        if (isinstance(protocol, EntanglementSwappingB)
                                and protocol.memory.name == memories_info[1].remote_memo):
                            return protocol

                protocol = EntanglementSwappingA(None, "ESA.%s.%s" % (memories[0].name, memories[1].name),
                                                 memories[0], memories[1],
                                                 success_prob=self.es_succ_prob, degradation=self.es_degradation)
                dsts = [info.remote_node for info in memories_info]
                req_funcs = [req_func1, req_func2]
                return protocol, dsts, req_funcs
            rule = Rule(10, es_rule_actionA, es_rule_conditionA)
            rules.append(rule)

            def es_rule_conditionB(memory_info: "MemoryInfo", manager: "MemoryManager") -> List["MemoryInfo"]:
                if (memory_info.state == "ENTANGLED"
                        and memory_info.index in memory_indices
                        and memory_info.remote_node not in [left, right]
                        and memory_info.fidelity >= reservation.fidelity):
                    return [memory_info]

                else:
                    return []
            
            rule = Rule(10, es_rule_actionB, es_rule_conditionB)
            rules.append(rule)

        for rule in rules:
            rule.set_reservation(reservation)

        return rules

    def load_rules(self, rules: List["Rule"], reservation: "Reservation") -> None:
        """Method to add created rules to resource manager.

        This method will schedule the resource manager to load all rules at the reservation start time.
        The rules will be set to expire at the reservation end time.

        Args:
            rules (List[Rules]): rules to add.
            reservation (Reservation): reservation that created the rules.
        """

        self.accepted_reservation.append(reservation)
        for card in self.timecards:

            if reservation in card.reservations:
                #if self.own.name == 'b' and card.memory_index == 0:
                #    #print ('Memory 0 in b is in this reservation')
                process = Process(self.own.resource_manager, "update",
                                  [None, self.own.memory_array[card.memory_index], "RAW"])
                event = Event(reservation.end_time, process, 1)
                self.own.timeline.schedule(event)

        for rule in rules:
            #if self.own.name == 'b':
            #    #print('number protocols for this rule: ', len(rule.protocols))
            process = Process(self.own.resource_manager, "load", [rule])
            event = Event(reservation.start_time, process)
            self.own.timeline.schedule(event)
            process = Process(self.own.resource_manager, "expire", [rule])
            event = Event(reservation.end_time, process, 0)
            self.own.timeline.schedule(event)

    def received_message(self, src, msg):
        """Method to receive messages directly (should not be used; receive through network manager)."""

        raise Exception("RSVP protocol should not call this function")

    def set_swapping_success_rate(self, prob: float) -> None:
        assert 0 <= prob <= 1
        self.es_succ_prob = prob

    def set_swapping_degradation(self, degradation: float) -> None:
        assert 0 <= degradation <= 1
        self.es_degradation = degradation


class Reservation():
    """Tracking of reservation parameters for the network manager.

    Attributes:
        initiator (str): name of the node that created the reservation request.
        responder (str): name of distant node with witch entanglement is requested.
        start_time (int): simulation time at which entanglement should be attempted.
        end_time (int): simulation time at which resources may be released.
        memory_size (int): number of entangled memory pairs requested.
    """

    def __init__(self, initiator: str, responder: str, start_time: int, end_time: int, memory_size: int,
                 fidelity: float, isvirtual:bool):#$$
        """Constructor for the reservation class.

        Args:
            initiator (str): node initiating the request.
            responder (str): node with which entanglement is requested.
            start_time (int): simulation start time of entanglement.
            end_time (int): simulation end time of entanglement.
            memory_size (int): number of entangled memories requested.
            fidelity (float): desired fidelity of entanglement.
        """

        self.initiator = initiator
        self.responder = responder
        self.start_time = start_time
        self.end_time = end_time
        self.memory_size = memory_size
        self.fidelity = fidelity
        self.isvirtual=isvirtual#$$
        assert self.start_time < self.end_time
        assert self.memory_size > 0

    def __str__(self):
        return "Reservation: initiator=%s, responder=%s, start_time=%d, end_time=%d, memory_size=%d, target_fidelity=%.2f" % (
            self.initiator, self.responder, self.start_time, self.end_time, self.memory_size, self.fidelity, self.isvirtual)#$$Not sure if need to add in return stmt


class MemoryTimeCard():
    """Class for tracking reservations on a specific memory.

    Attributes:
        memory_index (int): index of memory being tracked (in memory array).
        reservations (List[Reservation]): list of reservations for the memory.
    """

    def __init__(self, memory_index: int):
        """Constructor for time card class.

        Args:
            memory_index (int): index of memory to track.
        """

        self.memory_index = memory_index
        self.reservations = []

    def has_virtual_reservation(self):
        for res in self.reservations:
            if res.isvirtual:
                return True
        return False

    def add(self, reservation: "Reservation") -> bool:
        """Method to add reservation.

        Will use `schedule_reservation` method to determine index to insert reservation.

        Args:
            reservation (Reservation): reservation to add.

        Returns:
            bool: whether or not reservation was inserted successfully.
        """
        
        ##print('Trying to add reservation to this card with memory index: ', self.memory_index)
        pos, isCardVirtual = self.schedule_reservation(reservation)
        if pos >= 0:
            ##print('Reservation addition successful for this card')
            self.reservations.insert(pos, reservation)
            return True, isCardVirtual
        else:
            ##print('Reservation addition successful for this card')
            return False, isCardVirtual
        #self.reservations.insert(len(self.reservations), reservation)
        #return True
        """else:
            #print('Reservation addition failed to this card')
            return False"""
        
    def remove(self, reservation: "Reservation") -> bool:
        """Method to remove a reservation.

        Args:
            reservation (Reservation): reservation to remove.

        Returns:
            bool: if reservation was already on the memory or not.
        """

        try:
            pos = self.reservations.index(reservation)
            self.reservations.pop(pos)
            return True
        except ValueError:
            return False

    def schedule_reservation(self, resv: "Reservation") -> int:
        """Method to add reservation to a memory.

        Will return index at which reservation can be inserted into memory reservation list.
        If no space found for reservation, will raise an exception.

        

        Args:
            resv (Reservation): reservation to schedule.

        Returns:
            int: index to insert reservation in reservation list.

        Raises:
            Exception: no valid index to insert reservation.
        """
        isCardVirtual = False
        physical_reservations=[]
        for res in self.reservations:
            if res.isvirtual:#$ or self.reservation.isvirtual
                isCardVirtual = True
                pass
            else:
                physical_reservations.append(res)
        start, end = 0, len(physical_reservations) - 1
        for res in physical_reservations:
            while start <= end:
                mid = (start + end) // 2
                if physical_reservations[mid].start_time > res.end_time:
                    end = mid - 1
                elif physical_reservations[mid].end_time < res.start_time:
                    start = mid + 1
                elif max(physical_reservations[mid].start_time, res.start_time) <= min(physical_reservations[mid].end_time,
                                                                                    res.end_time):
                    return -1, isCardVirtual
                else:
                    raise Exception("Unexpected status")
        return start, isCardVirtual

        #$Previous code below for your reference
        """
        start, end = 0, len(self.reservations) - 1
        while start <= end:
            mid = (start + end) // 2
            if self.reservations[mid].start_time > resv.end_time:
                end = mid - 1
            elif self.reservations[mid].end_time < resv.start_time:
                start = mid + 1
            elif max(self.reservations[mid].start_time, resv.start_time) <= min(self.reservations[mid].end_time,
                                                                                resv.end_time):
                return -1
            else:
                raise Exception("Unexpected status")
        return start
        """


class QCap():
    """Class to collect local information for the reservation protocol

    Attributes:
        node (str): name of current node.
    """

    def __init__(self, node: str):
        self.node = node
