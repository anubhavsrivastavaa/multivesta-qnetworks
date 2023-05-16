import sequence
from numpy import random
from sequence.kernel.timeline import Timeline
from sequence.topology.topology import Topology
from sequence.topology.node import *
import math, sys
import networkx as nx
import matplotlib.pyplot as plt

from sequence.kernel.eventlist import EventList
import json

class SequenceModel:
     
    def __init__(self):
        # #print('--------Object instantiated---------')
        self.tl : Timeline = Timeline(4e12)
        self.topology = None
        self.already_set = False

    def set_simulator_for_new_simulation(self, seed: int):
        # #print('-------setting up simulator for new simulation-------')
        random.seed(seed)
        network_config = "linear-5-node.json"

        self.tl = Timeline(10e12)
        network_topo = Topology("network_topo", self.tl)
        network_topo.load_config(network_config)
        self.tl.set_topology(network_topo)
        self.tl.gen_threshold = 100

        self.tl.src, self.tl.dst = "a", "c"
        # self.tl.src, self.tl.dst = "a", "d"
        self.tl.swap_schedule = {'b':['a','c']}
        # self.tl.swap_schedule = {'b':['a','c'], 'c':['a','d']}
        # self.tl.swap_schedule = {'b':['a','c'], 'd':['c','e'], 'c':['a','e']}
        # self.tl.swap_schedule = {'b':['a','c'], 'c':['a','d'], 'd':['a','e']}

        #Testing a-b-c-d with hetergenous nodes
        # self.tl.swap_schedule = {'b':['a','c'], 'c':['a','d']}
        # self.tl.swap_schedule = {'b':['a','d'], 'c':['b','d']}
        # self.tl.src, self.tl.dst = "a", "d"

        configuration = json.load(open('config.json'))
        max_execution_time = 10
        # epr_lifetime = 0.01   #Usual value
        epr_lifetime = float(configuration['LIFE_TIME'])
        #print(f'lifetime: {epr_lifetime}')

        self.tl.gen_success_probability = 0.5
        swap_succ_prob = 0.5

        # #For retrials experiment
        # memory_lifetime = {'a': 0.010, 'b': 0.010, 'c': 0.008, 'd':0.005, 'e':0.005}
        # self.tl.gen_success_probability = 0.8
        # swap_succ_prob = 1
        # self.tl.src, self.tl.dst = "a", "e"
        # self.tl.swap_schedule = {'b':['a','c'], 'd':['c','e'], 'c':['a','e']}

        # #For comparing with different swap schedule:
        # memory_lifetime = {'a': 0.010, 'b': 0.010, 'c': 0.010, 'd':0.010, 'e':0.010}
        # self.tl.swap_schedule = {'b':['a','c'], 'd':['c','e'], 'c':['a','e']}
        # # self.tl.swap_schedule = {'b':['a','c'], 'c':['a','d'], 'd':['a','e']}

        # #For comparing with different swap schedule:
        # # self.tl.swap_schedule = {'b':['a','e'], 'c':['b','e'], 'd':['c','e']}
        
        def set_parameters(topology: Topology):
                # set memory parameters
                MEMO_FREQ = 2e3
                #MEMO_EXPIRE = 10 #inf ---- 1e-3..... starts at 0s, final entanglement at 0.4s (for a line graph )
                MEMO_EXPIRE = epr_lifetime
                MEMO_EFFICIENCY = 1
                MEMO_FIDELITY = 0.9349367588934053
                #MEMO_FIDELITY = 0.99
                for node in topology.get_nodes_by_type("QuantumRouter"):
                    node.memory_array.update_memory_params("frequency", MEMO_FREQ)
                    node.memory_array.update_memory_params("coherence_time", MEMO_EXPIRE)
                    # #Changes made to simulate heterogenous networks
                    # if node.name != 'c':
                    #     node.memory_array.update_memory_params("coherence_time", MEMO_EXPIRE)
                    # else:
                    #     node.memory_array.update_memory_params("coherence_time", 0.005)
                    
                    node.memory_array.update_memory_params("efficiency", MEMO_EFFICIENCY)
                    node.memory_array.update_memory_params("raw_fidelity", MEMO_FIDELITY)

                # #For retrials experiment
                # for node in topology.get_nodes_by_type("QuantumRouter"): 
                #     node.memory_array.update_memory_params("coherence_time", memory_lifetime[node.name])

                # set detector parameters
                #DETECTOR_EFFICIENCY = 0.9
                DETECTOR_EFFICIENCY = 0.99
                DETECTOR_COUNT_RATE = 5e7
                DETECTOR_RESOLUTION = 100
                for node in topology.get_nodes_by_type("BSMNode"):
                    node.bsm.update_detectors_params("efficiency", DETECTOR_EFFICIENCY)
                    node.bsm.update_detectors_params("count_rate", DETECTOR_COUNT_RATE)
                    node.bsm.update_detectors_params("time_resolution", DETECTOR_RESOLUTION)
                    
                # set entanglement swapping parameters
                #SWAP_SUCC_PROB = 0.95
                SWAP_SUCC_PROB = swap_succ_prob
                #SWAP_SUCC_PROB = 0.99
                #SWAP_SUCC_PROB = 0.95
                
                #SWAP_DEGRADATION = 0.99
                #SWAP_DEGRADATION = 1
                SWAP_DEGRADATION = 0.99
                
                for node in topology.get_nodes_by_type("QuantumRouter"):
                    node.network_manager.protocol_stack[1].set_swapping_success_rate(SWAP_SUCC_PROB)
                    node.network_manager.protocol_stack[1].set_swapping_degradation(SWAP_DEGRADATION)
                    
                # set quantum channel parameters
                ATTENUATION = 1e-5
                #ATTENUATION = 1e-10
                #ATTENUATION = 1e-8
                #ATTENUATION = attenuation
                QC_FREQ = 1e11
                for qc in topology.qchannels:
                    qc.attenuation = ATTENUATION
                    qc.frequency = QC_FREQ

        set_parameters(network_topo)

        self.tl.init()
        self.tl.events = EventList()

        nm = network_topo.nodes[self.tl.src].network_manager
        nm.request(self.tl.dst, start_time=1e12, end_time=20e12, memory_size=1, target_fidelity=0.4)
        #print('-------simulator set up for new simulation-------')
        # tl.run()
        self.topology = network_topo
    
    def one_step(self) -> None:
        #print(f'---Performing one simulation step')
        self.tl.run_step()
        return 0

    def run(self) -> None:
        #print('---Running Simulation----')
        self.tl.run()
        #print(self.tl.stop_rules)
        return 0

    def get_time(self) -> float:
        # #print(f'---Getting Time: {self.tl.time*0.000000000001} ----')
        return self.tl.time*0.000000000001

    def is_simulation_completed(self) -> int:
        return int(self.tl.has_completed)
    
    def a_c_entangled(self) -> int:
        return self.tl.stop_rules
    
    def a_c_time(self) -> float:
        return sum(map(sum, self.tl.gen_exec_count))/2 + sum(map(sum, self.tl.swap_exec_count))/2
    
    def entangled(self, node1, node2, args = []) -> float:
        #print(f'---checking if {node1} and {node2} are entangled at simulator time:{self.tl.time*0.000000000001}')
        #print(f'self.tl.entanglement_time: {self.tl.entanglement_time}')
        #print(f'self.tl.gen_exec_count: {self.tl.gen_exec_count}')
        return (node1+'-'+node2 in self.tl.entanglement_time.keys()) or (node2+'-'+node1 in self.tl.entanglement_time.keys())
        # if len(args) == 0:
        #     #print(f'---checking if {node1} and {node2} are entangled at simulator time:{self.tl.time*0.000000000001}')
        #     #if any memory is entangled -> return true
        #     for mem in self.tl.topology.nodes[node1].memory_array.memories:
        #         if mem.entangled_memory['node_id'] == node2:
        #             return True
        # else:
        #     #Check if all the memories in args are entangled
        #     pass
        # return False
    
    def entanglement_time(self, node1, node2, args = []) -> float:
        key = node1+'-'+node2
        #print(f'self.tl.entanglement_time: {self.tl.entanglement_time}')
        #print(f'self.tl.gen_exec_count: {self.tl.gen_exec_count}')
        if key in self.tl.entanglement_time.keys():
            return self.tl.entanglement_time[key]
        return -1

    def get_swap_order(self):
        #print(f'swap_order: {self.tl.swap_order}')
        return self.tl.swap_order

    def all_mem_life_above(self, lifetime):
        for node_obj in self.topology.get_nodes_by_type('QuantumRouter'):
            mem_0_lifetime = node_obj.memory_array.memories[0].coherence_time
            if mem_0_lifetime != -1 and mem_0_lifetime < lifetime:
                return False
        return True
    
    def swap_failed(self):
        # #print(f'---swap_failed---: {self.tl.hasSwapFailed}')
        return float(self.tl.hasSwapFailed)
    
    def retrial_count(self, node1, node2):
        #print(f'self.tl.gen_exec_count: {self.tl.gen_exec_count}')
        return self.tl.gen_exec_count[ord(node1)-ord('a')][ord(node2)-ord('a')]

    def fidelity(self, node1, node2):
        for node_obj in self.topology.get_nodes_by_type('QuantumRouter'):
            mem_0_lifetime = node_obj.memory_array.memories[0].coherence_time
            if mem_0_lifetime != -1 and mem_0_lifetime < lifetime:
                return False
        return True
    # #Not clear how to integrate this with multivesta
    # def set_swap_schedule(self, schedule):
    #     self.tl.swap_schedule = schedule
    
    # #Doesn't work
    # def set_memo_lifetime(self, lifetime):
    #     #print('entered set_memo')
    #     if not self.already_set:
    #         #print(f'setting coherence time to: {lifetime}')
    #         for node in self.topology.get_nodes_by_type("QuantumRouter"):
    #             node.memory_array.update_memory_params("coherence_time", lifetime)
    #         self.already_set = True
    #     return True
            



