"""Definition of Routing protocol.

This module defines the StaticRouting protocol, which uses a pre-generated static routing table to direct reservation hops.
Routing tables may be created manually, or generated and installed automatically by the `Topology` class.
Also included is the message type used by the routing protocol.
"""

from enum import Enum
from typing import Dict, TYPE_CHECKING
if TYPE_CHECKING:
    from ..topology.node import Node 


from ..message import Message
from ..protocol import StackProtocol
from .reservation import RSVPMsgType
import json
import math

class StaticRoutingMessage(Message):
    """Message used for communications between routing protocol instances.

    Attributes:
        msg_type (Enum): type of message, required by base `Message` class.
        receiver (str): name of destination protocol instance.
        payload (Message): message to be delivered to destination.
    """
    
    def __init__(self, msg_type: Enum, receiver: str, payload: "Message"):
        super().__init__(msg_type, receiver)
        self.payload = payload


class StaticRoutingProtocol(StackProtocol):
    """Class to route reservation requests.

    The `StaticRoutingProtocol` class uses a static routing table to direct the flow of reservation requests.
    This is usually defined based on the shortest quantum channel length.

    Attributes:
        own (Node): node that protocol instance is attached to.
        name (str): label for protocol instance.
        forwarding_table (Dict[str, str]): mapping of destination node names to name of node for next hop.
    """
    
    def __init__(self, own: "Node", name: str, forwarding_table: Dict):
        """Constructor for routing protocol.

        Args:
            own (Node): node protocol is attached to.
            name (str): name of protocol instance.
            forwarding_table (Dict[str, str]): forwarding routing table in format {name of destination node: name of next node}.
        """

        super().__init__(own, name)
        self.forwarding_table = forwarding_table

    def add_forwarding_rule(self, dst: str, next_node: str):
        """Adds mapping {dst: next_node} to forwarding table."""

        assert dst not in self.forwarding_table
        self.forwarding_table[dst] = next_node
        ##print('----------Next Hop-------------', next_node)

    def update_forwarding_rule(self, dst: str, next_node: str):
        """updates dst to map to next_node in forwarding table."""

        self.forwarding_table[dst] = next_node
        ##print('----------Next Hop-------------', next_node)

    def push(self, dst: str, msg: "Message"):
        """Method to receive message from upper protocols.

        Routing packages the message and forwards it to the next node in the optimal path (determined by the forwarding table).

        Args:
            dst (str): name of destination node.
            msg (Message): message to relay.

        Side Effects:
            Will invoke `push` method of lower protocol or network manager.
        """

        #Compute the next hop here using our logic
        #Pick the best possible nieghbor according to physical distance



        assert dst != self.own.name


        ##print('(dst, self.own.name) -----', (dst, self.own.name))
        #-----------#print(self.own.all_pair_shortest_dist)
        #dst = self.forwarding_table[dst]

        visited = []

        #If section will run during forward propagation
        if msg.msg_type != RSVPMsgType.APPROVE: 
            ##print('Message Info : ----------', msg.msg_type) 
            ##print('Inside Routing --------------------qcaps---------------- ', msg.qcaps[-1].node)
            ##print('type(Message) : ----------', type(msg))
                  #msg.reservation.memory_size is the demand size
            visited = [qcap.node for qcap in msg.qcaps]

            dst =  self.custom_next_best_hop(self.own.name, dst, msg.reservation.memory_size, visited)

        #Else section will run during backward propagation
        else:
            #print('path: ', msg.path)
            #Return the prevous node of current node 
            curr_ele_index = msg.path.index(self.own.name)
            ##print('Back routing phase: Next node  is ----', msg.path[curr_ele_index-1])
            dst = msg.path[curr_ele_index-1]        

        
        new_msg = StaticRoutingMessage(Enum, self.name, msg)
        
        ##print('--------------self.own.name------------', self.own.name)
        ##print('--------------dst------------', dst)
        self._push(dst=dst, msg=new_msg)

    #--------------------------------------------------
    def custom_next_best_hop(self, curr_node, dest, demand, visited):
        print('----Routing')
        #if curr_node == dest:
        #    return dest

        if (curr_node == 'm' and dest == 'l') or (curr_node == 'm' and dest == 'g'):
            return 'h'

        is_next_virtual = True
        all_pair_path = self.own.all_pair_shortest_dist
        neighbors = self.own.neighbors
        
        virtual_neighbors = self.own.find_virtual_neighbors()
        #if curr_node == 'h':
        #    #print('virtual_neighbors: ', virtual_neighbors)

        nodewise_dest_distance = all_pair_path[dest]
        nodewise_dest_distance = json.loads(json.dumps(nodewise_dest_distance))

        ##print('Demand: --------------- ', demand)
    
        
        #Greedy Step:
        #Pick the virtual neighbor that is closest to the destination
    
        least_dist = math.inf
        best_hop = None
        ##print('Current Node: ', curr_node)
        for node in nodewise_dest_distance:
            ##print((node,neighbor_dict[node]))
            if (node in virtual_neighbors.keys()) or (node in neighbors):
                ##print('Virtual neighbor found: ', node)
                dist = nodewise_dest_distance[node]
                if dist < least_dist:
                    best_hop = node
                    least_dist = dist

        """if best_hop != None:
            #print('virtual_neighbors[best_hop] --------------- ', virtual_neighbors[best_hop])"""
        #If such a virtual neighbor does not exist or cannot satisfy our demands then pick 
        #the best physical neighbor and generate entanglements through it
        #Or if we pick an already traversed neighbor
        
        ##print('Visited ----------------------', visited)
        best_hop_virtual_link_size = 0
        if best_hop in virtual_neighbors:
            best_hop_virtual_link_size = virtual_neighbors[best_hop]

        if best_hop == None or  best_hop_virtual_link_size < demand or ( best_hop in visited):
            is_next_virtual = False
            least_dist = math.inf
            best_hop = None
            
            """#print('Dist Matrix for destination node(',dest,') :  ')
            #print(nodewise_dest_distance)
            #print('Neighbors of current node(',curr_node,'):  ', neighbors)"""
            for node in nodewise_dest_distance:
                ##print((node,neighbor_dict[node]))
                if node in neighbors:
                    dist = nodewise_dest_distance[node]
                    if dist < least_dist:
                        best_hop = node
                        least_dist = dist


        
        ##print()
        ##print('---------Next Hop Calculation using Modified Greedy------------')
        ##print('Curr Node: ', curr_node,', picked neighbor: ', best_hop, ', distance b/w picked neighbor and destination ', least_dist)
        
        """#print('Virtual Neighbors of current node: ', self.own.find_virtual_neighbors())
        #print('---------------------------------------------------------------')
        #print()"""


        return best_hop
    #--------------------------------------------------

    def pop(self, src: str, msg: "StaticRoutingMessage"):
        """Message to receive reservation messages.

        Messages are forwarded to the upper protocol.

        Args:
            src (str): node sending the message.
            msg (StaticRoutingMessage): message received.

        Side Effects:
            Will call `pop` method of higher protocol.
        """

        self._pop(src=src, msg=msg.payload)

    def received_message(self, src: str, msg: "Message"):
        """Method to directly receive messages from node (should not be used)."""

        raise Exception("RSVP protocol should not call this function")

    def init(self):
        pass
