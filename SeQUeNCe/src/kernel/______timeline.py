"""Definition of main Timeline class.

This module defines the Timeline class, which provides an interface for the simulation kernel and drives event execution.
All entities are required to have an attached timeline for simulation.
"""

from _thread import start_new_thread
from math import inf
from sys import stdout
from time import time_ns, sleep
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .event import Event

from .eventlist import EventList
from ..utils import log
from .quantum_manager import QuantumManagerKet, QuantumManagerDensity

class Timeline:
    """Class for a simulation timeline.

    Timeline holds entities, which are configured before the simulation.
    Before the start of simulation, the timeline must initialize all controlled entities.
    The initialization of entities may schedule events.
    The timeline pushes these events to its event list.
    The timeline starts simulation by popping the top event in the event list repeatedly.
    The time of popped event becomes current simulation time of the timeline.
    The process of popped event is executed.
    The simulation stops if the timestamp on popped event is equal or larger than the stop time, or if the eventlist is empty.

    To monitor the progress of simulation, the Timeline.show_progress attribute can be modified to show/hide a progress bar.

    Attributes:
        events (EventList): the event list of timeline.
        entities (List[Entity]): the entity list of timeline used for initialization.
        time (int): current simulation time (picoseconds).
        stop_time (int): the stop (simulation) time of the simulation.
        schedule_counter (int): the counter of scheduled events
        run_counter (int): the counter of executed events
        is_running (bool): records if the simulation has stopped executing events.
        show_progress (bool): show/hide the progress bar of simulation.
        quantum_manager (QuantumManager): quantum state manager.
    """

    def __init__(self, stop_time=inf, formalism='ket_vector'):
        """Constructor for timeline.

        Args:
            stop_time (int): stop time (in ps) of simulation (default inf).
        """
        self.events = EventList()
        self.entities = []
        self.time = 0
        self.stop_time = stop_time
        self.schedule_counter = 0
        self.run_counter = 0
        self.is_running = False
        self.show_progress = False
        
        if formalism == 'ket_vector':
            self.quantum_manager = QuantumManagerKet()
        elif formalism == 'density_matrix':
            self.quantum_manager = QuantumManagerDensity()
        else:
            raise ValueError("Invalid formalism {}".format(formalism))

    def now(self) -> int:
        """Returns current simulation time."""

        return self.time

    def schedule(self, event: "Event") -> None:
        """Method to schedule an event."""

        self.schedule_counter += 1
        return self.events.push(event)

    def init(self) -> None:
        """Method to initialize all simulated entities."""
        log.logger.info("Timeline initial network")

        for entity in self.entities:
            entity.init()

    def run(self) -> None:
        """Main simulation method.

        The `run` method begins simulation of events.
        Events are continuously popped and executed, until the simulation time limit is reached or events are exhausted.
        A progress bar may also be displayed, if the `show_progress` flag is set.
        """

        #Event counters for virtual links
        j_counter = 0
        d_counter = 0
        d_events_time = []
        i_counter = 0
        i_events_time = []
        g_counter = 0
        h_counter = 0
        a_counter = 0
        b_counter = 0
        c_counter = 0
        k_counter = 0
        l_counter = 0
        type_set={'EMPTY'}
        type_name_set={'EMPTY'}
        d_process_set = {'EMPTY'}
        i_process_set = {'EMPTY'}
        h_process_set = {'EMPTY'}
        d_args_set = []
        i_args_set = []
        h_args_set = []
        d_remote_protocols = []
        h_remote_protocols = []

        log.logger.info("Timeline start simulation")
        tick = time_ns()
        self.is_running = True

        if self.show_progress:
            self.progress_bar()

        # log = {}
        prev_event_d, prev_event_d_time, event_after_d_begin_time = False, 0 , []
        prev_event_i, prev_event_i_time, event_after_i_begin_time = False, 0 , []
        prev_event_g, prev_event_g_time, event_after_g_begin_time = False, 0 , []
        prev_event_c, prev_event_c_time, event_after_c_begin_time = False, 0 , []
        d_event_duration, i_event_duration = [], []
        g_event_duration, c_event_duration = [], []

        count = 0
        while len(self.events) > 0:
            event = self.events.pop()
            if event.time >= self.stop_time:
                self.schedule(event)
                break
            """
            if count in [i for i in range(0, 200)]:
                ##print('Event start time: ', event.time)
                ##print('event.process.owner.name: ', event.process.owner.name)
                try:
                    ##print('type(event.process.act_params[1]).__name__: ', type(event.process.act_params[1]).__name__)
                except:
                    ##print('Exception: ', event.process.act_params)
                #if type(event.process.act_params[1]).__name__ ==  'ResourceManagerMessage':
                #    ##print('remote protocol: ', event.process.act_params[1].ini_protocol.name)
            """
            count += 1
            assert self.time <= event.time, "invalid event time for process scheduled on " + str(event.process.owner)
            if event.is_invalid():
                continue
            self.time = event.time            
            
            if prev_event_d:
            	event_after_d_begin_time.append(event.time)
            	d_event_duration.append(event.time - prev_event_d_time)
            	prev_event_d = False
            	prev_event_d_time = 0

            if prev_event_i:
            	event_after_i_begin_time.append(event.time)
            	i_event_duration.append(event.time - prev_event_i_time)
            	prev_event_i = False
            	prev_event_i_time = 0

            if prev_event_g:
            	event_after_g_begin_time.append(event.time)
            	g_event_duration.append(event.time - prev_event_g_time)
            	prev_event_g = False
            	prev_event_g_time = 0

            if prev_event_c:
            	event_after_c_begin_time.append(event.time)
            	c_event_duration.append(event.time - prev_event_c_time)
            	prev_event_c = False
            	prev_event_c_time = 0

            event_ticker_begin = time_ns()
            if event.time>5e12 and event.time<5.02e12:
            	#if type(event.process.owner) not in type_dict:
            	type_set.add(type(event.process.owner))
            	type_name_set.add(event.process.owner.name)
            	###print('event owner: ', event.process.owner.name)
            	if event.process.owner.name == 'j':
            		j_counter = j_counter+1
            	
            	if event.process.owner.name == 'd':
            		prev_event_d = True
            		prev_event_d_time = event.time
            		d_counter = d_counter+1
            		d_process_set.add(event.process.activation)
            		d_args_set.append([type(event.process.act_params[1]).__name__,
                                        event.process.act_params[1].ini_protocol,
                                        event.process.act_params[1].req_condition_func])
            		#d_args_set.append(event.process.act_params)
            		#if type(event.process.act_params[1]).__name__ ==  'ResourceManagerMessage':
            			##print('d remote protocol: ', event.process.act_params[1].ini_protocol.name)
            		d_events_time.append(event.time)
            		
            	if event.process.owner.name == 'i':
                    prev_event_i = True
                    prev_event_i_time = event.time
                    i_counter = i_counter+1
                    i_process_set.add(event.process.activation)
                    i_args_set.append(type(event.process.act_params[1]).__name__)
                    #if type(event.process.act_params[1]).__name__ ==  'ResourceManagerMessage':
                        ##print('i remote protocol: ', event.process.act_params[1].ini_protocol.name)
                    i_events_time.append(event.time)
            	
            	if event.process.owner.name == 'g':
                    prev_event_g = True
                    prev_event_g_time = event.time
                    g_counter = g_counter+1
                    
                    #i_process_set.add(event.process.activation)
                    #i_args_set.append(type(event.process.act_params[1]).__name__)
                    #if type(event.process.act_params[1]).__name__ ==  'ResourceManagerMessage':
                    #    ##print('i remote protocol: ', event.process.act_params[1].ini_protocol.name)
                    #g_events_time.append(event.time)
            	
            	if event.process.owner.name == 'c':
                    prev_event_c = True
                    prev_event_c_time = event.time
                    c_counter = c_counter+1
                    
                    #i_process_set.add(event.process.activation)
                    #i_args_set.append(type(event.process.act_params[1]).__name__)
                    #if type(event.process.act_params[1]).__name__ ==  'ResourceManagerMessage':
                    #    ##print('i remote protocol: ', event.process.act_params[1].ini_protocol.name)
                    #c_events_time.append(event.time)
            	
            	if event.process.owner.name == 'h':
            		h_counter = h_counter+1
            		h_process_set.add(event.process.activation)
            		h_args_set.append(type(event.process.act_params[1]).__name__)
            		#if type(event.process.act_params[1]).__name__ == 'ResourceManagerMessage':
            			##print('h remote protocol: ', event.process.act_params[1].ini_protocol.name)
            	if event.process.owner.name == 'a':
            		a_counter = a_counter+1
            	if event.process.owner.name == 'b':
            		b_counter = b_counter+1
            	#if event.process.owner.name == 'c':
            	#	c_counter = c_counter+1
            	if event.process.owner.name == 'k':
            		k_counter = k_counter+1
            	if event.process.owner.name == 'l':
            		l_counter = l_counter+1
            	
            # if not event.process.activation in log:
            #     log[event.process.activation] = 0
            # log[event.process.activation]+=1
            ###print('event execution begins at time= ', self.time)
            #if not (event.time>5e12 and event.time<5.4e12 and event.process.owner.name in ['d','i','g','c']):
            event.process.run()
            """event_ticker_end = time_ns()
            if event.time>5e12 and event.time<5.4e12:
            	if event.process.owner.name == 'd':
            		d_events_time.append(event_ticker_end - event_ticker_begin)
            	if event.process.owner.name == 'i':
            		i_events_time.append(event_ticker_end - event_ticker_begin)"""

            self.run_counter += 1

        # ##print('number of event', self.event_counter)
        # ##print('log:',log)

        self.is_running = False
        elapse = time_ns() - tick

        ##print("Timeline end simulation. Execution Time: %d ns; Scheduled Event: %d; Executed Event: %d" %
        #                (elapse, self.schedule_counter, self.run_counter))
        ##print('j_counter: ', j_counter)
        ##print('d_counter: ', d_counter)
        ##print('i_counter: ', i_counter)
        ##print('g_counter: ', g_counter)
        ##print('h_counter: ', h_counter)
        ##print('a_counter: ', a_counter)
        ##print('b_counter: ', b_counter)
        ##print('c_counter: ', c_counter)
        ##print('k_counter: ', k_counter)
        ##print('l_counter: ', l_counter)
        ##print()
        ##print('d_events_time: ', d_events_time)
        ##print()
        ##print()
        ##print('event_after_d_begin_time: ', event_after_d_begin_time)
        ##print()
        ##print()
        ##print('i_events_time: ', i_events_time)
        ##print()
        ##print()
        ##print('event_after_i_begin_time: ', event_after_i_begin_time)
        ##print()
        ##print('type_set: ', type_set)
        ##print('type_name_set: ', type_name_set)
        ##print('d_process_set', d_process_set)
        ##print('i_process_set', i_process_set)
        ###print('h_process_set', h_process_set)
        ##print('d_args_set', d_args_set)
        ###print('h_args_set', h_args_set)
        
        ##print('d_event_duration', d_event_duration)
        ##print('i_event_duration', i_event_duration)
        ##print('g_event_duration', g_event_duration)
        ##print('c_event_duration', c_event_duration)
        ##print('d events sum: ', sum(d_event_duration))
        ##print('i events sum: ', sum(i_event_duration))
        ##print('g events sum: ', sum(g_event_duration))
        ##print('c events sum: ', sum(c_event_duration))
        ##print('d+i+g+c sum: ', (sum(d_event_duration)+sum(i_event_duration)+sum(g_event_duration)+sum(c_event_duration)))

        log.logger.info("Timeline end simulation. Execution Time: %d ns; Scheduled Event: %d; Executed Event: %d" %
                        (elapse, self.schedule_counter, self.run_counter))

    def stop(self) -> None:
        """Method to stop simulation."""
        log.logger.info("Timeline is stopped")
        self.stop_time = self.now()

    def remove_event(self, event: "Event") -> None:
        self.events.remove(event)

    def update_event_time(self, event: "Event", time: int) -> None:
        """Method to change execution time of an event.

        Args:
            event (Event): event to reschedule.
            time (int): new simulation time (should be >= current time).
        """

        self.events.update_event_time(event, time)

    def seed(self, seed: int) -> None:
        """Sets random seed for simulation."""

        from numpy import random
        random.seed(seed)

    def progress_bar(self):
        """Method to draw progress bar.

        Progress bar will display the execution time of simulation, as well as the current simulation time.
        """

        def #print_time():
            start_time = time_ns()
            while self.is_running:
                exe_time = self.ns_to_human_time(time_ns() - start_time)
                sim_time = self.ns_to_human_time(self.time / 1e3)
                if self.stop_time == float('inf'):
                    stop_time = 'NaN'
                else:
                    stop_time = self.ns_to_human_time(self.stop_time / 1e3)
                process_bar = f'\rexecution time: {exe_time};     simulation time: {sim_time} / {stop_time}'
                ###print(f'{process_bar}', end="\r")
                stdout.flush()
                sleep(3)

        start_new_thread(print_time, ())

    def ns_to_human_time(self, nanosec: int) -> str:
        if nanosec >= 1e6:
            ms = nanosec / 1e6
            if ms >= 1e3:
                second = ms / 1e3
                if second >= 60:
                    minute = second // 60
                    second = second % 60
                    if minute >= 60:
                        hour = minute // 60
                        minute = minute % 60
                        return '%d hour: %d min: %.2f sec' % (hour, minute, second)
                    return '%d min: %.2f sec' % (minute, second)
                return '%.2f sec' % (second)
            return "%d ms" % (ms)
        return '0 ms'
