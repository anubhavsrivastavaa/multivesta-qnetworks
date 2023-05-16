# -*- coding: utf-8 -*-


import sys
from py4j.java_gateway import JavaGateway, GatewayParameters, CallbackServerParameters

#Here you should replace 'model_file_name' with the name of the .py file containing your model (without .py)
import sequence_model
import logging

class SimulationWrapper(object):

	# constructor for Python
	def __init__(self, model):
		self.model: sequence_model.SequenceModel = model

	# code to let multivesta initialize the simulator for a new simulation
	# that is, re-initialize the model to its initial state, and set the
	# new random seed
	def setSimulatorForNewSimulation(self, random_seed):
		print('setSimulatorForNewSimulation')
		self.model.set_simulator_for_new_simulation(random_seed)	

	# code to let multivesta ask the simulator to perform a step of simulation
	def performOneStepOfSimulation(self):
		print('onestep')
		self.model.one_step()

	# code to let multivesta ask the simulator to perform a
	# "whole simulation"
	# (i.e., until a stopping condition is found by the simulator)
	def performWholeSimulation(self):
		print('whole')
		self.model.run()

	# code to let multivesta ask the simulator the current simulated time
	def getTime(self):
		return float(self.model.get_time())


	# code to let multivesta ask the simulator to return the value of the
	# specified observation in the current state of the simulation
	def rval(self, observation):
		if type(observation) == int:
			if observation == 3:
				ret_val = self.model.is_simulation_completed()
				print('--- Is simulation complete: ', ret_val)
				return float(ret_val)
			if observation == 4:	#checks if the entanglement between a and c is complete
				ret_val = self.model.a_c_entangled()
				print('--- self.model.a_c_entangled(): ', ret_val)
				return float(ret_val)
			elif observation == 5:  #a_c entanglement time
				return float(self.model.entanglement_time())
		elif type(observation) == str:
			observation = observation.replace(' ', '')
			# print(observation)
			task, args = observation.split(':')
			# print(f'Task: {task} and Args: {args}')
			if task == "Entangled":
				node1, node2 = args[1:-1].split(',')
				ret_val = self.model.entangled(node1, node2)
				print(f'--- {node1} and {node2} entanglement status-> {ret_val}')
				return float(ret_val)
			elif task == "MEM_LIFETIME":
				lifetime = int(args.strip())
				ret_val = self.model.all_mem_life_above(lifetime)
				return float(ret_val)
			elif task == "SWAP_FAILED":
				return self.model.swap_failed()
			elif task == "RETRIALS":
				node1, node2 = args[1:-1].split(',')
				ret_val = self.model.retrial_count(node1, node2)
				print(f'--- {node1} and {node2} retrials count-> {ret_val}')
				return float(ret_val)
			elif task == "FIDELITY":
				node1, node2 = args[1:-1].split(',')
				ret_val = self.model.fidelity(node1, node2)
				print(f'--- {node1} and {node2} fidelity-> {ret_val}')
				return float(ret_val)
		

	class Java:
		implements = ['vesta.python.IPythonSimulatorWrapper']


if __name__ == '__main__':
	print('\n--------------------------')
	print('Entered Python Integartion')
	print('--------------------------')
	print(sys.argv)
	porta = int(sys.argv[1])
	callback_porta = int(sys.argv[2])
	print('Python engine: expecting connection with java on port: '+str(porta)+' and callback connection on port '+str(callback_porta))
	gateway = JavaGateway(start_callback_server=True,gateway_parameters=GatewayParameters(port=porta),callback_server_parameters=CallbackServerParameters(port=callback_porta))
	
	# logger = logging.getLogger("py4j")
	# logger.setLevel(logging.DEBUG)
	# logger.addHandler(logging.StreamHandler())
	# gateway.jvm.py4j.GatewayServer.turnLoggingOn()

	#Here you should put any initialization code you need to create an instance of
	#your model_file_name class
	
	model=sequence_model.SequenceModel()
	gateway.entry_point.playWithState(SimulationWrapper(model))