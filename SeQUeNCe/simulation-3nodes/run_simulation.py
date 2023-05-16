import sequence
from numpy import random
from sequence.kernel.timeline import Timeline
from sequence.topology.topology import Topology
from sequence.topology.node import *
import math, sys
import networkx as nx
import matplotlib.pyplot as plt

from sequence.kernel.eventlist import EventList

def run_simulation(max_execution_time, epr_life, gen_success_probability, swap_succ_prob, sim_gen_time, model_gen_time, model_swap_time):

    #max_execution_time = 1000

    def iteration():
        random.seed(0)
        network_config = "../simulation-3nodes/linear-3-node.json"
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
        epr_lifetime = epr_life
        #tl.gen_success_probability = 0.5
        tl.gen_success_probability = gen_success_probability
        # print(gen_success_probability)
        #swap_succ_prob = 0.5
        #sim_swap_gen_time = 0.001
        #model_swap_gen_time = 5
        #sim_gen_time = 0.002
        #model_gen_time = 5
        #model_swap_time = 10
        #unit_time = sim_swap_gen_time/model_swap_gen_time
        unit_time = sim_gen_time/model_gen_time
        #max_execution_time = 30 * unit_time
        epr_lifetime *= unit_time
    

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

        tl.init()
        tl.events = EventList()

        nm = network_topo.nodes[tl.src].network_manager
        nm.request(tl.dst, start_time=3e12, end_time=20e12, memory_size=1, target_fidelity=0.4)
        #nm.request("b", start_time=3e12, end_time=20e12, memory_size=1, target_fidelity=0.6)
        
        try:
            tl.run()
        except SystemExit:
            # print('This Iteration has Failed')
            pass

        is_a_entangled_c, is_c_entangled_a = False,False
        #is_a_entangled_d, is_d_entangled_a = False,False
        #is_a_entangled_b, is_b_entangled_a = False,False
        # print("A memories")
        # print("Index:\tEntangled Node:\tFidelity:\tEntanglement Time:\tState:")
        # for info in network_topo.nodes["a"].resource_manager.memory_manager:
        #     if info.remote_node == 'c' and info.state == 'ENTANGLED':
        #     #if info.remote_node == 'b' and info.state == 'ENTANGLED':
        #         is_a_entangled_c = True
        #         #is_a_entangled_b = True
        #     print("{:6}\t{:15}\t{:9}\t{}\t{}".format(str(info.index), str(info.remote_node),
        #                                         str(info.fidelity), str(info.entangle_time * 1e-12),str(info.state)))
                                                
        # print("B memories")
        # print("Index:\tEntangled Node:\tFidelity:\tEntanglement Time:")
        # for info in network_topo.nodes["b"].resource_manager.memory_manager:
        #     if info.remote_node == 'a' and info.state == 'ENTANGLED':
        #         is_b_entangled_a = True
        #     print("{:6}\t{:15}\t{:9}\t{}\t{}".format(str(info.index), str(info.remote_node),
        #                                         str(info.fidelity), str(info.entangle_time * 1e-12),str(info.state)))                                

        # #print(f'is_a_entangled_b : {is_a_entangled_b}  and is_b_entangled_a: {is_b_entangled_a}')

        
        # print("C memories")
        # print("Index:\tEntangled Node:\tFidelity:\tEntanglement Time:")
        # for info in network_topo.nodes["c"].resource_manager.memory_manager:
        #     if info.remote_node == 'a' and info.state == 'ENTANGLED':
        #         is_c_entangled_a = True
        #     print("{:6}\t{:15}\t{:9}\t{}\t{}".format(str(info.index), str(info.remote_node),
        #                                         str(info.fidelity), str(info.entangle_time * 1e-12),str(info.state)))

        # print("D memories")
        # print("Index:\tEntangled Node:\tFidelity:\tEntanglement Time:\tState:")
        # for info in network_topo.nodes["d"].resource_manager.memory_manager:
        #     if info.remote_node == 'a' and info.state == 'ENTANGLED':
        #         is_d_entangled_a = True
        #     print("{:6}\t{:15}\t{:9}\t{}\t{}".format(str(info.index), str(info.remote_node),
        #                                         str(info.fidelity), str(info.entangle_time * 1e-12),str(info.state)))
        

        # print('---------Decision Paramter Values---------')
        # #print('gen/swap time per operation: ',sim_swap_gen_time)
        # print('max time allowed: ', max_execution_time)
        # print('epr life time: ', epr_lifetime)
        # print('gen_exec_count: ', tl.gen_exec_count)
        # print('swap_exec_count: ', tl.swap_exec_count)
        # print('gen_threshold: ', tl.gen_threshold)
        # print('gen_success_probability: ', tl.gen_success_probability)
        # print('model_gen_time: ', model_gen_time)
        # print('model_swap_time: ', model_swap_time)
        # #print('swap_success_probability: ', tl.gen_success_probability)
        #total_time_taken = sim_swap_gen_time*(sum(map(sum, tl.gen_exec_count))+sum(map(sum,tl.swap_exec_count)))/2
        
        total_time_taken = model_gen_time*sum(map(sum, tl.gen_exec_count))/2 + model_swap_time*sum(map(sum,tl.swap_exec_count))/2

        # print('Total time taken:   ', total_time_taken)

        tl.gen_exec_count = [[0 for i in range(4)] for j in range(4)]
        tl.swap_exec_count = [[0 for i in range(4)] for j in range(4)]

        #print()
        #print('gen_exec_count: ', tl.gen_exec_count)
        #print('swap_exec_count: ', tl.swap_exec_count)

        #if is_a_entangled_c and is_c_entangled_a:
        #if is_a_entangled_b and is_b_entangled_a:
        
        if tl.stop_rules:   #This signifies E2E swap has happened
            if total_time_taken<=max_execution_time:
                # print('True')
                return True, total_time_taken, tl.hasSwapFailed
            else:
                # print('False in max time comparison')
                return False, total_time_taken, tl.hasSwapFailed
            #return True, total_time_taken
        else:
            # print('False in both entangled')
            return False, total_time_taken, tl.hasSwapFailed

    success_count, over_time_limit, swap_failed = 0, 0, 0
    total_trials =2000
    times = {'0'}
    for i in range(total_trials):
        # tl = Timeline(4e12)
        # tl.set_topology(network_topo)
        # tl.gen_threshold = 5
        # tl.gen_success_probability = 0.1
        flag, total_time_taken, hasSwapFailed = iteration()
        times.add(total_time_taken)
        if flag:
            success_count += 1
        if total_time_taken > max_execution_time and not hasSwapFailed:
            over_time_limit += 1
        if hasSwapFailed:
            swap_failed += 1

    # print('------------------------------')
    # print(f'Total Trials:  {total_trials}')
    # print(f'Successful Trials:  {success_count}')
    # print(f'Success probability : {success_count/total_trials}')
    # print(f'over_time_limit:  {over_time_limit}')
    # print(f'swap_failed:  {swap_failed}')
    # print(f'Times: {times}')
    # print('------------------------------')
    print(success_count/total_trials,  end='')

if __name__ == "__main__":
    run_simulation(int(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]), int(sys.argv[7]))
