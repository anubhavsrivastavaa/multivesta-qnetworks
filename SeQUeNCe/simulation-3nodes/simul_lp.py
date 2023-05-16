import sequence
from numpy import random
from sequence.kernel.timeline import Timeline
from sequence.topology.topology import Topology
from sequence.topology.node import *
import math, sys
import networkx as nx
import matplotlib.pyplot as plt

from sequence.kernel.eventlist import EventList

random.seed(0)
network_config = "linear-3-node.json"
# network_config = "../example/linear-4-node.json"
# network_config = "../example/linear-2-node.json"

tl = Timeline(4e12)
network_topo = Topology("network_topo", tl)
network_topo.load_config(network_config)
tl.set_topology(network_topo)
tl.gen_threshold = 100

tl.src, tl.dst = "a", "c"
# tl.src, tl.dst = "a", "d"
#max_execution_time = 50
#epr_lifetime = 15   #Need to look into this
# epr_lifetime = epr_life
#tl.gen_success_probability = 0.5
tl.gen_success_probability = 0.9
tl.swap_schedule = {'b':['a','c']}
# print(gen_success_probability)
#swap_succ_prob = 0.5
#sim_swap_gen_time = 0.001
#model_swap_gen_time = 5
#sim_gen_time = 0.002
#model_gen_time = 5
#model_swap_time = 10
#unit_time = sim_swap_gen_time/model_swap_gen_time
# unit_time = sim_gen_time/model_gen_time
# #max_execution_time = 30 * unit_time
# epr_lifetime *= unit_time


def set_parameters(topology: Topology):
    # set memory parameters
    MEMO_FREQ = 2e3
    #MEMO_EXPIRE = 10 #inf ---- 1e-3..... starts at 0s, final entanglement at 0.4s (for a line graph )
    MEMO_EXPIRE = 10
    MEMO_EFFICIENCY = 1
    MEMO_FIDELITY = 0.9349367588934053
    #MEMO_FIDELITY = 0.99
    for node in topology.get_nodes_by_type("QuantumRouter"):
        node.memory_array.update_memory_params("frequency", MEMO_FREQ)
        node.memory_array.update_memory_params("coherence_time", MEMO_EXPIRE)
        node.memory_array.update_memory_params("efficiency", MEMO_EFFICIENCY)
        node.memory_array.update_memory_params("raw_fidelity", MEMO_FIDELITY)

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
    SWAP_SUCC_PROB = 0.99
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

tl.init()
tl.events = EventList()

nm = network_topo.nodes[tl.src].network_manager
nm.request("c", start_time=3e12, end_time=20e12, memory_size=5, target_fidelity=0.4)
#nm.request("b", start_time=3e12, end_time=20e12, memory_size=1, target_fidelity=0.6)

tl.run()

print("A memories")
print("Index:\tEntangled Node:\tFidelity:\tEntanglement Time:\tState:")
for info in network_topo.nodes["a"].resource_manager.memory_manager:
    print("{:6}\t{:15}\t{:9}\t{}\t{}".format(str(info.index), str(info.remote_node),
                                         str(info.fidelity), str(info.entangle_time * 1e-12),str(info.state)))
                                        
print("B memories")
print("Index:\tEntangled Node:\tFidelity:\tEntanglement Time:")
for info in network_topo.nodes["b"].resource_manager.memory_manager:
    print("{:6}\t{:15}\t{:9}\t{}".format(str(info.index), str(info.remote_node),
                                         str(info.fidelity), str(info.entangle_time * 1e-12)))                                

print("C memories")
print("Index:\tEntangled Node:\tFidelity:\tEntanglement Time:")
for info in network_topo.nodes["c"].resource_manager.memory_manager:
    print("{:6}\t{:15}\t{:9}\t{}".format(str(info.index), str(info.remote_node),
                                         str(info.fidelity), str(info.entangle_time * 1e-12)))