* Integration of the simulator with multivesta through model(sequence_model.py) and MV_wrapper files
* Exposed tl.time, tl.is_a_c_entangled, tl.has_completed variables
* Corrected query by using # for recursion


* Removing the computation of is_a_c_entangled from the simulator to the query by exposing the entanglement status variables of all memories at nodes -> multi-parameter function calls?
e.g. rval(3, 'a', 'c')-> 3 stands for is_entangled and 'a', 'c' are the nodes whose entanglement status we're querying (a solution proposed below)

We also need iterators to iterate over all the memories so that we can check if any is entangled

-> Starting from a simple example of entanglement status of a and c

To query complicated stuff we can use the following format:
"TASK : (arg1, arg2,..., argN)" where the number and type of arguments can be fixed according to task and parsed by python wrapper

example: "Entangled: (a, c)" -> Are these two nodes entangled?
         "Entanglement_status: (a, [0, 1, 2 ..])" -> Are these memory indices at node entangled
         "Entangled_with: (a, c, MEM_INDEX or List[MEM_INDEXES])" -> are these memory indexes at 'a' entangled with 'c'?
         "Fidelity: " (a, MEM_INDEX)" -> fidelity of the memories at Node 'a'

We can also replace TASK with integer codes and enums

* Made some changes to timeline's time updation -> If all further events are after the simulator stop time, no next event can be executed therefore just update the current time of the simulator with the stop time. This allows us to query for all times without multivesta being stuck in infinite loop 




-----> 31 mar
topology of 5-10 nodes, we want to evaulate different routing protocols